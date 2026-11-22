pipeline {
  agent any

  parameters {
    choice(name: 'APP_DIR', choices: ['app_fixed', 'app_vulnerable'],
           description: 'Carpeta de la app a construir')
    booleanParam(name: 'ENFORCE_GATE', defaultValue: true,
           description: 'Fallar el pipeline si hay hallazgos medios/altos')
    booleanParam(name: 'RUN_ZAP', defaultValue: false,
           description: 'Ejecutar ZAP en modo comando (puede tardar 5-15 min)')
  }

  environment {
    BASE    = 'C:\\ev3'
    PY      = 'C:\\ev3\\.venv\\Scripts\\python.exe'
    ZAP     = 'C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.bat'
    REPORTS = "${WORKSPACE}\\reports"
  }

  stages {

    stage('Build') {
      steps {
        bat '''
          if not exist "%REPORTS%" mkdir "%REPORTS%"
          if not exist "%BASE%\\.venv" python -m venv "%BASE%\\.venv"
          "%PY%" -m pip install --upgrade pip
          "%PY%" -m pip install -r "%BASE%\\%APP_DIR%\\requirements.txt"
        '''
      }
    }

    stage('Test') {
      steps {
        bat '''
          cd /d "%BASE%\\%APP_DIR%"
          "%PY%" -m pytest -q --junitxml="%REPORTS%\\test-results.xml"
        '''
      }
      post { always { junit allowEmptyResults: true, testResults: 'reports/test-results.xml' } }
    }

    stage('SAST - Bandit') {
      steps {
        bat '''
          "%PY%" -m pip install bandit
          cd /d "%BASE%\\%APP_DIR%"
          "%PY%" -m bandit -r app.py -f txt -o "%REPORTS%\\bandit-report.txt"
          type "%REPORTS%\\bandit-report.txt"
        '''
        script {
          def rc = bat(returnStatus: true, script: '@echo off\ncd /d "%BASE%\\%APP_DIR%"\n"%PY%" -m bandit -r app.py -ll -q')
          if (rc != 0) {
            if (params.ENFORCE_GATE) { error('Bandit encontro vulnerabilidades medias/altas: pipeline bloqueado') }
            else { unstable('Bandit encontro vulnerabilidades (gate desactivado)') }
          }
        }
      }
    }

    stage('Dependencias - pip-audit') {
      steps {
        script {
          def rc = bat(returnStatus: true, script: '''
            "%PY%" -m pip install pip-audit
            "%PY%" -m pip_audit -r "%BASE%\\%APP_DIR%\\requirements.txt" > "%REPORTS%\\pip-audit-report.txt" 2>&1
            type "%REPORTS%\\pip-audit-report.txt"
          ''')
          if (rc != 0) {
            if (params.ENFORCE_GATE) { error('pip-audit encontro dependencias vulnerables') }
            else { unstable('pip-audit encontro dependencias vulnerables (gate desactivado)') }
          }
        }
      }
    }

    stage('Deploy') {
      steps {
        withEnv(['JENKINS_NODE_COOKIE=dontKillMe']) {
          bat '''
            powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
            cd /d "%BASE%\\%APP_DIR%"
            set LOG_FILE=%BASE%\\app.log
            start "flask-app" /B "%PY%" -m waitress --listen=127.0.0.1:5000 app:app
            ping -n 6 127.0.0.1 > nul
            curl -s "http://127.0.0.1:5000/hello?name=Ana"
          '''
        }
      }
    }

    stage('DAST - OWASP ZAP') {
      when { expression { params.RUN_ZAP } }
      steps {
        bat '''
          "%ZAP%" -cmd -port 8090 -quickurl "http://127.0.0.1:5000/hello?name=test" -quickout "%REPORTS%\\zap-report.html" -quickprogress
        '''
      }
    }
  }

  post {
    always { archiveArtifacts artifacts: 'reports/*', allowEmptyArchive: true }
  }
}
