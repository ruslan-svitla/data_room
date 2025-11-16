import { useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Typography, Grid, Paper, Button, Link } from '@mui/material';
import { useQuery } from 'react-query';
import { Cloud as CloudIcon } from '@mui/icons-material';
import { getGoogleDriveConnectionStatus } from '../services/googleDriveService';
import { getDocuments } from '../services/documentService';

const DashboardPage = () => {
  // Check Google Drive connection status
  const { data: connectionStatus } = useQuery(
    ['googleDriveStatus'],
    () => getGoogleDriveConnectionStatus(),
    { retry: false }
  );

  // Get recent documents
  const { data: documentsData, isLoading: isLoadingDocuments } = useQuery(
    ['documents'],
    () => getDocuments(),
    { retry: false }
  );

  // Helper function to format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Helper function to format file size
  const formatFileSize = (bytes?: number): string => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Google Drive Connection Status */}
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Google Drive Integration
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CloudIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="body1">
                Status:{' '}
                <strong>
                  {connectionStatus?.connected ? 'Connected' : 'Not Connected'}
                </strong>
              </Typography>
            </Box>

            {connectionStatus?.connected ? (
              <Typography variant="body2" color="text.secondary">
                Connected as {connectionStatus.user_email}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Connect to Google Drive to import your files
              </Typography>
            )}

            <Box sx={{ mt: 'auto', pt: 2 }}>
              <Button
                component={RouterLink}
                to="/integrations/google-drive"
                variant="contained"
                startIcon={<CloudIcon />}
              >
                {connectionStatus?.connected
                  ? 'Manage Google Drive'
                  : 'Connect Google Drive'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Documents */}
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Recent Documents
            </Typography>

            {isLoadingDocuments ? (
              <Typography>Loading documents...</Typography>
            ) : documentsData?.documents && documentsData.documents.length > 0 ? (
              <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                {documentsData.documents
                  .slice(0, 5)
                  .map((document) => (
                    <Box
                      key={document.id}
                      sx={{
                        py: 1,
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Typography variant="body1">{document.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Added on {formatDate(document.created_at)} • {formatFileSize(document.file_size || document.size)}
                      </Typography>
                    </Box>
                  ))}
                <Box sx={{ mt: 2 }}>
                  <Link
                    component={RouterLink}
                    to="/documents"
                    color="primary"
                  >
                    View all documents
                  </Link>
                </Box>
              </Box>
            ) : (
              <Typography>No documents yet. Import some from Google Drive!</Typography>
            )}
          </Paper>
        </Grid>

        {/* Additional widgets can be added here */}
      </Grid>
    </Box>
  );
};

export default DashboardPage;