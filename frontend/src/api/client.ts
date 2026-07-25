import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { clearAccessToken, getAccessToken, setAccessToken } from '@/services/tokenStore';
import type { ApiErrorBody, TokenResponse } from '@/types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  // Required for the httpOnly refresh cookie to be sent cross-origin.
  withCredentials: true,
  timeout: 60_000,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * A normalised error the UI can always render.
 *
 * Every failure — API error, network drop, timeout — arrives here in the same
 * three-part shape, so no component ever has to guess what to display.
 */
export class ApiError extends Error {
  readonly code: string;
  readonly what: string;
  readonly why: string;
  readonly nextStep: string;
  readonly status: number;
  readonly fields: Record<string, string>;
  readonly requestId: string | undefined;

  constructor(init: {
    code: string;
    what: string;
    why: string;
    nextStep: string;
    status: number;
    fields?: Record<string, string>;
    requestId?: string;
  }) {
    super(init.what);
    this.name = 'ApiError';
    this.code = init.code;
    this.what = init.what;
    this.why = init.why;
    this.nextStep = init.nextStep;
    this.status = init.status;
    this.fields = init.fields ?? {};
    this.requestId = init.requestId;
  }
}

const NETWORK_ERROR = new ApiError({
  code: 'NETWORK_ERROR',
  what: 'We could not reach the server.',
  why: 'Your connection may have dropped, or the service may be starting up.',
  nextStep:
    'Check your internet connection and try again. Free hosting tiers sleep when idle, so the first request can take up to 30 seconds.',
  status: 0,
});

const TIMEOUT_ERROR = new ApiError({
  code: 'TIMEOUT',
  what: 'The request took too long.',
  why: 'The server may be waking up, or the analysis may be unusually large.',
  nextStep: 'Wait a few seconds and try again.',
  status: 0,
});

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>;
    if (axiosError.code === 'ECONNABORTED') return TIMEOUT_ERROR;
    if (!axiosError.response) return NETWORK_ERROR;

    const body = axiosError.response.data;
    if (body?.error) {
      return new ApiError({
        code: body.error.code,
        what: body.error.what,
        why: body.error.why,
        nextStep: body.error.next_step,
        status: axiosError.response.status,
        fields: body.error.fields,
        requestId: body.error.request_id,
      });
    }

    return new ApiError({
      code: 'UNEXPECTED_RESPONSE',
      what: 'The server returned an unexpected response.',
      why: 'This is a fault in the service, not in anything you did.',
      nextStep: 'Try again in a moment.',
      status: axiosError.response.status,
    });
  }

  return new ApiError({
    code: 'UNKNOWN_ERROR',
    what: 'Something went wrong.',
    why: 'An unexpected problem occurred in the browser.',
    nextStep: 'Reload the page and try again.',
    status: 0,
  });
}

// --- Silent refresh --------------------------------------------------------
// A 401 with code TOKEN_EXPIRED is recoverable: swap the expired access token
// for a new one using the refresh cookie and replay the original request. Any
// other 401 means the session is genuinely over.

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

let refreshInFlight: Promise<string | null> | null = null;
let onSessionLost: (() => void) | null = null;

export function setSessionLostHandler(handler: (() => void) | null): void {
  onSessionLost = handler;
}

async function refreshAccessToken(): Promise<string | null> {
  // Concurrent 401s must trigger one refresh, not one per request.
  refreshInFlight ??= axios
    .post<TokenResponse>(`${BASE_URL}/auth/refresh`, null, { withCredentials: true })
    .then((response) => {
      setAccessToken(response.data.access_token);
      return response.data.access_token;
    })
    .catch(() => {
      clearAccessToken();
      return null;
    })
    .finally(() => {
      refreshInFlight = null;
    });

  return refreshInFlight;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const config = error.config as RetriableConfig | undefined;
    const code = error.response?.data?.error?.code;
    const isRefreshCall = config?.url?.includes('/auth/refresh');

    if (
      error.response?.status === 401 &&
      code === 'TOKEN_EXPIRED' &&
      config &&
      !config._retried &&
      !isRefreshCall
    ) {
      config._retried = true;
      const token = await refreshAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        return apiClient.request(config);
      }
      onSessionLost?.();
    }

    return Promise.reject(toApiError(error));
  },
);

export { refreshAccessToken };
