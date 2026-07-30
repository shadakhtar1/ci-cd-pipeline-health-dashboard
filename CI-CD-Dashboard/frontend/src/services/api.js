import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
});

export const getDashboard = () => api.get('/api/dashboard');
export const getBuilds = (params = {}) => api.get('/api/builds', { params });
export const refreshBuilds = () => api.post('/api/refresh');
