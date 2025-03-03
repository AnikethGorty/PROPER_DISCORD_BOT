import os
from dotenv import load_dotenv
import discord
import requests
import random
import asyncio
from bs4 import BeautifulSoup as bs
from discord.ext import commands

# Load environment variables
load_dotenv()  # ✅ You need this to load .env properly!
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Ensure token exists
if not TOKEN:
    raise ValueError("Bot token not found! Make sure it's in the .env file.")

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

async def send_periodic_messages():
    """Sends a Nectar Drop every 3 hours to all servers."""
    await bot.wait_until_ready()

    while not bot.is_closed():
        message = await fetch_nectar_drop()

        for guild in bot.guilds:
            channel = get_default_channel(guild)
            if channel:
                try:
                    await channel.send(message)
                    print(f"✅ Sent message to {guild.name} in #{channel.name}")
                except discord.Forbidden:
                    print(f"❌ No permission to send messages in {guild.name}")

        print("⏳ Waiting 3 hours before sending the next message...")
        await asyncio.sleep(3 * 60 * 60)  # Wait 3 hours (3 * 60 minutes * 60 seconds)

def get_default_channel(guild):
    """Finds the best text channel to send messages in."""
    # Try to find a channel named 'general' first
    for channel in guild.text_channels:
        if channel.name == "general" and channel.permissions_for(guild.me).send_messages:
            return channel  # Prefer #general if it's available

    # If no #general, return the first text channel where the bot has permission
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel

    return None  # If no valid channel is found


@bot.command()
async def quote(ctx):
    """Responds with a random Nectar Drop when !quote is used."""
    message = await fetch_nectar_drop()
    if not message:
        message = "⚠️ Sorry, I couldn't find a Nectar Drop right now. Please try again!"
    await ctx.send(message)

@bot.event
async def on_ready():
    print(f"🚀 Logged in as {bot.user}")
    print("🔍 Available Servers & Channels:")
    
    for guild in bot.guilds:
        print(f"📌 Server: {guild.name}")
        for channel in guild.text_channels:
            print(f"   ➜ #{channel.name} - ID: {channel.id}")

    bot.loop.create_task(send_periodic_messages())  # Start periodic messaging

bot.run(TOKEN)
