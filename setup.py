import os
import venv
import subprocess

# Define virtual environment directory
venv_dir = "venv"

# Create virtual environment if it doesn't exist
if not os.path.exists(venv_dir):
    venv.create(venv_dir, with_pip=True)
    print("✅ Virtual environment created!")

# Install dependencies
subprocess.call([os.path.join(venv_dir, "bin", "python"), "-m", "pip", "install", "-r", "requirements.txt"])

print("✅ Dependencies installed!")

# Run Streamlit app with correct filename
print("🚀 Launching FortiGate Policy Visualizer...")
subprocess.call([os.path.join(venv_dir, "bin", "streamlit"), "run", "app.py"])
