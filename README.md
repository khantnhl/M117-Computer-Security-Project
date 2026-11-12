# M117-Computer-Security-Project

# Create virtual environment
python -m venv .venv

# Activate environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Verify installation
python -m pip check
python -m agentdojo.scripts.benchmark --help

