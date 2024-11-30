from flask import Flask
import threading
from bot import main

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot ishlayapti!'

def run_bot():
    main()

# Bot threadini ishga tushirish
bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

if __name__ == '__main__':
    app.run()
