# Setup Guide - MiniML Lab

Complete step-by-step guide to get MiniML Lab up and running.

## System Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB for dependencies

## Installation Steps

### Step 1: Get OpenRouter API Key

1. Visit https://openrouter.ai
2. Sign up for free account
3. Go to API Keys section
4. Create new API key
5. Copy and save the key

### Step 2: Clone/Download Project

```bash
# Option A: Clone from Git (if available)
git clone https://github.com/username/MiniML-Lab.git
cd MiniML-Lab

# Option B: Download files manually
# Download all Python files into a directory
# mkdir MiniML-Lab && cd MiniML-Lab
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed aiohttp-3.9.1 numpy-1.24.3 pandas-2.1.3 ...
```

### Step 5: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env file with your editor
# Windows: notepad .env
# macOS/Linux: nano .env
```

Add your API key:
```env
OPENROUTER_API_KEY=sk-or-xxxxx...
```

### Step 6: Run Application

```bash
streamlit run app.py
```

Application will open automatically at `http://localhost:8501`

## Verification Checklist

- [ ] Python version >= 3.8: `python --version`
- [ ] Virtual environment activated: `(venv)` in terminal
- [ ] All dependencies installed: `pip list | grep streamlit`
- [ ] .env file configured with API key
- [ ] Port 8501 is available
- [ ] No firewall blocking localhost

## Troubleshooting Installation

### Python Not Found
```bash
# Ensure Python is in PATH
python --version

# If not found, reinstall Python from python.org
# Make sure to check "Add Python to PATH"
```

### Virtual Environment Issues
```bash
# Delete and recreate venv
rm -r venv  # Linux/macOS
rmdir /s venv  # Windows

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
```

### Dependency Conflicts
```bash
# Update pip first
pip install --upgrade pip

# Clear cache and reinstall
pip install --no-cache-dir -r requirements.txt
```

### Port Already in Use
```bash
# Use different port
streamlit run app.py --server.port 8502

# Or find and kill process using port 8501
# macOS/Linux:
lsof -i :8501
kill -9 <PID>

# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

## Docker Setup (Optional)

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.headless", "true"]
```

### Build and Run

```bash
# Build image
docker build -t miniml-lab .

# Run container
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=your_key \
  miniml-lab
```

## First-Time Usage

### Initial Setup (5 minutes)

1. **Launch App**
   - Run `streamlit run app.py`
   - Open browser to http://localhost:8501

2. **Enter API Key**
   - Paste OpenRouter API key in sidebar
   - Click "API Settings" to expand

3. **Generate Test Data**
   - Select "Synthetic Data" in Data Settings
   - Choose "classification" task
   - Click "Generate Synthetic Data"

4. **Initialize Agent**
   - Click "Initialize Agent" button
   - Wait for confirmation

5. **Run Experiment**
   - Go to Experimentation tab
   - Click "Run Single Iteration"
   - Monitor progress

6. **View Results**
   - Check Results tab for metrics
   - Download model in Model Artifacts tab

## Development Setup

For contributing or extending:

```bash
# Install additional dev dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black *.py

# Type checking
mypy *.py
```

## File Structure After Setup

```
MiniML-Lab/
├── venv/                    # Virtual environment (auto-created)
├── app.py                   # Main application
├── llm_agent.py            # Agent implementation
├── data_pipeline.py        # Data processing
├── model_manager.py        # Model management
├── requirements.txt        # Dependencies
├── .env                    # Configuration (KEEP SECRET!)
├── .env.example            # Config template
└── README.md               # Documentation
```

## Running on Different Machines

### Windows
```batch
cd path\to\MiniML-Lab
venv\Scripts\activate
streamlit run app.py
```

### macOS
```bash
cd path/to/MiniML-Lab
source venv/bin/activate
streamlit run app.py
```

### Linux (Ubuntu/Debian)
```bash
cd path/to/MiniML-Lab
source venv/bin/activate
streamlit run app.py
```

## Headless Mode (Server)

For running on remote server without GUI:

```bash
streamlit run app.py \
  --server.headless true \
  --server.port 8501 \
  --logger.level=warning
```

Then access at: `http://server-ip:8501`

## Performance Optimization

### For Slower Machines

1. **Reduce data size**
   - Lower n_samples in Data Settings
   - Use fewer features

2. **Use faster model**
   - Switch to faster LLM (Llama 2 instead of GPT-4)
   - Reduce max_tokens in config

3. **Adjust timeouts**
   - Increase MAX_EXECUTION_TIME in .env
   - Lower MAX_RETRIES

### For Better Performance

1. **Use GPU** (optional)
   - Install PyTorch with CUDA support
   - Models will use GPU automatically

2. **Increase resources**
   - Add more RAM
   - Use SSD for faster I/O

## Health Check

Verify installation with simple test:

```python
# test_install.py
import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np

print("✅ Streamlit:", st.__version__)
print("✅ Pandas:", pd.__version__)
print("✅ Scikit-learn available")
print("✅ All dependencies working!")
```

Run it:
```bash
python test_install.py
```

## Next Steps

1. **Read README.md** for feature overview
2. **Try example workflows** in documentation
3. **Configure your API key** properly
4. **Start with synthetic data** for testing
5. **Experiment with your data** once comfortable

## Getting Help

- Check troubleshooting in README.md
- Review error messages in console
- Check OpenRouter status: https://status.openrouter.ai
- Verify internet connection for API calls

## Security Notes

- ⚠️ Never commit .env file to Git
- ⚠️ Keep API key secret
- ⚠️ Use limited API scope if possible
- ⚠️ Monitor API usage and costs

## Uninstallation

To remove completely:

```bash
# Deactivate environment
deactivate

# Remove venv
rm -r venv  # or rmdir /s venv on Windows

# Delete project folder
rm -r MiniML-Lab
```

---

**Installation Complete!** 🎉

You're ready to start experimenting with autonomous ML models.

Questions? Check the README.md or troubleshooting section above.