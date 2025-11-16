import { createClient } from './axiosClient';

// Create a client instance for health endpoints
const healthClient = createClient();

// Define response interfaces
export interface HealthResponse {
  status: string;
  api_version: string;
  environment: string;
}

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
    return healthClient.get<HealthResponse>('/health');
  },
  
  /**
   * Get detailed health status including database connectivity
   */
  getDetailedHealth: (): Promise<DetailedHealthResponse> => {
    return healthClient.get<DetailedHealthResponse>('/health/detailed');
  }
};

export default healthService;