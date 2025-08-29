import discord
from discord.ext import commands
import asyncio
import logging
from config import BOT_TOKEN, BOT_PREFIX, BOT_DESCRIPTION
from workflow_graph import workflow_manager
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
            # Process message through LangGraph workflow
            response = await workflow_manager.process_message(
                message=message.content,
                lead_id=str(message.channel.id),
                discord_user_id=str(message.author.id)
            )
            
            await message.channel.send(response)
            logger.info(f'Responded to message in thread "{message.channel.name}"')
        except Exception as e:
            logger.error(f'Error responding to message in thread: {e}')
            await message.channel.send("I'm sorry, I encountered an error. Please try again or contact support.")
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

    try:
        # Initialize conversation state for the new thread
        workflow_manager.get_or_create_state(
            lead_id=str(thread.id),
            discord_user_id=str(thread.owner_id) if thread.owner_id else "unknown"
        )
        logger.info(f'Initialized conversation state for thread "{thread.name}"')
        
    except Exception as e:
        logger.error(f'Error initializing conversation state: {e}')

    # Send a welcome message to new threads
    try:
        welcome_message = ("🐾 Welcome to our pet grooming service! I'm here to help you get your furry friend "
                          "looking their best. To get started, just tell me about you and your pet!")
        await thread.send(welcome_message)
        logger.info(f'Sent welcome message to new thread "{thread.name}"')
    except Exception as e:
        logger.error(f'Error sending welcome message to new thread: {e}')

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
