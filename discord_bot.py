import discord
from discord.ext import commands
import asyncio
import logging
from config import BOT_TOKEN, BOT_PREFIX, BOT_DESCRIPTION
from google_sheets_service import sheets_service

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

@bot.command(name='update')
async def update_pet_info(ctx, lead_id: str, *, update_data: str):
    """
    Update pet information in Google Sheets.
    Usage: !update <lead_id> pet_name:Max species:Dog breed:Golden Retriever weight_kg:25.5 age_years:3
    """
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in threads!")
        return
    
    try:
        # Parse the update data (format: field:value field:value)
        updates = {}
        for item in update_data.split():
            if ':' in item:
                field, value = item.split(':', 1)
                updates[field] = value
        
        if not updates:
            await ctx.send("Please provide update data in format: field:value field:value")
            return
        
        # Update the record
        success = sheets_service.update_thread_record(lead_id, **updates)
        
        if success:
            await ctx.send(f"✅ Successfully updated record for lead {lead_id}")
        else:
            await ctx.send(f"❌ Failed to update record for lead {lead_id}")
            
    except Exception as e:
        logger.error(f"Error in update command: {e}")
        await ctx.send(f"❌ Error updating record: {str(e)}")

@bot.command(name='get')
async def get_pet_info(ctx, lead_id: str):
    """
    Get pet information from Google Sheets.
    Usage: !get <lead_id>
    """
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in threads!")
        return
    
    try:
        record = sheets_service.get_thread_record(lead_id)
        
        if record:
            embed = discord.Embed(
                title=f"Pet Information - Lead {lead_id}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Pet ID", value=record['pet_id'], inline=True)
            embed.add_field(name="Status", value=record['status'], inline=True)
            embed.add_field(name="Pet Name", value=record['pet_name'] or "Not set", inline=True)
            embed.add_field(name="Species", value=record['species'] or "Not set", inline=True)
            embed.add_field(name="Breed", value=record['breed'] or "Not set", inline=True)
            embed.add_field(name="Weight (kg)", value=record['weight_kg'] or "Not set", inline=True)
            embed.add_field(name="Age (years)", value=record['age_years'] or "Not set", inline=True)
            embed.add_field(name="Coat Condition", value=record['coat_condition'] or "Not set", inline=True)
            embed.add_field(name="Notes", value=record['notes'] or "No notes", inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ No record found for lead {lead_id}")
            
    except Exception as e:
        logger.error(f"Error in get command: {e}")
        await ctx.send(f"❌ Error retrieving record: {str(e)}")

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
        success = sheets_service.insert_thread_record(
            lead_id=str(thread.id)
        )
        
        if success:
            logger.info(f'Successfully recorded thread "{thread.name}" in Google Sheets')
        else:
            logger.warning(f'Failed to record thread "{thread.name}" in Google Sheets')
            
    except Exception as e:
        logger.error(f'Error recording thread in Google Sheets: {e}')

    # Optionally send a welcome message to new threads
    try:
        welcome_message = f"Welcome to the thread! I'm here to help. Send any message and I'll respond with static text."
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
