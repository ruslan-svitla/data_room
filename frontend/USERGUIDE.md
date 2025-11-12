# Data Room Google Drive Integration - User Guide

This guide will help you navigate and use the Google Drive integration feature in the Data Room application.

## Table of Contents

1. [Login](#1-login)
2. [Dashboard](#2-dashboard)
3. [Integrations](#3-integrations)
4. [Google Drive Integration](#4-google-drive-integration)
5. [Importing Files](#5-importing-files)
6. [Managing Imported Files](#6-managing-imported-files)
7. [Troubleshooting](#7-troubleshooting)

## 1. Login

1. Open the Data Room application in your browser
2. On the login screen, enter your username and password
   - Default test credentials: `user1` / `password1`
3. Click the "Login" button
4. If there are any issues, check the error message displayed on the screen

## 2. Dashboard

After logging in, you'll be directed to the Dashboard:

- The Dashboard shows a summary of your Data Room
- Active integrations are displayed with their status
- Recent activities are listed
- You can access all main features from the sidebar

## 3. Integrations

To manage your integrations:

1. Click "Integrations" in the sidebar
2. You'll see a list of available integrations
3. The Google Drive integration card shows the connection status
   - If connected, you'll see your Google account email
   - If not connected, you'll see a "Connect" button

## 4. Google Drive Integration

### Connecting to Google Drive

1. Go to the "Integrations" page
2. Click on the "Google Drive" card or "Connect" button
3. You'll be redirected to Google's authorization page
4. Sign in to your Google account and grant permissions to the application
5. You'll be redirected back to the Data Room application
6. Your Google Drive is now connected

### Browsing Google Drive Files

1. Go to the "Google Drive" page from the sidebar
2. You'll see a list of your Google Drive files and folders
3. Click on a folder to navigate into it
4. Use the breadcrumb navigation at the top to navigate back
5. Use the search bar to find specific files
6. Each file shows the name, type, size, and last modified date

## 5. Importing Files

To import files from Google Drive to Data Room:

1. Browse to the location of the files you want to import
2. Select files by clicking the checkbox next to them
3. Click the "Import Selected" button at the bottom
4. In the import dialog:
   - Choose whether to import recursively (for folders)
   - Choose whether to include shared files
   - Set the maximum folder depth (for recursive imports)
5. Click "Import" to start the process
6. A progress indicator will show the import status
7. When complete, a summary will show successful and failed imports

### Bulk Import Options

For folders:
- Enable "Recursive" to import all subfolders and their contents
- Set "Max Depth" to limit how deep the recursive import will go
- Enable "Include Shared Files" to import files shared with you

## 6. Managing Imported Files

After importing files:

1. Go to the "Documents" page from the sidebar
2. You'll see all imported files from various sources
3. Files imported from Google Drive will be marked with the source "Google Drive"
4. You can search, filter, and sort your documents
5. Click on a document to view its details or open it

## 7. Troubleshooting

### Connection Issues

If you have trouble connecting to Google Drive:
- Check your internet connection
- Ensure your Google account has sufficient permissions
- Try disconnecting and reconnecting

### Import Failures

If files fail to import:
- Check if the file type is supported
- Verify the file size is within limits
- Ensure you have sufficient permissions for the file
- Try importing the file individually

### Error Messages

Common error messages and solutions:
- "Not authenticated with Google Drive": Go to Integrations and reconnect
- "File not found": The file may have been deleted or permissions changed
- "Insufficient permissions": You don't have access to the file
- "File too large": The file exceeds the size limit

For additional help, contact your system administrator.