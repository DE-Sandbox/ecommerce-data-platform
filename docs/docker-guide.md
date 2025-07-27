# Modern Docker Containerization for Data Engineering (2025)

nThis guide covers modern Docker practices optimized for data engineering workloads, featuring multi-stage builds, security best practices, and performance optimizations.

## Multi-Stage Builds for Data Engineering

Modern Docker workflows use sophisticated multi-stage builds that reduce image sizes by 50% while maintaining full functionality.

### Our Multi-Stage Architecture

The `Dockerfile` in this project implements four specialized stages:

1. **Base Stage** - Common dependencies and UV installation
2. **Builder Stage** - Development tools and compilation
3. **Production Stage** - Minimal runtime image (default)
4. **Development Stage** - Full development environment
5. **Testing Stage** - Optimized for CI/CD
6. **Data Processor Stage** - Specialized for data workloads

### Building Different Stages

```bash
# Production build (default, smallest size)
docker build -t ecommerce-platform:prod .

# Development build (includes dev tools)
docker build --target development -t ecommerce-platform:dev .

# Testing build (runs all quality checks)
docker build --target testing -t ecommerce-platform:test .

# Data processing build (optimized for data workloads)
docker build --target data-processor -t ecommerce-platform:data .
```

## Performance Optimizations

### BuildKit and Caching

Enable BuildKit for advanced caching and parallelization:

```bash
# Enable BuildKit (recommended for all builds)
export DOCKER_BUILDKIT=1

# Or use buildx for advanced features
docker buildx build --cache-from type=gha --cache-to type=gha .
```

### Layer Caching Strategy

Our Dockerfile optimizes layer caching:

```dockerfile
# 1. Copy dependency files first (changes rarely)
COPY pyproject.toml uv.lock* ./

# 2. Install dependencies (expensive, cached when deps don't change)
RUN uv sync --no-dev

# 3. Copy application code last (changes frequently)
COPY --chown=appuser:appuser src/ ./src/
```

### Memory Optimization for Data Workloads

```dockerfile
# Configure memory settings for data processing
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV MALLOC_ARENA_MAX=2

# JVM settings for Spark/Kafka workloads
ENV JAVA_OPTS="-Xmx2g -XX:+UseG1GC -XX:G1HeapRegionSize=16m"
```

## Security Best Practices

### Non-Root User

Always run containers as non-root users:

```dockerfile
# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Switch to non-root user
USER appuser
```

### Minimal Base Images

Use slim or distroless base images:

```dockerfile
# Recommended: Python slim (smaller, fewer vulnerabilities)
FROM python:3.13-slim-bookworm AS base

# Alternative: Distroless (even smaller, more secure)
FROM gcr.io/distroless/python3-debian12 AS production
```

### Security Scanning

Integrate security scanning into your workflow:

```bash
# Scan for vulnerabilities with Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image ecommerce-platform:prod

# Scan with Docker Scout
docker scout cves ecommerce-platform:prod
```

## Data Engineering Specific Optimizations

### Volume Mounting for Large Datasets

```yaml
# docker-compose.yml
services:
  data-processor:
    build:
      context: .
      target: data-processor
    volumes:
      # Fast temporary storage for processing
      - type: tmpfs
        target: /tmp/processing
        tmpfs:
          size: 2g
      # Persistent data storage
      - ./data:/app/data:ro
      # Output directory
      - ./output:/app/output
```

### Resource Limits

```yaml
services:
  spark-worker:
    build: .
    deploy:
      resources:
        limits:
          memory: 4g
          cpus: '2.0'
        reservations:
          memory: 2g
          cpus: '1.0'
```

## Container Orchestration

### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Main application
  app:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    environment:
      - ENV=development
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from mount
    depends_on:
      - postgres
      - redis
      - localstack

  # Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_postgres.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # Message broker
  redpanda:
    image: redpandadata/redpanda:latest
    command:
      - redpanda start
      - --smp 1
      - --memory 1G
      - --overprovisioned
      - --node-id 0
      - --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092
      - --advertise-kafka-addr PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092
    ports:
      - "9092:9092"
      - "9644:9644"

  # AWS services emulation
  localstack:
    image: localstack/localstack:latest
    environment:
      - SERVICES=s3,dynamodb,kinesis,glue,athena
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    ports:
      - "4566:4566"
    volumes:
      - localstack_data:/tmp/localstack
      - /var/run/docker.sock:/var/run/docker.sock

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  postgres_data:
  localstack_data:
```

### Health Checks

Implement comprehensive health checks:

```dockerfile
# Application health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "unknown"),
        "database": await check_database_connection(),
        "storage": await check_s3_connection(),
    }
```

## CI/CD Integration

### GitHub Actions Build

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build and test
        uses: docker/build-push-action@v5
        with:
          context: .
          target: testing
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build production image
        uses: docker/build-push-action@v5
        with:
          context: .
          target: production
          tags: ecommerce-platform:latest
          cache-from: type=gha
```

### Multi-Architecture Builds

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ecommerce-platform:multiarch .
```

## Troubleshooting

### Common Issues

```bash
# Build cache issues
docker builder prune -f

# Layer size analysis
docker history ecommerce-platform:prod

# Container resource usage
docker stats

# Debugging failed builds
docker build --no-cache --progress=plain .

# Interactive debugging
docker run -it --entrypoint=/bin/bash ecommerce-platform:dev
```

### Performance Monitoring

```bash
# Monitor container performance
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Container resource limits
docker inspect ecommerce-platform | grep -i memory

# Build time analysis
time docker build .
```

## Development Environment Rules

### Stateless and Reproducible Environments

**CRITICAL: Docker containers must be stateless and reproducible. NEVER manually modify running containers.**

#### ❌ What NOT to Do

```bash
# NEVER run manual database commands
docker exec -i postgres psql -U postgres -c "CREATE DATABASE test_db;"
docker exec -i postgres psql -U postgres -d mydb -f schema.sql

# NEVER manually install packages in containers
docker exec -it myapp pip install pandas

# NEVER modify files directly in containers
docker exec -it myapp vi /app/config.py
```

#### ✅ Correct Approaches

1. **Database Initialization**: Use `docker-entrypoint-initdb.d/`
   ```yaml
   postgres:
     volumes:
       - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/01-init.sql
       - ./sql/schema/001_initial_schema.sql:/docker-entrypoint-initdb.d/02-schema.sql
   ```

2. **Application Configuration**: Use environment variables or mounted configs
   ```yaml
   app:
     environment:
       - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ecommerce
     volumes:
       - ./config:/app/config:ro
   ```

3. **Dependency Changes**: Update Dockerfile or requirements
   ```dockerfile
   # In Dockerfile
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   ```

### Testing with Docker

**Tests must create their own isolated environment:**

```python
# conftest.py
@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """Override docker-compose for tests."""
    return str(Path(__file__).parent / "docker-compose.test.yml")

@pytest.fixture(scope="session")
def docker_services(docker_services):
    """Ensure services are ready before tests."""
    docker_services.wait_until_responsive(
        check=lambda: is_postgres_ready(),
        timeout=30.0,
        pause=0.1,
    )
    return docker_services
```

### Container Lifecycle Management

1. **Development Workflow**
   ```bash
   # Start fresh environment
   docker-compose down -v  # Remove volumes for clean state
   docker-compose up -d
   
   # View logs
   docker-compose logs -f app
   
   # Restart after code changes
   docker-compose restart app
   ```

2. **Data Persistence**
   - Use named volumes for data that should persist
   - Use bind mounts for development code
   - Never rely on container filesystem for important data

3. **Environment Reproducibility**
   ```bash
   # This should ALWAYS work identically
   git clone <repo>
   cd <repo>
   docker-compose up -d
   # Application is ready, no manual steps needed
   ```

## Best Practices Summary

1. **Use multi-stage builds** to minimize production image size
2. **Implement security scanning** in your CI/CD pipeline
3. **Run as non-root user** for security
4. **Optimize layer caching** by copying dependencies before application code
5. **Use health checks** for container orchestration
6. **Implement proper resource limits** for data workloads
7. **Use tmpfs for temporary processing** to improve I/O performance
8. **Mount data volumes appropriately** for large datasets
9. **Enable BuildKit** for faster builds and advanced features
10. **Tag images semantically** for better version management
11. **NEVER manually modify containers** - maintain stateless, reproducible environments
12. **Use initialization scripts** for database setup, not manual commands
13. **Test in isolated environments** using docker-compose overrides or testcontainers

This modern Docker setup provides optimal performance, security, and maintainability for data engineering workloads while supporting efficient local development and CI/CD workflows.
