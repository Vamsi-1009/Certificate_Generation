#!/bin/bash
echo "🚀 Starting KIET Certificate Generation System..."

# 1. Activate Environment
source venv/Scripts/activate

# 2. Set Python Path
export PYTHONPATH=$PYTHONPATH:.

# 3. Clean and Verify
echo "Cleaning old outputs and verifying folders..."
python verify_setup.py

# 4. Generate Core Assets
echo "Generating Certificates and Verification Pages..."
python certificate_generator.py

# 5. Generate Frontend Dashboard
echo "Building Gallery View..."
python -m utils.frontend_utils

# 6. Package for Distribution
echo "Creating final ZIP package..."
python -m utils.dist_utils

echo "✨ All tasks complete! Open dashboard.html to see the results."
