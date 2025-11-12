import { LoginCredentials, LoginResponse, User } from '../types';
import { apiRequest } from './api';
import axios from 'axios';

export const loginUser = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  // Create form data
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  // Direct axios call with specific Content-Type for form data
  const response = await axios({
    method: 'POST',
    url: '/api/v1/auth/login',
    data: formData,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });

  return response.data;
};

export const getCurrentUser = async (): Promise<User> => {
  return apiRequest<User>({
    method: 'GET',
    url: '/users/me',
  });
};