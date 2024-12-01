from flask import Flask
import asyncio
import nest_asyncio
from bot import main as bot_main
from waitress import serve

# Enable nested event loops
nest_asyncio.apply()

app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Bot is running!', 200

async def run_bot():
    """Run the bot in the background"""
    try:
        await bot_main()
    except Exception as e:
        print(f"Bot error: {e}")

def run_server():
    """Run the Flask server with waitress"""
    serve(app, host='0.0.0.0', port=8000)

async def main():
    """Run both the bot and the server"""
    # Start the bot in the background
    bot_task = asyncio.create_task(run_bot())
    
    # Run the server in a separate thread using asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_server)
    
    # Wait for the bot to finish (it shouldn't unless there's an error)
    await bot_task

if __name__ == '__main__':
    # Run everything
    asyncio.run(main())
