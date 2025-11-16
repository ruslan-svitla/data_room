import React, { useEffect, useState } from 'react';
import { Box, Button, Card, CardContent, Typography, CircularProgress, Alert, Container, Grid } from '@mui/material';
import healthService, { HealthResponse, DetailedHealthResponse } from '../services/healthService';

const HealthPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<DetailedHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchHealthData();
  }, []);

  const fetchHealthData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await healthService.getHealth();
      setHealth(data);
      setDetailedHealth(null); // Reset detailed health when refreshing basic health
    } catch (err) {
      setError('Failed to fetch health data. Please make sure the API is running.');
      console.error('Health check error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetailedHealthData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await healthService.getDetailedHealth();
      setDetailedHealth(data);
    } catch (err) {
      setError('Failed to fetch detailed health data');
      console.error('Detailed health check error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Check if database is connected based on the string message
  const isDatabaseConnected = (dbStatus: string) => {
    return dbStatus && (
      dbStatus.includes('connected') && !dbStatus.includes('error')
    );
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        API Health Status
      </Typography>
      
      {loading && !health && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}
      
      {error && (
        <Alert severity="error" sx={{ my: 2 }}>
          {error}
          <Button 
            size="small" 
            sx={{ ml: 2 }} 
            onClick={fetchHealthData}
          >
            Retry
          </Button>
        </Alert>
      )}
      
      {health && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Basic Health
                </Typography>
                
                <Box sx={{ mt: 2, mb: 1 }}>
                  <Typography component="span" variant="body1">
                    Status: 
                  </Typography>
                  <Typography 
                    component="span" 
                    variant="body1" 
                    sx={{ 
                      ml: 1, 
                      color: health.status === 'healthy' ? 'green' : 'red',
                      fontWeight: 'bold'
                    }}
                  >
                    {health.status}
                  </Typography>
                </Box>
                
                <Typography variant="body1" gutterBottom>
                  Version: {health.api_version}
                </Typography>
                
                <Typography variant="body1">
                  Environment: {health.environment}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          {detailedHealth && (
            <>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Database
                    </Typography>
                    
                    <Box sx={{ mt: 2, mb: 1 }}>
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          color: isDatabaseConnected(detailedHealth.database) ? 'green' : 'red',
                          fontWeight: 'bold'
                        }}
                      >
                        {detailedHealth.database}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {detailedHealth.settings && (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Settings
                      </Typography>
                      
                      <Typography variant="body1" gutterBottom>
                        Debug Mode: {detailedHealth.settings.debug ? 'Enabled' : 'Disabled'}
                      </Typography>
                      
                      <Typography variant="body1">
                        Project Name: {detailedHealth.settings.project_name}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </>
          )}
        </Grid>
      )}
      
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button 
          variant="contained" 
          onClick={fetchHealthData}
          disabled={loading}
        >
          Refresh Health
        </Button>
        
        <Button 
          variant="outlined" 
          onClick={fetchDetailedHealthData} 
          disabled={loading || !health}
        >
          {detailedHealth ? 'Refresh Detailed Health' : 'Check Detailed Health'}
        </Button>
      </Box>
    </Container>
  );
};

export default HealthPage;