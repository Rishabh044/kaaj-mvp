import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      status: error.response?.status || 500,
    };

    if (error.response?.data) {
      const data = error.response.data as Record<string, unknown>;
      apiError.message =
        (data.detail as string) || (data.message as string) || apiError.message;
      apiError.details = data;
    } else if (error.message) {
      apiError.message = error.message;
    }

    return Promise.reject(apiError);
  }
);

export default apiClient;
