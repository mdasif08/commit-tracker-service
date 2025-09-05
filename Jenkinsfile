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
                    sh '''
                        docker build -t ${SERVICE_NAME}:${GIT_COMMIT_SHORT} .
                        docker tag ${SERVICE_NAME}:${GIT_COMMIT_SHORT} ${SERVICE_NAME}:latest
                        docker images | grep ${SERVICE_NAME}
                    '''
                }
                echo "✅ Docker image built successfully"
            }
        }

        stage('Run Tests') {
            steps {
                echo '🧪 Running tests...'
                script {
                    sh '''
                        docker run --rm \
                            -v $(pwd):/app \
                            -w /app \
                            python:3.11-slim \
                            bash -c "
                                apt-get update && apt-get install -y git curl build-essential
                                pip install -r requirements.txt
                                python -m pytest tests/ -v --tb=short
                            "
                    '''
                }
                echo "✅ All tests passed"
            }
        }

        stage('Code Quality') {
            steps {
                echo '🔍 Running code quality checks...'
                script {
                    sh '''
                        docker run --rm \
                            -v $(pwd):/app \
                            -w /app \
                            python:3.11-slim \
                            bash -c "
                                pip install flake8
                                flake8 src/ --max-line-length=100 --ignore=E203,W503
                            "
                    '''
                }
                echo "✅ Code quality checks passed"
            }
        }

        stage('Deploy Application') {
            steps {
                echo '🚀 Deploying application...'
                script {
                    sh '''
                        docker-compose down --remove-orphans || true
                        docker image prune -f || true
                        docker-compose up -d --build --force-recreate
                        echo "⏳ Waiting for services to start..."
                        sleep 30
                        docker-compose ps
                    '''
                }
                echo "✅ Application deployed successfully"
            }
        }

        stage('Health Check') {
            steps {
                echo '🏥 Performing health checks...'
                script {
                    sh '''
                        for i in $(seq 1 30); do
                            if curl -f ${HEALTH_URL} > /dev/null 2>&1; then
                                echo "✅ Health check passed"
                                break
                            fi
                            echo "⏳ Attempt $i/30 - waiting for service..."
                            sleep 10
                        done
                        curl -f ${HEALTH_URL}
                    '''
                }
                echo "✅ Health checks passed"
            }
        }

        stage('Verify Deployment') {
            steps {
                echo '🔍 Verifying deployment...'
                script {
                    sh '''
                        echo "📋 Container Status:"
                        docker-compose ps
                        echo "   Service Logs (last 20 lines):"
                        docker logs ${SERVICE_NAME} --tail 20 || true
                        curl -f http://localhost:8001/ || echo "❌ Root endpoint failed"
                        curl -f http://localhost:8001/health || echo "❌ Health endpoint failed"
                        curl -f http://localhost:8001/api/git/status || echo "❌ Git status endpoint failed"
                        curl -f http://localhost:8001/api/system || echo "❌ System endpoint failed"
                        curl -f http://localhost:8001/metrics || echo "❌ Metrics endpoint failed"
                    '''
                }
                echo "✅ Deployment verification completed"
            }
        }
    }

    post {
        success {
            echo '🎉 Pipeline completed successfully!'
            echo "🌐 Service URL: http://localhost:8001"
            echo "📚 API Docs: http://localhost:8001/api/docs"
            echo "📊 Metrics: http://localhost:8001/metrics"
        }
        failure {
            echo '❌ Pipeline failed!'
            echo '🔍 Troubleshooting steps:'
            echo '1. docker ps'
            echo '2. docker logs commit-tracker-service'
            echo '3. docker-compose ps'
            echo '4. curl http://localhost:8001/health'
        }
        always {
            echo '🧹 Cleaning up workspace...'
        }
    }
}