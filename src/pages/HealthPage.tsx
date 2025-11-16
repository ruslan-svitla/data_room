import React, { useEffect, useState } from 'react';
import healthService, { DetailedHealthResponse, HealthResponse } from '../services/healthService';
import './HealthPage.css';

const HealthPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<DetailedHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch basic health data on component mount
    fetchHealthData();
  }, []);

  const fetchHealthData = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await healthService.getHealth();
      setHealth(data);
    } catch (err) {
      setError('Failed to fetch health data');
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

  if (loading && !health) {
    return <div className="health-page">Loading health data...</div>;
  }

  if (error && !health) {
    return (
      <div className="health-page error">
        <h1>Error</h1>
        <p>{error}</p>
        <button onClick={fetchHealthData}>Retry</button>
      </div>
    );
  }

  // Check if database is connected based on the string message
  const isDatabaseConnected = (dbStatus: string) => {
    return dbStatus && (
      dbStatus.includes('connected') && !dbStatus.includes('error')
    );
  };

  return (
    <div className="health-page">
      <h1>API Health Status</h1>

      {health && (
        <div className="health-info">
          <div className="status-card">
            <h2>Basic Health</h2>
            <p>Status: <span className={health.status === 'healthy' ? 'status-up' : 'status-down'}>{health.status}</span></p>
            <p>Version: {health.api_version}</p>
            <p>Environment: {health.environment}</p>
          </div>
        </div>
      )}

      {detailedHealth && (
        <div className="detailed-health">
          <div className="status-card">
            <h2>Database</h2>
            <p>Status: <span className={isDatabaseConnected(detailedHealth.database) ? 'status-up' : 'status-down'}>
              {detailedHealth.database}
            </span></p>
          </div>

          {detailedHealth.settings && (
            <div className="status-card">
              <h2>Settings</h2>
              <p>Debug Mode: {detailedHealth.settings.debug ? 'Enabled' : 'Disabled'}</p>
              <p>Project Name: {detailedHealth.settings.project_name}</p>
            </div>
          )}
        </div>
      )}

      <div className="health-actions">
        <button onClick={fetchHealthData}>Refresh Health</button>
        <button onClick={fetchDetailedHealthData} disabled={loading}>
          {detailedHealth ? 'Refresh Detailed Health' : 'Check Detailed Health'}
        </button>
      </div>
    </div>
  );
};

export default HealthPage;