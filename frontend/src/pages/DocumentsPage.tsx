import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import {
    Box,
    Typography,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Tooltip,
    TextField,
    InputAdornment,
    CircularProgress,
    Alert,
    Chip, 
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Button
} from '@mui/material';
import {
  Search as SearchIcon,
  Delete as DeleteIcon,
  CloudDownload as CloudIcon,
  CloudDownload,
  DescriptionOutlined as FileIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as GenericFileIcon,
} from '@mui/icons-material';

import { getDocuments, deleteDocument, downloadDocument } from '../services/documentService';
import { Document } from '../types';

const DocumentsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [downloadLoading, setDownloadLoading] = useState<string | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);
  const queryClient = useQueryClient();
  
  // Query for documents
  const {
    data: documentsData,
    isLoading,
    error,
    refetch,
  } = useQuery(['documents'], () => getDocuments(), {
    // Ensure data is considered fresh for no longer than 30 seconds
    staleTime: 30000,
    // Set refetchOnWindowFocus to ensure documents refresh when user returns to the page
    refetchOnWindowFocus: true,
    // Re-fetch when coming back to page via navigation
    refetchOnMount: true,
  });
  
  // Fallback for unexpected API response structure
  // This handles case when API directly returns Document[] instead of {documents: Document[]}
  const documents = Array.isArray(documentsData) ? documentsData : 
                  (documentsData?.documents || []);
  
  // Filter documents based on search term
  const filteredDocuments = documents
    ? documents.filter((doc: Document) =>
        doc.name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : [];
  
  // Add debug logging to help identify issues
  useEffect(() => {
    if (documentsData) {
      console.log("Documents data received:", documentsData);
      console.log("Documents converted:", documents);
      console.log("Filtered documents:", filteredDocuments);
      console.log("Data type:", Array.isArray(documentsData) ? 'Array[]' : 'Object');
    } else if (error) {
      console.error("Error fetching documents:", error);
    }
  }, [documentsData, documents, filteredDocuments, error]);
  
  // Listen for URL changes and document visibility changes to refresh data
  useEffect(() => {
    // Refetch when the component mounts
    refetch();
  
    // Set up an event listener for visibilitychange
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('Document page is now visible, refreshing data...');
        refetch();
      }
    };
  
    // Listen for visibility changes (user coming back to the tab)
    document.addEventListener('visibilitychange', handleVisibilityChange);
  
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [refetch]);
  
  // Helper function to format file size
  const formatFileSize = (bytes?: number): string => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // Helper to get the correct size field
  const getFileSize = (document: Document): number => {
    return document.size || document.file_size || 0;
  };
  
  // Helper function to format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };
  
  // Helper function to get file icon based on mime type or file type
  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) {
      return <ImageIcon color="primary" />;
    } else if (mimeType.includes('pdf')) {
      return <PdfIcon color="error" />;
    } else if (mimeType.includes('document') || mimeType.includes('text')) {
      return <FileIcon color="info" />;
    } else {
      return <GenericFileIcon />;
    }
  };
  
  // Helper to get the correct file type field (handle both mime_type and file_type)
  const getFileType = (document: Document): string => {
    return document.mime_type || document.file_type as string;
  };
  
  // Helper function to get source icon
  const getSourceIcon = (source?: string) => {
    if (source === 'google_drive') {
      return <CloudIcon fontSize="small" sx={{ color: '#4285F4' }} />;
    }
    return undefined;
  };
  
  // Helper function to determine document source from description
  const getDocumentSource = (document: Document) => {
    if (document.source) {
      return document.source;
    }
  
    // Extract source from description if available
    if (document.description?.includes('Google Drive')) {
      return 'google_drive';
    }
  
    return undefined;
  };
  
  // Open confirmation dialog before deleting
  const confirmDelete = (document: Document) => {
    setDocumentToDelete(document);
    setConfirmDialogOpen(true);
  };

  // Cancel delete operation
  const handleCancelDelete = () => {
    setConfirmDialogOpen(false);
    setDocumentToDelete(null);
  };
  
  // Handle document deletion after confirmation
  const handleDeleteDocument = async () => {
    if (!documentToDelete) return;
  
    const documentId = documentToDelete.id;
  
    try {
      setConfirmDialogOpen(false);
      setDeleteLoading(documentId);
      await deleteDocument(documentId);
      // Refresh the documents data after deletion
      queryClient.invalidateQueries(['documents']);
    } catch (error) {
      console.error('Error deleting document:', error);
      // Show error notification here if you have a notification system
    } finally {
      setDeleteLoading(null);
      setDocumentToDelete(null);
    }
  };
  
  // Handle document download
  const handleDownloadDocument = async (document: Document) => {
    try {
      setDownloadLoading(document.id);
      await downloadDocument(document.id, document.name);
    } catch (error) {
      console.error('Error downloading document:', error);
      // Show error notification here if you have a notification system
    } finally {
      setDownloadLoading(null);
    }
  };
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Documents
      </Typography>
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search documents..."
          value={searchTerm}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />
        
        {/* Debug info during development */}
        <Typography variant="caption" color="textSecondary" display="block" gutterBottom>
          Total documents: {documents?.length || 0}, Filtered: {filteredDocuments.length}, 
          Data type: {Array.isArray(documentsData) ? 'Array' : (documentsData ? 'Object' : 'null')}
        </Typography>
        
        {isLoading ? (
          <Box display="flex" justifyContent="center" my={3}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">
            {error instanceof Error ? error.message : 'Failed to load documents'}
          </Alert>
        ) : filteredDocuments && filteredDocuments.length > 0 ? (
          <TableContainer>
            <Table aria-label="documents table">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Added</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredDocuments.map((document: Document) => (
                  <TableRow key={document.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getFileIcon(getFileType(document))}
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            ml: 1, 
                            cursor: 'pointer', 
                            '&:hover': { textDecoration: 'underline', color: 'primary.main' },
                            display: 'flex',
                            alignItems: 'center'
                          }}
                          onClick={() => handleDownloadDocument(document)}
                        >
                          {document.name}
                          {downloadLoading === document.id && (
                            <CircularProgress size={16} sx={{ ml: 1 }} />
                          )}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{getFileType(document).split('/')[1]}</TableCell>
                    <TableCell>{formatFileSize(getFileSize(document))}</TableCell>
                    <TableCell>{formatDate(document.created_at)}</TableCell>
                    <TableCell>
                      {(document.source || document.description?.includes('Google Drive')) && (
                        <Tooltip title={document.description || `Imported from ${getDocumentSource(document)}`}>
                          <Chip
                            size="small"
                            label={getDocumentSource(document)?.replace('_', ' ') || 'google drive'}
                            icon={getSourceIcon(getDocumentSource(document))}
                          />
                        </Tooltip>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <Tooltip title="Download">
                          <IconButton 
                            size="small" 
                            color="primary" 
                            onClick={() => handleDownloadDocument(document)}
                            disabled={downloadLoading === document.id || deleteLoading === document.id}
                            sx={{ mr: 1 }}
                          >
                            {downloadLoading === document.id ? <CircularProgress size={20} /> : <CloudDownload />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton 
                            size="small" 
                            color="error" 
                            onClick={() => confirmDelete(document)}
                            disabled={deleteLoading === document.id || downloadLoading === document.id}
                          >
                            {deleteLoading === document.id ? <CircularProgress size={20} /> : <DeleteIcon />}
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No documents found. Import some from Google Drive!
          </Alert>
        )}
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialogOpen}
        onClose={handleCancelDelete}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Confirm Deletion
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete "{documentToDelete?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteDocument} color="error" variant="contained" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import limitations note for users */}
      <Box sx={{ mt: 4, mb: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          <strong>Note:</strong> For cost-saving and reliability, there are limits on document imports.<br />
          You can import up to <b>99 documents</b> and use up to <b>500 MB</b> of total storage.<br />
          If you reach these limits, please contact support for options.
        </Typography>
      </Box>
    </Box>
  );
};

export default DocumentsPage;

