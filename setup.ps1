$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================"
Write-Host "                 PIT SENSE SETUP"
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# Check Python
# ------------------------------------------------------------

Write-Host "[1/7] Checking Python..."

try {
    $pythonVersion = python --version
    Write-Host "Found: $pythonVersion"
}
catch {
    Write-Host ""
    Write-Host "ERROR: Python is not installed or not available in PATH."
    Write-Host "Install Python and run this script again."
    exit 1
}

# ------------------------------------------------------------
# Create virtual environment
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/7] Creating virtual environment..."

if (!(Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "Virtual environment created."
}
else {
    Write-Host "Virtual environment already exists."
}

# ------------------------------------------------------------
# Activate virtual environment
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/7] Activating virtual environment..."

$activateScript = ".\.venv\Scripts\Activate.ps1"

if (!(Test-Path $activateScript)) {
    Write-Host "ERROR: Could not find virtual environment activation script."
    exit 1
}

& $activateScript

# ------------------------------------------------------------
# Upgrade pip
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/7] Updating pip..."

python -m pip install --upgrade pip

# ------------------------------------------------------------
# Install CPU-only PyTorch
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/7] Installing CPU-only PyTorch..."

python -m pip install torch --index-url https://download.pytorch.org/whl/cpu

# ------------------------------------------------------------
# Install project dependencies
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/7] Installing PitSense dependencies..."

python -m pip install -r requirements.txt

# ------------------------------------------------------------
# Download models
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/7] Downloading Hugging Face models..."

python setup_models.py

# ------------------------------------------------------------
# Finish
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host "             PIT SENSE SETUP COMPLETE"
Write-Host "============================================================"
Write-Host ""

Write-Host "Next steps:"
Write-Host ""
Write-Host "1. Create a .env file from .env.example"
Write-Host "2. Add your own Gemini API key"
Write-Host "3. Add your Hugging Face token if required"
Write-Host "4. Start the PitSense backend"
Write-Host "5. Start the frontend"
Write-Host ""

Write-Host "To activate the environment later:"
Write-Host ""
Write-Host "    .\.venv\Scripts\activate"
Write-Host ""

Write-Host "Setup finished successfully."