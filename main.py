import discord
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ["TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    delete_old_messages.start()

@tasks.loop(hours=168)  # Run weekly
async def delete_old_messages():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found.")
        return

    print("Starting to delete old messages...")
    limit_time = datetime.now().astimezone().replace(tzinfo=None) - timedelta(days=60)
    total_deleted = 0
    error_count = 0

    while True:
        deleted_in_batch = 0
        try:
            async for msg in channel.history(limit=100):  # Process in smaller batches
                if msg.created_at.replace(tzinfo=None) < limit_time:
                    try:
                        await msg.delete()
                        deleted_in_batch += 1
                        total_deleted += 1
                        if total_deleted % 10 == 0:
                            print(f"Deleted {total_deleted} messages so far...")
                        await asyncio.sleep(1)  # Avoid rate limiting
                    except discord.errors.Forbidden:
                        print("Bot lacks permission to delete messages")
                        return
                    except Exception as e:
                        error_count += 1
                        print(f"Failed to delete message: {e}")
                        if error_count > 5:
                            print("Too many errors encountered, stopping deletion process")
                            return

            if deleted_in_batch == 0:  # No more old messages found
                break

        except Exception as e:
            print(f"Critical error during message deletion: {e}")
            break

    print(f"Message deletion completed. Total deleted: {total_deleted}, Errors: {error_count}")
    print("Bot deletion task finished")

keep_alive()
bot.run(TOKEN)