// AuthTwin Control-Plane Configuration
export const AUTHTWIN_CONFIG = {
  API_BASE_URL: import.meta.env.VITE_AUTHTWIN_API_URL
    ? `${import.meta.env.VITE_AUTHTWIN_API_URL.replace(/\/$/, '')}/api/v1`
    : '/api/v1',
  CONTROL_PLANE_ORIGINS: [window.location.origin],
  INTERCEPTOR_PROXY_PREFIX: '/api/v1/interceptor/proxy'
};
