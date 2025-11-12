import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert, Button } from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from 'react-query';

const GoogleAuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(true);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    const processAuth = async () => {
      try {
        // Handle redirect from Google OAuth
        console.log('Google auth callback page loaded');
        console.log('Auth status:', isAuthenticated ? 'Authenticated' : 'Not authenticated');
        console.log('User:', user ? `${user.email} (${user.id})` : 'None');
  
        // Check for error parameter in URL
        const url = new URL(window.location.href);
        const errorParam = url.searchParams.get('error');
  
        if (errorParam) {
          console.error('Error from OAuth process:', errorParam);
          setError(`Google authentication error: ${errorParam}`);
          setProcessing(false);
          return;
        }
  
        if (!isAuthenticated) {
          // If we aren't authenticated yet but this is our first attempt, wait a bit
          if (attempts < 5) {
            console.log(`Not authenticated yet, waiting... (Attempt ${attempts + 1}/5)`);
            setAttempts(prev => prev + 1);
            setTimeout(() => processAuth(), 1000);
            return;
          }
  
          setError('You must be logged in to connect to Google Drive');
          setProcessing(false);
          return;
        }
  
        // Invalidate any cached queries to ensure fresh data
        console.log('Authentication confirmed, invalidating cached queries');
        queryClient.invalidateQueries(['googleDriveStatus']);
  
        // Wait a bit to ensure backend processed the callback
        setTimeout(() => {
          // Navigate back to the Google Drive page
          console.log('Redirecting to Google Drive integration page');
          navigate('/integrations/google-drive', { replace: true });
        }, 2000);
      } catch (err) {
        console.error('Error processing Google auth callback:', err);
        setError('Failed to complete Google authentication');
        setProcessing(false);
      }
    };
  
    processAuth();
  }, [isAuthenticated, navigate, queryClient, user, attempts]);

  if (error) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="100vh">
        <Alert severity="error" sx={{ mb: 2, maxWidth: '80%' }}>
          {error}
        </Alert>
        <Typography variant="body1" sx={{ mt: 2 }}>
          <a href="/login">Go to Login</a> | <a href="/integrations/google-drive">Back to Google Drive</a>
        </Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="100vh">
      <CircularProgress size={60} sx={{ mb: 4 }} />
      <Typography variant="h6">Processing Google Authentication</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
        Please wait while we complete your Google Drive connection...
      </Typography>
    </Box>
  );
};

export default GoogleAuthCallback;