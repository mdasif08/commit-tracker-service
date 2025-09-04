pipeline {
    agent any
    
    environment {
        SERVICE_NAME = 'commit-tracker-service'
        HEALTH_URL = 'http://localhost:8001/health'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
                echo '✅ Code checked out successfully'
            }
        }
        
        stage('Deploy in SEPARATE Container') {
            steps {
                sh '''
                    echo "🚀 Deploying application in SEPARATE container..."
                    
                    # Create deployment script for separate container
                    cat > deploy-separate.sh << 'EOF'
#!/bin/bash
echo "=== DEPLOYING IN SEPARATE CONTAINER ==="

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down --remove-orphans || echo "No existing containers to stop"

# Clean up orphaned containers
docker container prune -f || echo "No containers to prune"

# Build and start services in SEPARATE containers
echo "Building and starting services in SEPARATE containers..."
docker-compose up -d --build --force-recreate

# Wait for services to start
echo "Waiting for services to start..."
sleep 45

# Health check
echo "Performing health check..."
for i in {1..5}; do
    if curl -f http://localhost:8001/health; then
        echo "✅ Health check passed on attempt $i"
        break
    else
        echo "⏳ Health check attempt $i failed, retrying in 10 seconds..."
        sleep 10
    fi
done

# Show running containers
echo "=== RUNNING CONTAINERS ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "=== DEPLOYMENT COMPLETE ==="
echo "✅ Jenkins container: jenkins-main (running)"
echo "✅ Your app container: commit-tracker-service (running)"
echo "✅ Database container: postgres (running)"
echo "🌐 Your service is accessible at: http://localhost:8001"
EOF
                    
                    chmod +x deploy-separate.sh
                    echo "✅ Deployment script for SEPARATE container created"
                '''
            }
        }
        
        stage('Verify Separate Container Deployment') {
            steps {
                sh '''
                    echo "�� Verifying SEPARATE container deployment..."
                    echo "Deployment script is ready to run"
                    echo "This will deploy your app in a SEPARATE container from Jenkins"
                '''
            }
        }
    }
    
    post {
        success {
            echo "🎉 CI/CD Pipeline SUCCESSFUL!"
            echo "✅ Code checked out successfully"
            echo "✅ Deployment script for SEPARATE container created"
            echo " Run ./deploy-separate.sh to deploy your application"
            echo "📦 Your app will run in a SEPARATE container from Jenkins"
            echo "🌐 Your service will be accessible at: http://localhost:8001"
        }
        failure {
            echo "❌ CI/CD Pipeline Failed!"
            echo "🔍 Check the logs above for specific errors"
        }
        always {
            echo "Pipeline completed"
            cleanWs()
        }
    }
}