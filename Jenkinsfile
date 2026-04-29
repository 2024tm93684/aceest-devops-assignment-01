pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "hisajwan/aceest-fitness"
        DOCKER_TAG   = "v3.2.4"
        SONAR_HOST   = "http://host.docker.internal:9000"
    }

    triggers {
        pollSCM('H/5 * * * *')   // auto-trigger: checks GitHub every 5 minutes
    }

    stages {

        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Build Environment') {
            steps {
                sh 'python3 -m pip install -r requirements.txt --break-system-packages'
            }
        }

        stage('Lint') {
            steps {
                sh 'python3 -m flake8 app.py --max-line-length=120 --ignore=E501'
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''python3 -m pytest test_app.py -v \
                    --cov=app \
                    --cov-report=term-missing \
                    --cov-report=xml:coverage.xml \
                    --cov-fail-under=80'''
            }
            post {
                always {
                    // Archive test coverage XML as build artifact
                    archiveArtifacts artifacts: 'coverage.xml', fingerprint: true
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh """
                        docker run --rm \\
                            -e SONAR_HOST_URL=${SONAR_HOST} \\
                            -e SONAR_TOKEN=${SONAR_TOKEN} \\
                            -e SONAR_SCANNER_OPTS="-Dsonar.projectKey=aceest-fitness -Dsonar.projectName=ACEest Fitness -Dsonar.sources=. -Dsonar.inclusions=app.py -Dsonar.python.version=3 -Dsonar.python.coverage.reportPaths=coverage.xml" \\
                            -v \${WORKSPACE}:/usr/src \\
                            sonarsource/sonar-scanner-cli
                    """
                }
            }
        }

        stage('Docker Build & Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                        echo ${DOCKER_IMAGE}:${DOCKER_TAG} > build-artifact.txt
                    """
                }
            }
            post {
                always {
                    // Archive Docker image tag as build artifact for this version
                    archiveArtifacts artifacts: 'build-artifact.txt', fingerprint: true
                }
            }
        }

        stage('Test Inside Container') {
            // Assignment requirement: "Execute Pytest-based automated tests inside the containerised environment"
            steps {
                sh """
                    docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} \
                        python3 -m pytest test_app.py -v \
                        --cov=app --cov-report=term-missing --cov-fail-under=80
                """
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh """
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/aceest-fitness --timeout=120s
                """
            }
        }

    }

    post {
        success { echo 'BUILD SUCCESSFUL — deployed to Minikube' }
        failure { echo 'BUILD FAILED — check lint errors, test failures, or coverage below 80%' }
    }
}