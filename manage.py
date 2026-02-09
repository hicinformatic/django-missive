#!/usr/bin/env python
"""Django's command-line utility for administrative tasks using qualitybase."""
import os

import sys
import threading
import time

# Import and use qualitybase's django manage.py functions
from qualitybase.services.django.manage import main

# Override DJANGO_SETTINGS_MODULE for this project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')


def start_ngrok_tunnel(port: int = 8000):
    """Start ngrok tunnel for the Django development server."""
    try:
        from pyngrok import ngrok
        
        # Configure ngrok auth token if available
        ngrok_token = os.getenv('NGROK_TOKEN') or os.getenv('NGROK_AUTHTOKEN')
        if ngrok_token:
            ngrok.set_auth_token(ngrok_token)
        else:
            print("⚠️  NGROK_TOKEN not set. Using ngrok without authentication (limited features).")
        
        # Get the port from the URL if it's in the format "host:port"
        if ':' in str(port):
            port = int(str(port).split(':')[-1])
        else:
            port = int(port)
        
        # Start ngrok tunnel
        public_url = ngrok.connect(port)
        print(f"\n🌐 Ngrok tunnel active: {public_url}\n")
        return public_url
    except ImportError:
        print("⚠️  pyngrok not installed. Install it with: pip install pyngrok")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting ngrok tunnel: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Check if --ngrok option is present
    if '--ngrok' in sys.argv:
        sys.argv.remove('--ngrok')
        
        # Find runserver command and extract port
        if 'runserver' in sys.argv:
            runserver_index = sys.argv.index('runserver')
            port = sys.argv[runserver_index + 1] if len(sys.argv) > runserver_index + 1 else '8000'
            
            # Start ngrok tunnel in a separate thread
            tunnel_thread = threading.Thread(target=start_ngrok_tunnel, args=(port,), daemon=True)
            tunnel_thread.start()
            
            # Give ngrok a moment to start
            time.sleep(1)
    
    main()
