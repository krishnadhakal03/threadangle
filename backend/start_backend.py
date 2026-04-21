"""
Backend server startup script
Run this to start the Threadangle backend API
"""
import subprocess
import sys
import os

def install_dependencies():
    """Install all required packages"""
    packages = [
        'fastapi',
        'uvicorn[standard]',
        'sqlalchemy',
        'aiosqlite',
        'python-dotenv',
        'anthropic',
        'httpx',
        'beautifulsoup4',
        'python-jose[cryptography]',
        'passlib[bcrypt]',
        'python-multipart',
        'stripe',
        'slowapi',
        'aiosmtplib',
        'email-validator',
        'pydantic[email]',
        'youtube-transcript-api',
    ]
    
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet'] + packages)
        print("✅ All dependencies installed!\n")
    except subprocess.CalledProcessError:
        print("⚠️  Some packages may have failed to install, trying to continue...\n")

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Threadangle backend server...")
    print("📍 Server will run on: http://127.0.0.1:8000")
    print("📚 API docs available at: http://127.0.0.1:8000/docs")
    print("\nPress CTRL+C to stop the server\n")
    print("="*60)
    
    try:
        subprocess.call([
            sys.executable, '-m', 'uvicorn',
            'main:app',
            '--reload',
            '--host', '127.0.0.1',
            '--port', '8000'
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")

if __name__ == '__main__':
    # Change to backend directory if not already there
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if dependencies need to be installed
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencies already installed\n")
    except ImportError:
        install_dependencies()
    
    # Start the server
    start_server()
