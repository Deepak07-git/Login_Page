# PyPortal

A modern, responsive Flask authentication portal and dashboard.

## Features

- User authentication with secure password hashing via Werkzeug (`generate_password_hash`, `check_password_hash`).
- Session-based authorization for protected dashboard route.
- Modern responsive split-screen UI styled with Plus Jakarta Sans typography.
- Password visibility toggle.

## Getting Started

### 1. Clone the repository
```bash
git clone <repository-url>
cd files
```

### 2. Set up virtual environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

### Demo Credentials
- **Username:** `deepak`
- **Password:** `python123`
