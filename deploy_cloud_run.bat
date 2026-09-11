@echo off
REM ==============================================================================
REM LifeBridge AI — Google Cloud Run Automated Deployment (Windows)
REM ==============================================================================

set SERVICE_NAME=lifebridge-ai
if "%REGION%"=="" set REGION=us-central1

echo ============================================================
echo  LifeBridge AI - Google Cloud Run Deployment
echo ============================================================

where gcloud >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: 'gcloud' CLI is not found on PATH.
    echo Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i
if "%PROJECT_ID%"=="" (
    echo ERROR: No active GCP project configured.
    echo Run: gcloud config set project YOUR_PROJECT_ID
    exit /b 1
)

echo Active Project: %PROJECT_ID%
echo Target Region:  %REGION%
echo Service Name:   %SERVICE_NAME%
echo.

echo Step 1: Enabling Cloud APIs...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com --project=%PROJECT_ID%

echo Step 2: Deploying to Cloud Run...
call gcloud run deploy %SERVICE_NAME% ^
    --source=. ^
    --platform=managed ^
    --region=%REGION% ^
    --allow-unauthenticated ^
    --set-env-vars="GEMINI_MODEL=gemini-2.5-flash" ^
    --min-instances=0 ^
    --max-instances=10 ^
    --memory=512Mi ^
    --cpu=1 ^
    --timeout=60s ^
    --project=%PROJECT_ID%

echo.
echo ============================================================
echo  Deployment Finished!
echo ============================================================
