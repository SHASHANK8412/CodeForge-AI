import logging

logger = logging.getLogger("aiforge.deployment.nginx")


class NginxGenerator:
    """
    NginxGenerator builds production Nginx configuration (nginx.conf) for reverse proxying,
    API routing (/api/), static frontend serving, gzip compression, and security headers.
    """

    def generate_nginx_conf(self) -> str:
        return """events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    server {
        listen 80;
        server_name localhost;

        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Content-Type-Options "nosniff";

        # Static Frontend SPA
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # Backend REST API Reverse Proxy
        location /api/ {
            proxy_pass http://backend:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""


# Global NginxGenerator Instance
global_nginx_generator = NginxGenerator()
