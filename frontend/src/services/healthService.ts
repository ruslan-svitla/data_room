import {request} from './api';

/**
 * Interface for health response data
 */
export interface HealthResponse {
  status: string;
  api_version: string;
  environment: string;
}

/**
 * Interface for detailed health response data
 */
export interface DetailedHealthResponse extends HealthResponse {
  database: string;
  settings?: {
    debug: boolean;
    project_name: string;
  };
}

/**
 * Health service to check API status
 */
export const healthService = {
  /**
   * Get basic health status
   */
  getHealth: (): Promise<HealthResponse> => {
    return request<HealthResponse>({
      method: 'GET',
      url: '/health'
    });
  },

  /**
   * Get detailed health status including database connectivity
   */
  getDetailedHealth: (): Promise<DetailedHealthResponse> => {
    return request<DetailedHealthResponse>({
      method: 'GET',
      url: '/health/detailed'
    });
  }
};

export default healthService;