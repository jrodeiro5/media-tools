# Dockerfile and docker-compose

- Implement Dockerfiles in component folders; use "docker compose" (not legacy "docker-compose" binary)

- Implement separate docker-compose.yml for local development with debug configs and volume mounts for code reloading

- limit logs to a maximum size; export only required ports; mount folders from current directory (not native volumes); set restart policy to "unless-stopped"; include healthchecks where applicable; define service dependencies

- Implement .dockerignore files for each component to exclude unnecessary files

- Update system components as first Dockerfile step for security and currency

- Use multistep Dockerfile builds where frameworks require it to minimize image size and exclude build tools/intermediate files

- Do not expose ports outside the network in docker-compose.yml unless required by design

- Create docker-compose-deployment.yml for remote deployment using registry-based image pulls with tags from JenkinsFile build versions; update with each component version.txt change; use in ansible if requested

- Fix specific versions instead of :latest, always at least 2 days old unless we need to fix a specific vulnerability

[rev. 5]
