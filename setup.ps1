$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================"
Write-Host "                   PIT SENSE SETUP"
Write-Host "============================================================"
Write-Host ""

# ============================================================
# Stage 1: Check Python
# ============================================================

Write-Host "[1/7] Checking Python..."

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
}

if ($null -eq $pythonCmd) {
    Write-Host ""
    Write-Host "ERROR: Python was not found in PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10+ from https://python.org and check 'Add to PATH'."
    exit 1
}

$pythonVersion = & $pythonCmd --version 2>&1
Write-Host "OK  $pythonVersion" -ForegroundColor Green

# ============================================================
# Stage 2: Create / verify root .venv
# ============================================================

Write-Host ""
Write-Host "[2/7] Setting up virtual environment at .venv ..."

if (!(Test-Path ".venv")) {
    & $pythonCmd -m venv .venv
    Write-Host "OK  Virtual environment created at .venv" -ForegroundColor Green
} else {
    Write-Host "OK  .venv already exists, skipping creation." -ForegroundColor Yellow
}

$venvPython = ".venv\Scripts\python.exe"

if (!(Test-Path $venvPython)) {
    Write-Host ""
    Write-Host "ERROR: $venvPython not found. The virtual environment may be corrupt." -ForegroundColor Red
    Write-Host "Delete .venv and run setup.ps1 again."
    exit 1
}

Write-Host "OK  Using $venvPython" -ForegroundColor Green

# ============================================================
# Stage 3: Upgrade pip
# ============================================================

Write-Host ""
Write-Host "[3/7] Upgrading pip..."
& $venvPython -m pip install --upgrade pip --quiet
Write-Host "OK  pip upgraded." -ForegroundColor Green

# ============================================================
# Stage 4: Install CPU-only PyTorch
# ============================================================

Write-Host ""
Write-Host "[4/7] Installing CPU-compatible PyTorch..."
& $venvPython -m pip install torch --index-url https://download.pytorch.org/whl/cpu
Write-Host "OK  PyTorch installed (CPU build)." -ForegroundColor Green

# ============================================================
# Stage 5: Install backend dependencies
# ============================================================

Write-Host ""
Write-Host "[5/7] Installing backend dependencies from backend\requirements.txt ..."

if (!(Test-Path "backend\requirements.txt")) {
    Write-Host "ERROR: backend\requirements.txt not found." -ForegroundColor Red
    exit 1
}

& $venvPython -m pip install -r backend\requirements.txt
Write-Host "OK  Backend dependencies installed." -ForegroundColor Green

# ============================================================
# Stage 6: Download Hugging Face models locally
#
# setup_models.py at repo root delegates to backend/setup_models.py.
# Models are saved into backend\models\:
#   backend\models\parakeet         (nvidia/parakeet-tdt-0.6b-v3)
#   backend\models\audio_emotion    (ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition)
#   backend\models\text_emotion     (j-hartmann/emotion-english-distilroberta-base)
#
# No Hugging Face API token is required.
# Models run locally on CPU after download.
# Re-running this stage is safe; already-downloaded models are reused.
# ============================================================

Write-Host ""
Write-Host "[6/7] Downloading Hugging Face models into backend\models\ ..."

if (!(Test-Path "setup_models.py")) {
    Write-Host "ERROR: setup_models.py not found in repository root." -ForegroundColor Red
    exit 1
}

& $venvPython setup_models.py
Write-Host "OK  Models downloaded." -ForegroundColor Green

# ============================================================
# Stage 7: Configure backend\.env
#
# The application reads GEMINI_API_KEY via:
#   1. os.getenv("GEMINI_API_KEY")  (environment variable)
#   2. backend/.env                  (read directly by llm_summary._get_api_key)
#   3. repo-root .env               (fallback in _get_api_key)
#
# We create backend\.env from backend\.env.example so the app
# finds it at location 2. An existing file is never overwritten.
# ============================================================

Write-Host ""
Write-Host "[7/7] Configuring backend\.env ..."

if (Test-Path "backend\.env") {
    Write-Host "OK  backend\.env already exists, leaving it unchanged." -ForegroundColor Yellow
} else {
    if (Test-Path "backend\.env.example") {
        Copy-Item "backend\.env.example" "backend\.env"
        Write-Host "OK  Created backend\.env from backend\.env.example" -ForegroundColor Green
    } elseif (Test-Path ".env.example") {
        Copy-Item ".env.example" "backend\.env"
        Write-Host "OK  Created backend\.env from .env.example" -ForegroundColor Green
    } else {
        Set-Content "backend\.env" "GEMINI_API_KEY=`nGEMINI_MODEL=gemini-3.6-flash"
        Write-Host "OK  Created default backend\.env" -ForegroundColor Green
    }
}

# ============================================================
# Done
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "              PIT SENSE SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Setup is idempotent. Running it again is safe." -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Configure Gemini (optional):"
Write-Host "       Open backend\.env and set:"
Write-Host "       GEMINI_API_KEY=your_gemini_api_key_here"
Write-Host "       If left blank, PitSense uses local rule-based fallback mode."
Write-Host ""
Write-Host "  2. Start the backend API server:"
Write-Host "       cd backend"
Write-Host "       ..\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000"
Write-Host "       Backend runs at http://localhost:8000"
Write-Host ""
Write-Host "  3. Start the frontend (open a separate terminal):"
Write-Host "       cd frontend"
Write-Host "       npm install"
Write-Host "       npm run dev"
Write-Host "       Dashboard runs at http://localhost:5173"
Write-Host ""