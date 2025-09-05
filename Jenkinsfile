pipeline {
    agent any
    
    environment {
        SERVICE_NAME = 'commit-tracker-service'
        HEALTH_URL = 'http://localhost:8001/health'
        WORKSPACE_ROOT = "${WORKSPACE}"
        PROJECT_DIR = "${WORKSPACE}/commit-tracker-service"
    }
    
    stages {
        stage('Pre-Flight Checks') {
            steps {
                echo '🔍 Pre-flight system verification...'
                script {
                    sh '''
                        echo "=== System Pre-Flight Checks ==="
                        
                        # Check Docker
                        if ! command -v docker &> /dev/null; then
                            echo "❌ Docker not found"
                            exit 1
                        fi
                        
                        # Check Docker daemon
                        if ! docker ps &> /dev/null; then
                            echo "❌ Docker daemon not running"
                            exit 1
                        fi
                        
                        # Check Docker Compose
                        if ! command -v docker-compose &> /dev/null; then
                            echo "❌ Docker Compose not found"
                            exit 1
                        fi
                        
                        # Check Git
                        if ! command -v git &> /dev/null; then
                            echo "❌ Git not found"
                            exit 1
                        fi
                        
                        # Check curl
                        if ! command -v curl &> /dev/null; then
                            echo "❌ curl not found"
                            exit 1
                        fi
                        
                        # Check available disk space (minimum 2GB)
                        available_space=$(df . | tail -1 | awk '{print $4}')
                        if [ "$available_space" -lt 2097152 ]; then
                            echo "❌ Insufficient disk space (need at least 2GB)"
                            exit 1
                        fi
                        
                        # Check available memory (minimum 1GB)
                        available_memory=$(free -m | awk 'NR==2{print $7}')
                        if [ "$available_memory" -lt 1024 ]; then
                            echo "❌ Insufficient memory (need at least 1GB)"
                            exit 1
                        fi
                        
                        echo "✅ All pre-flight checks passed"
                    '''
                }
            }
        }
        
        stage('Guaranteed Repository Setup') {
            steps {
                echo '📋 Setting up repository with 100% success guarantee...'
                script {
                    sh '''
                        echo "=== Guaranteed Repository Setup ==="
                        
                        # Step 1: Clean workspace completely
                        echo "�� Cleaning workspace..."
                        cd ${WORKSPACE_ROOT}
                        rm -rf * .*
                        
                        # Step 2: Clone repository with retry mechanism
                        echo "�� Cloning repository..."
                        max_attempts=5
                        attempt=1
                        
                        while [ $attempt -le $max_attempts ]; do
                            echo "Attempt $attempt/$max_attempts"
                            
                            if git clone https://github.com/mdasif08/commit-tracker-service.git .; then
                                echo "✅ Repository cloned successfully"
                                break
                            else
                                echo "❌ Clone attempt $attempt failed"
                                if [ $attempt -eq $max_attempts ]; then
                                    echo "❌ All clone attempts failed"
                                    exit 1
                                fi
                                sleep 5
                                attempt=$((attempt + 1))
                            fi
                        done
                        
                        # Step 3: Verify repository structure
                        echo "🔍 Verifying repository structure..."
                        
                        required_files=(
                            "Jenkinsfile"
                            "Dockerfile"
                            "docker-compose.yml"
                            "requirements.txt"
                            "src/main.py"
                        )
                        
                        for file in "${required_files[@]}"; do
                            if [ ! -f "$file" ]; then
                                echo "❌ Required file missing: $file"
                                exit 1
                            fi
                        done
                        
                        # Step 4: Set up Git configuration
                        echo "⚙️ Setting up Git configuration..."
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@ci.local"
                        
                        # Step 5: Verify Git status
                        echo "📊 Git repository status:"
                        echo "Repository URL: $(git config --get remote.origin.url)"
                        echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
                        echo "Latest commit: $(git rev-parse --short HEAD)"
                        echo "Working directory clean: $(git status --porcelain | wc -l) files changed"
                        
                        # Set environment variables
                        export GIT_COMMIT_SHORT=$(git rev-parse --short HEAD)
                        export GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
                        export GIT_REPO_URL=$(git config --get remote.origin.url)
                        
                        echo "✅ Repository setup completed successfully"
                    '''
                    
                    // Set Jenkins environment variables
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_BRANCH = sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Bulletproof Docker Build') {
            steps {
                echo '�� Bulletproof Docker build process...'
                script {
                    sh '''
                        echo "=== Bulletproof Docker Build ==="
                        
                        # Step 1: Clean Docker environment completely
                        echo "🧹 Cleaning Docker environment..."
                        docker system prune -af || true
                        docker builder prune -af || true
                        docker volume prune -f || true
                        docker network prune -f || true
                        
                        # Step 2: Verify Dockerfile exists and is valid
                        echo "🔍 Verifying Dockerfile..."
                        if [ ! -f "Dockerfile" ]; then
                            echo "❌ Dockerfile not found"
                            exit 1
                        fi
                        
                        # Step 3: Test Dockerfile syntax
                        echo "�� Testing Dockerfile syntax..."
                        if ! docker build --dry-run . > /dev/null 2>&1; then
                            echo "❌ Dockerfile syntax error"
                            exit 1
                        fi
                        
                        # Step 4: Build with comprehensive error handling
                        echo "🔨 Building Docker image..."
                        max_build_attempts=3
                        build_attempt=1
                        
                        while [ $build_attempt -le $max_build_attempts ]; do
                            echo "Build attempt $build_attempt/$max_build_attempts"
                            
                            if docker build --no-cache \
                                --build-arg BUILD_TIMESTAMP=$(date +%Y%m%d-%H%M%S) \
                                --build-arg GIT_COMMIT=${GIT_COMMIT_SHORT} \
                                -t ${SERVICE_NAME}:${GIT_COMMIT_SHORT} \
                                -t ${SERVICE_NAME}:latest \
                                .; then
                                echo "✅ Docker build successful"
                                break
                            else
                                echo "❌ Build attempt $build_attempt failed"
                                if [ $build_attempt -eq $max_build_attempts ]; then
                                    echo "❌ All build attempts failed"
                                    exit 1
                                fi
                                sleep 10
                                build_attempt=$((build_attempt + 1))
                            fi
                        done
                        
                        # Step 5: Verify image was created
                        echo "🔍 Verifying Docker image..."
                        if ! docker images | grep -q ${SERVICE_NAME}; then
                            echo "❌ Docker image not found after build"
                            exit 1
                        fi
                        
                        echo "✅ Docker build completed successfully"
                    '''
                }
            }
        }
        
        stage('Guaranteed Deployment') {
            steps {
                echo '🚀 Guaranteed deployment process...'
                script {
                    sh '''
                        echo "=== Guaranteed Deployment ==="
                        
                        # Step 1: Stop all existing containers
                        echo "🛑 Stopping existing containers..."
                        docker-compose down --remove-orphans --timeout 30 || true
                        
                        # Step 2: Verify docker-compose.yml
                        echo "🔍 Verifying docker-compose.yml..."
                        if [ ! -f "docker-compose.yml" ]; then
                            echo "❌ docker-compose.yml not found"
                            exit 1
                        fi
                        
                        # Step 3: Test docker-compose configuration
                        echo "�� Testing docker-compose configuration..."
                        if ! docker-compose config > /dev/null 2>&1; then
                            echo "❌ docker-compose.yml configuration error"
                            exit 1
                        fi
                        
                        # Step 4: Deploy with retry mechanism
                        echo "�� Deploying services..."
                        max_deploy_attempts=3
                        deploy_attempt=1
                        
                        while [ $deploy_attempt -le $max_deploy_attempts ]; do
                            echo "Deploy attempt $deploy_attempt/$max_deploy_attempts"
                            
                            if docker-compose up -d --force-recreate; then
                                echo "✅ Deployment successful"
                                break
                            else
                                echo "❌ Deploy attempt $deploy_attempt failed"
                                if [ $deploy_attempt -eq $max_deploy_attempts ]; then
                                    echo "❌ All deploy attempts failed"
                                    exit 1
                                fi
                                sleep 15
                                deploy_attempt=$((deploy_attempt + 1))
                            fi
                        done
                        
                        # Step 5: Wait for services to start
                        echo "⏳ Waiting for services to start..."
                        sleep 30
                        
                        # Step 6: Verify containers are running
                        echo "🔍 Verifying container status..."
                        if ! docker-compose ps | grep -q "Up"; then
                            echo "❌ No containers are running"
                            docker-compose ps
                            exit 1
                        fi
                        
                        echo "✅ Deployment completed successfully"
                    '''
                }
            }
        }
        
        stage('Comprehensive Health Verification') {
            steps {
                echo '🏥 Comprehensive health verification...'
                script {
                    sh '''
                        echo "=== Comprehensive Health Verification ==="
                        
                        # Step 1: Wait for service to be ready
                        echo "⏳ Waiting for service to be ready..."
                        max_health_attempts=60  # 10 minutes total
                        health_attempt=1
                        
                        while [ $health_attempt -le $max_health_attempts ]; do
                            echo "Health check attempt $health_attempt/$max_health_attempts"
                            
                            # Check if container is running
                            if ! docker ps | grep -q ${SERVICE_NAME}; then
                                echo "❌ Container ${SERVICE_NAME} is not running"
                                docker ps -a | grep ${SERVICE_NAME}
                                exit 1
                            fi
                            
                            # Check if port is accessible
                            if curl -f ${HEALTH_URL} > /dev/null 2>&1; then
                                echo "✅ Service is healthy"
                                break
                            fi
                            
                            if [ $health_attempt -eq $max_health_attempts ]; then
                                echo "❌ Service failed to become healthy after $max_health_attempts attempts"
                                echo "Container logs:"
                                docker logs ${SERVICE_NAME} --tail 100
                                exit 1
                            fi
                            
                            sleep 10
                            health_attempt=$((health_attempt + 1))
                        done
                        
                        # Step 2: Test all endpoints
                        echo "🧪 Testing all endpoints..."
                        
                        endpoints=(
                            "http://localhost:8001/"
                            "http://localhost:8001/health"
                            "http://localhost:8001/api/git/status"
                            "http://localhost:8001/api/system"
                            "http://localhost:8001/metrics"
                        )
                        
                        failed_endpoints=0
                        for endpoint in "${endpoints[@]}"; do
                            echo "Testing: $endpoint"
                            if curl -f "$endpoint" > /dev/null 2>&1; then
                                echo "✅ $endpoint - OK"
                            else
                                echo "❌ $endpoint - FAILED"
                                failed_endpoints=$((failed_endpoints + 1))
                            fi
                        done
                        
                        if [ $failed_endpoints -gt 0 ]; then
                            echo "❌ $failed_endpoints endpoints failed"
                            exit 1
                        fi
                        
                        # Step 3: Performance check
                        echo "📊 Performance check..."
                        response_time=$(curl -o /dev/null -s -w '%{time_total}' ${HEALTH_URL})
                        echo "Health endpoint response time: ${response_time}s"
                        
                        if (( $(echo "$response_time > 5.0" | bc -l) )); then
                            echo "⚠️ Performance warning - response time > 5s"
                        else
                            echo "✅ Performance check passed"
                        fi
                        
                        echo "✅ All health checks passed"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '�� Pipeline completed successfully!'
            script {
                sh '''
                    echo "=== SUCCESS SUMMARY ===" > success_report.txt
                    echo "Status: SUCCESS" >> success_report.txt
                    echo "Service: ${SERVICE_NAME}" >> success_report.txt
                    echo "Version: ${GIT_COMMIT_SHORT}" >> success_report.txt
                    echo "Branch: ${GIT_BRANCH}" >> success_report.txt
                    echo "Build: ${BUILD_NUMBER}" >> success_report.txt
                    echo "Timestamp: $(date)" >> success_report.txt
                    echo "Service URL: http://localhost:8001" >> success_report.txt
                    echo "Health Check: ${HEALTH_URL}" >> success_report.txt
                    echo "API Docs: http://localhost:8001/api/docs" >> success_report.txt
                    echo "Metrics: http://localhost:8001/metrics" >> success_report.txt
                '''
            }
        }
        
        failure {
            echo '❌ Pipeline failed - collecting diagnostic information...'
            script {
                sh '''
                    echo "=== FAILURE ANALYSIS ===" > failure_report.txt
                    echo "Status: FAILED" >> failure_report.txt
                    echo "Build: ${BUILD_NUMBER}" >> failure_report.txt
                    echo "Commit: ${GIT_COMMIT_SHORT}" >> failure_report.txt
                    echo "Timestamp: $(date)" >> failure_report.txt
                    echo "" >> failure_report.txt
                    
                    echo "=== SYSTEM INFORMATION ===" >> failure_report.txt
                    echo "Docker Version:" >> failure_report.txt
                    docker --version >> failure_report.txt 2>&1 || echo "Docker not available" >> failure_report.txt
                    echo "Docker Compose Version:" >> failure_report.txt
                    docker-compose --version >> failure_report.txt 2>&1 || echo "Docker Compose not available" >> failure_report.txt
                    echo "Git Version:" >> failure_report.txt
                    git --version >> failure_report.txt 2>&1 || echo "Git not available" >> failure_report.txt
                    echo "" >> failure_report.txt
                    
                    echo "=== CONTAINER STATUS ===" >> failure_report.txt
                    docker-compose ps >> failure_report.txt 2>&1 || echo "No containers running" >> failure_report.txt
                    echo "" >> failure_report.txt
                    
                    echo "=== SERVICE LOGS ===" >> failure_report.txt
                    docker logs ${SERVICE_NAME} --tail 100 >> failure_report.txt 2>&1 || echo "No service logs available" >> failure_report.txt
                    echo "" >> failure_report.txt
                    
                    echo "=== RECOVERY RECOMMENDATIONS ===" >> failure_report.txt
                    echo "1. Check Docker daemon status: sudo systemctl status docker" >> failure_report.txt
                    echo "2. Verify port 8001 is not in use: netstat -tlnp | grep 8001" >> failure_report.txt
                    echo "3. Check system resources: free -h && df -h" >> failure_report.txt
                    echo "4. Verify network connectivity: ping github.com" >> failure_report.txt
                    echo "5. Check Jenkins workspace permissions: ls -la ${WORKSPACE}" >> failure_report.txt
                '''
            }
        }
        
        always {
            echo '�� Final cleanup...'
            script {
                sh '''
                    echo "=== Final Cleanup ==="
                    
                    # Remove temporary files
                    rm -f success_report.txt failure_report.txt || true
                    
                    # Clean up Docker resources (keep latest images)
                    docker image prune -f || true
                    
                    echo "✅ Cleanup completed"
                '''
            }
        }
    }
}