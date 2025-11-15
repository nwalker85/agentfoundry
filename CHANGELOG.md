# Changelog

All notable changes to Agent Foundry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.1-dev] - 2025-11-15

### Changed
- Migrated LiveKit from Homebrew installation to Docker Compose service
- Updated docker-compose.yml with LiveKit service configuration
- Modified backend LIVEKIT_URL to use Docker internal networking (ws://livekit:7880)
- Added LiveKit health checks and service dependencies in Docker Compose
- Removed Homebrew LiveKit dependency from local development workflow

### Infrastructure
- LiveKit now runs as containerized service (livekit/livekit-server:latest)
- Improved local development setup with consistent Docker networking
- Added service health checks for Redis and LiveKit
- Added depends_on configuration for backend service

### Technical Details
- HTTP/WebSocket port: 7880
- RTC TCP port: 7881
- WebRTC UDP range: 40000-40100
- Redis health check integration
- Volume mount for LiveKit config: ./livekit-config.yaml

### Fixed
- Frontend LiveKit connection using localhost:7880 port mapping
- Backend-to-LiveKit communication via Docker internal networking

## [0.8.0-dev] - 2025-11-14

### Added
- Initial LiveKit voice integration
- FastAPI backend with MCP server capabilities
- LangGraph agent orchestration
- WebSocket support for text chat
- Next.js frontend with chat UI
- Docker Compose multi-service setup
- Redis for state management
- Agent registry system (YAML-based)

### Infrastructure
- Docker containerization for all services
- Multi-service orchestration via Docker Compose
- Volume mounts for hot-reload development
- Network isolation via Docker bridge network

---

[Unreleased]: https://github.com/ravenhelm/agentfoundry/compare/v0.8.1-dev...HEAD
[0.8.1-dev]: https://github.com/ravenhelm/agentfoundry/compare/v0.8.0-dev...v0.8.1-dev
[0.8.0-dev]: https://github.com/ravenhelm/agentfoundry/releases/tag/v0.8.0-dev
