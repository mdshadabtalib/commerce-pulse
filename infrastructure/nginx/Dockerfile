FROM nginx:1.27-alpine

RUN apk add --no-cache \
    openssl \
    curl \
    certbot \
    certbot-nginx

COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /etc/nginx/certs /var/cache/nginx /var/log/nginx /usr/share/nginx/html

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/self-signed.key \
    -out /etc/nginx/certs/self-signed.crt \
    -subj "/C=US/ST=State/L=City/O=CommercePulse/CN=localhost" 2>/dev/null || true

RUN addgroup -g 1001 -S nginx-user \
    && adduser -u 1001 -D -S -G nginx-user nginx-user \
    && chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx /etc/nginx/certs

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
