"""
AIForge V2 – Axios API Client Generator
=======================================
Generates Axios HTTP client with JWT interceptors, base URL config, and error handlers.
"""

from typing import List
from v2.agents.frontend.models import FrontendService


class ReactAPIGenerator:

    def generate_default_services(self, project_name: str) -> List[FrontendService]:
        return [
            FrontendService(
                service_name="apiClient",
                endpoints_covered=["/api/v1/auth/login", "/api/v1/projects", "/api/v1/planner/analyze"],
                code_content="""import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v2',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
"""
            )
        ]


global_api_generator = ReactAPIGenerator()
