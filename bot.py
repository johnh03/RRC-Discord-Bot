import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import pytz 
from datetime import time
from flask import Flask
from threading import Thread

#Load Environment Variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#Configuration

# 🚨 IMPORTANT: REPLACE THESE PLACEHOLDERS WITH YOUR ACTUAL IDs
ANNOUNCEMENT_CHANNEL_ID = 1430988196438868039 # <-- REPLACE WITH YOUR CHANNEL ID
ANNOUNCEMENT_ROLE_ID = 1430991759361708132   # <-- REPLACE WITH THE ROLE ID

GOOGLE_MAPS_LINK = "https://maps.app.goo.gl/ydEawALn1PHo2e4A7"
EST_TZ = pytz.timezone('America/New_York')
SCHEDULED_TIME = time(hour=8, minute=0, tzinfo=EST_TZ)


#Bot Setup
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

# Create the role mention string
ROLE_MENTION = f"<@&{ANNOUNCEMENT_ROLE_ID}>"


#Announcement Messages
TUESDAY_MESSAGE = (
    f"{ROLE_MENTION} **TUESDAY RUN ANNOUNCEMENT!** 🏃‍♀️\n"
    "⏰ **Time:** Today at **4:10 PM EST**\n"
    "📍 **Meeting Spot:** [RRC Regular Meeting Spot]({})\n"
    "See you there for a great run!"
).format(GOOGLE_MAPS_LINK)

THURSDAY_MESSAGE = (
    f"{ROLE_MENTION} **THURSDAY RUN ANNOUNCEMENT!** 👟\n"
    "⏰ **Time:** Today at **4:10 PM EST**\n"
    "📍 **Meeting Spot:** [RRC Regular Meeting Spot]({})\n"
    "Let's crush this week's run! See you at the spot."
).format(GOOGLE_MAPS_LINK)


#Test Command
@bot.command(name='testrun', help='Sends a sample run announcement immediately for testing.')
@commands.has_permissions(administrator=True) # Recommended: only allow admins to run test commands
async def test_announcement(ctx):
    """Sends a sample run announcement message instantly."""
    
    # We'll send the Tuesday message for the test
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    
    if channel:
        # Send the message
        await channel.send(TUESDAY_MESSAGE)
        
        # Confirm to the user who ran the command
        await ctx.send(f"✅ **RRC Bot Test Successful!** The sample Tuesday announcement has been sent to <#{ANNOUNCEMENT_CHANNEL_ID}>.")
        print(f"Test announcement triggered by {ctx.author} and sent.")
    else:
        await ctx.send(f"❌ **Error:** The announcement channel (ID: {ANNOUNCEMENT_CHANNEL_ID}) could not be found.")

#Scheduled Task
@tasks.loop(time=SCHEDULED_TIME)
async def scheduled_announcement():
    # ... (code remains the same as before) ...
    await bot.wait_until_ready()
    
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)

    current_day_est = discord.utils.utcnow().astimezone(EST_TZ).weekday()

    if channel:
        if current_day_est == 1: # Tuesday
            await channel.send(TUESDAY_MESSAGE)
            print(f"Sent Tuesday announcement at {discord.utils.utcnow().astimezone(EST_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        elif current_day_est == 3: # Thursday
            await channel.send(THURSDAY_MESSAGE)
            print(f"Sent Thursday announcement at {discord.utils.utcnow().astimezone(EST_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print(f"Error: Announcement channel with ID {ANNOUNCEMENT_CHANNEL_ID} not found for scheduled task.")


#Bot Events
@bot.event
async def on_ready():
    print('-------------------------------------------')
    print(f'Logged in as: {bot.user} (ID: {bot.user.id})')
    print(f"Scheduled announcement time (EST/EDT): {SCHEDULED_TIME.strftime('%I:%M %p %Z')}")
    
    if not scheduled_announcement.is_running():
        scheduled_announcement.start()
        print("Scheduled announcement task has been started.")
    print('-------------------------------------------')

#Keep Alive Web Server
app = Flask('')

@app.route('/')
def home():
    return "RRC Club Run Bot is online!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()

#Run the Bot
if __name__ == '__main__':
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("FATAL ERROR: Bot failed to log in. Check your DISCORD_TOKEN in the .env file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")