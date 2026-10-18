import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/v1'
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('auth_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getAuthenticatedUserId(): number | null {
  if (typeof window === 'undefined') return null;
  const value = Number(window.localStorage.getItem('auth_user_id'));
  return Number.isInteger(value) && value > 0 ? value : null;
}

export function saveAuthSession(token: string, userId: number, role: string): void {
  window.localStorage.setItem('auth_token', token);
  window.localStorage.setItem('auth_user_id', String(userId));
  window.localStorage.setItem('auth_role', role);
}
