# Running in GitHub Codespaces

This repository is configured to run in GitHub Codespaces with zero setup required.

## Quick Start with Codespaces

1. **Open in Codespaces:**
   - Go to https://github.com/manjumh021/flow_manager
   - Click the green **Code** button
   - Select **Codespaces** tab
   - Click **Create codespace on main**

2. **Wait for Setup:**
   - The dev container will automatically build
   - Python 3.9 will be installed
   - Dependencies from `requirements.txt` will be installed automatically
   - PORT 5000 will be automatically forwarded

3. **Run the Application:**
   ```bash
   python3 app.py
   ```

4. **Access the API:**
   - Codespaces will show a notification about port 5000
   - Click "Open in Browser" to access the API
   - Or use the PORTS tab to get the forwarded URL

5. **Test the Flow:**
   ```bash
   # In a new terminal
   curl -X POST http://localhost:5000/flow/execute \
     -H "Content-Type: application/json" \
     -d @sample_flow.json
   ```

## What's Included

The dev container configuration (`.devcontainer/devcontainer.json`) provides:
- Python 3.9 runtime
- Automatic dependency installation
- Port forwarding for Flask (5000)
- VS Code Python extensions
- Pre-configured Python settings

## Manual Setup (if not using Codespaces)

If you want to run locally without Codespaces:

```bash
# Clone the repo
git clone https://github.com/manjumh021/flow_manager.git
cd flow_manager

# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 app.py
```

## Using Dev Containers Locally

If you have Docker and VS Code with the Dev Containers extension:

1. Open the folder in VS Code
2. Click "Reopen in Container" when prompted
3. Wait for the container to build
4. Run `python3 app.py`
