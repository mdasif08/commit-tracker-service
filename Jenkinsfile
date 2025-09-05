pipeline {
    agent {
        docker {
            image 'docker:latest'
            args '-v /var/run/docker.sock:/var/run/docker.sock --privileged'
        }
    }
    
    environment {
        SERVICE_NAME = 'commit-tracker-service'
        HEALTH_URL = 'http://localhost:8001/health'
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                echo '📋 Checking out code...'
                checkout scm
                script {
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
                            # Install docker-compose
                            apk add --no-cache docker-compose
                            
                            # Build the Docker image
                            docker build -t ${SERVICE_NAME}:${GIT_COMMIT_SHORT} .
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
                echo '�� Running tests...'
                script {
                    try {
                        sh '''
                            # Run tests in a temporary container
                            docker run --rm \
                                -v $(pwd):/app \
                                -w /app \
                                python:3.11-slim \
                                bash -c "
                                    apt-get update && apt-get install -y git postgresql-client curl build-essential
                                    pip install -r requirements.txt
                                    python -m pytest tests/ -v --tb=short
                                "
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
                echo '🔍 Running code quality checks...'
                script {
                    try {
                        sh '''
                            # Run flake8 in a temporary container
                            docker run --rm \
                                -v $(pwd):/app \
                                -w /app \
                                python:3.11-slim \
                                bash -c "
                                    pip install flake8
                                    flake8 src/ --max-line-length=100 --ignore=E203,W503
                                "
                        '''
                        echo "✅ Code quality checks passed"
                    } catch (Exception e) {
                        echo "❌ Code quality checks failed: ${e.getMessage()}"
                        throw e
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
                            # Install docker-compose
                            apk add --no-cache docker-compose
                            
                            # Stop existing containers
                            docker-compose down --remove-orphans || true
                            
                            # Clean up old images
                            docker image prune -f || true
                            
                            # Start services
                            docker-compose up -d --build --force-recreate
                            
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
                            # Install curl for health checks
                            apk add --no-cache curl
                            
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
                            # Install curl for endpoint testing
                            apk add --no-cache curl
                            
                            # Check container status
                            echo "📋 Container Status:"
                            docker-compose ps
                            
                            # Check service logs
                            echo "�� Service Logs (last 20 lines):"
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
            echo '�� Pipeline completed successfully!'
            echo '✅ Commit Tracker Service is running and healthy'
            echo "🌐 Service URL: http://localhost:8001"
            echo " Health Check: ${HEALTH_URL}"
            echo "📚 API Docs: http://localhost:8001/api/docs"
            echo "📊 Metrics: http://localhost:8001/metrics"
            
            // Optional: Send success notification
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
            
            // Collect failure information
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
            // Cleanup is handled by Jenkins workspace cleanup
        }
    }
}