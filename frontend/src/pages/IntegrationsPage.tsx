import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  CardMedia,
  CardActions,
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import { Cloud as GoogleDriveIcon, Warning as WarningIcon } from '@mui/icons-material';
import { getGoogleDriveConnectionStatus, checkGoogleApiCredentials } from '../services/googleDriveService';

const IntegrationsPage = () => {
  const navigate = useNavigate();

  // Query for Google Drive connection status
  const { data: connectionStatus, isLoading } = useQuery(
    ['googleDriveStatus'],
    () => getGoogleDriveConnectionStatus(),
    { retry: false }
  );

  // Query for Google API credentials status
  const { data: apiCredentialsStatus } = useQuery(
    ['googleApiCredentialsStatus'],
    () => checkGoogleApiCredentials(),
    { retry: false }
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Integrations
      </Typography>
      
      <Typography variant="body1" paragraph>
        Connect your Data Room to external services to import and manage your documents.
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 1 }}>
        {/* Google Drive Integration Card */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardMedia
              component="div"
              sx={{
                bgcolor: '#f8f9fa',
                py: 4,
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <GoogleDriveIcon sx={{ fontSize: 60, color: '#4285F4' }} />
            </CardMedia>
            
            <CardContent sx={{ flexGrow: 1 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h5" component="h2">
                  Google Drive
                </Typography>
                {!isLoading && (
                  <Chip
                    label={connectionStatus?.connected ? 'Connected' : 'Not Connected'}
                    color={connectionStatus?.connected ? 'success' : 'default'}
                    size="small"
                  />
                )}
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              <Typography variant="body2" color="text.secondary">
                Import documents, spreadsheets, presentations, and more from your Google Drive.
                Maintain folder structure and easily manage your files.
              </Typography>
              
              {connectionStatus?.connected && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Connected as: <strong>{connectionStatus.user_email}</strong>
                </Typography>
              )}
            
              {apiCredentialsStatus && !apiCredentialsStatus.valid && (
                <Alert severity="warning" icon={<WarningIcon />} sx={{ mt: 2 }}>
                  {apiCredentialsStatus.message || 'Google Drive service is temporarily unavailable. Please try again later.'}
                </Alert>
              )}
            </CardContent>
            
            <CardActions>
              <Button 
                size="medium" 
                variant="contained"
                onClick={() => navigate('/integrations/google-drive')}
                disabled={apiCredentialsStatus && !apiCredentialsStatus.valid}
                fullWidth
              >
                {connectionStatus?.connected ? 'Manage' : 'Connect'}
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        {/* Placeholder for future integrations */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', opacity: 0.6 }}>
            <CardMedia
              component="div"
              sx={{
                bgcolor: '#f8f9fa',
                py: 4,
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <Box sx={{ 
                width: 60, 
                height: 60, 
                borderRadius: '12px',
                bgcolor: '#ddd',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Typography variant="h5" color="text.secondary">DB</Typography>
              </Box>
            </CardMedia>
            
            <CardContent sx={{ flexGrow: 1 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h5" component="h2">
                  Dropbox
                </Typography>
                <Chip label="Coming Soon" color="primary" size="small" />
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              <Typography variant="body2" color="text.secondary">
                Import your files from Dropbox. This integration will be available soon.
              </Typography>
            </CardContent>
            
            <CardActions>
              <Button size="medium" variant="outlined" disabled fullWidth>
                Coming Soon
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        {/* Another placeholder for future integrations */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', opacity: 0.6 }}>
            <CardMedia
              component="div"
              sx={{
                bgcolor: '#f8f9fa',
                py: 4,
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <Box sx={{ 
                width: 60, 
                height: 60, 
                borderRadius: '12px',
                bgcolor: '#ddd',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Typography variant="h5" color="text.secondary">MS</Typography>
              </Box>
            </CardMedia>
            
            <CardContent sx={{ flexGrow: 1 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h5" component="h2">
                  Microsoft OneDrive
                </Typography>
                <Chip label="Coming Soon" color="primary" size="small" />
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              <Typography variant="body2" color="text.secondary">
                Connect your Microsoft OneDrive account to import documents. This integration will be available soon.
              </Typography>
            </CardContent>
            
            <CardActions>
              <Button size="medium" variant="outlined" disabled fullWidth>
                Coming Soon
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default IntegrationsPage;