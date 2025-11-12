import {
  GoogleDriveConnectionStatus,
  GoogleDriveFileList,
  GoogleDriveFile,
  GoogleDriveStorageInfo,
  GoogleDriveImportRequest,
  GoogleDriveImportResult,
} from '../types';
import { apiRequest } from './api';

// Check connection status
export const getGoogleDriveConnectionStatus = async (): Promise<GoogleDriveConnectionStatus> => {
  console.log('Fetching Google Drive connection status');

  // Log the current authentication token
  const token = localStorage.getItem('token');
  console.log('Using auth token:', token ? 'Present (not shown for security)' : 'None');

  try {
    const response = await apiRequest<GoogleDriveConnectionStatus>({
      method: 'GET',
      url: '/integrations/google/status',
      // Add a cache-busting parameter to avoid caching issues
      params: { _t: new Date().getTime() },
    });
    console.log('Google Drive status response:', response);
    return response;
  } catch (error) {
    console.error('Error fetching Google Drive status:', error);
    // Return a default response structure when there's an error
    return { connected: false, user_email: null };
  }
};

// Start Google Drive authentication
export const initiateGoogleDriveAuth = async (): Promise<{ authorization_url: string }> => {
  try {
    console.log('Initiating Google Drive authentication');
    const response = await apiRequest<{ authorization_url: string }>({
      method: 'POST',
      url: '/integrations/google/link',
    });
    console.log('Google Drive auth URL received:', response.authorization_url ? 'URL Present' : 'Missing URL');
    return response;
  } catch (error) {
    console.error('Error initiating Google Drive authentication:', error);
    throw error;
  }
};

// Disconnect from Google Drive
export const disconnectGoogleDrive = async (): Promise<{ detail: string }> => {
  return apiRequest<{ detail: string }>({
    method: 'DELETE',
    url: '/integrations/google/disconnect',
  });
};

// List files in Google Drive
export const listGoogleDriveFiles = async (
  folderId?: string,
  pageToken?: string
): Promise<GoogleDriveFileList> => {
  const params: Record<string, string> = {};
  
  if (folderId) {
    params.folder_id = folderId;
  }
  
  if (pageToken) {
    params.page_token = pageToken;
  }
  
  return apiRequest<GoogleDriveFileList>({
    method: 'GET',
    url: '/integrations/google/files',
    params,
  });
};

// Get Google Drive file details
export const getGoogleDriveFile = async (fileId: string): Promise<GoogleDriveFile> => {
  return apiRequest<GoogleDriveFile>({
    method: 'GET',
    url: `/integrations/google/files/${fileId}`,
  });
};

// Search Google Drive files
export const searchGoogleDriveFiles = async (query: string): Promise<GoogleDriveFileList> => {
  return apiRequest<GoogleDriveFileList>({
    method: 'GET',
    url: '/integrations/google/search',
    params: { query },
  });
};

// Get Google Drive storage info
export const getGoogleDriveStorageInfo = async (): Promise<GoogleDriveStorageInfo> => {
  return apiRequest<GoogleDriveStorageInfo>({
    method: 'GET',
    url: '/integrations/google/storage',
  });
};

// Check if Google Drive API credentials are valid
export const checkGoogleApiCredentials = async (): Promise<{ valid: boolean; message?: string }> => {
  try {
    // Add a cache busting parameter to ensure we get fresh results
    const response = await apiRequest<{ valid: boolean; message?: string }>({  
      method: 'GET',
      url: '/integrations/google/api-status',
      params: { _t: new Date().getTime() }, // Add timestamp to prevent caching
    });
    console.log('Google API credentials check result:', response);
    return response;
  } catch (error) {
    console.error('Error checking Google API credentials:', error);
    return { valid: false, message: 'Unable to verify Google API credentials' };
  }
};

// Import files from Google Drive
export const importFromGoogleDrive = async (
  request: GoogleDriveImportRequest
): Promise<GoogleDriveImportResult> => {
  return apiRequest<GoogleDriveImportResult>({
    method: 'POST',
    url: '/integrations/google/import',
    data: request,
  });
};