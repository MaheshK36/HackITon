#!/usr/bin/env bash
# CyberSeer Quick Start Script
# Run this to setup and execute Phase 1 pipeline

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          CyberSeer Phase 1: Data Pipeline Setup               ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Check Python
echo ""
echo "[1] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "[2] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv
echo ""
echo "[3] Activating virtual environment..."
source venv/bin/activate
echo "✓ Activated"

# Install dependencies
echo ""
echo "[4] Installing dependencies from requirements.txt..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create directories
echo ""
echo "[5] Verifying data directories..."
mkdir -p data/{raw/{cicids2018,ctu13},processed,sequences,graphs}
echo "✓ Data directories ready"

# Run pipeline
echo ""
echo "[6] Running Phase 1 pipeline..."
echo "    This will use synthetic data if real data is not found."
echo ""

python3 ml/preprocessing/data_loader.py
echo ""
python3 ml/preprocessing/preprocess_dataset.py
echo ""
python3 ml/preprocessing/build_sequences.py
echo ""
python3 ml/preprocessing/build_graphs.py
echo ""
python3 ml/preprocessing/validate_dataset.py

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Phase 1 Complete ✓                         ║"
echo "║                                                                ║"
echo "║  Check validation_report.json for detailed statistics.        ║"
echo "║  Processed data ready in:                                     ║"
echo "║    - data/processed/features.csv                              ║"
echo "║    - data/sequences/X_sequences.npy                           ║"
echo "║    - data/sequences/y_sequences.npy                           ║"
echo "║    - data/graphs/graphs.json                                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next: Start Phase 2 - Baseline Models"
echo "  python3 ml/models/baseline.py"
