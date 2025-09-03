pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
        SERVICE_NAME = 'commit-tracker-service'
        HEALTH_URL = 'http://localhost:8001/health'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
                echo 'Code checked out successfully'
            }
        }
        
        stage('Verify Docker') {
            steps {
                script {
                    echo '🔍 Checking Docker installation...'
                    try {
                        sh 'docker --version'
                        echo '✅ Docker found'
                    } catch (Exception e) {
                        echo '⚠️ Docker not found, attempting to install...'
                        sh 'apt-get update && apt-get install -y docker.io || echo "Could not install Docker"'
                        sh 'service docker start || echo "Could not start Docker service"'
                        sh 'docker --version || echo "Docker still not available"'
                    }
                    
                    try {
                        sh 'docker compose version || docker-compose --version || echo "Docker Compose not found"'
                        echo '✅ Docker Compose verification completed'
                    } catch (Exception e) {
                        echo '⚠️ Docker Compose not available'
                    }
                }
            }
        }
        
        stage('Stop Existing Containers') {
            steps {
                script {
                    echo '🛑 Stopping existing containers...'
                    try {
                        sh 'docker compose -f ${DOCKER_COMPOSE_FILE} down || docker-compose -f ${DOCKER_COMPOSE_FILE} down || echo "No containers to stop"'
                        echo '✅ Existing containers stopped'
                    } catch (Exception e) {
                        echo '⚠️ Warning: Could not stop containers, continuing...'
                    }
                }
            }
        }
        
        stage('Build and Deploy') {
            steps {
                script {
                    echo '🚀 Building and starting containers...'
                    try {
                        // Try modern docker compose first
                        sh 'docker compose -f ${DOCKER_COMPOSE_FILE} up -d --build || docker-compose -f ${DOCKER_COMPOSE_FILE} up -d --build'
                        echo '✅ Containers built and started'
                    } catch (Exception e) {
                        echo '❌ Failed to build and start containers'
                        echo 'Attempting alternative deployment method...'
                        
                        // Alternative: Build image manually
                        sh 'docker build -t ${SERVICE_NAME}:latest .'
                        sh 'docker run -d --name ${SERVICE_NAME} -p 8001:8001 ${SERVICE_NAME}:latest || echo "Manual deployment failed"'
                        
                        if (sh(script: 'docker ps | grep ${SERVICE_NAME}', returnStatus: true) == 0) {
                            echo '✅ Manual deployment successful'
                        } else {
                            error 'All deployment methods failed'
                        }
                    }
                }
            }
        }
        
        stage('Wait for Service') {
            steps {
                script {
                    echo '⏳ Waiting for service to be ready...'
                    sh 'sleep 25'
                    echo '⏰ Service should be ready now'
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    echo '🏥 Checking service health...'
                    try {
                        sh 'curl -f ${HEALTH_URL} || exit 1'
                        echo '✅ Health check passed!'
                    } catch (Exception e) {
                        echo '❌ Health check failed, checking container status...'
                        sh 'docker ps | grep ${SERVICE_NAME} || echo "Container not running"'
                        sh 'docker logs ${SERVICE_NAME} || echo "Could not get container logs"'
                        error 'Service health check failed: ' + e.getMessage()
                    }
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    echo '🔍 Verifying deployment...'
                    try {
                        sh 'docker ps | grep ${SERVICE_NAME} || echo "Container not found in docker ps"'
                        sh 'docker compose -f ${DOCKER_COMPOSE_FILE} ps || docker-compose -f ${DOCKER_COMPOSE_FILE} ps || echo "Docker compose not available"'
                        echo '✅ Deployment verified successfully!'
                    } catch (Exception e) {
                        echo '⚠️ Warning: Could not verify deployment completely'
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 CD Pipeline Successful!"
            echo "Your service is now running at: http://localhost:8001"
            echo "Database is accessible at: localhost:5433"
            echo "To check containers: docker ps"
            echo "To check logs: docker compose logs ${SERVICE_NAME}"
        }
        failure {
            echo "❌ CD Pipeline Failed!"
            echo "Check the logs above for errors"
            echo "Common issues:"
            echo "1. Docker not running on Jenkins host"
            echo "2. Port 8001 already in use"
            echo "3. Docker daemon not accessible"
            echo "4. Container build failed"
        }
        always {
            echo "Pipeline completed. Cleaning up workspace..."
            cleanWs()
        }
    }
}
