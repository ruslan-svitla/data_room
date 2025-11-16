/**
 * Unit tests for documentService
 * 
 * Tests the API service layer that handles document operations
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getDocuments, getDocument, deleteDocument, downloadDocument } from './documentService';
import * as api from './api';

// Mock the api module
vi.mock('./api', () => ({
    apiRequest: vi.fn(),
}));

describe('documentService', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getDocuments', () => {
        it('should fetch documents and transform response', async () => {
            // Arrange
            const mockDocuments = [
                { id: '1', name: 'Doc 1', file_type: 'application/pdf' },
                { id: '2', name: 'Doc 2', file_type: 'text/plain' },
            ];

            vi.mocked(api.apiRequest).mockResolvedValue(mockDocuments);

            // Act
            const result = await getDocuments();

            // Assert
            expect(api.apiRequest).toHaveBeenCalledWith({
                method: 'GET',
                url: '/documents',
                params: {},
            });
            expect(result).toEqual({ documents: mockDocuments });
        });

        it('should pass folder_id parameter when provided', async () => {
            // Arrange
            const folderId = 'folder-123';
            vi.mocked(api.apiRequest).mockResolvedValue([]);

            // Act
            await getDocuments(folderId);

            // Assert
            expect(api.apiRequest).toHaveBeenCalledWith({
                method: 'GET',
                url: '/documents',
                params: { folder_id: folderId },
            });
        });
    });

    describe('getDocument', () => {
        it('should fetch a single document by ID', async () => {
            // Arrange
            const mockDocument = { id: '123', name: 'Test Doc' };
            vi.mocked(api.apiRequest).mockResolvedValue(mockDocument);

            // Act
            const result = await getDocument('123');

            // Assert
            expect(api.apiRequest).toHaveBeenCalledWith({
                method: 'GET',
                url: '/documents/123',
            });
            expect(result).toEqual(mockDocument);
        });
    });

    describe('deleteDocument', () => {
        it('should send DELETE request for document', async () => {
            // Arrange
            vi.mocked(api.apiRequest).mockResolvedValue(undefined);

            // Act
            await deleteDocument('123');

            // Assert
            expect(api.apiRequest).toHaveBeenCalledWith({
                method: 'DELETE',
                url: '/documents/123',
            });
        });
    });

    describe('downloadDocument', () => {
        it('should fetch download URL and trigger download', async () => {
            // Arrange
            const mockDownloadUrl = 'https://s3.amazonaws.com/bucket/file.pdf';
            vi.mocked(api.apiRequest).mockResolvedValue({
                download_url: mockDownloadUrl,
            });

            // Mock document.createElement and related DOM methods
            const mockLink = {
                href: '',
                setAttribute: vi.fn(),
                click: vi.fn(),
                style: { display: '' },
            };
            const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
            const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
            const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

            // Act
            await downloadDocument('123', 'test.pdf');

            // Assert
            expect(api.apiRequest).toHaveBeenCalledWith({
                method: 'GET',
                url: '/documents/123/download',
            });
            expect(createElementSpy).toHaveBeenCalledWith('a');
            expect(mockLink.href).toBe(mockDownloadUrl);
            expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'test.pdf');
            expect(mockLink.click).toHaveBeenCalled();
            expect(appendChildSpy).toHaveBeenCalled();
            expect(removeChildSpy).toHaveBeenCalled();

            // Cleanup
            createElementSpy.mockRestore();
            appendChildSpy.mockRestore();
            removeChildSpy.mockRestore();
        });

        it('should throw error when no download URL is returned', async () => {
            // Arrange
            vi.mocked(api.apiRequest).mockResolvedValue({
                download_url: null,
            });

            // Act & Assert
            await expect(downloadDocument('123', 'test.pdf')).rejects.toThrow(
                'No download URL received from server'
            );
        });

        it('should handle API errors gracefully', async () => {
            // Arrange
            const error = new Error('Network error');
            vi.mocked(api.apiRequest).mockRejectedValue(error);

            // Act & Assert
            await expect(downloadDocument('123', 'test.pdf')).rejects.toThrow('Network error');
        });
    });
});
