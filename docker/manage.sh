#!/bin/bash
# Docker management script for MASB

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to use docker-compose or docker compose
docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

# Build images
build() {
    print_header "🏗️  Building MASB Docker images..."
    docker_compose_cmd build
    print_status "Build completed successfully!"
}

# Start services
start() {
    local profile=${1:-""}
    print_header "🚀 Starting MASB services..."
    
    if [ "$profile" == "dev" ]; then
        print_status "Starting in development mode..."
        docker_compose_cmd --profile development up -d
    elif [ "$profile" == "prod" ]; then
        print_status "Starting in production mode..."
        docker_compose_cmd --profile production up -d
    else
        print_status "Starting in default mode..."
        docker_compose_cmd up -d masb-app masb-db masb-redis
    fi
    
    print_status "Services started successfully!"
    print_status "Web interface: http://localhost:8080"
}

# Stop services
stop() {
    print_header "🛑 Stopping MASB services..."
    docker_compose_cmd down
    print_status "Services stopped successfully!"
}

# Restart services
restart() {
    print_header "🔄 Restarting MASB services..."
    stop
    start "$1"
}

# View logs
logs() {
    local service=${1:-"masb-app"}
    print_header "📋 Showing logs for $service..."
    docker_compose_cmd logs -f "$service"
}

# Execute command in container
exec_cmd() {
    local service=${1:-"masb-app"}
    shift
    local cmd=${@:-"bash"}
    
    print_header "🔧 Executing command in $service container..."
    docker_compose_cmd exec "$service" $cmd
}

# Show status
status() {
    print_header "📊 MASB Services Status"
    docker_compose_cmd ps
    
    echo ""
    print_header "📈 Resource Usage"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Clean up
cleanup() {
    print_header "🧹 Cleaning up MASB resources..."
    
    print_warning "This will remove all containers, images, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker_compose_cmd down -v --rmi all
        docker system prune -f
        print_status "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Database operations
db_init() {
    print_header "🗄️  Initializing database..."
    docker_compose_cmd exec masb-app python init_database.py
    print_status "Database initialized!"
}

db_backup() {
    local backup_name="masb_backup_$(date +%Y%m%d_%H%M%S).db"
    print_header "💾 Creating database backup..."
    
    docker_compose_cmd exec masb-app python -m src.storage.cli backup --output "/app/data/$backup_name"
    
    # Copy to host
    docker cp "$(docker_compose_cmd ps -q masb-app):/app/data/$backup_name" "./backups/$backup_name"
    print_status "Database backup created: ./backups/$backup_name"
}

db_restore() {
    local backup_file=$1
    if [ -z "$backup_file" ]; then
        print_error "Please specify backup file path"
        exit 1
    fi
    
    print_header "📥 Restoring database from backup..."
    
    # Copy backup to container
    docker cp "$backup_file" "$(docker_compose_cmd ps -q masb-app):/app/data/restore_backup.db"
    
    # Restore
    docker_compose_cmd exec masb-app python -m src.storage.cli restore "/app/data/restore_backup.db" --force
    
    print_status "Database restored successfully!"
}

# Show help
show_help() {
    print_header "🤖 MASB Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                   Build Docker images"
    echo "  start [dev|prod]        Start services (default, dev, or prod mode)"
    echo "  stop                    Stop all services"
    echo "  restart [dev|prod]      Restart services"
    echo "  logs [service]          Show logs (default: masb-app)"
    echo "  exec [service] [cmd]    Execute command in container"
    echo "  status                  Show services status"
    echo "  cleanup                 Remove all containers, images, and volumes"
    echo ""
    echo "Database Commands:"
    echo "  db-init                 Initialize database"
    echo "  db-backup               Create database backup"
    echo "  db-restore <file>       Restore database from backup"
    echo ""
    echo "Examples:"
    echo "  $0 start dev            # Start in development mode"
    echo "  $0 logs masb-app        # Show application logs"
    echo "  $0 exec masb-app bash   # Open bash in app container"
    echo "  $0 db-backup            # Create database backup"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start "$2"
            ;;
        stop)
            stop
            ;;
        restart)
            restart "$2"
            ;;
        logs)
            logs "$2"
            ;;
        exec)
            exec_cmd "$2" "${@:3}"
            ;;
        status)
            status
            ;;
        cleanup)
            cleanup
            ;;
        db-init)
            db_init
            ;;
        db-backup)
            db_backup
            ;;
        db-restore)
            db_restore "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Create necessary directories
mkdir -p backups

# Run main function
main "$@"