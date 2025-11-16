import { createContext, ReactNode, useContext, useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthState, User, LoginCredentials, GoogleLoginCredentials } from '../types';
import { loginUser, getCurrentUser, loginWithGoogle } from '../services/authService';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  loginGoogle: (credentials: GoogleLoginCredentials) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [auth, setAuth] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: localStorage.getItem('token'),
  });
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    console.log('Auth context initializing, token present:', !!token);
    console.log('Current path:', location.pathname);
  
    if (token) {
      const verifyTokenAndGetUser = async () => {
        try {
          console.log('Verifying token and fetching current user...');
          const user = await getCurrentUser();
          console.log('User verified successfully:', user);
          setAuth({
            isAuthenticated: true,
            user,
            token,
          });
  
          // If we're at the callback URL and authenticated, let's keep the auth state
          if (location.pathname === '/auth/google/callback') {
            console.log('At Google callback URL with authenticated user');
          }
        } catch (error) {
          console.error('Failed to get current user:', error);
          localStorage.removeItem('token');
          setAuth({
            isAuthenticated: false,
            user: null,
            token: null,
          });
        } finally {
          setIsLoading(false);
        }
      };
  
      verifyTokenAndGetUser();
    } else {
      console.log('No token found, user is not authenticated');
      setIsLoading(false);
    }
  }, [location.pathname]);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    console.log('Attempting login...');
  
    try {
      const response = await loginUser(credentials);
      const { access_token } = response;
      console.log('Login successful, got access token');
      localStorage.setItem('token', access_token);
  
      console.log('Fetching current user data...');
      const user = await getCurrentUser();
      console.log('User data received:', user);
  
      setAuth({
        isAuthenticated: true,
        user,
        token: access_token,
      });
  
      console.log('Login complete, navigating to dashboard');
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  const loginGoogle = async (credentials: GoogleLoginCredentials) => {
    setIsLoading(true);
    console.log('Attempting Google login...');
  
    try {
      const response = await loginWithGoogle(credentials);
      const { access_token } = response;
      console.log('Google login successful, got access token');
      localStorage.setItem('token', access_token);
  
      console.log('Fetching current user data...');
      const user = await getCurrentUser();
      console.log('User data received:', user);
  
      setAuth({
        isAuthenticated: true,
        user,
        token: access_token,
      });
  
      console.log('Google login complete, navigating to dashboard');
      navigate('/dashboard');
    } catch (error) {
      console.error('Google login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setAuth({
      isAuthenticated: false,
      user: null,
      token: null,
    });
    navigate('/login');
  };

  const value = useMemo(
    () => ({
      ...auth,
      login,
      loginGoogle,
      logout,
      isLoading,
    }),
    [auth, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};