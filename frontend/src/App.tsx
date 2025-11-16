import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import IntegrationsPage from './pages/IntegrationsPage';
import GoogleDrivePage from './pages/GoogleDrivePage';
import GoogleAuthCallback from './pages/GoogleAuthCallback';
import HealthPage from './pages/HealthPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/health" element={<HealthPage />} />
        
          {/* Special route for Google Auth callback */}
          <Route path="/auth/google/callback" element={
            <ProtectedRoute>
              <GoogleAuthCallback />
            </ProtectedRoute>
          } />
        
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="integrations/google-drive" element={<GoogleDrivePage />} />
          </Route>
        
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
    </AuthProvider>
  );
}

export default App;