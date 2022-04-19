pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        echo "building ..."
      }
    }
    stage('run') {
      steps {
        echo "testing ${BRANCH_NAME} ${JOB_BASE_NAME} ${NODE_NAME} ${WORKSPACE} ${BUILD_URL} ${GIT_COMMIT}"
      }
    }
  }
}
