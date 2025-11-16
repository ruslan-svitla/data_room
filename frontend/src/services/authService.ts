import { LoginCredentials, LoginResponse, User, GoogleLoginCredentials } from '../types';
import { apiRequest, request } from './api';

export const loginUser = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  // Create form data
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  // Use request for login with specific Content-Type for form data
  return request<LoginResponse>({
    method: 'POST',
    url: '/api/v1/auth/login',
    data: formData,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
};

export const getCurrentUser = async (): Promise<User> => {
  return apiRequest<User>({
    method: 'GET',
    url: '/users/me',
  });
};

export const loginWithGoogle = async (credentials: GoogleLoginCredentials): Promise<LoginResponse> => {
  return request<LoginResponse>({
    method: 'POST',
    url: '/api/v1/auth/google',
    data: credentials,
    headers: {
      'Content-Type': 'application/json'
    }
  });
};