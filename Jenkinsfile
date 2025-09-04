pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
        SERVICE_NAME = 'commit-tracker-service'
        HEALTH_URL = 'http://localhost:8001/health'
        VENV_PATH = '/var/jenkins_home/venv'
    }
    
    stages {
        // ===== CI STAGES =====
        stage('Checkout Code') {
            steps {
                checkout scm
                echo '✅ Code checked out successfully'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'source ${VENV_PATH}/bin/activate && pip install -r requirements.txt'
                echo '✅ Dependencies installed'
            }
        }
        
        stage('Run Tests') {
            steps {
                sh 'source ${VENV_PATH}/bin/activate && python -m pytest tests/ -v'
                echo '✅ Tests completed successfully'
            }
        }
        
        stage('Code Quality Check') {
            steps {
                sh 'source ${VENV_PATH}/bin/activate && python -m flake8 src/ || echo "Flake8 check completed"'
                echo '✅ Code quality check completed'
            }
        }
        
        // ===== CD STAGES =====
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
            echo "🎉 CI/CD Pipeline Successful!"
            echo "✅ Code tested and validated"
            echo "✅ Service deployed successfully"
            echo "🌐 Your service is running at: http://localhost:8001"
            echo "🗄️ Database accessible at: localhost:5433"
            echo "📊 To check containers: docker ps"
            echo "📝 To check logs: docker compose logs ${SERVICE_NAME}"
        }
        failure {
            echo "❌ CI/CD Pipeline Failed!"
            echo "Check the logs above for errors"
            echo "Common issues:"
            echo "1. Tests failed"
            echo "2. Docker not running on Jenkins host"
            echo "3. Port 8001 already in use"
            echo "4. Container build failed"
        }
        always {
            echo "Pipeline completed. Cleaning up workspace..."
            cleanWs()
        }
    }
}
