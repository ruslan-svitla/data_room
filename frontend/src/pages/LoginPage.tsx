import { useState, FormEvent } from 'react';
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
} from '@mui/material';
import { Lock as LockIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

const LoginPage = () => {
  const { isAuthenticated, login, isLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

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
          </Box>
        </Paper>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 4 }}>
          {'Test credentials: '}
          <Link color="primary" href="#" onClick={() => { setUsername('user1'); setPassword('password1'); }}>
            user1 / password1
          </Link>
        </Typography>
      </Box>
    </Container>
  );
};

export default LoginPage;