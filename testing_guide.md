# Google Drive Integration Testing Guide

This guide explains how to test the Google Drive integration functionality in the Data Room backend application. The integration allows users to authenticate with Google Drive and import selected files and folders into the Data Room.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Authentication](#authentication)
3. [Google Drive Operations](#google-drive-operations)
4. [File Import](#file-import)
5. [Disconnection](#disconnection)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before testing the Google Drive integration, ensure you have:

1. **Google Cloud Project Configuration**
   - Created a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enabled the Google Drive API
   - Created OAuth credentials (Web application type)
   - Added `http://localhost:8000/api/v1/integrations/google/callback` as an authorized redirect URI

2. **Environment Variables**
   - Set up the following variables in your `.env` file:
     ```
     GOOGLE_DRIVE_CLIENT_ID=your_client_id_here
     GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret_here
     GOOGLE_DRIVE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback
     ```

3. **Backend Server**
   - Started the backend server with `uvicorn app.main:app --reload`

## Authentication

### Step 1: Login to the Data Room Application

First, you need to authenticate with the Data Room application to obtain a JWT token:

```bash
# Login to obtain JWT token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }' \
  | json_pp
```

Expected Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save the `access_token` for use in subsequent requests.

### Step 2: Initiate Google Drive Authentication

Start the OAuth flow to connect with Google Drive:

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/google/link" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}" \
  | json_pp
```

Expected Response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=..."
}
```

### Step 3: Complete OAuth Flow

1. Copy the `auth_url` from the previous response
2. Open it in your browser
3. Sign in to your Google account if necessary
4. Grant the requested permissions
5. You'll be redirected to a URL like:
   `http://localhost:8000/api/v1/integrations/google/callback?code=4/0AfJohXmCD3Kxxxxxxxxxx`
6. The backend will automatically exchange this code for access and refresh tokens

### Step 4: Verify Connection Status

Confirm that the Google Drive connection was successful:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "connected": true,
  "user_email": "your-email@gmail.com"
}
```

## Google Drive Operations

### List Files from Google Drive

Retrieve a list of files from the connected Google Drive:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/files" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "files": [
    {
      "id": "1aBcD_EfGhIjKlMnOpQrStUv",
      "name": "Example Document.docx",
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 12345,
      "created_time": "2023-06-15T10:30:45Z",
      "modified_time": "2023-06-16T14:20:30Z",
      "is_folder": false,
      "web_view_link": "https://drive.google.com/file/d/1aBcD_EfGhIjKlMnOpQrStUv/view"
    },
    {
      "id": "2aBcD_EfGhIjKlMnOpQrStUv",
      "name": "Example Folder",
      "mime_type": "application/vnd.google-apps.folder",
      "size": null,
      "created_time": "2023-05-10T08:15:22Z",
      "modified_time": "2023-06-01T11:45:33Z",
      "is_folder": true,
      "web_view_link": "https://drive.google.com/drive/folders/2aBcD_EfGhIjKlMnOpQrStUv"
    }
    // More files...
  ],
  "next_page_token": "someTokenValue123"
}
```

You can also list files in a specific folder:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/files?folder_id=FOLDER_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

### View File Details

Get detailed information about a specific file:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/files/FILE_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "id": "1aBcD_EfGhIjKlMnOpQrStUv",
  "name": "Example Document.docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "size": 12345,
  "created_time": "2023-06-15T10:30:45Z",
  "modified_time": "2023-06-16T14:20:30Z",
  "is_folder": false,
  "web_view_link": "https://drive.google.com/file/d/1aBcD_EfGhIjKlMnOpQrStUv/view",
  "description": "This is an example document",
  "starred": false,
  "trashed": false,
  "parents": ["parentFolderId123"]
}
```

### Search Files

Search for files in Google Drive:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/search?query=example" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "files": [
    {
      "id": "1aBcD_EfGhIjKlMnOpQrStUv",
      "name": "Example Document.docx",
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 12345,
      "created_time": "2023-06-15T10:30:45Z",
      "modified_time": "2023-06-16T14:20:30Z",
      "is_folder": false,
      "web_view_link": "https://drive.google.com/file/d/1aBcD_EfGhIjKlMnOpQrStUv/view"
    }
    // More matching files...
  ]
}
```

### Check Storage Usage

View storage utilization information:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/storage" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "usage": 2500000000,  // Bytes used
  "limit": 15000000000,  // Total storage limit
  "usage_in_drive": 2000000000,  // Bytes used in Drive
  "usage_in_drive_trash": 500000000  // Bytes used in Trash
}
```

## File Import

### Import a Single File

Import one file from Google Drive to the Data Room:

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/google/import" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["FILE_ID"],
    "parent_folder_id": null,
    "recursive": false,
    "include_shared": false
  }' \
  | json_pp
```

Expected Response:
```json
{
  "import_id": "imp_123456789",
  "status": "completed", 
  "results": {
    "successful": [
      {
        "file_id": "1aBcD_EfGhIjKlMnOpQrStUv",
        "name": "Example Document.docx",
        "data_room_id": "dr_987654321"
      }
    ],
    "failed": []
  },
  "total_files": 1,
  "successful_count": 1,
  "failed_count": 0
}
```

### Import a Folder (Recursively)

Import a folder and all its contents:

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/google/import" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["FOLDER_ID"],
    "parent_folder_id": null,
    "recursive": true,
    "include_shared": true,
    "max_depth": 3
  }' \
  | json_pp
```

Expected Response:
```json
{
  "import_id": "imp_987654321",
  "status": "completed",
  "results": {
    "successful": [
      {
        "file_id": "3aBcD_EfGhIjKlMnOpQrStUv",
        "name": "Document1.pdf",
        "data_room_id": "dr_123456"
      },
      {
        "file_id": "4aBcD_EfGhIjKlMnOpQrStUv",
        "name": "Spreadsheet.xlsx",
        "data_room_id": "dr_789012"
      }
      // More files...
    ],
    "failed": []
  },
  "total_files": 10,
  "successful_count": 10,
  "failed_count": 0
}
```

### Import Google Workspace Documents

Google Docs, Sheets, and Slides will be automatically converted to Office formats:

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/google/import" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["GDOC_ID"],
    "parent_folder_id": null,
    "recursive": false
  }' \
  | json_pp
```

Expected Response:
```json
{
  "import_id": "imp_abcdef123",
  "status": "completed",
  "results": {
    "successful": [
      {
        "file_id": "GDOC_ID",
        "name": "My Google Doc.docx", // Note the conversion to Office format
        "data_room_id": "dr_456789"
      }
    ],
    "failed": []
  },
  "total_files": 1,
  "successful_count": 1,
  "failed_count": 0
}
```

### Verify Imported Files

Check that files were properly imported into the Data Room:

```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "documents": [
    {
      "id": "dr_987654321",
      "name": "Example Document.docx",
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 12345,
      "created_at": "2023-08-21T15:42:30Z",
      "source": "google_drive",
      "source_id": "1aBcD_EfGhIjKlMnOpQrStUv"
    },
    // Other imported files...
  ]
}
```

## Disconnection

### Disconnect from Google Drive

Remove the connection to Google Drive:

```bash
curl -X DELETE "http://localhost:8000/api/v1/integrations/google/disconnect" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "detail": "Successfully disconnected from Google Drive"
}
```

### Verify Disconnection

Confirm that the connection has been removed:

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/google/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | json_pp
```

Expected Response:
```json
{
  "connected": false,
  "user_email": null
}
```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Errors**
   - Ensure your Google Cloud OAuth credentials are correctly configured
   - Check that the redirect URI exactly matches what's in Google Cloud Console
   - Verify that the Google Drive API is enabled

2. **Token Refresh Issues**
   - If you get 401 Unauthorized errors after some time, the token might have expired
   - The system should automatically refresh the token, but if issues persist, disconnect and reconnect

3. **Permission Issues**
   - Ensure you've granted all requested permissions during OAuth flow
   - For shared files, ensure the `include_shared` parameter is set to `true`

4. **Import Failures**
   - Check the `failed` array in the import response for specific error messages
   - Verify file size limits (default maximum is usually 10MB)
   - Ensure proper error handling for Google Workspace documents that require export

### Testing Error Scenarios

1. **Invalid File ID**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/integrations/google/import" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "file_ids": ["invalid_id_123"],
       "parent_folder_id": null,
       "recursive": false
     }' \
     | json_pp
   ```

   Expected Response:
   ```json
   {
     "import_id": "imp_error123",
     "status": "completed",
     "results": {
       "successful": [],
       "failed": [
         {
           "file_id": "invalid_id_123",
           "error": "File not found or insufficient permissions"
         }
       ]
     },
     "total_files": 1,
     "successful_count": 0,
     "failed_count": 1
   }
   ```

2. **Authentication Error (After Disconnecting)**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/integrations/google/files" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     | json_pp
   ```

   Expected Response:
   ```json
   {
     "detail": "Not authenticated with Google Drive. Please connect your account."
   }
   ```

## Testing Script

For convenient testing, here's a Python script you can use to automate the OAuth flow and testing process:

```python
import requests
import webbrowser
import json
import time
from urllib.parse import urlparse, parse_qs

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "your_email@example.com"
PASSWORD = "your_password"

def pretty_print(data):
    print(json.dumps(data, indent=2))

def get_auth_token():
    """Get JWT authentication token from the Data Room API"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    data = response.json()
    return data["access_token"]

def test_google_drive_integration():
    # Step 1: Get JWT token
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Initiate Google Drive authentication
    print("Initiating Google Drive authentication...")
    response = requests.post(
        f"{BASE_URL}/integrations/google/link",
        headers=headers,
        json={}
    )
    data = response.json()
    auth_url = data["auth_url"]
    
    # Step 3: Open browser for authentication
    print(f"Opening browser for authentication: {auth_url}")
    webbrowser.open(auth_url)
    
    # Step 4: Wait for user to complete authentication
    callback_url = input("After authenticating, paste the callback URL here: ")
    parsed_url = urlparse(callback_url)
    code = parse_qs(parsed_url.query)["code"][0]
    
    # Step 5: Complete authentication with code
    print("Completing authentication...")
    response = requests.get(f"{BASE_URL}/integrations/google/callback?code={code}")
    
    # Step 6: Check connection status
    print("\nChecking connection status...")
    response = requests.get(f"{BASE_URL}/integrations/google/status", headers=headers)
    pretty_print(response.json())
    
    # Step 7: List files
    print("\nListing files from Google Drive...")
    response = requests.get(f"{BASE_URL}/integrations/google/files", headers=headers)
    files_data = response.json()
    pretty_print(files_data)
    
    # Step 8: Select a file ID for testing
    if "files" in files_data and files_data["files"]:
        file_id = files_data["files"][0]["id"]
        
        # Step 9: Get file details
        print(f"\nGetting details for file {file_id}...")
        response = requests.get(f"{BASE_URL}/integrations/google/files/{file_id}", headers=headers)
        pretty_print(response.json())
        
        # Step 10: Import the file
        print(f"\nImporting file {file_id}...")
        response = requests.post(
            f"{BASE_URL}/integrations/google/import",
            headers=headers,
            json={"file_ids": [file_id], "recursive": False}
        )
        pretty_print(response.json())
    
    # Step 11: Search files
    print("\nSearching for files...")
    response = requests.get(f"{BASE_URL}/integrations/google/search?query=document", headers=headers)
    pretty_print(response.json())
    
    # Step 12: Check storage usage
    print("\nChecking storage usage...")
    response = requests.get(f"{BASE_URL}/integrations/google/storage", headers=headers)
    pretty_print(response.json())
    
    # Step 13: Verify imported files
    print("\nVerifying imported files...")
    response = requests.get(f"{BASE_URL}/documents", headers=headers)
    pretty_print(response.json())
    
    # Step 14: Disconnect (uncomment to test)
    # print("\nDisconnecting from Google Drive...")
    # response = requests.delete(f"{BASE_URL}/integrations/google/disconnect", headers=headers)
    # pretty_print(response.json())
    
    print("\nTesting completed!")

if __name__ == "__main__":
    test_google_drive_integration()
```

---

If all tests pass successfully, your Google Drive integration is working correctly. For additional information or support, please refer to the API documentation or contact the development team.