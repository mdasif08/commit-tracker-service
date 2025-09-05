pipeline {
    agent any
    
    environment {
        SERVICE_NAME = 'commit-tracker-service'
        HEALTH_URL = 'http://localhost:8001/health'
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                echo '📋 Checking out code...'
                script {
                    if (fileExists('.git')) {
                        echo "ℹ Git repo already checked out by Jenkins (Pipeline from SCM). Skipping checkout."
                    } else {
                        deleteDir()
                        checkout scm
                    }

                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_BRANCH = sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "✅ Code checked out - Branch: ${env.GIT_BRANCH}, Commit: ${env.GIT_COMMIT_SHORT}"
            }
        }
        
        stage('Build Application') {
            steps {
                echo '🔨 Building Docker image...'
                script {
                    try {
                        sh '''
                            # Clean up Docker cache and build without cache
                            docker system prune -f
                            docker builder prune -f
                            
                            # Build the Docker image without cache
                            docker build --no-cache -t ${SERVICE_NAME}:${GIT_COMMIT_SHORT} .
                            docker tag ${SERVICE_NAME}:${GIT_COMMIT_SHORT} ${SERVICE_NAME}:latest
                            
                            # Verify image was created
                            docker images | grep ${SERVICE_NAME}
                        '''
                        echo "✅ Docker image built successfully"
                    } catch (Exception e) {
                        echo "❌ Docker build failed: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo '🧪 Running tests...'
                script {
                    try {
                        sh '''
                            # Get the current working directory (Jenkins workspace)
                            WORKSPACE_DIR=$(pwd)
                            echo "Workspace directory: $WORKSPACE_DIR"
                            
                            # List files to verify requirements.txt exists
                            echo "Files in workspace:"
                            ls -la
                            
                            # Verify requirements.txt exists
                            if [ ! -f "requirements.txt" ]; then
                                echo "❌ requirements.txt not found!"
                                exit 1
                            fi
                            
                            # Create a Dockerfile for testing
                            cat > Dockerfile.test << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git curl build-essential postgresql-client

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy source code and scripts
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

# Copy .git directory to make it a proper Git repository
COPY .git/ ./.git/

# Set Python path to include scripts directory
ENV PYTHONPATH=/app/scripts:/app/src

# Initialize Git configuration for testing
RUN git config --global user.name "Test User" && \
    git config --global user.email "test@example.com"

# Run tests
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
EOF
                            
                            # Clean up any existing test images
                            docker rmi ${SERVICE_NAME}-test 2>/dev/null || true
                            
                            # Build and run test container without cache
                            docker build --no-cache -f Dockerfile.test -t ${SERVICE_NAME}-test .
                            docker run --rm ${SERVICE_NAME}-test
                            
                            # Clean up test image
                            docker rmi ${SERVICE_NAME}-test || true
                        '''
                        echo "✅ All tests passed"
                    } catch (Exception e) {
                        echo "❌ Tests failed: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }
        
        stage('Code Quality') {
            steps {
                echo '🔍 Running code quality checks (non-blocking)...'
                script {
                    try {
                        sh '''
                            # Create a Dockerfile for code quality
                            cat > Dockerfile.quality << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git curl build-essential

# Set working directory
WORKDIR /app

# Install flake8
RUN pip install flake8

# Copy source code
COPY src/ ./src/

# Run flake8 with warnings only (non-blocking)
CMD ["flake8", "src/", "--max-line-length=100", "--ignore=E203,W503,E305", "--show-source", "--statistics"]
EOF
                            
                            # Clean up any existing quality images
                            docker rmi ${SERVICE_NAME}-quality 2>/dev/null || true
                            
                            # Build and run quality check container without cache
                            docker build --no-cache -f Dockerfile.quality -t ${SERVICE_NAME}-quality .
                            docker run --rm ${SERVICE_NAME}-quality || echo "⚠️ Code quality issues found but continuing..."
                            
                            # Clean up quality check image
                            docker rmi ${SERVICE_NAME}-quality || true
                        '''
                        echo "✅ Code quality checks completed (non-blocking)"
                    } catch (Exception e) {
                        echo "⚠️ Code quality checks had issues but continuing: ${e.getMessage()}"
                        // Don't throw the exception - make it non-blocking
                    }
                }
            }
        }
        
        stage('Deploy Application') {
            steps {
                echo '🚀 Deploying application...'
                script {
                    try {
                        sh '''
                            # Stop existing containers
                            docker-compose down --remove-orphans || true
                            
                            # Clean up old images and build without cache
                            docker image prune -f || true
                            docker-compose build --no-cache
                            docker-compose up -d --force-recreate
                            
                            # Wait for services to start
                            echo "⏳ Waiting for services to start..."
                            sleep 30
                            
                            # Check if containers are running
                            docker-compose ps
                        '''
                        echo "✅ Application deployed successfully"
                    } catch (Exception e) {
                        echo "❌ Deployment failed: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo '🏥 Performing health checks...'
                script {
                    try {
                        sh '''
                            # Wait for application to be ready
                            echo "⏳ Waiting for application to be ready..."
                            for i in $(seq 1 30); do
                                if curl -f ${HEALTH_URL} > /dev/null 2>&1; then
                                    echo "✅ Health check passed"
                                    break
                                fi
                                echo "⏳ Attempt $i/30 - waiting for service..."
                                sleep 10
                            done
                            
                            # Final health check
                            curl -f ${HEALTH_URL} || {
                                echo "❌ Final health check failed"
                                exit 1
                            }
                            
                            # Get health status
                            echo "📊 Health Status:"
                            curl -s ${HEALTH_URL} | jq '.' || curl -s ${HEALTH_URL}
                        '''
                        echo "✅ Health checks passed"
                    } catch (Exception e) {
                        echo "❌ Health check failed: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                echo '🔍 Verifying deployment...'
                script {
                    try {
                        sh '''
                            # Check container status
                            echo "📋 Container Status:"
                            docker-compose ps
                            
                            # Check service logs
                            echo "📋 Service Logs (last 20 lines):"
                            docker logs ${SERVICE_NAME} --tail 20
                            
                            # Test all critical endpoints
                            echo "🧪 Testing endpoints..."
                            
                            # Test root endpoint
                            curl -f http://localhost:8001/ || echo "❌ Root endpoint failed"
                            
                            # Test health endpoint
                            curl -f http://localhost:8001/health || echo "❌ Health endpoint failed"
                            
                            # Test git status endpoint
                            curl -f http://localhost:8001/api/git/status || echo "❌ Git status endpoint failed"
                            
                            # Test system endpoint
                            curl -f http://localhost:8001/api/system || echo "❌ System endpoint failed"
                            
                            # Test metrics endpoint
                            curl -f http://localhost:8001/metrics || echo "❌ Metrics endpoint failed"
                            
                            echo "✅ All endpoint tests completed"
                        '''
                        echo "✅ Deployment verification completed"
                    } catch (Exception e) {
                        echo "❌ Deployment verification failed: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 Pipeline completed successfully!'
            echo '✅ Commit Tracker Service is running and healthy'
            echo "🌐 Service URL: http://localhost:8001"
            echo " Health Check: ${HEALTH_URL}"
            echo "📚 API Docs: http://localhost:8001/api/docs"
            echo "📊 Metrics: http://localhost:8001/metrics"
            
            script {
                try {
                    sh '''
                        echo "Pipeline Status: SUCCESS" > pipeline_status.txt
                        echo "Service URL: http://localhost:8001" >> pipeline_status.txt
                        echo "Health Check: ${HEALTH_URL}" >> pipeline_status.txt
                        echo "Build: ${BUILD_NUMBER}" >> pipeline_status.txt
                        echo "Commit: ${GIT_COMMIT_SHORT}" >> pipeline_status.txt
                    '''
                } catch (Exception e) {
                    echo "Failed to create status file: ${e.getMessage()}"
                }
            }
        }
        
        failure {
            echo '❌ Pipeline failed!'
            echo '🔍 Troubleshooting steps:'
            echo '1. Check Docker is running: docker ps'
            echo '2. Check service logs: docker logs commit-tracker-service'
            echo '3. Check container status: docker-compose ps'
            echo '4. Verify Docker socket access: docker ps'
            echo '5. Check health endpoint: curl http://localhost:8001/health'
            
            script {
                try {
                    sh '''
                        echo "Pipeline Status: FAILED" > pipeline_status.txt
                        echo "Build: ${BUILD_NUMBER}" >> pipeline_status.txt
                        echo "Commit: ${GIT_COMMIT_SHORT}" >> pipeline_status.txt
                        echo "Error: Pipeline failed at stage" >> pipeline_status.txt
                        
                        # Collect container logs
                        echo "=== Container Logs ===" >> failure_logs.txt
                        docker logs commit-tracker-service --tail 50 >> failure_logs.txt 2>&1 || true
                        docker logs commit-tracker-postgres --tail 20 >> failure_logs.txt 2>&1 || true
                        
                        # Collect container status
                        echo "=== Container Status ===" >> failure_logs.txt
                        docker-compose ps >> failure_logs.txt 2>&1 || true
                        
                        # Collect system info
                        echo "=== System Info ===" >> failure_logs.txt
                        docker version >> failure_logs.txt 2>&1 || true
                        docker-compose version >> failure_logs.txt 2>&1 || true
                    '''
                } catch (Exception e) {
                    echo "Failed to collect failure information: ${e.getMessage()}"
                }
            }
        }
        
        always {
            echo '🧹 Cleaning up workspace...'
        }
    }
}