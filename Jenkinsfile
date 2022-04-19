pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        echo "building ..."
        sh 'docker image rm DB_CLASS_2022'
        echo "docker image rm ..."
        script {
          def dockerImage = docker.build("DB_CLASS_2022")
        }        
      }
    }
    stage('run') {
      steps {
        echo "run"
        script {
          dockerImage.withRun('-p 9010:5000')
        }
      }
    }
  }
}
