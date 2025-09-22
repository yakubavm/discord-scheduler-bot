#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=====================================================================================
=================== DISCORD MESSAGE SCHEDULER BOT ===================
=====================================================================================

Author: Viktor Yakuba
Contact for questions and suggestions:
- Email: yakubavm@gmail.com, yakubavm@outlook.com
- Telegram: t.me/yakubavm
- Discord: yakubavm

---

DESCRIPTION:
This bot is a powerful tool for creating and managing a queue of scheduled
messages on your Discord server. It allows you to plan publications with a
set interval, adding text and files (images, documents, etc.) to them.
The bot saves the entire queue and settings in files, so upon restart, it will
resume its work from where it left off.

KEY FEATURES:
- Asynchronous operation: Does not block other processes and uses resources efficiently.
- Data persistence: The queue and settings are saved in files and are not lost.
- File support: Ability to attach up to 10 files to one message.
- Flexible management: A full set of commands for configuring the channel, interval,
  viewing, and modifying the queue.
- Interactivity: Uses slash commands, confirmation buttons, and a context menu
  for convenient interaction.
- Import/Export: Ability to save and load the queue from a file.
- Logging: Keeps a detailed log of its work for easy monitoring and
  troubleshooting.

---

INSTALLATION AND LAUNCH INSTRUCTIONS:

1. PREREQUISITES:
   - Python version 3.11 or newer installed.

2. INSTALLING DEPENDENCIES:
   It is recommended to create a virtual environment to isolate the project.
   
   # Create a virtual environment (optional, but recommended)
   python -m venv .venv
   source .venv/bin/activate  # For Linux/macOS
   .venv\\Scripts\\activate    # For Windows

   # Install the required libraries
   pip install discord.py aiohttp aiofiles python-dotenv

3. CONFIGURING THE BOT IN DISCORD:
   - Go to the Discord Developer Portal: https://discord.com/developers/applications
   - Create a new bot (click the "New Application" button).
   - Go to the "Bot" tab.
   - Click "Reset Token" to generate a token. Copy it.
   - **IMPORTANT:** Create a file named `.env` in the same directory as the script.
   - Inside the `.env` file, add the following line, pasting your token:
     DISCORD_BOT_TOKEN="YOUR_COPIED_TOKEN_HERE"
   - Enable "Privileged Gateway Intents":
     - `MESSAGE CONTENT INTENT` - required for working with message content.
   - To add the bot to a server, go to the "OAuth2" -> "URL Generator" tab.
   - Select the following scopes:
     - `bot`
     - `applications.commands`
   - In "Bot Permissions", select the necessary permissions:
     - `Send Messages`
     - `Attach Files`
     - `Read Message History`
     - `Use Application Commands`
     - `Administrator` (Recommended, as commands are now for administrators)
   - Copy the generated link and open it in your browser to add the bot
     to your server.

4. RUNNING THE BOT:

   ► ON WINDOWS:
     Open Command Prompt (cmd) or PowerShell, navigate to the folder with the file, and
     run the command:
     python discord_scheduler_bot.py

   ► ON LINUX / MACOS:
     Open a terminal, navigate to the folder with the file, and run the command:
     python3 discord_scheduler_bot.py

   ► FOR CONTINUOUS OPERATION (ON A SERVER / VDS):
     To keep the bot running in the background and prevent it from stopping when the terminal is closed,
     use `screen` or `nohup`.

     - With `screen` (recommended):
       # Create a new session named "discord_bot"
       screen -S discord_bot
       # Run the bot inside the session
       python3 discord_scheduler_bot.py
       # Detach from the session, leaving it running: press Ctrl+A, then D
       # To return to the session:
       screen -r discord_bot

     - With `nohup`:
       nohup python3 discord_scheduler_bot.py &

   ► ON A NAS (SYNOLOGY / QNAP):
     - Install Python 3 from your NAS's package center.
     - Upload the `discord_scheduler_bot.py` file and the `bot_data` folder to the NAS.
     - Open "Control Panel" -> "Task Scheduler".
     - Create a new "Scheduled Task" -> "User-defined script".
     - In the "General" tab, give the task a name.
     - In the "Task Settings" tab, in the "Run command" field, paste:
       /usr/bin/python3 /volume1/path/to/your/script/discord_scheduler_bot.py
       (replace `/volume1/path/to/your/script/` with the actual path to the file).
     - Run the task manually to check its operation.

---

LIST OF BOT COMMANDS (SLASH COMMANDS):

/set_channel [channel]
  - Description: Sets the text channel where messages from the queue will be published.
  - Arguments: `channel` - the text channel.

/add_message [content] [attachment1 ... attachment10]
  - Description: Adds a new message to the queue. You can add text and up to 10 files.
  - Arguments: `content` - the message text, `attachment` - files to attach.

Add to Queue (Context Menu)
  - Description: Allows you to add any existing message to the queue by right-clicking
    it and selecting "Apps" -> "Add to Queue".

/set_interval [minutes]
  - Description: Sets the interval in minutes between message publications.
  - Arguments: `minutes` - a number (minimum 1).

/view_queue
  - Description: Shows the current state of the queue: total number of messages, status
    (active/paused), time of the next post, and a list of upcoming messages.

/delete_message [message_id]
  - Description: Deletes a message from the queue by its unique ID.
  - Arguments: `message_id` - the ID of the message, which can be seen in `/view_queue`.

/clear_queue
  - Description: Completely clears the entire message queue. Requires confirmation via buttons.

/pause
  - Description: Temporarily pauses the publication of messages from the queue.

/resume
  - Description: Resumes the publication of messages after a pause.

/status
  - Description: Shows the current bot settings: channel, interval, queue size, and status.

/export_queue
  - Description: Exports the current queue and settings to a `queue_backup.json` file for backup.

/import_queue [file]
  - Description: Adds messages from an export file to the current queue.
  - Arguments: `file` - a `.json` file obtained via the `/export_queue` command.

---
ATTENTION: Remember to create a .env file and set your DISCORD_BOT_TOKEN!
=====================================================================================
"""

import discord
from discord.ext import commands, tasks
from discord.app_commands import checks
import asyncio
import aiohttp
import aiofiles
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
import tempfile
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, cast, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Type hints only
import time

# ================================
# CONFIGURATION
# ================================

# Load environment variables from a .env file
load_dotenv()

# !!! IMPORTANT: Don't forget to add your bot token to the .env file. !!!
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Data storage path
DATA_DIR = Path("bot_data")
TEMP_DIR = Path("temp_attachments") 
QUEUE_FILE = DATA_DIR / "message_queue.json"
CONFIG_FILE = DATA_DIR / "bot_config.json"
LOG_FILE = "scheduler_bot.log"

# Default settings
DEFAULT_INTERVAL_MINUTES = 120  # 2 hours
MAX_ATTACHMENTS = 10
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB (Discord limit)
ATTACHMENT_CLEANUP_DAYS = 7

# Colors for Embed messages
COLORS = {
    'success': 0x00ff00,
    'error': 0xff0000,
    'warning': 0xffaa00,
    'info': 0x0099ff
}

# ================================
# CONTEXT MENU (MODULE LEVEL)
# ================================

@discord.app_commands.context_menu(name="Add to Queue")
@checks.has_permissions(administrator=True)
async def add_to_queue_context(interaction: discord.Interaction, message: discord.Message):
    """Adds a message to the queue via the context menu"""
    bot = cast('SchedulerBot', interaction.client)
    
    try:
        if not message.content and not message.attachments:
            embed = discord.Embed(
                title="❌ Error",
                description="Message has no content or attachments",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Download attachments
        attachments = []
        if message.attachments:
            if len(message.attachments) > MAX_ATTACHMENTS:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Too many attachments. Maximum is {MAX_ATTACHMENTS}",
                    color=COLORS['error']
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            for attachment in message.attachments:
                file_info = await bot.attachment_manager.download_attachment(attachment)
                if file_info:
                    attachments.append(file_info)
        
        # Add to the queue
        message_id = await bot.scheduler.add_message(
            message.content or "",
            attachments,
            interaction.user.id
        )
        
        embed = discord.Embed(
            title="✅ Message Added to Queue",
            description=f"Message added with ID: {message_id}",
            color=COLORS['success']
        )
        
        if message.content:
            embed.add_field(
                name="Content", 
                value=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                inline=False
            )
        
        if attachments:
            embed.add_field(
                name="Attachments",
                value=f"{len(attachments)} file(s)",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Error adding message: {e}",
            color=COLORS['error']
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(embed=embed, ephemeral=True)

# ================================
# LOGGING SETUP
# ================================

def setup_logging():
    """Sets up the logging system with file rotation"""
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure the rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Configure the console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure the main logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# ================================
# ATTACHMENT MANAGER CLASS
# ================================

class AttachmentManager:
    """Class for managing file attachments"""
    
    def __init__(self):
        self.temp_dir = TEMP_DIR
        self.temp_dir.mkdir(exist_ok=True)
        self.session = None
    
    async def initialize(self):
        """Initializes the aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Closes the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def download_attachment(self, attachment: discord.Attachment) -> Optional[Dict[str, Any]]:
        """
        Downloads an attachment from Discord
        
        Args:
            attachment: A Discord Attachment object
            
        Returns:
            A dictionary with file information or None on error
        """
        try:
            if attachment.size > MAX_FILE_SIZE:
                logging.warning(f"File {attachment.filename} too large: {attachment.size} bytes")
                return None
            
            # Create a unique filename
            timestamp = int(time.time())
            safe_filename = f"{timestamp}_{attachment.filename}"
            file_path = self.temp_dir / safe_filename
            
            # Download the file
            async with self.session.get(attachment.url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    file_info = {
                        'filename': attachment.filename,
                        'path': str(file_path),
                        'content_type': attachment.content_type,
                        'size': attachment.size,
                        'download_time': datetime.datetime.utcnow().isoformat()
                    }
                    
                    logging.info(f"Downloaded attachment: {attachment.filename}")
                    return file_info
                else:
                    logging.error(f"Failed to download {attachment.filename}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logging.error(f"Error downloading attachment {attachment.filename}: {e}")
            return None
    
    async def cleanup_old_files(self):
        """Cleans up old temporary files"""
        try:
            cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=ATTACHMENT_CLEANUP_DAYS)
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_mtime = datetime.datetime.utcfromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        logging.info(f"Cleaned up old file: {file_path.name}")
                        
        except Exception as e:
            logging.error(f"Error during file cleanup: {e}")
    
    def get_discord_files(self, file_infos: List[Dict[str, Any]]) -> List[discord.File]:
        """
        Creates a list of discord.File objects from file information
        
        Args:
            file_infos: A list of dictionaries with file information
            
        Returns:
            A list of discord.File objects
        """
        discord_files = []
        
        for file_info in file_infos:
            try:
                file_path = Path(file_info['path'])
                if file_path.exists():
                    discord_file = discord.File(str(file_path), filename=file_info['filename'])
                    discord_files.append(discord_file)
                else:
                    logging.warning(f"File not found: {file_path}")
            except Exception as e:
                logging.error(f"Error creating discord.File: {e}")
        
        return discord_files

# ================================
# MESSAGE SCHEDULER CLASS
# ================================

class MessageScheduler:
    """Class for managing the message queue and scheduling publications"""
    
    def __init__(self):
        self.queue: List[Dict[str, Any]] = []
        self.config = {
            'channel_id': None,
            'interval_minutes': DEFAULT_INTERVAL_MINUTES,
            'last_post_time': None,
            'is_paused': False
        }
        self.queue_lock = asyncio.Lock()
        self.next_message_id = 1
    
    async def load_data(self):
        """Loads data from files"""
        try:
            # Create the data directory
            DATA_DIR.mkdir(exist_ok=True)
            
            # Load the queue
            if QUEUE_FILE.exists():
                async with aiofiles.open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():
                        data = json.loads(content)
                        if data is not None:
                            self.queue = data.get('queue', [])
                            self.next_message_id = data.get('next_id', 1)
            
            # Load the configuration
            if CONFIG_FILE.exists():
                async with aiofiles.open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():
                        loaded_config = json.loads(content)
                        if loaded_config:
                            self.config.update(loaded_config)
                    
        except Exception as e:
            logging.error(f"Error loading data: {e}")
    
    async def save_data(self):
        """Saves data to files"""
        try:
            # Save the queue
            queue_data = {
                'queue': self.queue,
                'next_id': self.next_message_id
            }
            async with aiofiles.open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(queue_data, indent=2, ensure_ascii=False))
            
            # Save the configuration
            async with aiofiles.open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.config, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logging.error(f"Error saving data: {e}")
    
    async def add_message(self, content: str, attachments: List[Dict[str, Any]], author_id: int) -> int:
        """
        Adds a message to the queue
        
        Args:
            content: The message text
            attachments: A list of attachments
            author_id: The ID of the message author
            
        Returns:
            The message ID in the queue
        """
        async with self.queue_lock:
            # If the queue was empty, set the "last post time"
            # so the first post isn't published instantly.
            if not self.queue:
                self.config['last_post_time'] = datetime.datetime.utcnow().isoformat()
                
            message_id = self.next_message_id
            self.next_message_id += 1
            
            message = {
                'id': message_id,
                'content': content,
                'attachments': attachments,
                'author_id': author_id,
                'added_time': datetime.datetime.utcnow().isoformat(),
                'status': 'pending'
            }
            
            self.queue.append(message)
            await self.save_data()
            
            logging.info(f"Added message to queue: ID {message_id}")
            return message_id
    
    async def get_next_message(self) -> Optional[Dict[str, Any]]:
        """Gets the next message from the queue"""
        async with self.queue_lock:
            if self.queue:
                return self.queue[0]
            return None
    
    async def remove_message(self, message_id: int) -> bool:
        """
        Removes a message from the queue by ID
        
        Args:
            message_id: The ID of the message
            
        Returns:
            True if the message was removed
        """
        async with self.queue_lock:
            for i, message in enumerate(self.queue):
                if message['id'] == message_id:
                    removed_message = self.queue.pop(i)
                    await self.save_data()
                    logging.info(f"Removed message from queue: ID {message_id}")
                    return True
            return False
    
    async def clear_queue(self):
        """Clears the entire queue"""
        async with self.queue_lock:
            self.queue.clear()
            await self.save_data()
            logging.info("Queue cleared")
    
    async def get_queue_info(self, limit: int = 5) -> Dict[str, Any]:
        """
        Gets information about the queue
        
        Args:
            limit: The number of messages to display
            
        Returns:
            A dictionary with queue information
        """
        async with self.queue_lock:
            next_post_time = self.get_next_post_time()
            
            return {
                'total_messages': len(self.queue),
                'next_messages': self.queue[:limit],
                'next_post_time': next_post_time,
                'is_paused': self.config['is_paused'],
                'channel_id': self.config['channel_id'],
                'interval_minutes': self.config['interval_minutes']
            }
    
    def get_next_post_time(self) -> Optional[str]:
        """Calculates the time of the next publication"""
        if self.config['is_paused'] or not self.queue:
            return None
        
        if self.config['last_post_time']:
            last_time = datetime.datetime.fromisoformat(self.config['last_post_time'])
            next_time = last_time + datetime.timedelta(minutes=self.config['interval_minutes'])
            return next_time.isoformat()
        else:
            # If this is the first publication, it will post immediately
            return datetime.datetime.utcnow().isoformat()
    
    async def should_post_now(self) -> bool:
        """Checks if it's time for a publication"""
        if self.config['is_paused'] or not self.queue:
            return False
        
        now = datetime.datetime.utcnow()
        
        if self.config['last_post_time']:
            last_time = datetime.datetime.fromisoformat(self.config['last_post_time'])
            time_since_last = now - last_time
            return time_since_last.total_seconds() >= (self.config['interval_minutes'] * 60)
        else:
            # If this is the first publication
            return True
    
    async def mark_as_posted(self):
        """Marks the time of the last publication"""
        self.config['last_post_time'] = datetime.datetime.utcnow().isoformat()
        await self.save_data()
    
    async def export_queue(self, file_path: str):
        """Exports the queue to a file"""
        try:
            export_data = {
                'queue': self.queue,
                'config': self.config,
                'export_time': datetime.datetime.utcnow().isoformat()
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(export_data, indent=2, ensure_ascii=False))
                
            logging.info(f"Queue exported to {file_path}")
        except Exception as e:
            logging.error(f"Error exporting queue: {e}")
            raise
    
    async def import_queue(self, file_path: str):
        """Imports the queue from a file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                import_data = json.loads(content)
            
            async with self.queue_lock:
                # Add messages from the import to the current queue
                imported_queue = import_data.get('queue', [])
                for message in imported_queue:
                    # Update the ID to avoid conflicts
                    message['id'] = self.next_message_id
                    self.next_message_id += 1
                    self.queue.append(message)
                
                await self.save_data()
                
            logging.info(f"Queue imported from {file_path}, added {len(imported_queue)} messages")
            return len(imported_queue)
            
        except Exception as e:
            logging.error(f"Error importing queue: {e}")
            raise

# ================================
# MAIN BOT CLASS  
# ================================

class SchedulerBot(commands.Bot):
    """The main Discord bot class for scheduling messages"""
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.scheduler = MessageScheduler()
        self.attachment_manager = AttachmentManager()
        self.logger = logging.getLogger(__name__)
    
    async def setup_hook(self):
        """Sets up the bot on startup"""
        await self.attachment_manager.initialize()
        await self.scheduler.load_data()
        
        # Add the Cog with commands
        await self.add_cog(SchedulerCommands(self))
        
        # Add the context menu
        self.tree.add_command(add_to_queue_context)
        
        # Start tasks
        self.publish_loop.start()
        self.cleanup_loop.start()
        
        # Sync commands
        try:
            await self.tree.sync()
            self.logger.info("Slash commands synced successfully")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        self.logger.info(f"Bot is ready! Logged in as {self.user}")
        self.logger.info(f"Bot is in {len(self.guilds)} guilds")
    
    async def close(self):
        """Closes the bot"""
        self.publish_loop.cancel()
        self.cleanup_loop.cancel()
        await self.attachment_manager.close()
        await super().close()
    
    @tasks.loop(minutes=1)
    async def publish_loop(self):
        """The main message publishing loop"""
        try:
            if await self.scheduler.should_post_now():
                await self.publish_next_message()
        except Exception as e:
            self.logger.error(f"Error in publish loop: {e}")
    
    @tasks.loop(hours=6)
    async def cleanup_loop(self):
        """Loop for cleaning up old files"""
        try:
            await self.attachment_manager.cleanup_old_files()
        except Exception as e:
            self.logger.error(f"Error in cleanup loop: {e}")
    
    async def publish_next_message(self):
        """Publishes the next message from the queue"""
        try:
            message = await self.scheduler.get_next_message()
            if not message:
                return
            
            channel_id = self.scheduler.config['channel_id']
            if not channel_id:
                self.logger.warning("No channel set for publishing")
                return
            
            # Get the channel from cache or via API
            channel = self.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.fetch_channel(channel_id)
                except:
                    self.logger.error(f"Channel {channel_id} not found")
                    return
            
            # Check the channel type
            if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                self.logger.error(f"Channel {channel_id} is not a text channel")
                return
            
            # Prepare files
            files = self.attachment_manager.get_discord_files(message['attachments'])
            
            # Publish the message
            if message['content'] or files:
                await channel.send(content=message['content'] or None, files=files)
                
                # Remove from queue and update time
                await self.scheduler.remove_message(message['id'])
                await self.scheduler.mark_as_posted()
                
                channel_name = getattr(channel, 'name', 'DM')
                self.logger.info(f"Published message ID {message['id']} to {channel_name}")
            
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")
    

# ================================
# COG CLASSES WITH COMMANDS
# ================================

class SchedulerCommands(commands.Cog):
    """Cog class for message scheduler commands"""
    
    def __init__(self, bot: SchedulerBot):
        self.bot = bot
        self.scheduler = bot.scheduler
        self.attachment_manager = bot.attachment_manager
    
    @discord.app_commands.command(name="set_channel", description="Set the channel for publishing messages")
    @discord.app_commands.describe(channel="The channel where messages will be published")
    @checks.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Sets the channel for publications"""
        try:
            self.scheduler.config['channel_id'] = channel.id
            await self.scheduler.save_data()
            
            embed = discord.Embed(
                title="✅ Channel Set",
                description=f"Publishing channel set to {channel.mention}",
                color=COLORS['success']
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error setting channel: {e}")
    
    @discord.app_commands.command(name="add_message", description="Add a message to the queue with up to 10 attachments")
    @discord.app_commands.describe(
        content="The message content to add to queue",
        attachment1="File to attach (up to 10 total)",
        attachment2="Additional file to attach",
        attachment3="Additional file to attach",
        attachment4="Additional file to attach",
        attachment5="Additional file to attach",
        attachment6="Additional file to attach",
        attachment7="Additional file to attach",
        attachment8="Additional file to attach",
        attachment9="Additional file to attach",
        attachment10="Additional file to attach"
    )
    @checks.has_permissions(administrator=True)
    async def add_message(
        self, 
        interaction: discord.Interaction, 
        content: str, 
        attachment1: Optional[discord.Attachment] = None,
        attachment2: Optional[discord.Attachment] = None,
        attachment3: Optional[discord.Attachment] = None,
        attachment4: Optional[discord.Attachment] = None,
        attachment5: Optional[discord.Attachment] = None,
        attachment6: Optional[discord.Attachment] = None,
        attachment7: Optional[discord.Attachment] = None,
        attachment8: Optional[discord.Attachment] = None,
        attachment9: Optional[discord.Attachment] = None,
        attachment10: Optional[discord.Attachment] = None
    ):
        """Adds a message to the queue via slash command"""
        try:
            await interaction.response.defer(ephemeral=True)

            attachments = []
            
            all_attachments = [
                att for att in [
                    attachment1, attachment2, attachment3, attachment4, attachment5, 
                    attachment6, attachment7, attachment8, attachment9, attachment10
                ] if att is not None
            ]

            if len(all_attachments) > MAX_ATTACHMENTS: # Although Discord limits this anyway
                await self.send_error(interaction, f"Too many files! Maximum is {MAX_ATTACHMENTS}.")
                return

            for attachment in all_attachments:
                if attachment.size > MAX_FILE_SIZE:
                    await self.send_error(interaction, f"File '{attachment.filename}' is too large! Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f}MB.")
                    continue # Skip the oversized file
                
                file_info = await self.attachment_manager.download_attachment(attachment)
                if file_info:
                    attachments.append(file_info)
                else:
                    # Warn, but continue if other files are okay
                    await interaction.followup.send(f"⚠️ Could not download the attachment: {attachment.filename}", ephemeral=True)

            # Check if there's anything to add (text or successfully downloaded files)
            if not content and not attachments:
                await self.send_error(interaction, "Nothing to add. Please provide content or at least one valid attachment.")
                return

            message_id = await self.scheduler.add_message(content, attachments, interaction.user.id)
            
            embed = discord.Embed(
                title="✅ Message Added",
                description=f"Message added to queue with ID: {message_id}",
                color=COLORS['success']
            )
            if content:
                embed.add_field(name="Content", value=content[:100] + "..." if len(content) > 100 else content, inline=False)
            
            # Show the number of added files
            if attachments:
                embed.add_field(name="Attachments", value=f"{len(attachments)} file(s) added", inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"An unexpected error occurred: {e}")
    
    @discord.app_commands.command(name="set_interval", description="Set the publishing interval in minutes")
    @discord.app_commands.describe(minutes="Interval between posts in minutes")
    @checks.has_permissions(administrator=True)
    async def set_interval(self, interaction: discord.Interaction, minutes: int):
        """Sets the publication interval"""
        try:
            if minutes < 1:
                await self.send_error(interaction, "Interval must be at least 1 minute")
                return
            
            self.scheduler.config['interval_minutes'] = minutes
            await self.scheduler.save_data()
            
            embed = discord.Embed(
                title="⏰ Interval Updated",
                description=f"Publishing interval set to {minutes} minutes",
                color=COLORS['success']
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error setting interval: {e}")
    
    @discord.app_commands.command(name="view_queue", description="View the current message queue")
    @checks.has_permissions(administrator=True)
    async def view_queue(self, interaction: discord.Interaction):
        """Views the message queue"""
        try:
            queue_info = await self.scheduler.get_queue_info()
            
            embed = discord.Embed(
                title="📋 Message Queue",
                color=COLORS['info']
            )
            
            embed.add_field(
                name="Total Messages",
                value=str(queue_info['total_messages']),
                inline=True
            )
            
            embed.add_field(
                name="Status",
                value="⏸️ Paused" if queue_info['is_paused'] else "▶️ Active",
                inline=True
            )
            
            if queue_info['next_post_time']:
                next_time = datetime.datetime.fromisoformat(queue_info['next_post_time'])
                embed.add_field(
                    name="Next Post",
                    value=f"<t:{int(next_time.timestamp())}:R>",
                    inline=True
                )
            
            # Show the first few messages
            if queue_info['next_messages']:
                queue_text = ""
                for i, msg in enumerate(queue_info['next_messages'][:5]):
                    content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                    attachments_count = len(msg['attachments'])
                    attachments_text = f" ({attachments_count} files)" if attachments_count > 0 else ""
                    queue_text += f"`{msg['id']}` - {content_preview}{attachments_text}\n"
                
                embed.add_field(
                    name="Next Messages",
                    value=queue_text or "No messages in queue",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error viewing queue: {e}")
    
    @discord.app_commands.command(name="delete_message", description="Delete a message from queue by ID")
    @discord.app_commands.describe(message_id="The ID of the message to delete")
    @checks.has_permissions(administrator=True)
    async def delete_message(self, interaction: discord.Interaction, message_id: int):
        """Deletes a message from the queue by ID"""
        try:
            success = await self.scheduler.remove_message(message_id)
            
            if success:
                embed = discord.Embed(
                    title="🗑️ Message Deleted",
                    description=f"Message with ID {message_id} has been removed from queue",
                    color=COLORS['success']
                )
            else:
                embed = discord.Embed(
                    title="❌ Message Not Found",
                    description=f"No message found with ID {message_id}",
                    color=COLORS['error']
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error deleting message: {e}")
    
    @discord.app_commands.command(name="clear_queue", description="Clear all messages from queue (requires confirmation)")
    @checks.has_permissions(administrator=True)
    async def clear_queue(self, interaction: discord.Interaction):
        """Clears the entire queue with confirmation"""
        try:
            # Create confirmation buttons
            view = ClearQueueView(self.scheduler)
            
            embed = discord.Embed(
                title="⚠️ Clear Queue Confirmation",
                description="Are you sure you want to clear the entire message queue? This action cannot be undone.",
                color=COLORS['warning']
            )
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await self.send_error(interaction, f"Error clearing queue: {e}")
    
    @discord.app_commands.command(name="pause", description="Pause message publishing")
    @checks.has_permissions(administrator=True)
    async def pause(self, interaction: discord.Interaction):
        """Pauses publications"""
        try:
            self.scheduler.config['is_paused'] = True
            await self.scheduler.save_data()
            
            embed = discord.Embed(
                title="⏸️ Publishing Paused",
                description="Message publishing has been paused",
                color=COLORS['warning']
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error pausing: {e}")
    
    @discord.app_commands.command(name="resume", description="Resume message publishing")
    @checks.has_permissions(administrator=True)
    async def resume(self, interaction: discord.Interaction):
        """Resumes publications"""
        try:
            self.scheduler.config['is_paused'] = False
            await self.scheduler.save_data()
            
            embed = discord.Embed(
                title="▶️ Publishing Resumed",
                description="Message publishing has been resumed",
                color=COLORS['success']
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error resuming: {e}")
    
    @discord.app_commands.command(name="status", description="Show bot status and configuration")
    @checks.has_permissions(administrator=True)
    async def cmd_status(self, interaction: discord.Interaction):
        """Shows the bot's status"""
        try:
            queue_info = await self.scheduler.get_queue_info()
            
            embed = discord.Embed(
                title="🤖 Bot Status",
                color=COLORS['info']
            )
            
            # Publishing channel
            channel_id = queue_info['channel_id']
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if isinstance(channel, (discord.TextChannel, discord.Thread)):
                    channel_text = channel.mention
                else:
                    channel_text = f"Channel ID: {channel_id} (not found)"
            else:
                channel_text = "Not set"
            
            embed.add_field(name="Publishing Channel", value=channel_text, inline=False)
            embed.add_field(name="Interval", value=f"{queue_info['interval_minutes']} minutes", inline=True)
            embed.add_field(name="Queue Size", value=str(queue_info['total_messages']), inline=True)
            embed.add_field(name="Status", value="⏸️ Paused" if queue_info['is_paused'] else "▶️ Active", inline=True)
            
            if queue_info['next_post_time'] and not queue_info['is_paused']:
                next_time = datetime.datetime.fromisoformat(queue_info['next_post_time'])
                embed.add_field(name="Next Post", value=f"<t:{int(next_time.timestamp())}:R>", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.send_error(interaction, f"Error getting status: {e}")
    
    @discord.app_commands.command(name="export_queue", description="Export queue to a file")
    @checks.has_permissions(administrator=True)
    async def export_queue(self, interaction: discord.Interaction):
        """Exports the queue to a file"""
        try:
            await interaction.response.defer()
            
            # Create a temporary file for export
            export_path = f"queue_export_{int(time.time())}.json"
            await self.scheduler.export_queue(export_path)
            
            # Send the file
            file = discord.File(export_path, filename=f"queue_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            embed = discord.Embed(
                title="📤 Queue Exported",
                description="Queue has been exported to a file",
                color=COLORS['success']
            )
            
            await interaction.followup.send(embed=embed, file=file)
            
            # Delete the temporary file
            os.unlink(export_path)
            
        except Exception as e:
            await self.send_error(interaction, f"Error exporting queue: {e}")
    
    @discord.app_commands.command(name="import_queue", description="Import queue from an attached file")
    @checks.has_permissions(administrator=True)
    async def import_queue(self, interaction: discord.Interaction, file: discord.Attachment):
        """Imports the queue from a file"""
        try:
            if not file.filename.endswith('.json'):
                await self.send_error(interaction, "File must be a JSON file")
                return
            
            await interaction.response.defer()
            
            # Download the file
            temp_path = f"temp_import_{int(time.time())}.json"
            await file.save(temp_path)
            
            # Import the queue
            imported_count = await self.scheduler.import_queue(temp_path)
            
            embed = discord.Embed(
                title="📥 Queue Imported",
                description=f"Successfully imported {imported_count} messages to the queue",
                color=COLORS['success']
            )
            
            await interaction.followup.send(embed=embed)
            
            # Delete the temporary file
            os.unlink(temp_path)
            
        except Exception as e:
            await self.send_error(interaction, f"Error importing queue: {e}")
    
    async def send_error(self, interaction: discord.Interaction, message: str):
        """Sends an error message"""
        embed = discord.Embed(
            title="❌ Error",
            description=message,
            color=COLORS['error']
        )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

# ================================
# VIEW CLASSES FOR INTERACTION
# ================================

class ClearQueueView(discord.ui.View):
    """View for confirming queue clearing"""
    
    def __init__(self, scheduler: MessageScheduler):
        super().__init__(timeout=30)
        self.scheduler = scheduler
    
    @discord.ui.button(label="Confirm Clear", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirms clearing the queue"""
        # Additional check to ensure the user is an administrator
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to do this.", ephemeral=True)
            return

        try:
            await self.scheduler.clear_queue()
            
            embed = discord.Embed(
                title="🗑️ Queue Cleared",
                description="All messages have been removed from the queue",
                color=COLORS['success']
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error clearing queue: {e}",
                color=COLORS['error']
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancels clearing the queue"""
        embed = discord.Embed(
            title="❌ Cancelled",
            description="Queue clearing has been cancelled",
            color=COLORS['info']
        )
        await interaction.response.edit_message(embed=embed, view=None)

# ================================
# BOT STARTUP
# ================================

async def main():
    """Main function to start the bot"""
    # Check for the token
    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: Please set your Discord bot token in the .env file as DISCORD_BOT_TOKEN!")
        return
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Discord Scheduler Bot...")
    
    # Create and run the bot
    bot = SchedulerBot()
    
    try:
        await bot.start(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided")
        print("❌ ERROR: Invalid bot token!")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"❌ ERROR: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")

    # === After running the code, don't be alarmed by the large number of messages, it's normal ===