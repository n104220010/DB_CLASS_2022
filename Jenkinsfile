pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        echo "building ..."
        
        script {
          try{
          sh 'docker image rm DB_CLASS_2022'
          } catch (Exception e) {
          }
          
          echo "docker image rm ..."
          def dockerImage = docker.build("DB_CLASS_2022/1.0")
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
