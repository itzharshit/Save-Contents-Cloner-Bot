import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import asyncio
import logging
# import subprocess # Not used in the provided snippet
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from database import db
from config import Telegram
from boot import start_client # Assuming this is defined elsewhere

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# --- Health Check Server ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/kaithheathcheck":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Save-Contents bot is up :)".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_health_check_server(port):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logging.info(f"[Health Check] Server starting on port {port}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"[Health Check] Failed to start server on port {port}: {e}")

health_port = int(os.getenv("PORT", 8080)) # Use PORT environment variable
# Start the health check server in a separate thread BEFORE starting the bot
health_thread = threading.Thread(target=run_health_check_server, args=(health_port,), daemon=True)
health_thread.start()
# Give the server a moment to start (optional, but might help)
import time
time.sleep(1)
# --------------------------

bot = Client(
    in_memory=True,
    name="SaveContentBot",
    api_id=Telegram.API_ID,
    api_hash=Telegram.API_HASH,
    bot_token=Telegram.BOT_TOKEN,
)

# --- Bot Handlers ---
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    logging.info(f"User {user_id} started the bot.")
    await message.reply(
        "Hi, I can create a contents-saver bot for public channels for free.\n"
        "Just send/forward your Bot Token to me, and I will handle the rest.\n\n"
        "You can get your bot token from @BotFather."
    )
    if not await db.is_inserted("users", user_id):
        await db.insert("users", user_id)

@bot.on_message(filters.private & filters.command("stats") & filters.user(Telegram.AUTH_USER_ID))
async def stats_handler(client: Client, message: Message):
    user_count = len(await db.fetch_all("users"))
    total_user_count = len(await db.fetch_all("total_users"))
    bot_list = await db.fetch_all("bots")
    bot_count = len(bot_list)
    bot_users = "\n".join(bot_list) if bot_list else "No bots registered."
    logging.info(f"Admin requested stats: {user_count} users, {bot_count} bots.")
    await message.reply(
        f"👥 **User Count:** {user_count}\n"
        f"👥 **Total User Count:** {total_user_count}\n"
        f"🤖 **Bot Count:** {bot_count}\n\n"
        f"**Registered Bots:**\n{bot_users}"
    )

@bot.on_message(filters.private)
async def bot_clone_handler(client: Client, message: Message):
    user_id = message.from_user.id
    msg = await message.reply("⏳ Processing...")

    match = re.search(r"\b([0-9]+:[\w-]+)", message.text)
    if not match:
        await msg.edit("❌ No valid Bot Token found. Get it from @BotFather.")
        return

    bot_token = match.group(1)
    if await db.is_inserted("tokens", bot_token):
        await msg.edit("⚠️ This bot is already running.")
        return

    client_name = re.sub(r'[^a-zA-Z0-9]', '', bot_token)
    try:
        await msg.edit("🚀 Starting your bot...")
        new_bot = Client(
            in_memory=True,
            name=client_name,
            api_id=Telegram.API_ID,
            api_hash=Telegram.API_HASH,
            bot_token=bot_token,
            plugins={"root": "plugins"}, # Ensure this path is correct
        )

        await new_bot.start()
        await new_bot.set_bot_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("users", "Total Users on this bot"),
            BotCommand("source", "Source code of this bot"),
        ])

        bot_info = await new_bot.get_me()
        await db.insert("bots", f"@{bot_info.username}")
        await db.insert("tokens", bot_token)
        logging.info(f"New bot created: @{bot_info.username} by user {user_id}.")

        # Fix the URL space issue
        await msg.edit(
            f"✅ Successfully started @{bot_info.username}.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Start Bot", url=f"https://t.me/{bot_info.username}")]] # Removed space
            ),
        )
        # Consider if start_client needs to be awaited or run differently
        # asyncio.create_task(start_client(bot_token))
        # Or if it's synchronous:
        # start_client(bot_token)

    except Exception as e:
        logging.error(f"Error in bot creation by {user_id}: {e}", exc_info=True) # Added exc_info for better logs
        await msg.edit("❌ An error occurred. Check your token and try again.")
        # print(e) # Logging already handles this

@bot.on_message(filters.private & filters.command("logs") & filters.user(Telegram.AUTH_USER_ID))
async def send_logs(client: Client, message: Message):
    if os.path.exists("logs.txt"): # Ensure logs are written to this file
        await message.reply_document("logs.txt")
    else:
        await message.reply("No logs available.")

# --- Main Execution ---
async def main():
    # Start the Pyrogram bot
    await bot.start()
    bot_info = await bot.get_me()
    print(
        f"✅ Bot @{bot_info.username} is running!\n"
        f"Follow me on GitHub → https://github.com/Harshit-shrivastav \n\n"
        "██████╗ ██╗   ██╗██████╗  ██████╗  ██████╗  █████╗ ███╗   ███╗███╗   ███╗███████╗██████╗ ███████╗\n"
        "██╔══██╗██║   ██║██╔══██╗██╔════╝ ██╔════╝ ██╔══██╗████╗ ████║████╗ ████║██╔════╝██╔══██╗██╔════╝\n"
        "██████╔╝██║   ██║██████╔╝██║  ███╗██║  ███╗███████║██╔████╔██║██╔████╔██║█████╗  ██████╔╝███████╗\n"
        "██╔═══╝ ██║   ██║██╔═══╝ ██║   ██║██║   ██║██╔══██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██╔═══╝ ╚════██║\n"
        "██║     ╚██████╔╝██║     ╚██████╔╝╚██████╔╝██║  ██║██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗██║     ███████║\n"
        "╚═╝      ╚═════╝ ╚═╝      ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚═╝     ╚══════╝\n"
    )
    # Keep the main loop running
    await asyncio.Future()  # run forever

# Run the main function within the asyncio event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Shutting down...")
    finally:
        # Ensure proper cleanup if needed (e.g., stopping the bot gracefully)
        # This part might need adjustment based on how Pyrogram handles shutdown
        pass
