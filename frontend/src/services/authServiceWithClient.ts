import {createApiClient} from './apiClient';

// API URL from environment variables or fall back to relative path
const API_URL = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : '/api/v1';

// Create an authenticated API client
const authClient = createApiClient({
    baseURL: `${API_URL}/auth`,
    headers: {
        'Content-Type': 'application/json'
    },
    withCredentials: true  // Enable sending cookies with cross-origin requests
}).handleAuthErrors();  // Add auth error handling automatically

// Set auth token if available
const token = localStorage.getItem('token');
if (token) {
    authClient.setAuthToken(token);
}

/**
 * Interface for login request data
 */
interface LoginRequest {
    username: string;
    password: string;
}

/**
 * Interface for token response
 */
interface TokenResponse {
    access_token: string;
    token_type: string;
}

/**
 * Interface for user data
 */
interface UserData {
    id: string;
    email: string;
    is_active: boolean;
    is_superuser?: boolean;
    full_name?: string;
}

/**
 * Login with username and password
 *
 * @param credentials - Login credentials
 * @returns Token response with access token
 */
export const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await authClient.getAxiosInstance().post<TokenResponse>(
        '/login/access-token',
        formData.toString(),
        {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        }
    );

    // Store the token in local storage
    localStorage.setItem('token', response.data.access_token);

    // Update the auth token in the client
    authClient.setAuthToken(response.data.access_token);

    return response.data;
};

/**
 * Get current user information
 *
 * @returns User data
 */
export const getCurrentUser = async (): Promise<UserData> => {
    return await authClient.get<UserData>('/users/me');
};

/**
 * Logout the current user
 */
export const logout = (): void => {
    localStorage.removeItem('token');
    window.location.href = '/login';
};

export default {
    login,
    getCurrentUser,
    logout
};