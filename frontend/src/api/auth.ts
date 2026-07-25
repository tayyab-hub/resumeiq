import { apiClient } from '@/api/client';
import type { TokenResponse, User } from '@/types';

export interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<TokenResponse>('/auth/register', payload).then((r) => r.data),

  login: (payload: LoginPayload) =>
    apiClient.post<TokenResponse>('/auth/login', payload).then((r) => r.data),

  refresh: () => apiClient.post<TokenResponse>('/auth/refresh').then((r) => r.data),

  logout: () => apiClient.post<void>('/auth/logout').then(() => undefined),

  me: () => apiClient.get<User>('/auth/me').then((r) => r.data),

  updateProfile: (fullName: string) =>
    apiClient.patch<User>('/users/me', { full_name: fullName }).then((r) => r.data),

  changePassword: (currentPassword: string, newPassword: string) =>
    apiClient
      .post<void>('/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      .then(() => undefined),

  deleteAccount: (password: string) =>
    apiClient
      .delete<void>('/users/me', { data: { password, confirmation: 'DELETE' } })
      .then(() => undefined),
};
