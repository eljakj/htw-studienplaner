# Stage 1: build the neutral page. Only build.py, src/ and the fictional example profile are copied,
# so no personal profile can end up in the image.
FROM python:3.14-alpine AS build
WORKDIR /app
COPY build.py ./
COPY src ./src
COPY demo/profile.demo.json ./demo/profile.demo.json
RUN python build.py --out /out/index.html

# Stage 2: serve it with nginx as a non-root user on port 8080.
FROM nginxinc/nginx-unprivileged:1.30-alpine
ARG REVISION=unknown
LABEL org.opencontainers.image.title="HTW Studienplaner" \
      org.opencontainers.image.description="Study plan for Angewandte Informatik (B), HTW Berlin: one static HTML file served by nginx" \
      org.opencontainers.image.source="https://github.com/eljakj/htw-studienplaner" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.revision="${REVISION}"
COPY --chmod=644 docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build --chmod=644 /out/index.html /usr/share/nginx/html/index.html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
