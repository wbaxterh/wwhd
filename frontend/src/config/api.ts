// API Configuration
export const API_URL = 'https://api.weshuber.com';

// Helper to get full API endpoint
export const getApiUrl = (path: string) => {
  return `${API_URL}${path}`;
};