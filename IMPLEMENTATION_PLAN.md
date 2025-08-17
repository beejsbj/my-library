# Docker-in-Docker Implementation Plan

## Overview

This implementation plan provides a step-by-step approach to transform the current file-based portable library into a truly portable containerized solution using Docker-in-Docker (DinD) technology.

## Implementation Strategy

### Phase 1: Proof of Concept (Week 1)
**Goal**: Validate the DinD approach and measure benefits

#### Step 1.1: Create Base DinD Container
```dockerfile
# Dockerfile.portable-library
FROM docker:24-dind

# Install required tools
RUN apk add --no-cache \
    docker-compose \
    make \
    curl \
    bash \
    tar \
    gzip

# Create application directory
WORKDIR /portable-library

# Copy current stack
COPY docker-compose.yml .
COPY .env .
COPY Makefile .
COPY README.md .
COPY library/ ./library/

# Create startup script
COPY scripts/startup.sh /startup.sh
RUN chmod +x /startup.sh

# Expose all service ports
EXPOSE 3306 6060 8080 8084 13378

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:6060 || exit 1

CMD ["/startup.sh"]
```

#### Step 1.2: Create Startup Script
```bash
#!/bin/bash
# scripts/startup.sh

set -e

echo "=== Portable Library Container Starting ==="

# Start Docker daemon in background
echo "Starting Docker daemon..."
dockerd-entrypoint.sh &

# Wait for Docker daemon to be ready
echo "Waiting for Docker daemon..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker info >/dev/null 2>&1; then
        echo "Docker daemon is ready!"
        break
    fi
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    echo "ERROR: Docker daemon failed to start within 60 seconds"
    exit 1
fi

# Change to application directory
cd /portable-library

# Fix environment file if needed
if grep -q "Americea/Toronto" .env; then
    echo "Fixing timezone typo in .env..."
    sed -i 's/Americea\/Toronto/America\/Toronto/g' .env
fi

# Start the portable library stack
echo "Starting portable library services..."
make start

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Verify services are running
echo "Verifying service health..."
docker compose ps

# Keep container running and monitor services
echo "=== Portable Library Container Ready ==="
echo "Services available at:"
echo "  - Booklore: http://localhost:6060"
echo "  - Audiobookshelf: http://localhost:13378"
echo "  - qBittorrent: http://localhost:8080"
echo "  - Book Downloader: http://localhost:8084"

# Monitor and restart services if needed
while true; do
    if ! docker compose ps --status running --quiet | wc -l | grep -q "5"; then
        echo "WARNING: Some services are not running. Attempting restart..."
        docker compose up -d
    fi
    sleep 60
done
```

#### Step 1.3: Build and Test Script
```bash
#!/bin/bash
# scripts/build-and-test.sh

set -e

echo "Building portable library container..."
docker build -t portable-library:latest -f Dockerfile.portable-library .

echo "Testing container startup..."
docker run -d --privileged --name portable-library-test \
    -p 3306:3306 \
    -p 6060:6060 \
    -p 8080:8080 \
    -p 8084:8084 \
    -p 13378:13378 \
    portable-library:latest

echo "Waiting for services to start..."
sleep 120

echo "Testing service endpoints..."
curl -f http://localhost:6060 && echo "✓ Booklore is responding"
curl -f http://localhost:13378 && echo "✓ Audiobookshelf is responding"
curl -f http://localhost:8080 && echo "✓ qBittorrent is responding"
curl -f http://localhost:8084 && echo "✓ Book Downloader is responding"

echo "Stopping test container..."
docker stop portable-library-test
docker rm portable-library-test

echo "✓ Proof of concept test completed successfully!"
```

### Phase 2: Production Implementation (Week 2-3)
**Goal**: Create production-ready containerized solution

#### Step 2.1: Optimize Container Size
```dockerfile
# Dockerfile.portable-library-optimized
FROM docker:24-dind-alpine

# Multi-stage build for smaller image
FROM docker:24-dind-alpine as base
RUN apk add --no-cache docker-compose make curl bash

FROM base as app
WORKDIR /portable-library

# Copy only necessary files
COPY docker-compose.yml .env Makefile ./
COPY library/ ./library/
COPY scripts/ ./scripts/

# Optimize startup
RUN chmod +x scripts/*.sh

EXPOSE 3306 6060 8080 8084 13378
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD scripts/health-check.sh

CMD ["scripts/startup-optimized.sh"]
```

#### Step 2.2: Enhanced Health Monitoring
```bash
#!/bin/bash
# scripts/health-check.sh

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon not responding"
    exit 1
fi

# Check all services
services=("booklore:6060" "audiobookshelf:13378" "qbittorrent:8080" "book-downloader-booklore:8084")
for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    
    if ! curl -f -s http://localhost:$port >/dev/null; then
        echo "Service $name not responding on port $port"
        exit 1
    fi
done

echo "All services healthy"
exit 0
```

#### Step 2.3: Backup and Restore Mechanisms
```bash
#!/bin/bash
# scripts/backup-container.sh

BACKUP_NAME="portable-library-$(date +%Y%m%d-%H%M%S)"

echo "Creating container backup: $BACKUP_NAME"

# Stop container gracefully
docker stop portable-library

# Create container snapshot
docker commit portable-library $BACKUP_NAME

# Export container image
docker save $BACKUP_NAME | gzip > "backups/${BACKUP_NAME}.tar.gz"

# Restart container
docker start portable-library

echo "Backup created: backups/${BACKUP_NAME}.tar.gz"
```

```bash
#!/bin/bash
# scripts/restore-container.sh

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

echo "Restoring from backup: $BACKUP_FILE"

# Stop and remove existing container
docker stop portable-library 2>/dev/null || true
docker rm portable-library 2>/dev/null || true

# Load backup image
docker load < "$BACKUP_FILE"

# Extract image name from backup
IMAGE_NAME=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep portable-library | head -1)

# Run restored container
docker run -d --privileged --name portable-library \
    -p 3306:3306 \
    -p 6060:6060 \
    -p 8080:8080 \
    -p 8084:8084 \
    -p 13378:13378 \
    "$IMAGE_NAME"

echo "Container restored and running"
```

### Phase 3: Advanced Features (Week 4)
**Goal**: Add enterprise-grade features

#### Step 3.1: Configuration Management
```yaml
# docker-compose.portable.yml
version: "3.9"

services:
  portable-library:
    build:
      context: .
      dockerfile: Dockerfile.portable-library-optimized
    container_name: portable-library
    privileged: true
    ports:
      - "3306:3306"
      - "6060:6060"
      - "8080:8080"
      - "8084:8084"
      - "13378:13378"
    volumes:
      - portable-library-data:/portable-library/library
    environment:
      - PORTABLE_LIBRARY_MODE=production
      - BACKUP_SCHEDULE=daily
      - HEALTH_CHECK_INTERVAL=30
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "scripts/health-check.sh"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s

volumes:
  portable-library-data:
    driver: local
```

#### Step 3.2: Automated Updates
```bash
#!/bin/bash
# scripts/update-container.sh

set -e

echo "Starting portable library update process..."

# Create backup before update
scripts/backup-container.sh

# Pull latest image
docker pull portable-library:latest

# Stop current container
docker stop portable-library

# Remove old container
docker rm portable-library

# Start new container with same configuration
docker run -d --privileged --name portable-library \
    -p 3306:3306 \
    -p 6060:6060 \
    -p 8080:8080 \
    -p 8084:8084 \
    -p 13378:13378 \
    -v portable-library-data:/portable-library/library \
    portable-library:latest

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 120

# Verify update was successful
if scripts/health-check.sh; then
    echo "✓ Update completed successfully"
else
    echo "✗ Update failed, consider rolling back"
    exit 1
fi
```

## Deployment Instructions

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd portable-library

# Build container
docker build -t portable-library:latest -f Dockerfile.portable-library .

# Run container
docker run -d --privileged --name portable-library \
    -p 3306:3306 \
    -p 6060:6060 \
    -p 8080:8080 \
    -p 8084:8084 \
    -p 13378:13378 \
    portable-library:latest

# Check status
docker logs -f portable-library
```

### Production Deployment
```bash
# Use docker-compose for production
docker-compose -f docker-compose.portable.yml up -d

# Monitor services
docker-compose -f docker-compose.portable.yml logs -f

# Create backup
scripts/backup-container.sh

# Update container
scripts/update-container.sh
```

## Migration from Current System

### Step 1: Backup Current System
```bash
# Create backup of current file-based system
make backup
```

### Step 2: Build Container with Current Data
```bash
# Build container including current library data
docker build -t portable-library:migration -f Dockerfile.portable-library .
```

### Step 3: Test Migration
```bash
# Run container and verify all data is preserved
docker run -d --privileged --name portable-library-migration-test \
    -p 3306:3306 \
    -p 6060:6060 \
    -p 8080:8080 \
    -p 8084:8084 \
    -p 13378:13378 \
    portable-library:migration

# Test all services and verify data integrity
scripts/test-migration.sh
```

### Step 4: Switch to Container-Based System
```bash
# Stop current system
make stop

# Start containerized system
docker run -d --privileged --name portable-library \
    -p 3306:3306 \
    -p 6060:6060 \
    -p 8080:8080 \
    -p 8084:8084 \
    -p 13378:13378 \
    portable-library:migration
```

## Success Criteria

### Phase 1 Success Metrics
- [ ] Container builds successfully
- [ ] All services start within container
- [ ] Services accessible from host
- [ ] No setup required after container start
- [ ] Application state preserved across container restarts

### Phase 2 Success Metrics
- [ ] Container size < 2GB
- [ ] Startup time < 2 minutes
- [ ] Automated backup/restore working
- [ ] Health monitoring functional
- [ ] Resource usage < 20% overhead

### Phase 3 Success Metrics
- [ ] Automated updates working
- [ ] Configuration management implemented
- [ ] Monitoring and logging operational
- [ ] Production deployment successful

## Risk Mitigation

### Technical Risks
- **Docker-in-Docker complexity**: Use well-tested DinD patterns and extensive testing
- **Performance overhead**: Monitor resource usage and optimize container configuration
- **Security concerns**: Implement proper security contexts and access controls

### Operational Risks
- **Migration complexity**: Thorough testing and rollback procedures
- **Container size**: Multi-stage builds and optimization techniques
- **Backup strategy**: Multiple backup mechanisms and validation procedures

## Timeline

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Proof of Concept | Working DinD container, basic functionality |
| 2 | Production Prep | Optimized container, backup/restore, health checks |
| 3 | Production Deploy | Production deployment, monitoring, documentation |
| 4 | Advanced Features | Automated updates, configuration management |

## Conclusion

This implementation plan transforms the portable library from a file-based backup system to a true containerized solution that preserves complete application state. The Docker-in-Docker approach eliminates the root cause of application state preservation issues by capturing the entire runtime environment.

**Next Steps:**
1. Begin Phase 1 implementation
2. Create proof of concept container
3. Validate state preservation benefits
4. Proceed with production implementation based on results