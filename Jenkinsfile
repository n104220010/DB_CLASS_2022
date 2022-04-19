pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        echo "building ..."
        
        script {
          try{
            sh 'docker stop db_class'
            sh 'docker rm db_class'
          } catch (Exception e) {
          }

          try {
            sh 'docker image rm db_class_2022:1.0'
          } catch (Exception e) {
          }
          
          echo "docker image rm ..."
          def dockerImage = docker.build("db_class_2022:1.0")
        }        
      }
    }
    stage('run') {
      steps {
        echo "run"
        script {
          // docker.image("db_class_2022:1.0").withRun('-p 9010:5000') {}
          sh 'docker run -d --name db_class -p 9010:5000  db_class_2022:1.0'
        }
      }
    }
  }
}
