from flask import Flask
import threading
from bot import main as bot_main

app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Bot is running!', 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

def run_bot():
    bot_main()

if __name__ == '__main__':
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Run Flask server in main thread
    run_flask()
