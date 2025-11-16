// User types
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
  auth_provider?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface GoogleLoginCredentials {
  id_token: string;
  access_token?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Document types
export interface Document {
  id: string;
  name: string;
  size?: number;
  file_size?: number; // alternative field name from API
  mime_type?: string;
  file_type?: string; // alternative field name from API
  created_at: string;
  updated_at: string | null;
  owner_id: string;
  folder_id: string | null;
  source?: string;
  source_id?: string;
  description?: string;
  is_public?: boolean;
  file_path?: string;
  is_deleted?: boolean;
}

// Folder types
export interface Folder {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  owner_id: string;
  parent_id: string | null;
}

// Google Drive types
export interface GoogleDriveFile {
  id: string;
  name: string;
  mime_type: string;
  size: number | null;
  created_time: string;
  modified_time: string;
  is_folder: boolean;
  web_view_link: string;
  parents?: string[];
}

export interface GoogleDriveFileList {
  files: GoogleDriveFile[];
  next_page_token?: string;
  current_folder?: GoogleDriveFile;
  parent_folders?: GoogleDriveFile[];
  is_root?: boolean;
}

export interface GoogleDriveStorageInfo {
  usage: number;
  limit: number;
  usage_in_drive: number;
  usage_in_drive_trash: number;
}

export interface GoogleDriveConnectionStatus {
  connected: boolean;
  user_email: string | null;
}

export interface GoogleDriveImportRequest {
  file_ids: string[];
  parent_folder_id?: string | null;
  include_folders?: boolean;
  max_depth?: number;
}

export interface GoogleDriveImportResult {
  imported_document_ids: string[];
  imported_folder_ids: string[];
  skipped_items: {
    id: string;
    name: string;
    error: string;
  }[];
  total_documents_imported: number;
  total_folders_imported: number;
  total_skipped: number;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  error?: string;
}