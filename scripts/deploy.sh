#!/bin/bash

# Deployment script for NZ IT Job Scraper
# Usage: ./scripts/deploy.sh [production|staging|development]

set -e

ENVIRONMENT=${1:-development}
PROJECT_NAME="job-scraper"
DOCKER_COMPOSE_FILE="docker-compose.yml"

echo "🚀 Deploying NZ IT Job Scraper to $ENVIRONMENT environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration before continuing."
    echo "   Especially set your DATABASE_URL and OPENAI_API_KEY"
    read -p "Press Enter to continue after editing .env file..."
fi

# Create necessary directories
mkdir -p logs nginx/ssl

# Set environment-specific configurations
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Configuring for production..."
    export FLASK_ENV=production
    export DEBUG=false
elif [ "$ENVIRONMENT" = "staging" ]; then
    echo "🧪 Configuring for staging..."
    export FLASK_ENV=staging
    export DEBUG=true
else
    echo "💻 Configuring for development..."
    export FLASK_ENV=development
    export DEBUG=true
fi

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose pull

# Build application image
echo "🔨 Building application image..."
docker-compose build

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Setting up database..."
docker-compose exec web python main.py setup

# Run initial scrape
echo "🕷️  Running initial scrape..."
docker-compose exec web python main.py scrape --test

# Check service health
echo "🏥 Checking service health..."
sleep 5

if docker-compose ps | grep -q "Up"; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Web interface: http://localhost:5000"
    echo "📊 Database: localhost:5432"
    echo "📝 Logs: docker-compose logs -f"
    echo ""
    echo "🔧 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Restart: docker-compose restart"
    echo "   Manual scrape: docker-compose exec web python main.py scrape"
else
    echo "❌ Deployment failed. Check logs with: docker-compose logs"
    exit 1
fi

# Setup cron job for backup (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "💾 Setting up database backup..."
    
    # Create backup script
    cat > scripts/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U scraper_user job_scraper_db > "\$BACKUP_DIR/backup_\$DATE.sql"
find \$BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOF

    chmod +x scripts/backup.sh
    
    echo "📅 Add this to your crontab for daily backups:"
    echo "   0 2 * * * /path/to/your/project/scripts/backup.sh"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "   Environment: $ENVIRONMENT"
echo "   Timestamp: $(date)"
