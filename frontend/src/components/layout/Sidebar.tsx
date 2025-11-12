import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DocumentsIcon,
  Folder as FolderIcon,
  Storage as IntegrationsIcon,
  ExpandLess,
  ExpandMore,
  Cloud as CloudIcon,
} from '@mui/icons-material';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [integrationsOpen, setIntegrationsOpen] = useState(
    location.pathname.startsWith('/integrations')
  );

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const handleIntegrationsClick = () => {
    setIntegrationsOpen(!integrationsOpen);
    if (!location.pathname.startsWith('/integrations')) {
      navigate('/integrations');
    }
  };

  return (
    <List component="nav" sx={{ mt: 1 }}>
      <ListItemButton
        selected={location.pathname === '/dashboard'}
        onClick={() => handleNavigate('/dashboard')}
      >
        <ListItemIcon>
          <DashboardIcon />
        </ListItemIcon>
        <ListItemText primary="Dashboard" />
      </ListItemButton>

      <ListItemButton
        selected={location.pathname === '/documents'}
        onClick={() => handleNavigate('/documents')}
      >
        <ListItemIcon>
          <DocumentsIcon />
        </ListItemIcon>
        <ListItemText primary="Documents" />
      </ListItemButton>

      <Divider sx={{ my: 2 }} />

      <ListItemButton onClick={handleIntegrationsClick}>
        <ListItemIcon>
          <IntegrationsIcon />
        </ListItemIcon>
        <ListItemText primary="Integrations" />
        {integrationsOpen ? <ExpandLess /> : <ExpandMore />}
      </ListItemButton>

      <Collapse in={integrationsOpen} timeout="auto" unmountOnExit>
        <List component="div" disablePadding>
          <ListItemButton
            sx={{ pl: 4 }}
            selected={location.pathname === '/integrations/google-drive'}
            onClick={() => handleNavigate('/integrations/google-drive')}
          >
            <ListItemIcon>
              <CloudIcon />
            </ListItemIcon>
            <ListItemText primary="Google Drive" />
          </ListItemButton>
        </List>
      </Collapse>
    </List>
  );
};

export default Sidebar;