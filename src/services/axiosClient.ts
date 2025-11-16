import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Default config using environment variables
const defaultConfig: AxiosRequestConfig = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Minimal Axios client wrapper
 */
export class AxiosClient {
  private instance: AxiosInstance;

  constructor(config: AxiosRequestConfig = {}) {
    this.instance = axios.create({
      ...defaultConfig,
      ...config,
    });
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.delete(url, config);
    return response.data;
  }

  // Set auth token if needed
  setAuthToken(token: string): this {
    this.instance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    return this;
  }
}

// Export a simple factory function to create clients
export const createClient = (config?: AxiosRequestConfig): AxiosClient => {
  return new AxiosClient(config);
};

// Export default client instance for simple usage
export default new AxiosClient();