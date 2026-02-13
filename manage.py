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
    from pyngrok import ngrok

    ngrok_token = os.getenv('NGROK_TOKEN') or os.getenv('NGROK_AUTHTOKEN')
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)

    if ':' in str(port):
        port = int(str(port).split(':')[-1])
    else:
        port = int(port)

    tunnel = ngrok.connect(port)
    public_url = tunnel.public_url

    print(f"\n🌐 Ngrok tunnel active: {public_url}\n")

    return public_url


if __name__ == '__main__':
    # Check if --ngrok option is present
    if '--ngrok' in sys.argv:
        sys.argv.remove('--ngrok')
        
        # Find runserver command and extract port
        if 'runserver' in sys.argv:
            runserver_index = sys.argv.index('runserver')
            port = sys.argv[runserver_index + 1] if len(sys.argv) > runserver_index + 1 else '8000'
            
            
            # Start ngrok tunnel in a separate thread
            public_url = start_ngrok_tunnel(port)

            os.environ["NGROK_PUBLIC_URL"] = public_url
            
            # Give ngrok a moment to start
            time.sleep(1)
    
    main()
