import { Document } from '../types';
import { apiRequest } from './api';

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

// Download document - fetches download URL and redirects to it
export const downloadDocument = async (id: string, fileName: string): Promise<void> => {
  try {
    // Get the download URL from the API
    const response = await apiRequest<{ download_url: string }>({
      method: 'GET',
      url: `/documents/${id}/download`,
    });

    // Redirect to the download URL
    if (response.download_url) {
      // Create a temporary link and click it to trigger download
      const link = document.createElement('a');
      link.href = response.download_url;
      link.target = '_blank';
      link.setAttribute('download', fileName);
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();

      // Clean up
      document.body.removeChild(link);
    } else {
      throw new Error('No download URL received from server');
    }
  } catch (error) {
    console.error('Error downloading document:', error);
    throw error;
  }
};