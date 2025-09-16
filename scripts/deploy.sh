#!/bin/bash

# Deployment script for Merchant Center Monitor
# Supports Google Cloud Run and Vercel deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    print_success "All requirements met"
}

# Deploy to Google Cloud Run
deploy_cloud_run() {
    print_status "Deploying to Google Cloud Run..."
    
    # Get project ID
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No Google Cloud project set. Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    print_status "Using project: $PROJECT_ID"
    
    # Build and push image
    print_status "Building Docker image..."
    docker build -t gcr.io/$PROJECT_ID/merchant-monitor .
    
    print_status "Pushing image to Container Registry..."
    docker push gcr.io/$PROJECT_ID/merchant-monitor
    
    # Deploy to Cloud Run
    print_status "Deploying to Cloud Run..."
    gcloud run deploy merchant-monitor \
        --image gcr.io/$PROJECT_ID/merchant-monitor \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --memory 512Mi \
        --cpu 1 \
        --max-instances 10 \
        --set-env-vars ENVIRONMENT=production
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe merchant-monitor --region=us-central1 --format='value(status.url)')
    print_success "Deployed to: $SERVICE_URL"
    
    # Create Cloud Scheduler job
    print_status "Creating Cloud Scheduler job..."
    gcloud scheduler jobs create http merchant-monitor-cron \
        --schedule "*/30 * * * *" \
        --uri "$SERVICE_URL/tasks/run" \
        --http-method POST \
        --headers Content-Type=application/json \
        --time-zone UTC \
        --region us-central1 || print_warning "Scheduler job may already exist"
    
    print_success "Cloud Scheduler job created"
    
    # Test deployment
    print_status "Testing deployment..."
    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        print_success "Health check passed"
    else
        print_warning "Health check failed - please check the deployment"
    fi
    
    print_success "Google Cloud Run deployment completed!"
    print_status "Dashboard: $SERVICE_URL/dashboard"
    print_status "API Docs: $SERVICE_URL/docs"
}

# Deploy to Vercel
deploy_vercel() {
    print_status "Deploying to Vercel..."
    
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI not found. Install with: npm i -g vercel"
        exit 1
    fi
    
    # Deploy
    vercel --prod
    
    print_success "Vercel deployment completed!"
    print_status "Cron job is automatically configured in vercel.json"
}

# Main deployment function
main() {
    echo "🚀 Merchant Center Monitor Deployment"
    echo "====================================="
    
    # Check requirements
    check_requirements
    
    # Ask for deployment target
    echo ""
    echo "Select deployment target:"
    echo "1) Google Cloud Run"
    echo "2) Vercel"
    echo "3) Both"
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            deploy_cloud_run
            ;;
        2)
            deploy_vercel
            ;;
        3)
            deploy_cloud_run
            echo ""
            deploy_vercel
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "Deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Configure environment variables in your deployment platform"
    echo "2. Set up Google Service Account and Merchant Center access"
    echo "3. Configure SendGrid API key"
    echo "4. Test the deployment with a manual check"
}

# Run main function
main "$@"
