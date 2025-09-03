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
        
        stage('Stop Existing Containers') {
            steps {
                script {
                    echo 'Stopping existing containers...'
                    sh "docker-compose -f ${DOCKER_COMPOSE_FILE} down || true"
                    echo 'Existing containers stopped'
                }
            }
        }
        
        stage('Build and Deploy') {
            steps {
                script {
                    echo 'Building and starting containers...'
                    sh "docker-compose -f ${DOCKER_COMPOSE_FILE} up -d --build"
                    echo 'Containers started successfully'
                }
            }
        }
        
        stage('Wait for Service') {
            steps {
                script {
                    echo 'Waiting for service to be ready...'
                    sh 'sleep 15'
                    echo 'Service should be ready now'
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    echo 'Checking service health...'
                    sh "curl -f ${HEALTH_URL} || exit 1"
                    echo 'Health check passed!'
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    echo 'Verifying deployment...'
                    sh "docker ps | grep ${SERVICE_NAME}"
                    echo 'Deployment verified successfully!'
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 CD Pipeline Successful!"
            echo "Your service is now running at: http://localhost:8001"
            echo "Database is accessible at: localhost:5433"
        }
        failure {
            echo "❌ CD Pipeline Failed!"
            echo "Check the logs above for errors"
        }
        always {
            echo "Pipeline completed. Cleaning up workspace..."
            cleanWs()
        }
    }
}
