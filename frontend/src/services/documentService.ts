import { Document } from '../types';
import { apiRequest } from './api';
import api from './api';

export const getDocuments = async (folderId?: string): Promise<{ documents: Document[] }> => {
  const params: Record<string, string> = {};

  if (folderId) {
    params.folder_id = folderId;
  }

  // API returns an array, but our frontend expects {documents: Document[]}
  const response = await apiRequest<Document[]>({
    method: 'GET',
    url: '/documents',
    params,
  });
  
  // Transform the API response to match what the frontend expects
  return { documents: response };
};

export const getDocument = async (id: string): Promise<Document> => {
  return apiRequest<Document>({
    method: 'GET',
    url: `/documents/${id}`,
  });
};

export const deleteDocument = async (id: string): Promise<void> => {
  return apiRequest<void>({
    method: 'DELETE',
    url: `/documents/${id}`,
  });
};

// Download document - returns a blob directly instead of using apiRequest
export const downloadDocument = async (id: string, fileName: string): Promise<void> => {
  try {
    // Use axios directly to get the blob
    const response = await api.get(`/documents/${id}/download`, {
      responseType: 'blob'
    });

    // Get content type from the response or use a generic one
    const contentType = response.headers['content-type'] || 'application/octet-stream';

    // Create URL for the blob - explicitly specify content type to force download behavior
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/octet-stream' }));

    // Create temporary link element to trigger download
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName); // The download attribute forces download behavior

    // For extra certainty, add these attributes (may not be needed but doesn't hurt)
    link.setAttribute('type', 'application/octet-stream');
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();

    // Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
  } catch (error) {
    console.error('Error downloading document:', error);
    throw error;
  }
};