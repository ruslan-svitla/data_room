import { useState, FormEvent, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Container,
  Link,
  TextField,
  Typography,
  Paper,
  Alert,
  Divider,
} from '@mui/material';
import { Lock as LockIcon } from '@mui/icons-material';
import GoogleIcon from '@mui/icons-material/Google';
import { useAuth } from '../context/AuthContext';

// Function to handle Google OAuth
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, options: any) => void;
          prompt: () => void;
        };
      };
    };
  }
}

const LoginPage = () => {
  const { isAuthenticated, login, loginGoogle, isLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  // Initialize Google Sign-In
  useEffect(() => {
    // Load the Google Sign-In API script
    const loadGoogleScript = () => {
      if (window.google?.accounts) {
        initializeGoogleSignIn();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogleSignIn;
      document.body.appendChild(script);
    };

    const initializeGoogleSignIn = () => {
      if (window.google?.accounts) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
          callback: handleGoogleResponse,
          auto_select: false,
        });
        setGoogleLoaded(true);
      }
    };

    loadGoogleScript();
  }, []);

  // Render Google button when the API is loaded
  useEffect(() => {
    if (googleLoaded && window.google?.accounts) {
      const googleButtonContainer = document.getElementById('google-signin-button');
      if (googleButtonContainer) {
        window.google.accounts.id.renderButton(googleButtonContainer, {
          theme: 'outline',
          size: 'large',
          width: '100%',
          text: 'signin_with',
        });
      }
    }
  }, [googleLoaded]);

  // Callback for Google Sign-In
  const handleGoogleResponse = async (response: any) => {
    console.log('Google response:', response);
    try {
      if (response.credential) {
        await loginGoogle({ id_token: response.credential });
      } else {
        throw new Error('Failed to get credentials from Google');
      }
    } catch (err: any) {
      console.error('Google login error:', err);
      setError(err.message || 'Failed to authenticate with Google');
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await login({ username, password });
    } catch (err: any) {
      console.error('Login error:', err);

      // Handle Axios error with response
      if (err?.response?.data) {
        // Handle FastAPI standard error format
        if (typeof err.response.data === 'object' && 'detail' in err.response.data) {
          setError(String(err.response.data.detail));
        }
        // Handle string error response
        else if (typeof err.response.data === 'string') {
          setError(err.response.data);
        }
        // Handle form validation errors
        else if (Array.isArray(err.response.data)) {
          setError(err.response.data.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', '));
        }
        else {
          setError('Login failed. Please check your credentials.');
        }
      }
      // Handle network errors
      else if (err.message) {
        setError(`Connection error: ${err.message}`);
      }
      // Fallback error
      else {
        setError('Login failed. Please try again later.');
      }
    }
  };

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
            <LockIcon />
          </Avatar>
          <Typography component="h1" variant="h5">
            Sign in to Data Room
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1, width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isLoading}
              sx={{ mt: 3, mb: 2 }}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>

            <Box sx={{ mt: 3, mb: 1 }}>
              <Divider>or</Divider>
            </Box>

            <Box id="google-signin-button" sx={{ mt: 2, mb: 2, width: '100%', display: 'flex', justifyContent: 'center' }}>
              {/* Google Sign-In button will be rendered here */}
              {!googleLoaded && (
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<GoogleIcon />}
                  disabled
                  sx={{ mt: 1 }}
                >
                  Sign in with Google
                </Button>
              )}
            </Box>
          </Box>
        </Paper>


      </Box>
    </Container>
  );
};

export default LoginPage;