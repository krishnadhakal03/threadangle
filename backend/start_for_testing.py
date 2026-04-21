"""
Start both backend and frontend for comprehensive manual testing
This script will:
1. Check if all dependencies are installed
2. Start backend server on port 8000
3. Start frontend dev server on port 5173
4. Open browser to http://localhost:5173
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def print_header(message):
    print("\n" + "="*70)
    print(f"🚀 {message}")
    print("="*70 + "\n")

def check_backend_dependencies():
    print_header("Checking Backend Dependencies")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'anthropic',
        'stripe',
        'youtube-transcript-api',
        'python-multipart'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Installing missing packages...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--break-system-packages",
            *missing
        ])
    else:
        print("\n✅ All backend dependencies installed")

def check_frontend_dependencies():
    print_header("Checking Frontend Dependencies")
    
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    node_modules = os.path.join(frontend_dir, 'node_modules')
    
    if not os.path.exists(node_modules):
        print("❌ node_modules not found")
        print("Installing frontend dependencies...")
        
        subprocess.run(['npm', 'install'], cwd=frontend_dir, shell=True)
    else:
        print("✅ Frontend dependencies installed")

def start_backend():
    print_header("Starting Backend Server on Port 8000")
    
    backend_dir = os.path.dirname(__file__)
    
    # Start uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--reload", 
        "--port", "8000",
        "--host", "0.0.0.0"
    ], cwd=backend_dir)

def start_frontend():
    print_header("Starting Frontend Dev Server on Port 5173")
    
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    
    # Start npm dev server
    subprocess.run(['npm', 'run', 'dev'], cwd=frontend_dir, shell=True)

def open_browser():
    time.sleep(3)  # Wait for servers to start
    print_header("Opening Browser")
    webbrowser.open('http://localhost:5173')

if __name__ == "__main__":
    print("\n╔" + "═"*68 + "╗")
    print("║" + " "*15 + "THREADANGLE LOCAL TESTING ENVIRONMENT" + " "*15 + "║")
    print("╚" + "═"*68 + "╝")
    
    # Check dependencies
    check_backend_dependencies()
    check_frontend_dependencies()
    
    print_header("Starting Servers")
    print("Backend will run on: http://localhost:8000")
    print("Frontend will run on: http://localhost:5173")
    print("\nPress Ctrl+C to stop both servers\n")
    
    # Start backend in thread
    backend_thread = Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a bit for backend to start
    time.sleep(2)
    
    # Start frontend in thread
    frontend_thread = Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    # Open browser
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n✅ Shutting down servers...")
        print("Testing session complete!")
