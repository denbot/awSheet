#!/usr/bin/env python3

import csv
import discord
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz
import re
import google.auth

# Load the Discord token from the .env file
load_dotenv()
# Set the DISCORD_TOKEN variable from the token in the .env file
TOKEN = os.getenv('DISCORD_TOKEN')

# Set the timezone to Denver
mtz = pytz.timezone('America/Denver')

# Create a new Discord client with intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Create an empty dictionary
badge_names = {}

# Read the badge_names.csv file
with open('badge_names.csv', 'r') as f:
    # Create a csv reader object
    reader = csv.reader(f)
    for row in reader:
        # Define the variables from the csv file
        badge_id, name, discord_id = row
        # Add the badge_id and discord_id to the badge_names dictionary
        badge_names[discord_id] = badge_id

# Event handler for when the bot is ready
@client.event
# Define the async function
async def on_message(message):
    global question_index
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Use regex to check if the message contains anything about checking in or out
    if re.match(r"(how)? ?(do|to)? ?(i|we)? ?(check|forg[eo]t|need|scan) ?(to|2)? ?(scan|check|clock|sign)? ?(in|out)?", message.content.lower()):
        # Get the author of the message
        author = message.author
        # Send a message to the channel with instructions on how to check in or out
        await message.channel.send(f"I can update today's attendance sheet!\nPlease @mention me with your id like this:\n\n@awSheet out 6:30pm\nor this:\n@awSheet out now")
    
    # check if any message is directed at the bot by name
    if client.user.mentioned_in(message):
        # Get the author of the message
        author = message.author
        # Extract the user's input after the bot's mention
        user_input = message.content[len(f"<@!{client.user.id}>"):].lower()

        # Get the current time from the message timestamp
        tstamp = str(message.created_at)
        # Convert the time to a datetime object
        utc_time = datetime.strptime(tstamp, '%Y-%m-%d %H:%M:%S.%f%z')
        # Convert the time to Denver time
        mt_time = utc_time.astimezone(mtz)
        # Format the time to a string
        mt_now_time = mt_time.strftime('%m-%d-%Y %H:%M:%S')
        # Extract the date from the time
        mt_now_day = mt_now_time[:10]

        # check if the message after the botname matches the following regex: [0-9]{6} (in|out) 'now'
        if re.match(r"(in|out) now", user_input):
            # get the badge_id from badge_names dictionary based on the discord id in message.author.id
            badge_id = badge_names.get(str(message.author.id))
            # Create a new dictionary with the key of badge_id
            badge_id_dict = {badge_id: {}}
            # Extract the in or out and store it in the badge_id_dict dictionary
            badge_id_dict[badge_id]['inout'] = re.search(r"(in|out)", user_input).group(0)
            # Store mt_time in the badge_id_dict dictionary
            badge_id_dict[badge_id]['time'] = mt_now_time
            # send badge_data to <./cliWrite2sheets.py student_id in_or_out "time"> to update the attendance sheet
            os.system(f"python3 cliWrite2sheets.py {badge_id} {badge_id_dict[badge_id]['inout']} \"{badge_id_dict[badge_id]['time']}\"")
            # Provie the user with a confirmation message
            await message.channel.send(f"Thanks {author.mention}! I've submitted:\n{badge_id} {badge_id_dict[badge_id]['inout']} {badge_id_dict[badge_id]['time']}.")
            # Delete the badge_id_dict dictionary
            del badge_id_dict
            # Delete the badge_id variable
            badge_id = ''

        if re.match(r"(in|out) (1[0-2]|0?[1-9]):[0-5][0-9] ?(am|pm)", user_input):
            badge_id = badge_names.get(str(message.author.id))
            badge_id_dict = {badge_id: {}}
            # Extract the in or out and store it in the badge_id_dict dictionary
            badge_id_dict[badge_id]['inout'] = re.search(r"(in|out)", user_input).group(0)
            # Extract the time and store it in the badge_id_dict dictionary
            time = re.search(r"(1[0-2]|0?[1-9]):[0-5][0-9] ?(am|pm)", user_input).group().replace("am", " am").replace("pm", " pm")
            
            # Create a string with the date and time and convert it to a datetime object
            date_str = '{} {}'.format(mt_now_day, time)
            # Convert the date_str to a datetime object
            date_obj = datetime.strptime(date_str, '%m-%d-%Y %I:%M %p')
            # Convert the date_obj to a string
            date_formatted = date_obj.strftime('%m-%d-%Y %H:%M')
            # Add :00 to the end of date_formatted
            date_formatted = date_formatted + ":00"
            # Write the date_formatted to the badge_id_dict dictionary
            badge_id_dict[badge_id]["time"] = date_formatted

            # send badge_data to <./cliWrite2sheets.py student_id in_or_out "time"> to update the attendance sheet
            os.system(f"python3 cliWrite2sheets.py {badge_id} {badge_id_dict[badge_id]['inout']} \"{date_formatted}\"")
            # Provie the user with a confirmation message
            await message.channel.send(f"Thanks {author.mention}! I've submitted:\n{badge_id} {badge_id_dict[badge_id]['inout']} {date_formatted}.")
            # Delete the badge_id_dict dictionary
            del badge_id_dict
            # Reset the badge_id variable
            badge_id = ''
# Start the bot
client.run(TOKEN)
