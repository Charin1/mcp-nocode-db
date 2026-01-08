import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Use a custom event to notify the app to logout, which is safer than a hard redirect
      window.dispatchEvent(new Event("logout"));
    }
    return Promise.reject(error);
  }
);

export default apiClient;