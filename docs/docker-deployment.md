# Docker Deployment Guide for MASB

This guide explains how to deploy MASB using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- At least 2GB of available RAM
- At least 5GB of available disk space

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd MASB
chmod +x docker/manage.sh
```

### 2. Start MASB (Default Mode)

```bash
# Build and start services
./docker/manage.sh build
./docker/manage.sh start

# Check status
./docker/manage.sh status
```

MASB will be available at http://localhost:8080

### 3. Initialize Database

```bash
./docker/manage.sh db-init
```

## Deployment Modes

### Development Mode

For development with hot-reload and debugging:

```bash
./docker/manage.sh start dev
```

Features:
- Hot reload on code changes
- Debug port (5678) for remote debugging
- Volume mounted source code
- Development dependencies included

### Production Mode

For production deployment with Nginx proxy:

```bash
./docker/manage.sh start prod
```

Features:
- Nginx reverse proxy with SSL support
- Rate limiting and security headers
- Optimized for performance
- Health checks enabled

### Default Mode

For basic deployment:

```bash
./docker/manage.sh start
```

Features:
- Core MASB application
- SQLite database
- Redis caching
- Basic monitoring

## Services

### Core Services

- **masb-app**: Main MASB application (port 8080)
- **masb-db**: PostgreSQL database (port 5432)
- **masb-redis**: Redis cache (port 6379)

### Optional Services

- **masb-nginx**: Nginx reverse proxy (ports 80/443)
- **masb-dev**: Development version with debugging

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
MASB_DATABASE_URL=postgresql://masb_user:masb_password@masb-db:5432/masb

# API Keys (required for evaluation)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
COHERE_API_KEY=your_cohere_key
GOOGLE_API_KEY=your_google_key

# Application Settings
MASB_LOG_LEVEL=INFO
MASB_CACHE_ENABLED=true
MASB_WEB_HOST=0.0.0.0
MASB_WEB_PORT=8080

# Security
FLASK_SECRET_KEY=your_secret_key_here
```

### Volume Mounts

Data is persisted in Docker volumes:

- `masb_data`: Application data and database
- `masb_logs`: Application logs
- `masb_results`: Evaluation results
- `masb_cache`: Cache files

## Management Commands

### Service Management

```bash
# Start services
./docker/manage.sh start [dev|prod]

# Stop services
./docker/manage.sh stop

# Restart services
./docker/manage.sh restart [dev|prod]

# View service status
./docker/manage.sh status

# View logs
./docker/manage.sh logs [service_name]
```

### Database Management

```bash
# Initialize database
./docker/manage.sh db-init

# Create backup
./docker/manage.sh db-backup

# Restore from backup
./docker/manage.sh db-restore backup_file.db
```

### Container Operations

```bash
# Execute command in container
./docker/manage.sh exec masb-app bash

# Execute Python command
./docker/manage.sh exec masb-app python -m src.storage.cli list

# View application logs
./docker/manage.sh logs masb-app
```

## Monitoring and Health Checks

### Health Endpoints

- Application: http://localhost:8080/health
- Database: Check with `./docker/manage.sh exec masb-db pg_isready`
- Redis: Check with `./docker/manage.sh exec masb-redis redis-cli ping`

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
./docker/manage.sh logs masb-app
./docker/manage.sh logs masb-db
./docker/manage.sh logs masb-redis
```

### Resource Usage

```bash
# View resource usage
./docker/manage.sh status

# Detailed container stats
docker stats
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
./docker/manage.sh db-backup

# Manual backup
docker-compose exec masb-db pg_dump -U masb_user masb > backup.sql
```

### Volume Backup

```bash
# Backup all data volumes
docker run --rm -v masb_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/masb_data_backup.tar.gz -C /data .
```

### Restore

```bash
# Restore database
./docker/manage.sh db-restore backup.db

# Restore volumes
docker run --rm -v masb_data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/masb_data_backup.tar.gz -C /data
```

## SSL/TLS Configuration

For production deployment with SSL:

1. Place SSL certificates in `docker/ssl/`:
   - `cert.pem` (certificate)
   - `key.pem` (private key)

2. Uncomment HTTPS section in `docker/nginx.conf`

3. Start with production profile:
   ```bash
   ./docker/manage.sh start prod
   ```

## Scaling and Performance

### Horizontal Scaling

Scale the application service:

```bash
docker-compose up -d --scale masb-app=3
```

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  masb-app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `docker-compose.yml`
2. **Permission issues**: Check file permissions and user ownership
3. **Database connection**: Verify database service is running
4. **Memory issues**: Increase Docker memory allocation

### Debug Mode

```bash
# Start in development mode with debugging
./docker/manage.sh start dev

# Attach debugger to port 5678
# Use VS Code with Python extension and remote debugging
```

### Logs and Debugging

```bash
# View all logs
./docker/manage.sh logs

# View specific service logs with timestamps
docker-compose logs -t masb-app

# Enter container for debugging
./docker/manage.sh exec masb-app bash
```

## Cleanup

```bash
# Stop and remove containers
./docker/manage.sh stop

# Complete cleanup (removes volumes and images)
./docker/manage.sh cleanup
```

## Production Deployment Checklist

- [ ] Set secure passwords in environment variables
- [ ] Configure SSL certificates
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Review security settings
- [ ] Test backup and recovery procedures
- [ ] Configure firewall rules
- [ ] Set up reverse proxy with rate limiting
- [ ] Enable health checks