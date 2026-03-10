pipeline {
    agent any
    stages {
        stage('Checkout')         { steps { checkout scm } }
        stage('Build Environment') { steps { sh 'pip install -r requirements.txt' } }
        stage('Lint')             { steps { sh 'flake8 app.py --max-line-length=120 --ignore=E501' } }
        stage('Unit Tests') {
            steps {
                sh 'pytest test_app.py -v --cov=app --cov-report=term-missing --cov-fail-under=80'
            }
            // Quality Gate: build FAILS automatically if coverage drops below 80%
        }
        stage('Docker Build')     { steps { sh 'docker build -t aceest-fitness:latest .' } }
    }
    post {
        success { echo 'BUILD SUCCESSFUL — all stages passed, coverage ≥ 80%' }
        failure { echo 'BUILD FAILED — check lint errors, test failures, or coverage below 80%' }
    }
}