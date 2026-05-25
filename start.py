"""
Railway launcher — starts token_server.py then agent.py in the same container.
token_server.py claims Railway's PORT (HTTP traffic).
agent.py runs with PORT=8081 (internal LiveKit HTTP server).
"""
import subprocess
import os
import sys
import time
import logging
 
logging.basicConfig(level=logging.INFO, format='[launcher] %(message)s')
 
def main():
    env = os.environ.copy()
    railway_port = env.get('PORT', '8080')
    logging.info(f"Railway PORT={railway_port} → token_server.py")
 
    # Start token server on Railway's PORT
    token_proc = subprocess.Popen(
        [sys.executable, 'token_server.py'],
        env=env
    )
 
    # Give Flask a moment to bind
    time.sleep(2)
 
    if token_proc.poll() is not None:
        logging.error("token_server.py exited early — check for import errors")
        sys.exit(1)
 
    logging.info("token_server running, starting agent on PORT=8081")
 
    # Start LiveKit agent with a different PORT so it doesn't conflict
    agent_env = env.copy()
    agent_env['PORT'] = '8081'
 
    agent_proc = subprocess.Popen(
        [sys.executable, 'agent.py', 'start'],
        env=agent_env
    )
 
    # Wait — if either process dies, exit so Railway restarts
    while True:
        time.sleep(5)
        if token_proc.poll() is not None:
            logging.error("token_server.py died — restarting container")
            agent_proc.terminate()
            sys.exit(1)
        if agent_proc.poll() is not None:
            logging.error("agent.py died — restarting container")
            token_proc.terminate()
            sys.exit(1)
 
if __name__ == '__main__':
    main()
