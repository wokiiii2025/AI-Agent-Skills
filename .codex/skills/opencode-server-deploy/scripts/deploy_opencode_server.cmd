@echo off
setlocal

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%~dp0deploy_opencode_server.py" %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%~dp0deploy_opencode_server.py" %*
  exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL%==0 (
  python3 "%~dp0deploy_opencode_server.py" %*
  exit /b %ERRORLEVEL%
)

echo Python 3 was not found. Install Python 3, then retry.
exit /b 1
