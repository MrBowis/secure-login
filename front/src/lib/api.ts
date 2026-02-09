import axios, { AxiosError } from 'axios';
import {
  RegisterRequest,
  RegisterResponse,
  Setup2FARequest,
  Setup2FAResponse,
  Verify2FARequest,
  Verify2FAResponse,
  LoginRequest,
  LoginResponse,
  ErrorResponse,
  User,
  UpdateProfileRequest,
  UpdateProfileResponse,
  AdminUsersResponse,
} from './types';

// Configuración de Axios
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper para manejar errores de API
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>;
    
    if (axiosError.response?.data?.detail) {
      const detail = axiosError.response.data.detail;
      
      // Si es un array de errores de validación
      if (Array.isArray(detail)) {
        return detail
          .map((err) => `${err.loc.join('.')}: ${err.msg}`)
          .join(', ');
      }
      
      // Si es un string
      return detail;
    }
    
    return axiosError.message || 'Error al comunicarse con el servidor';
  }
  
  return 'Error desconocido';
};

// Endpoint: POST /auth/register
export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  try {
    const response = await api.post<RegisterResponse>('/auth/register', data);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: POST /auth/setup-2fa
export const setup2FA = async (data: Setup2FARequest): Promise<Setup2FAResponse> => {
  try {
    const response = await api.post<Setup2FAResponse>('/auth/setup-2fa', data);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: POST /auth/verify-2fa
export const verify2FA = async (data: Verify2FARequest): Promise<Verify2FAResponse> => {
  try {
    const response = await api.post<Verify2FAResponse>('/auth/verify-2fa', data);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: POST /auth/login
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  try {
    const response = await api.post<LoginResponse>('/auth/login', data);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Helper para obtener headers con token
const getAuthHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`,
});

// Endpoint: GET /auth/me
export const getMyProfile = async (token: string): Promise<User> => {
  try {
    const response = await api.get<User>('/auth/me', {
      headers: getAuthHeaders(token),
    });
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: PATCH /auth/me
export const updateMyProfile = async (
  token: string,
  data: UpdateProfileRequest
): Promise<UpdateProfileResponse> => {
  try {
    const response = await api.patch<UpdateProfileResponse>('/auth/me', data, {
      headers: getAuthHeaders(token),
    });
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: GET /auth/admin/users
export const getAllUsers = async (token: string): Promise<User[]> => {
  try {
    const response = await api.get<AdminUsersResponse>('/auth/admin/users', {
      headers: getAuthHeaders(token),
    });
    return response.data.users;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: PATCH /auth/admin/users/{user_uuid}
export const updateUser = async (
  token: string,
  userId: string,
  data: UpdateProfileRequest
): Promise<UpdateProfileResponse> => {
  try {
    const response = await api.patch<UpdateProfileResponse>(
      `/auth/admin/users/${userId}`,
      data,
      {
        headers: getAuthHeaders(token),
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

// Endpoint: DELETE /auth/admin/users/{user_uuid}
export const deleteUser = async (token: string, userId: string): Promise<{ message: string }> => {
  try {
    const response = await api.delete<{ message: string }>(`/auth/admin/users/${userId}`, {
      headers: getAuthHeaders(token),
    });
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};

export default api;
