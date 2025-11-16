import axios, { AxiosError, AxiosRequestConfig } from 'axios';

// Get base URL from environment variables or fall back to relative path
const BASE_URL = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : '';
const API_PATH = '/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true  // This enables sending cookies with cross-origin requests
});

// For debugging
console.log(`API configured with base URL: ${BASE_URL}`);


// Add request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const status = error.response?.status;
    
    // Handle authentication errors
    if (status === 401) {
      localStorage.removeItem('token');
      // Only redirect if not already on the login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Generic function to handle API requests
export const request = async <T>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await api(config);
    return response.data;
  } catch (error) {
    // Don't transform the error, just pass it through
    // This allows components to access the full error object including response data
    throw error;
  }
};

// Generic function to handle API requests with '/api/v1' path
export const apiRequest = async <T>(config: AxiosRequestConfig): Promise<T> => {
  try {
    // Update the URL to include the API path
    const updatedConfig = { ...config };
    if (updatedConfig.url) {
      // Ensure we don't double-add the API path
      if (!updatedConfig.url.startsWith(API_PATH)) {
        updatedConfig.url = `${API_PATH}${updatedConfig.url}`;
      }
    }
    const response = await api(updatedConfig);
    return response.data;
  } catch (error) {
    // Don't transform the error, just pass it through
    // This allows components to access the full error object including response data
    throw error;
  }
};

export default api;