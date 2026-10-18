"""
start.py — Starts Qenagebeya with Daphne (ASGI) for real WebSocket support.

Usage:
    python start.py
    
This replaces 'python manage.py runserver' when you need live chat.
The site runs on http://127.0.0.1:8000/ exactly as before.
"""
import os
import sys
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')

def main():
    print("=" * 55)
    print("  🇪🇹 Qenagebeya — Starting ASGI Server (Daphne)")
    print("=" * 55)
    print()
    print("  Store:      http://127.0.0.1:8000/")
    print("  Live:       http://127.0.0.1:8000/live/")
    print("  Admin:      http://127.0.0.1:8000/portal/")
    print("  Vendor:     http://127.0.0.1:8000/vendor/dashboard/")
    print("  Makerspace: http://127.0.0.1:8000/makerspace/")
    print()
    print("  WebSocket:  ws://127.0.0.1:8000/ws/live/<uuid>/")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 55)
    print()

    cmd = [
        sys.executable, '-m', 'daphne',
        '-b', '127.0.0.1',
        '-p', '8000',
        '--verbosity', '1',
        'qenagebeya.asgi:application',
    ]

    try:
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except FileNotFoundError:
        print("ERROR: daphne not found.")
        print("Install with:  pip install daphne")
        print()
        print("Falling back to runserver (WebSockets may not work)...")
        os.system(f'{sys.executable} manage.py runserver')

if __name__ == '__main__':
    main()
