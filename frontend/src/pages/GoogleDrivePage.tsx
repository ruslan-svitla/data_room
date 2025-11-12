import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  Grid,
  CircularProgress,
  Breadcrumbs,
  Link,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  Chip,
  Tooltip,
  LinearProgress,
  ToggleButtonGroup,
  ToggleButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Cloud as CloudIcon,
  CloudOff as CloudOffIcon,
  Search as SearchIcon,
  ArrowBack as ArrowBackIcon,
  Folder as FolderIcon,
  Description as FileIcon,
  CloudDownload as ImportIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Image as ImageIcon,
  VideoLibrary as VideoIcon,
  AudioFile as AudioIcon,
  PictureAsPdf as PdfIcon,
  TableChart as SpreadsheetIcon,
  Slideshow as PresentationIcon,
  Article as DocumentIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
} from '@mui/icons-material';

import {
  getGoogleDriveConnectionStatus,
  initiateGoogleDriveAuth,
  disconnectGoogleDrive,
  listGoogleDriveFiles,
  searchGoogleDriveFiles,
  importFromGoogleDrive,
  checkGoogleApiCredentials,
} from '../services/googleDriveService';
import { GoogleDriveFile, GoogleDriveImportRequest, GoogleDriveImportResult } from '../types';

const GoogleDrivePage = () => {
  const queryClient = useQueryClient();
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>();
  // Define the type for path items
  type FolderPathItem = { id: string | undefined; name: string };

  const [folderPath, setFolderPath] = useState<FolderPathItem[]>([
    { id: undefined, name: 'Root' },
  ]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [isSearchMode, setIsSearchMode] = useState(false);

  // API credentials status
  const [apiCredentialsValid, setApiCredentialsValid] = useState<boolean | null>(null);
  const [apiCredentialsMessage, setApiCredentialsMessage] = useState<string | undefined>();

  // View mode state (grid or list)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(() => {
    const savedViewMode = localStorage.getItem('googleDriveViewMode');
    return (savedViewMode === 'list' ? 'list' : 'grid') as 'grid' | 'list';
  });

  // Import dialog state
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [includeFolders, setIncludeFolders] = useState(true);
  const [maxDepth, setMaxDepth] = useState(5);
  const [importResult, setImportResult] = useState<GoogleDriveImportResult | null>(null);

  // Query for connection status
  const {
    data: connectionStatus,
    isLoading: isLoadingStatus,
    error: connectionError,
    refetch: refetchStatus,
  } = useQuery(['googleDriveStatus'], () => getGoogleDriveConnectionStatus(), {
    retry: false,
  });

  // Query for file listing
  const {
    data: fileListData,
    isLoading: isLoadingFiles,
    error: filesError,
    refetch: refetchFiles,
  } = useQuery(
    ['googleDriveFiles', currentFolderId],
    () => listGoogleDriveFiles(currentFolderId),
    {
      enabled: !!connectionStatus?.connected && !isSearchMode,
      retry: false,
    }
  );

  // Query for search results
  const {
    data: searchResults,
    isLoading: isLoadingSearch,
    error: searchError,
  } = useQuery(
    ['googleDriveSearch', searchQuery],
    () => searchGoogleDriveFiles(searchQuery),
    {
      enabled: !!connectionStatus?.connected && !!searchQuery && isSearchMode,
      retry: false,
    }
  );

  // Mutation for initiating auth
  const { mutate: initiateAuth, isLoading: isAuthenticating } = useMutation(
    initiateGoogleDriveAuth,
    {
      onSuccess: (data) => {
        window.location.href = data.authorization_url;
      },
    }
  );

  // Mutation for disconnecting
  const { mutate: disconnect, isLoading: isDisconnecting } = useMutation(
    disconnectGoogleDrive,
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['googleDriveStatus']);
        setCurrentFolderId(undefined);
        setFolderPath([{ id: undefined, name: 'Root' }]);
        setSelectedFiles([]);
      },
    }
  );

  // Mutation for importing files
  const { mutate: importFiles, isLoading: isImporting } = useMutation(
    (request: GoogleDriveImportRequest) => importFromGoogleDrive(request),
    {
      onSuccess: (data) => {
        console.log('Import successful, received data:', data);
        setImportResult(data);
        // Invalidate documents query so DocumentsPage refreshes
        queryClient.invalidateQueries(['documents']);
      },
      onError: (error) => {
        console.error('Import failed:', error);
        // Create a safe error result
        setImportResult({
          imported_document_ids: [],
          imported_folder_ids: [],
          skipped_items: [{ id: 'error', name: 'Error', error: String(error) }],
          total_documents_imported: 0,
          total_folders_imported: 0,
          total_skipped: 1
        });
      }
    }
  );

  // Check if Google API credentials are valid
  useEffect(() => {
    const checkApiCredentials = async () => {
      try {
        const status = await checkGoogleApiCredentials();
        console.log('API credentials check returned:', status);
        setApiCredentialsValid(status.valid);
        setApiCredentialsMessage(status.message);
      } catch (error) {
        setApiCredentialsValid(false);
        setApiCredentialsMessage('Failed to check API credentials status');
        console.error('Error checking API credentials:', error);
      }
    };
  
    // Initial check
    checkApiCredentials();
  
    // Set up interval to check periodically (every 30 seconds)
    const intervalId = setInterval(() => {
      console.log('Performing periodic API credentials check');
      checkApiCredentials();
    }, 30000);
  
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);
  
  // Effect to check URL for OAuth callback
  useEffect(() => {
    const url = new URL(window.location.href);
    const code = url.searchParams.get('code');
    const error = url.searchParams.get('error');
  
    // Clean up URL parameters
    window.history.replaceState({}, document.title, '/integrations/google-drive');
  
    if (code) {
      console.log('OAuth code received, refreshing connection status');
      // Refresh the status to confirm the authentication worked
      setTimeout(() => {
        // Force invalidate any cache to get fresh data
        queryClient.invalidateQueries(['googleDriveStatus']);
        refetchStatus();
      }, 2000); // Increase timeout to ensure backend has time to process
    }
  
    if (error) {
      console.error('Google Drive authentication error:', error);
      // Set an error state or show a notification
      alert(`Error connecting to Google Drive: ${error}`);
    }
  }, [refetchStatus, queryClient]);
  
  // Force reload the auth status when the page loads to ensure correct state
  useEffect(() => {
    // Check if we have a token but aren't connected
    const token = localStorage.getItem('token');
  
    if (token) {
      console.log('Token exists, refreshing Google Drive status');
      // First clear any existing data to avoid confusion
      queryClient.resetQueries(['googleDriveStatus']);
      // Then fetch fresh data
      refetchStatus();
  
      // Set an interval to check status a few more times (in case of backend processing delay)
      const statusCheckInterval = setInterval(() => {
        console.log('Rechecking Google Drive connection status');
        refetchStatus();
      }, 3000);
  
      // Clear interval after a few checks
      setTimeout(() => {
        clearInterval(statusCheckInterval);
      }, 12000); // 4 checks total
  
      // Clean up on unmount
      return () => {
        clearInterval(statusCheckInterval);
      };
    } else {
      console.log('No auth token found, user needs to login');
    }
  }, [refetchStatus, queryClient]);

  // Handle folder navigation
  const navigateToFolder = (folderId: string | undefined, folderName: string) => {
    setCurrentFolderId(folderId);
  
    if (folderId === undefined) {
      // Going back to root
      setFolderPath([{ id: undefined, name: 'Root' }]);
    } else {
      // Find the index of the folder in the path if it exists
      const folderIndex = folderPath.findIndex((item) => item.id === folderId);
  
      if (folderIndex !== -1) {
        // If folder is in path, trim the path up to this folder
        setFolderPath(folderPath.slice(0, folderIndex + 1));
      } else {
        // Otherwise add to the path
        const pathItem: FolderPathItem = { id: folderId, name: folderName };
        setFolderPath([...folderPath, pathItem]);
      }
    }
  
    // Clear selection when navigating
    setSelectedFiles([]);
  
    // If in search mode, exit it when navigating
    if (isSearchMode) {
      setIsSearchMode(false);
      setSearchQuery('');
    }
  };
  
  // Update folder path when we receive data
  useEffect(() => {
    if (!isSearchMode && fileListData) {
      // If we're at root, reset the path
      if (fileListData.is_root) {
        setFolderPath([{ id: undefined, name: 'Root' }]);
      } 
      // If we have a current folder
      else if (fileListData.current_folder) {
        const currentFolder = fileListData.current_folder;
  
        // Check if this folder is already in the path
        const folderIndex = folderPath.findIndex(item => item.id === currentFolder.id);
        if (folderIndex === -1) {
          // It's not in the path, so we need to rebuild path
          // If we have parent folders, add them to the path
          const newPath: FolderPathItem[] = [{ id: undefined, name: 'Root' }];
          
          if (fileListData.parent_folders && fileListData.parent_folders.length > 0) {
            // We know about direct parent
            fileListData.parent_folders.forEach(parent => {
              const pathItem: FolderPathItem = { id: parent.id, name: parent.name };
              newPath.push(pathItem);
            });
          }
          
          // Add current folder to path
          const currentFolderPathItem: FolderPathItem = { id: currentFolder.id, name: currentFolder.name };
          newPath.push(currentFolderPathItem);
          setFolderPath(newPath);
        }
      }
    }
  }, [fileListData, isSearchMode]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setIsSearchMode(true);
      // Clear selection when searching
      setSelectedFiles([]);
    }
  };

  // Handle clearing search
  const handleClearSearch = () => {
    setIsSearchMode(false);
    setSearchQuery('');
    // Refetch the current folder contents
    refetchFiles();
  };
  
  // Handle view mode change
  const handleViewModeChange = (_: React.MouseEvent<HTMLElement>, newViewMode: 'grid' | 'list' | null) => {
    if (newViewMode !== null) {
      setViewMode(newViewMode);
      localStorage.setItem('googleDriveViewMode', newViewMode);
    }
  };

  // Handle file selection toggle
  const toggleFileSelection = (fileId: string) => {
    setSelectedFiles((prev) =>
      prev.includes(fileId)
        ? prev.filter((id) => id !== fileId)
        : [...prev, fileId]
    );
  };

  // Handle import dialog
  const handleOpenImportDialog = () => {
    try {
      setImportDialogOpen(true);
      setImportResult(null);
    } catch (err) {
      console.error('Error opening import dialog:', err);
      // Create a fallback UI state
      alert('There was a problem opening the import dialog. Please try again.');
    }
  };

  const handleCloseImportDialog = () => {
    setImportDialogOpen(false);
    if (importResult) {
      // Refresh files list if import was successful
      refetchFiles();
  
      // Make sure documents list is refreshed when we return to documents page
      queryClient.invalidateQueries(['documents']);
    }
  };

  const handleImport = () => {
    try {
      const request: GoogleDriveImportRequest = {
        file_ids: selectedFiles,
        include_folders: includeFolders,
        max_depth: maxDepth,
      };
  
      console.log('Sending import request:', request);
      importFiles(request);
    } catch (err) {
      console.error('Error submitting import request:', err);
      // Provide fallback UI state
      setImportResult({
        imported_document_ids: [],
        imported_folder_ids: [],
        skipped_items: selectedFiles.map(id => ({
          id: id,
          name: filesToDisplay?.find(f => f.id === id)?.name || 'Unknown file',
          error: 'Internal application error. Please try again.'
        })),
        total_documents_imported: 0,
        total_folders_imported: 0,
        total_skipped: selectedFiles.length
      });
    }
  };

  // Determine if it's loading
  const isLoading = isLoadingStatus || isLoadingFiles || isLoadingSearch || isAuthenticating || isDisconnecting || isImporting;

  // Get the current files to display (either from folder listing or search results)
  const filesToDisplay = isSearchMode ? searchResults?.files : fileListData?.files;

  // Helper function to get icon for file type
  const getFileIcon = (file: GoogleDriveFile) => {
    if (file.is_folder) return <FolderIcon color="primary" />;
    
    const mimeType = file.mime_type || '';
    
    if (mimeType.includes('image/')) return <ImageIcon color="success" />;
    if (mimeType.includes('video/')) return <VideoIcon color="error" />;
    if (mimeType.includes('audio/')) return <AudioIcon color="secondary" />;
    if (mimeType.includes('pdf')) return <PdfIcon color="error" />;
    if (mimeType.includes('spreadsheet') || mimeType.includes('excel') || mimeType.includes('sheet')) 
      return <SpreadsheetIcon color="success" />;
    if (mimeType.includes('presentation') || mimeType.includes('powerpoint') || mimeType.includes('slides')) 
      return <PresentationIcon color="warning" />;
    if (mimeType.includes('document') || mimeType.includes('word') || mimeType.includes('text/')) 
      return <DocumentIcon color="primary" />;
    
    return <FileIcon />;
  };

  // Render connection status and authentication UI
  const renderConnectionStatus = () => {
    if (isLoadingStatus) {
      return (
        <Box display="flex" alignItems="center">
          <CircularProgress size={20} sx={{ mr: 1 }} />
          <Typography>Checking connection status...</Typography>
        </Box>
      );
    }
  
    if (connectionError) {
      let errorMessage = 'Failed to check connection status';
  
      if (connectionError && typeof connectionError === 'object') {
        if ('response' in connectionError && connectionError.response && 
            typeof connectionError.response === 'object' && 'data' in connectionError.response) {
          const responseData = connectionError.response.data;
          if (responseData && typeof responseData === 'object' && 'detail' in responseData) {
            errorMessage = String(responseData.detail);
          }
        } else if ('message' in connectionError && typeof connectionError.message === 'string') {
          errorMessage = connectionError.message;
        }
      }
  
      return (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorMessage}
        </Alert>
      );
    }
  
    // Display warning if Google API credentials are invalid
    if (apiCredentialsValid === false) {
      return (
        <Box>
          <Alert severity="warning" icon={<CloudOffIcon />} sx={{ mb: 2 }}>
            {apiCredentialsMessage || 'Google Drive service is temporarily unavailable. Please try again later.'}
          </Alert>
          <Button
            variant="contained"
            startIcon={<CloudIcon />}
            onClick={() => initiateAuth()}
            disabled={true}
          >
            Connect to Google Drive
          </Button>
        </Box>
      );
    }
  
    if (!connectionStatus?.connected) {
      return (
        <Box>
          <Alert severity="info" icon={<CloudOffIcon />} sx={{ mb: 2 }}>
            You are not connected to Google Drive. Connect to access your files.
          </Alert>
          <Button
            variant="contained"
            startIcon={<CloudIcon />}
            onClick={() => initiateAuth()}
            disabled={isAuthenticating || apiCredentialsValid === false}
          >
            {isAuthenticating ? 'Connecting...' : 'Connect to Google Drive'}
          </Button>
        </Box>
      );
    }
  
    return (
      <Box display="flex" flexDirection="column">
        <Alert severity="success" icon={<CloudIcon />} sx={{ mb: 2 }}>
          Connected to Google Drive as {connectionStatus.user_email}
        </Alert>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Button
            variant="outlined"
            color="error"
            startIcon={<CloudOffIcon />}
            onClick={() => disconnect()}
            disabled={isDisconnecting}
          >
            {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
          </Button>
  
          {selectedFiles.length > 0 && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<ImportIcon />}
              onClick={handleOpenImportDialog}
              disabled={isImporting}
            >
              Import {selectedFiles.length} {selectedFiles.length === 1 ? 'item' : 'items'}
            </Button>
          )}
        </Box>
      </Box>
    );
  };

  // Render breadcrumb navigation
  const renderBreadcrumbs = () => {
    return (
      <Breadcrumbs separator="›" aria-label="breadcrumb" sx={{ mb: 2 }}>
        {folderPath.map((folder, index) => {
          const isLast = index === folderPath.length - 1;
          
          return isLast ? (
            <Typography key={folder.id || 'root'} color="text.primary">
              {folder.name}
            </Typography>
          ) : (
            <Link
              key={folder.id || 'root'}
              component="button"
              underline="hover"
              color="inherit"
              onClick={() => navigateToFolder(folder.id, folder.name)}
            >
              {folder.name}
            </Link>
          );
        })}
      </Breadcrumbs>
    );
  };

  // Render search bar
  const renderSearchBar = () => {
    return (
      <Box sx={{ mb: 2 }}>
        <Box component="form" onSubmit={handleSearch} sx={{ mb: 2 }}>
          <TextField
            fullWidth
            placeholder="Search in Google Drive"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: isSearchMode && (
                <InputAdornment position="end">
                  <IconButton onClick={handleClearSearch} edge="end">
                    <CloseIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Box>
  
        {/* View mode toggle */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={handleViewModeChange}
            size="small"
            aria-label="view mode"
          >
            <ToggleButton value="grid" aria-label="grid view">
              <GridViewIcon fontSize="small" />
              <Typography variant="caption" sx={{ ml: 0.5 }}>Grid</Typography>
            </ToggleButton>
            <ToggleButton value="list" aria-label="list view">
              <ListViewIcon fontSize="small" />
              <Typography variant="caption" sx={{ ml: 0.5 }}>List</Typography>
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Box>
    );
  };

  // Render files list
  const renderFilesList = () => {
    if (isLoadingFiles || isLoadingSearch) {
      return (
        <Box sx={{ mt: 2 }}>
          <CircularProgress />
        </Box>
      );
    }
  
    if (filesError || searchError) {
      const error = filesError || searchError;
      let errorMessage = 'Failed to load files';
  
      if (error && typeof error === 'object') {
        if ('response' in error && error.response && 
            typeof error.response === 'object' && 'data' in error.response) {
          const responseData = error.response.data;
          if (responseData && typeof responseData === 'object' && 'detail' in responseData) {
            errorMessage = String(responseData.detail);
          }
        } else if ('message' in error && typeof error.message === 'string') {
          errorMessage = error.message;
        }
      }
  
      return (
        <Alert severity="error" sx={{ mt: 2 }}>
          {errorMessage}
        </Alert>
      );
    }
  
    if (!filesToDisplay || filesToDisplay.length === 0) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          {isSearchMode
            ? 'No files match your search'
            : currentFolderId
            ? 'This folder is empty'
            : 'Your Google Drive is empty'}
        </Alert>
      );
    }
  
    // Format date helper function
    const formatDate = (dateString: string) => {
      const date = new Date(dateString);
      return date.toLocaleString();
    };
  
    // Search results title if in search mode
    const searchResultsTitle = isSearchMode && (
      <Typography variant="subtitle1" sx={{ mb: 2 }}>
        Search results for "{searchQuery}"
      </Typography>
    );
  
    // Grid view rendering
    if (viewMode === 'grid') {
      return (
        <>
          {searchResultsTitle}
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {filesToDisplay.map((file) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={file.id}>
                <Paper
                  elevation={2}
                  sx={{
                    p: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    cursor: file.is_folder ? 'pointer' : 'default',
                    position: 'relative',
                    border: selectedFiles.includes(file.id)
                      ? '2px solid #1976d2'
                      : '2px solid transparent',
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: '0 5px 15px rgba(0,0,0,0.08)',
                    },
                  }}
                  onClick={() => {
                    if (file.is_folder) {
                      navigateToFolder(file.id, file.name);
                    } else {
                      toggleFileSelection(file.id);
                    }
                  }}
                >
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      display: !file.is_folder ? 'flex' : 'none',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '2px solid #e0e0e0',
                      bgcolor: selectedFiles.includes(file.id) ? 'primary.main' : 'transparent',
                    }}
                    onClick={(e) => {
                      if (!file.is_folder) {
                        e.stopPropagation();
                        toggleFileSelection(file.id);
                      }
                    }}
                  >
                    {selectedFiles.includes(file.id) && <CheckIcon fontSize="small" sx={{ color: 'white' }} />}
                  </Box>
  
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 1,
                    }}
                  >
                    {getFileIcon(file)}
                  </Box>
  
                  <Tooltip title={file.name} placement="top">
                    <Typography
                      variant="subtitle2"
                      align="center"
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {file.name}
                    </Typography>
                  </Tooltip>
  
                  <Typography variant="caption" color="text.secondary" align="center">
                    {file.size ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : ''}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </>
      );
    }
  
    // List view rendering
    return (
      <>
        {searchResultsTitle}
        <TableContainer component={Paper} sx={{ mt: 1 }}>
          <Table size="small" aria-label="files table">
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" width="48px"></TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Modified</TableCell>
                <TableCell>Created</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filesToDisplay.map((file) => {
                const isSelected = selectedFiles.includes(file.id);
                return (
                  <TableRow 
                    key={file.id}
                    hover
                    onClick={() => {
                      if (file.is_folder) {
                        navigateToFolder(file.id, file.name);
                      } else {
                        toggleFileSelection(file.id);
                      }
                    }}
                    sx={{
                      cursor: file.is_folder ? 'pointer' : 'default',
                      backgroundColor: isSelected ? 'rgba(25, 118, 210, 0.08)' : 'inherit',
                      '&:hover': {
                        backgroundColor: isSelected ? 'rgba(25, 118, 210, 0.12)' : 'rgba(0, 0, 0, 0.04)',
                      }
                    }}
                  >
                    <TableCell padding="checkbox">
                      {!file.is_folder && (
                        <Box 
                          sx={{
                            width: 24,
                            height: 24,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '2px solid #e0e0e0',
                            bgcolor: isSelected ? 'primary.main' : 'transparent',
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFileSelection(file.id);
                          }}
                        >
                          {isSelected && <CheckIcon fontSize="small" sx={{ color: 'white' }} />}
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getFileIcon(file)}
                        <Tooltip title={file.name}>
                          <Typography 
                            variant="body2"
                            sx={{
                              maxWidth: '300px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {file.name}
                          </Typography>
                        </Tooltip>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {file.is_folder ? 'Folder' : file.mime_type?.split('/')[1] || 'File'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {file.size ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(file.modified_time)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(file.created_time)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </>
    );
  };

  // Render import dialog
  const renderImportDialog = () => {
    // Add a debug log to see what data we have
    console.log("Import result state:", importResult);
  
    return (
      <Dialog
        open={importDialogOpen}
        onClose={handleCloseImportDialog}
        aria-labelledby="import-dialog-title"
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle id="import-dialog-title">
          Import from Google Drive
        </DialogTitle>
        <DialogContent>
          {isImporting ? (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Importing files...
              </Typography>
              <LinearProgress />
            </Box>
          ) : importResult ? (
            <Box sx={{ mt: 2 }}>
              <Alert 
                severity={importResult.total_skipped > 0 ? "warning" : "success"}
                sx={{ mb: 2 }}
              >
                {importResult.total_documents_imported + importResult.total_folders_imported} items imported successfully.
                {importResult.total_skipped > 0 && ` ${importResult.total_skipped} items skipped.`}
              </Alert>
              
              {(importResult.imported_document_ids.length > 0 || importResult.imported_folder_ids.length > 0) && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Successfully imported:
                  </Typography>
                  <Box sx={{ maxHeight: '150px', overflow: 'auto' }}>
                    {/* Show document IDs since we don't have names in the response */}
                    {importResult.imported_document_ids.map((id) => (
                      <Chip
                        key={`doc-${id}`}
                        icon={<CheckIcon />}
                        label={`Document: ${id.substring(0, 8)}...`}
                        color="success"
                        size="small"
                        sx={{ m: 0.5 }}
                      />
                    ))}
                    {importResult.imported_folder_ids.map((id) => (
                      <Chip
                        key={`folder-${id}`}
                        icon={<CheckIcon />}
                        label={`Folder: ${id.substring(0, 8)}...`}
                        color="success"
                        size="small"
                        sx={{ m: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>
              )}
              
              {importResult.skipped_items.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Skipped items:
                  </Typography>
                  <Box sx={{ maxHeight: '150px', overflow: 'auto' }}>
                    {importResult.skipped_items.map((item) => (
                      <Tooltip key={`skipped-${item.id}`} title={item.error || 'Unknown error'}>
                        <Chip
                          icon={<CloseIcon />}
                          label={item.name || item.id || 'Unknown file'}
                          color="error"
                          size="small"
                          sx={{ m: 0.5 }}
                        />
                      </Tooltip>
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          ) : (
            <>
              <Typography variant="body2" sx={{ mb: 2 }}>
                You are about to import {selectedFiles.length} {selectedFiles.length === 1 ? 'item' : 'items'} from Google Drive to your Data Room.
              </Typography>
              
              {selectedFiles.some((id) => {
                const file = filesToDisplay?.find((f) => f.id === id);
                return file?.is_folder;
              }) && (
                <Box sx={{ mt: 2 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={includeFolders}
                        onChange={(e) => setIncludeFolders(e.target.checked)}
                      />
                    }
                    label="Import folder contents recursively"
                  />
                  
                  {includeFolders && (
                    <TextField
                      type="number"
                      label="Maximum folder depth"
                      value={maxDepth}
                      onChange={(e) => setMaxDepth(parseInt(e.target.value, 10) || 1)}
                      inputProps={{ min: 1, max: 10 }}
                      size="small"
                      sx={{ ml: 4, width: 150 }}
                    />
                  )}
                </Box>
              )}
              
              {/* Removed checkbox for includeShared as it's not supported by the backend */}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseImportDialog}>
            {importResult ? 'Close' : 'Cancel'}
          </Button>
          {!importResult && !isImporting && (
            <Button onClick={handleImport} variant="contained" disabled={isImporting}>
              Import
            </Button>
          )}
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <CloudIcon sx={{ mr: 1, color: 'primary.main' }} fontSize="large" />
        <Typography variant="h4">Google Drive Integration</Typography>
      </Box>

      {renderConnectionStatus()}

      {connectionStatus?.connected && (
        <Paper sx={{ mt: 4, p: 3 }}>
          {/* Back button for search mode */}
          {isSearchMode && (
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={handleClearSearch}
              sx={{ mb: 2 }}
            >
              Back to files
            </Button>
          )}

          {/* Breadcrumbs for navigation */}
          {!isSearchMode && renderBreadcrumbs()}

          {/* Search bar */}
          {renderSearchBar()}

          {/* Files list */}
          {renderFilesList()}
        </Paper>
      )}

      {/* Import dialog */}
      {renderImportDialog()}
    </Box>
  );
};

export default GoogleDrivePage;