import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pytz 
from datetime import time, datetime, timedelta
from flask import Flask
from threading import Thread
import asyncio
import re

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


# --- NEW POLL COMMAND ---

@bot.command(name='poll', help='Creates a poll. Usage: !poll "Poll Prompt" choice1, choice2, ... [duration #d #h #m]')
async def poll(ctx, *, args: str):
    """
    Creates a poll with multiple choices and an optional duration.
    
    Format: !poll "Poll Prompt" choice1, choice2, choice3 [duration 1d 2h 3m]
    
    - Prompt must be in double quotes.
    - Choices must be comma-separated.
    - Duration is optional and must be in brackets.
    """
    
    # --- 1. Parse Duration (if it exists) ---
    duration_str = ""
    total_seconds = 0
    days, hours, minutes = 0, 0, 0
    
    # Regex to find the duration string at the end, e.g., [1d 2h 3m]
    duration_match = re.search(r'\[\s*(?:(\d+)\s*d)?\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*\]$', args)
    
    if duration_match:
        # Extract days, hours, minutes
        days_str, hours_str, minutes_str = duration_match.groups()
        
        days = int(days_str) if days_str else 0
        hours = int(hours_str) if hours_str else 0
        minutes = int(minutes_str) if minutes_str else 0
        
        # Calculate total duration in seconds
        total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60)
        
        if total_seconds > 0:
            duration_str = f" This poll will end in {days}d {hours}h {minutes}m."
        
        # Remove the duration part from the args string to parse the rest
        args = args[:duration_match.start()].strip()

    # --- 2. Parse Prompt and Choices ---
    try:
        # Find the prompt inside the first pair of double quotes
        prompt_match = re.match(r'"(.*?)"', args)
        if not prompt_match:
            await ctx.send("❌ **Invalid Format!** Poll prompt must be enclosed in double quotes.")
            await ctx.send("Usage: `!poll \"Poll Prompt\" choice1, choice2, ... [duration #d #h #m]`")
            return
            
        prompt = prompt_match.group(1)
        
        # The rest of the string after the prompt contains the choices
        choices_str = args[prompt_match.end():].strip()
        
        if not choices_str:
            raise ValueError("No choices provided.")
            
        # Split choices by comma and strip whitespace
        choices = [choice.strip() for choice in choices_str.split(',') if choice.strip()]
        
        if len(choices) < 2:
            await ctx.send("❌ **Invalid Poll!** You must provide at least 2 choices.")
            return
            
        if len(choices) > 10:
            await ctx.send("❌ **Invalid Poll!** You can have a maximum of 10 choices.")
            return

    except Exception as e:
        print(f"Poll command error: {e}")
        await ctx.send("❌ **Invalid Format!** Please check your syntax.")
        await ctx.send("Usage: `!poll \"Poll Prompt\" choice1, choice2, ... [duration #d #h #m]`")
        return

    # --- 3. Create and Send Poll Embed ---
    
    # Emojis for reactions (up to 10)
    react_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    description_lines = []
    for i, choice in enumerate(choices):
        description_lines.append(f"{react_emojis[i]} **{choice}**")
    
    poll_description = "\n\n".join(description_lines)

    embed = discord.Embed(
        title=f"📊 **{prompt}**",
        description=poll_description,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Poll started by {ctx.author.display_name}.{duration_str}")

    # Send the poll message
    try:
        poll_message = await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **Error:** I don't have permission to send embeds in this channel.")
        return

    # Add reactions to the poll message
    for i in range(len(choices)):
        try:
            await poll_message.add_reaction(react_emojis[i])
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I don't have permission to add reactions in this channel.")
            return
            
    # Send a confirmation to the user (and delete it)
    await ctx.message.delete() # Deletes the user's !poll command
    
    # --- 4. Handle Poll End (if duration was set) ---
    if total_seconds > 0:
        # Wait for the duration
        await asyncio.sleep(total_seconds)
        
        try:
            # Fetch the message again to get the final reaction counts
            updated_message = await ctx.channel.fetch_message(poll_message.id)
        except discord.NotFound:
            # The poll message was deleted
            print(f"Poll message {poll_message.id} not found. Cannot send results.")
            return
        except discord.Forbidden:
            await ctx.send(f"❌ **Error:** I can't read the poll message <{poll_message.jump_url}> to get results.")
            return

        # --- Tally Results ---
        results = {}
        total_votes = 0
        
        for i, choice in enumerate(choices):
            emoji = react_emojis[i]
            # Find the reaction corresponding to the emoji
            reaction = discord.utils.get(updated_message.reactions, emoji=emoji)
            
            if reaction:
                # Subtract 1 for the bot's own reaction
                vote_count = reaction.count - 1
                results[choice] = vote_count
                total_votes += vote_count
            else:
                results[choice] = 0

        # --- Create and Send Results Embed ---
        results_description_lines = []
        
        # Sort results by vote count (highest first)
        sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)
        
        for choice, votes in sorted_results:
            # Calculate percentage
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            results_description_lines.append(f"**{choice}**: {votes} votes ({percentage:.1f}%)")

        results_description = "\n".join(results_description_lines)

        results_embed = discord.Embed(
            title=f"**Poll Results: {prompt}**",
            description=results_description,
            color=discord.Color.green()
        )
        results_embed.set_footer(text=f"A total of {total_votes} votes were cast.")

        # Send the results as a reply to the original poll
        await poll_message.reply(embed=results_embed)
        
        # Optional: Edit the original poll to show it has ended
        try:
            ended_embed = poll_message.embeds[0]
            ended_embed.set_footer(text=f"Poll started by {ctx.author.display_name}. [POLL ENDED]")
            ended_embed.color = discord.Color.dark_grey()
            await poll_message.edit(embed=ended_embed)
        except discord.Forbidden:
            pass # Not critical if this fails


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
