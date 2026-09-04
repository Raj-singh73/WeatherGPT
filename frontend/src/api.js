import axios from 'axios';

// Default to relative /api (handled by Vite proxy in dev, or web server in prod)
const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Resilient Interceptor: If Vite proxy returns 502/504 or network error, automatically failover to direct backend port 8000
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isProxyError = error.response?.status === 502 || error.response?.status === 504 || error.code === 'ERR_NETWORK';
    
    if (isProxyError && !originalRequest._retry) {
      originalRequest._retry = true;
      // Failover directly to localhost:8000
      originalRequest.baseURL = 'http://localhost:8000/api';
      console.warn('[API Failover] Proxy returned 502/Network error. Retrying directly against http://localhost:8000/api ...');
      return client(originalRequest);
    }
    return Promise.reject(error);
  }
);

export const api = {
  getHealth: () => client.get('/health').then(r => r.data),
  getCurrentWeather: (location = 'Nagpur', lat = null, lon = null) => 
    client.get('/weather/current', { params: { location, ...(lat != null && lon != null ? { lat, lon } : {}) } }).then(r => r.data),
  getForecast: (location = 'Nagpur', days = 7, lat = null, lon = null) => 
    client.get('/weather/forecast', { params: { location, days, ...(lat != null && lon != null ? { lat, lon } : {}) } }).then(r => r.data),
  getLocations: () => client.get('/weather/location').then(r => r.data),
  getWeatherHistory: (limit = 30) => client.get('/weather/history', { params: { limit } }).then(r => r.data),
  getAlerts: (location = 'Nagpur', lat = null, lon = null) => 
    client.get('/alerts', { params: { location, ...(lat != null && lon != null ? { lat, lon } : {}) } }).then(r => r.data),
  getClimateTrends: () => client.get('/climate/trends').then(r => r.data),
  getCycloneSystems: () => client.get('/cyclone/live-systems').then(r => r.data),
  getDistrictHierarchy: (district, state) => client.get('/location/district-hierarchy', { params: { district, state } }).then(r => r.data),
  getVillagesInBlock: (block, district, state) => client.get('/location/villages', { params: { block, district, state } }).then(r => r.data),
  detectVillage: (query, block, district, state) => client.get('/location/detect-village', { params: { query, block, district, state } }).then(r => r.data),
  suggestLocations: (q, state, district) => client.get('/location/suggest', { params: { q, state, district } }).then(r => r.data),
  lookupPincode: (pincode) => client.get('/location/pincode', { params: { pincode } }).then(r => r.data),
  reverseGeocode: (lat, lon) => client.get('/location/reverse-geocode', { params: { lat, lon } }).then(r => r.data),
  getFarmerAdvisory: (payload) => client.post('/farmer/advisory', payload).then(r => r.data),
  predictRisk: (payload) => client.post('/predict/risk', payload).then(r => r.data),
  chat: (payload) => client.post('/chat', payload).then(r => r.data),
  chatVoice: (formData) => client.post('/chat/voice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data),
};

export default api;
