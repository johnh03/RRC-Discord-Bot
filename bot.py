import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pytz 
from datetime import time, datetime, timedelta
from flask import Flask
from threading import Thread

#Load Environment Variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


# Tracks the last successful announcement time (datetime.date object)
# This will be used to prevent multiple announcements on the same Tuesday/Thursday.
last_announcement_date = None

#Configuration

# 🚨 IMPORTANT: REPLACE THESE PLACEHOLDERS WITH YOUR ACTUAL IDs
ANNOUNCEMENT_CHANNEL_ID = 1430988196438868039 # <-- REPLACE WITH YOUR CHANNEL ID
ANNOUNCEMENT_ROLE_ID = 1430991759361708132   # <-- REPLACE WITH THE ROLE ID

GOOGLE_MAPS_LINK = "https://maps.app.goo.gl/ydEawALn1PHo2e4A7"
EST_TZ = pytz.timezone('America/New_York')


#Bot Setup
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

# Create the role mention string
ROLE_MENTION = f"<@&{ANNOUNCEMENT_ROLE_ID}>"

#Base Announcement Messages 
BASE_TIME = "**4:10 PM EST**"
BASE_SPOT = f"[RRC Regular Meeting Spot]({GOOGLE_MAPS_LINK})"

TUESDAY_BASE_MESSAGE = (
    f"{ROLE_MENTION} **TUESDAY RUN ANNOUNCEMENT!** 🏃‍♀️\n"
    f"⏰ **Time:** Today at {BASE_TIME}\n"
    f"📍 **Meeting Spot:** {BASE_SPOT}\n"
    "See you there for a great run!"
)

THURSDAY_BASE_MESSAGE = (
    f"{ROLE_MENTION} **THURSDAY RUN ANNOUNCEMENT!** 👟\n"
    f"⏰ **Time:** Today at {BASE_TIME}\n"
    f"📍 **Meeting Spot:** {BASE_SPOT}\n"
    "Let's crush this week's run! See you at the spot."
)


#COMMAND: !clubrun
@bot.command(name='clubrun', help='Sends the run announcement for Tuesday/Thursday. Use with `!clubrun [text]` to add extra details in triple backticks.')
@commands.has_permissions(administrator=True) # Recommended: only allow admins to run this critical command
async def club_run_announcement(ctx, *, additional_text=None):
    global last_announcement_date
    
    # Get the current day in EST (weekday 0=Monday, 1=Tuesday, 3=Thursday)
    now_est = datetime.now(EST_TZ)
    current_day_est = now_est.weekday()
    
    # 1. Determine if it's Tuesday (1) or Thursday (3)
    if current_day_est == 1:
        # Tuesday
        day_name = "Tuesday"
        base_message = TUESDAY_BASE_MESSAGE
    elif current_day_est == 3:
        # Thursday
        day_name = "Thursday"
        base_message = THURSDAY_BASE_MESSAGE
    else:
        # Not a scheduled run day
        await ctx.send(f"❌ **Error:** Today ({now_est.strftime('%A')}) is not a scheduled run day (Tuesday or Thursday).")
        return

    # 2. Check if the announcement has already been sent today
    today_date = now_est.date()
    if last_announcement_date == today_date:
        await ctx.send(f"⚠️ **Announcement Already Sent:** The **{day_name}** club run announcement has already been made today ({today_date.strftime('%Y-%m-%d')}).")
        return

    # Get the announcement channel
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if not channel:
        await ctx.send(f"❌ **Error:** The announcement channel (ID: {ANNOUNCEMENT_CHANNEL_ID}) could not be found.")
        return

    # 3. Build the final message
    final_message = base_message
    if additional_text:
        # Check for triple backticks and clean up the input
        if additional_text.startswith('```') and additional_text.endswith('```'):
            # Remove triple backticks from the start and end
            clean_text = additional_text[3:-3].strip()
        else:
            clean_text = additional_text.strip()
            
        # Append the additional text clearly
        final_message += f"\n\n---\n**⚠️ CLUB UPDATE ⚠️**\n{clean_text}"
        
        # Log the addition
        print(f"Added custom text to the {day_name} announcement: '{clean_text}'")


    # Send the announcement
    await channel.send(final_message)
    
    # Update the state variable to prevent re-sending
    last_announcement_date = today_date
    
    # Confirmation message in the command channel
    await ctx.send(f"✅ **Success!** The **{day_name}** club run announcement has been successfully sent to <#{ANNOUNCEMENT_CHANNEL_ID}>.")


# Test Command
@bot.command(name='testrun', help='Tests the current run announcement and custom text logic.')
@commands.has_permissions(administrator=True) 
async def test_announcement(ctx, *, additional_text=None):
    """Sends a sample Tuesday announcement with optional custom text."""
    channel = ctx.channel # Send test to the current channel
    
    final_message = TUESDAY_BASE_MESSAGE
    
    if additional_text:
        if additional_text.startswith('```') and additional_text.endswith('```'):
            clean_text = additional_text[3:-3].strip()
        else:
            clean_text = additional_text.strip()
            
        final_message += f"\n\n---\n**⚠️ TEST UPDATE ⚠️**\n{clean_text}"
        
    await channel.send(final_message)
    
    await ctx.send("✅ **RRC Bot Test Successful!** The sample Tuesday announcement with your custom text has been sent.")
    print(f"Test announcement triggered by {ctx.author}.")



#Bot Events
@bot.event
async def on_ready():
    print('-------------------------------------------')
    print(f'Logged in as: {bot.user} (ID: {bot.user.id})')
    print(f"Announcement Channel ID: {ANNOUNCEMENT_CHANNEL_ID}")
    print(f"Announcement Role ID: {ANNOUNCEMENT_ROLE_ID}")
    print('-------------------------------------------')


#Keep Alive Web Server
app = Flask('')

@app.route('/')
def home():
    # Return 200 OK status for Render's health check
    return "RRC Club Run Bot is online!"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    # CRITICAL: host="0.0.0.0" is needed to listen on the public network interface.
    app.run(host="0.0.0.0", port=port)

def keep_alive():
  # Start the web server in a separate thread
  t = Thread(target=run_server)
  t.start()

#Run the Bot
if __name__ == '__main__':
    try:
        # CRITICAL FIX: Start the web server first
        keep_alive()
        
        # Then start the Discord bot (this blocks the main thread)
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("FATAL ERROR: Bot failed to log in. Check your DISCORD_TOKEN environment variable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
