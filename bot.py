import os
from dotenv import load_dotenv
import discord
import requests
import random
import asyncio
from bs4 import BeautifulSoup as bs
from datetime import datetime, time, timedelta
from discord.ext import commands

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Ensure token exists
if not TOKEN:
    raise ValueError("Bot token not found! Make sure it's in the .env file.")

CHANNEL_ID = 1346081090992869438  # Replace with your actual channel ID

# Set up bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Needed for command processing
bot = commands.Bot(command_prefix="!", intents=intents)

async def fetch_nectar_drop():
    """Fetches a random Nectar Drop from Vanipedia."""
    url = 'https://vanipedia.org/wiki/Category:Nectar_Drops_from_Srila_Prabhupada'
    response = requests.get(url)
    soup = bs(response.text, 'html.parser')

    h2_tag = soup.find('h2', string=lambda text: "Pages in category" in text)
    if h2_tag:
        category_section = h2_tag.find_next('div')
        links = category_section.find_all('a', href=True) if category_section else []

        if links:
            random_link = random.choice(links)
            selected_href = "https://vanipedia.org" + random_link['href']
            print("Randomly Selected Link:", selected_href)
            
            quote_url = requests.get(selected_href)
            quote_soup = bs(quote_url.text, 'html.parser')
            nectar_spans = quote_soup.find_all('span', class_='nectardroptext')

            nectar_texts = [span.get_text(strip=True) for span in nectar_spans]

            if nectar_texts:
                return random.choice(nectar_texts)  # Return a random nectar drop
            else:
                return "Could not find any nectar drop text on the selected page."
        else:
            return "No links found in the category section."
    else:
        return "Could not find the 'Pages in category' header."

async def send_daily_message():
    """Sends a nectar drop every day at 6:00 PM."""
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        print(f"Error: Could not find channel with ID {CHANNEL_ID}")
        return

    while not bot.is_closed():
        now = datetime.now()
        target_time = time(18, 0)  # 6:00 PM
        target_datetime = datetime.combine(now.date(), target_time)

        if now > target_datetime:
            target_datetime += timedelta(days=1)

        wait_time = (target_datetime - now).total_seconds()
        print(f"Waiting {wait_time} seconds until next message...")
        
        await asyncio.sleep(wait_time)
        message = await fetch_nectar_drop()
        await channel.send(message)

@bot.command()
async def quote(ctx):
    """Responds with a random Nectar Drop when !quote is used."""
    message = await fetch_nectar_drop()
    await ctx.send(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Available Channels:")
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f"{channel.name} - ID: {channel.id}")


bot.run(TOKEN)
