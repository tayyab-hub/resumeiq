import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { AuthProvider } from '@/hooks/useAuth';
import { useAuth } from '@/hooks/authContext';
import { authApi } from '@/api/auth';
import { apiClient, restoreSession, setSessionLostHandler } from '@/api/client';
import { clearAccessToken, getAccessToken, setAccessToken } from '@/services/tokenStore';
import type { TokenResponse, User } from '@/types';
import { ProfilePage } from '@/pages/ProfilePage';
import { LoginPage } from '@/pages/LoginPage';

const userA = {
  id: 'a',
  email: 'a@example.com',
  full_name: 'Fictional A',
  created_at: '2026-10-15',
  is_active: true,
} as User;
const userB = { ...userA, id: 'b', email: 'b@example.com', full_name: 'Fictional B' };
const token = (user: User) =>
  ({ access_token: 'fictional-token-' + user.id, token_type: 'bearer', user }) as TokenResponse;
const originalAdapter = apiClient.defaults.adapter;
afterEach(() => {
  vi.restoreAllMocks();
  clearAccessToken();
  setSessionLostHandler(null);
  apiClient.defaults.adapter = originalAdapter;
});

function SessionControls() {
  const auth = useAuth();
  return (
    <>
      <span>{auth.user?.full_name ?? 'Signed out'}</span>
      <button onClick={() => void auth.logout()}>Logout</button>
      <button onClick={() => void auth.login('b@example.com', 'FictionalPassword2026!')}>
        Login B
      </button>
    </>
  );
}

describe('Browser session privacy', () => {
  it('ends the current session after a successful password change and explains the next step', async () => {
    vi.spyOn(axios, 'post').mockResolvedValue({ data: token(userA) });
    const change = vi.spyOn(authApi, 'changePassword').mockResolvedValue(undefined);
    const client = new QueryClient();
    client.setQueryData(['dashboard-stats'], { total: 1 });
    render(
      <QueryClientProvider client={client}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/profile']}>
            <Routes>
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/login" element={<LoginPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByLabelText(/Full name/)).toHaveValue('Fictional A'));
    await userEvent.type(screen.getByLabelText(/^Current password/), 'FictionalOld2026!');
    await userEvent.type(screen.getByLabelText(/^New password/), 'FictionalNew2026!');
    await userEvent.type(screen.getByLabelText(/^Confirm new password/), 'FictionalNew2026!');
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }));
    await screen.findByRole('heading', { name: 'Sign in to ResumeIQ' });
    expect(screen.getByText(/All sessions have ended/)).toBeInTheDocument();
    expect(change).toHaveBeenCalledWith('FictionalOld2026!', 'FictionalNew2026!');
    expect(getAccessToken()).toBeNull();
    expect(client.getQueryData(['dashboard-stats'])).toBeUndefined();
  });
  it('removes cached reports and cancels old queries before another account signs in', async () => {
    vi.spyOn(axios, 'post').mockResolvedValue({ data: token(userA) });
    vi.spyOn(authApi, 'logout').mockResolvedValue(undefined);
    vi.spyOn(authApi, 'login').mockResolvedValue(token(userB));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <AuthProvider>
          <SessionControls />
        </AuthProvider>
      </QueryClientProvider>,
    );
    await screen.findByText('Fictional A');
    client.setQueryData(['analyses', 1, 10], { items: [{ title: 'A private report' }] });
    let oldSignal: AbortSignal | undefined;
    let finishOld!: (value: string) => void;
    const oldRequest = client
      .fetchQuery({
        queryKey: ['analysis', 'a-private-id'],
        queryFn: ({ signal }) => {
          oldSignal = signal;
          return new Promise<string>((resolve) => {
            finishOld = resolve;
          });
        },
      })
      .catch(() => undefined);
    await userEvent.click(screen.getByRole('button', { name: 'Logout' }));
    await screen.findByText('Signed out');
    await userEvent.click(screen.getByRole('button', { name: 'Login B' }));
    await screen.findByText('Fictional B');
    await act(async () => {
      finishOld('A late private result');
      await oldRequest;
    });
    expect(client.getQueryData(['analyses', 1, 10])).toBeUndefined();
    expect(client.getQueryData(['analysis', 'a-private-id'])).toBeUndefined();
    expect(oldSignal?.aborted).toBe(true);
  });
});

function rejectWith(code: string, config: InternalAxiosRequestConfig) {
  return Promise.reject(
    new AxiosError('Fictional API error', 'ERR_BAD_REQUEST', config, undefined, {
      status: 401,
      statusText: 'Unauthorized',
      config,
      headers: {},
      data: {
        error: { code, what: 'Session rejected', why: 'Test fixture', next_step: 'Sign in' },
      },
    }),
  );
}

describe('Session rejection handling', () => {
  it.each(['success', 'failure'])(
    'ignores a late refresh %s after the account changes',
    async (outcome) => {
      setAccessToken('fictional-old-account');
      let resolveRefresh!: (value: unknown) => void;
      let rejectRefresh!: (reason: Error) => void;
      const post = vi.spyOn(axios, 'post').mockImplementation(
        () =>
          new Promise((resolve, reject) => {
            resolveRefresh = resolve;
            rejectRefresh = reject;
          }),
      );
      const pending = restoreSession();
      clearAccessToken();
      expect(post.mock.calls[0]?.[2]?.signal?.aborted).toBe(true);
      setAccessToken('fictional-new-account');
      if (outcome === 'success') resolveRefresh({ data: token(userA) });
      else rejectRefresh(new Error('Late old-session failure'));
      expect(await pending).toBeNull();
      expect(getAccessToken()).toBe('fictional-new-account');
    },
  );
  it('does not sign out a new account when an earlier request is rejected late', async () => {
    setAccessToken('fictional-old-account');
    let rejectOld!: () => void;
    const lost = vi.fn();
    setSessionLostHandler(lost);
    apiClient.defaults.adapter = (config) =>
      new Promise((_, reject) => {
        rejectOld = () => void rejectWith('TOKEN_INVALID', config).catch(reject);
      });
    const pending = apiClient.get('/analyses');
    const rejection = expect(pending).rejects.toMatchObject({ status: 401 });
    await waitFor(() => expect(rejectOld).toBeDefined());
    clearAccessToken();
    setAccessToken('fictional-new-account');
    rejectOld();
    await rejection;
    expect(getAccessToken()).toBe('fictional-new-account');
    expect(lost).not.toHaveBeenCalled();
  });
  it('does not replay an old protected request after account change during renewal', async () => {
    setAccessToken('fictional-old-account');
    let finish!: (value: unknown) => void;
    const post = vi.spyOn(axios, 'post').mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const lost = vi.fn();
    setSessionLostHandler(lost);
    const adapter = vi.fn((config: InternalAxiosRequestConfig) =>
      rejectWith('TOKEN_EXPIRED', config),
    );
    apiClient.defaults.adapter = adapter;
    const pending = apiClient.get('/analyses');
    const rejection = expect(pending).rejects.toMatchObject({ status: 401 });
    await waitFor(() => expect(post).toHaveBeenCalledOnce());
    clearAccessToken();
    setAccessToken('fictional-new-account');
    finish({ data: token(userA) });
    await rejection;
    expect(adapter).toHaveBeenCalledOnce();
    expect(lost).not.toHaveBeenCalled();
    expect(getAccessToken()).toBe('fictional-new-account');
  });
  it('clears a revoked access token and the signed-in UI', async () => {
    setAccessToken('fictional-revoked');
    const lost = vi.fn();
    setSessionLostHandler(lost);
    apiClient.defaults.adapter = (config) => rejectWith('TOKEN_INVALID', config);
    await expect(apiClient.get('/analyses')).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBeNull();
    expect(lost).toHaveBeenCalledOnce();
  });
  it('keeps the session when confirmation password is incorrect', async () => {
    setAccessToken('fictional-valid');
    const lost = vi.fn();
    setSessionLostHandler(lost);
    apiClient.defaults.adapter = (config) => rejectWith('PASSWORD_INCORRECT', config);
    await expect(apiClient.post('/users/me/password')).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBe('fictional-valid');
    expect(lost).not.toHaveBeenCalled();
  });
  it('renews an expired access token once and replays the original request', async () => {
    setAccessToken('fictional-expired');
    const refresh = vi.spyOn(axios, 'post').mockResolvedValue({ data: token(userA) });
    const lost = vi.fn();
    setSessionLostHandler(lost);
    let attempts = 0;
    apiClient.defaults.adapter = (config) =>
      ++attempts === 1
        ? rejectWith('TOKEN_EXPIRED', config)
        : Promise.resolve({
            status: 200,
            statusText: 'OK',
            config,
            headers: {},
            data: { title: 'Private report' },
          });
    expect((await apiClient.get('/analyses/report')).data.title).toBe('Private report');
    expect(refresh).toHaveBeenCalledOnce();
    expect(attempts).toBe(2);
    expect(lost).not.toHaveBeenCalled();
  });
  it('ends the session if renewal fails, without replaying the protected request', async () => {
    setAccessToken('fictional-expired');
    const refresh = vi.spyOn(axios, 'post').mockRejectedValue(new Error('Unavailable refresh'));
    const lost = vi.fn();
    setSessionLostHandler(lost);
    const adapter = vi.fn((config: InternalAxiosRequestConfig) =>
      rejectWith('TOKEN_EXPIRED', config),
    );
    apiClient.defaults.adapter = adapter;
    await expect(apiClient.get('/analyses')).rejects.toMatchObject({ status: 401 });
    expect(refresh).toHaveBeenCalledOnce();
    expect(adapter).toHaveBeenCalledOnce();
    expect(lost).toHaveBeenCalledOnce();
    expect(getAccessToken()).toBeNull();
  });
});
