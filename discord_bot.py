import discord
from discord.ext import commands
import asyncio
import logging
from config import BOT_TOKEN, BOT_PREFIX, BOT_DESCRIPTION

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(command_prefix=BOT_PREFIX, description=BOT_DESCRIPTION, intents=intents)

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="Responding to threads"))

@bot.event
async def on_message(message):
    """Event triggered when a message is sent in any channel or thread."""
    # Check if the message is in a thread
    if isinstance(message.channel, discord.Thread) and not message.author.bot:
        logger.info(f'Received message in thread "{message.channel.name}": {message.content}')
        
        try:
            await message.channel.send("This is a response from bot.")
            logger.info(f'Responded to message in thread "{message.channel.name}"')
        except Exception as e:
            logger.error(f'Error responding to message in thread: {e}')
    elif not message.author.bot:
        await message.channel.send("Please start a new thread using /thread command to get started.")

    # Process commands (if any)
    await bot.process_commands(message)

@bot.event
async def on_thread_create(thread):
    """Event triggered when a new thread is created."""
    logger.info(f'New thread created: "{thread.name}" in channel "{thread.parent.name}"')

    # Attempt to make the thread private (invitable=False, type=private)
    try:
        # Only proceed if the thread is not already private
        if not thread.invitable or thread.type == discord.ChannelType.private_thread:
            logger.info(f'Thread "{thread.name}" is already private.')
        else:
            # Only the thread creator and the bot will have access
            await thread.edit(invitable=False)
            logger.info(f'Set thread "{thread.name}" to private (invitable=False).')
    except Exception as e:
        logger.error(f'Error making thread private: {e}')

    # Optionally send a welcome message to new threads
    try:
        welcome_message = f"Welcome to the thread! I'm here to help. Send any message and I'll respond with static text."
        await thread.send(welcome_message)
        logger.info(f'Sent welcome message to new thread "{thread.name}"')
    except Exception as e:
        logger.error(f'Error sending welcome message to new thread: {e}')

@bot.command(name='threadinfo')
async def thread_info(ctx):
    """Command to show information about the current thread."""
    if isinstance(ctx.channel, discord.Thread):
        thread = ctx.channel
        embed = discord.Embed(
            title="Thread Information",
            color=discord.Color.blue()
        )
        embed.add_field(name="Thread Name", value=thread.name, inline=True)
        embed.add_field(name="Thread ID", value=thread.id, inline=True)
        embed.add_field(name="Parent Channel", value=thread.parent.name, inline=True)
        embed.add_field(name="Created At", value=thread.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Message Count", value=thread.message_count, inline=True)
        embed.add_field(name="Is Archived", value=thread.archived, inline=True)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("This command can only be used in threads!")

async def main():
    """Main function to run the bot."""
    try:
        logger.info("Starting Discord bot...")
        await bot.start(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Failed to login: Invalid bot token")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
