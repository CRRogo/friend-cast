import os
import logging
import webbrowser
import tkinter as tk

from dotenv import load_dotenv
import discord
from discord import app_commands


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


class FriendCastBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        # Enable presence and members intents for streaming detection
        intents.presences = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        # Don't read environment variables here - they'll be loaded later

    async def setup_hook(self) -> None:
        # Read environment variable at runtime (after load_dotenv() has been called)
        guild_id_env = os.getenv("DISCORD_GUILD_ID")
        logging.info("DISCORD_GUILD_ID from env: %s", guild_id_env)
        
        # Prefer guild-specific sync when DISCORD_GUILD_ID is provided for instant availability
        if guild_id_env:
            try:
                guild_id = int(guild_id_env)
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logging.info("Slash commands synced to guild %s", guild_id)
                return
            except Exception as sync_error:
                logging.warning("Guild sync failed (%s), falling back to global sync", sync_error)

        await self.tree.sync()
        logging.info("Slash commands synced globally")


client = FriendCastBot()


def is_allowed_channel(interaction: discord.Interaction) -> bool:
    """Check if the command is being used in an allowed channel"""
    allowed_channel_name = "crr-bot-test"
    
    # Check if it's a guild (server) channel
    if interaction.guild is None:
        return False
    
    # Check if the channel name matches
    return interaction.channel.name == allowed_channel_name


@client.tree.command(name="ping", description="Respond with pong and latency")
async def ping(interaction: discord.Interaction) -> None:
    # Check if command is used in allowed channel
    if not is_allowed_channel(interaction):
        await interaction.response.send_message(
            "❌ This command can only be used in the #crr-bot-test channel.",
            ephemeral=True  # Only visible to the user who ran the command
        )
        return
    
    latency_ms = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! {latency_ms}ms")


@client.tree.command(name="streaming", description="Check if a user is currently streaming")
async def streaming(interaction: discord.Interaction, user: discord.Member = None) -> None:
    # Check if command is used in allowed channel
    if not is_allowed_channel(interaction):
        await interaction.response.send_message(
            "❌ This command can only be used in the #crr-bot-test channel.",
            ephemeral=True
        )
        return
    
    # If no user specified, check the command author
    if user is None:
        user = interaction.user
    
    # Check if user is streaming
    is_streaming = user.activity and user.activity.type == discord.ActivityType.streaming
    
    if is_streaming:
        stream_title = user.activity.name if user.activity.name else "Unknown"
        stream_url = user.activity.url if user.activity.url else "No URL"
        await interaction.response.send_message(
            f"🎮 **{user.display_name}** is currently streaming!\n"
            f"**Title:** {stream_title}\n"
            f"**URL:** {stream_url}"
        )
    else:
        await interaction.response.send_message(
            f"❌ **{user.display_name}** is not currently streaming."
        )


@client.tree.command(name="watch", description="Open Google.com and respond with the name of the user")
async def watch(interaction: discord.Interaction) -> None:
    # Check if command is used in allowed channel
    if not is_allowed_channel(interaction):
        await interaction.response.send_message(
            "❌ This command can only be used in the #crr-bot-test channel.",
            ephemeral=True
        )
        return
    
    # Open Google.com in the default web browser
    try:
        webbrowser.open("https://www.google.com")
        await interaction.response.send_message(
            f"Hello, **{interaction.user.display_name}**! Opening Google.com..."
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Hello, **{interaction.user.display_name}**! (Failed to open browser: {e})"
        )


def test_browser_tiling() -> None:
    """Test function to open 4 browser windows in a tiled arrangement"""
    try:
        import subprocess
        import time
        import os
        
        # Get screen dimensions
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Calculate window dimensions (2x2 grid)
        window_width = screen_width // 2
        window_height = screen_height // 2
        
        # URLs to open
        urls = [
            "https://www.google.com",
            "https://www.youtube.com", 
            "https://www.github.com",
            "https://www.stackoverflow.com"
        ]
        
        print(f"Screen resolution: {screen_width}x{screen_height}")
        print(f"Window size: {window_width}x{window_height}")
        
        # Open browsers in separate windows
        for i, url in enumerate(urls):
            # Calculate position (2x2 grid)
            x = (i % 2) * window_width
            y = (i // 2) * window_height
            
            print(f"Opening window {i+1}: {url} at position ({x}, {y})")
            
            try:
                # Method 1: Use os.startfile (Windows specific) - this was working
                os.startfile(url)
                
                # Small delay between opening windows
                time.sleep(1.0)
                
            except Exception as e:
                print(f"Failed to open {url} with os.startfile: {e}")
                try:
                    # Method 2: Use subprocess with different approach
                    subprocess.Popen([
                        "cmd", "/c", "start", "", url
                    ], shell=True)
                    time.sleep(1.0)
                except Exception as e2:
                    print(f"Failed to open {url} with subprocess: {e2}")
                    # Fallback to regular webbrowser
                    webbrowser.open(url)
                    time.sleep(1.0)
        
        print("SUCCESS: Attempted to open 4 browser windows!")
        print("Each should open in a separate window instance")
        
    except Exception as e:
        print(f"ERROR: Error opening browser windows: {e}")
    finally:
        root.destroy()


def test_browser_control_advanced() -> None:
    """Test function to open and control browser windows with tracking"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time
        
        print("Testing advanced browser control with window tracking...")
        
        # URLs to open
        urls = [
            "https://www.google.com",
            "https://www.youtube.com", 
            "https://www.github.com",
            "https://www.stackoverflow.com"
        ]
        
        # New URLs to navigate to
        new_urls = [
            "https://www.reddit.com",
            "https://www.twitter.com", 
            "https://www.linkedin.com",
            "https://www.netflix.com"
        ]
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        drivers = []
        
        print("Opening 4 browser windows...")
        
        # Open each browser window and track it
        for i, url in enumerate(urls):
            try:
                # Create a new driver instance for each window
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                
                # Position the window (2x2 grid)
                screen_width = 1920  # You can get this dynamically
                screen_height = 1080
                window_width = screen_width // 2
                window_height = screen_height // 2
                
                x = (i % 2) * window_width
                y = (i // 2) * window_height
                
                driver.set_window_position(x, y)
                driver.set_window_size(window_width, window_height)
                
                drivers.append(driver)
                print(f"Opened window {i+1}: {url} at position ({x}, {y})")
                time.sleep(1)
                
            except Exception as e:
                print(f"Failed to open window {i+1}: {e}")
        
        print(f"\nSuccessfully opened {len(drivers)} windows!")
        print("Waiting 3 seconds before changing URLs...")
        time.sleep(3)
        
        # Now change URLs in each tracked window
        print("\nChanging URLs in tracked windows...")
        for i, driver in enumerate(drivers):
            try:
                new_url = new_urls[i]
                print(f"Window {i+1}: Changing to {new_url}")
                driver.get(new_url)
                time.sleep(1)
                
            except Exception as e:
                print(f"Failed to change URL in window {i+1}: {e}")
        
        print("\nSUCCESS: All windows updated!")
        print("Press Enter to close all windows...")
        input()
        
        # Close all tracked windows
        for i, driver in enumerate(drivers):
            try:
                driver.quit()
                print(f"Closed window {i+1}")
            except Exception as e:
                print(f"Failed to close window {i+1}: {e}")
                
    except ImportError:
        print("ERROR: Selenium not installed. Install with: py -3 -m pip install selenium")
    except Exception as e:
        print(f"ERROR: Advanced browser control failed: {e}")


def main() -> None:
    configure_logging()
    load_dotenv()
    
    # Debug: Check if .env file exists and what we're reading
    import os
    env_file_path = os.path.join(os.getcwd(), '.env')
    logging.info("Looking for .env file at: %s", env_file_path)
    logging.info(".env file exists: %s", os.path.exists(env_file_path))
    
    # Debug: Show all environment variables that start with DISCORD
    discord_env_vars = {k: v for k, v in os.environ.items() if k.startswith('DISCORD')}
    logging.info("DISCORD environment variables: %s", discord_env_vars)

    token = os.getenv("DISCORD_TOKEN")
    # Allow setting DISCORD_GUILD_ID before client init, re-init if needed
    # (Client is already constructed above; env is read inside the instance.)
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN not set. Create a .env file or set env var."
        )

    # Debug: Show token length and first few characters (for troubleshooting)
    logging.info("Token length: %d characters", len(token))
    logging.info("Token starts with: %s", token[:10] + "...")
    
    client.run(token)


if __name__ == "__main__":
    import sys
    
    # Check if user wants to test browser functions
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            print("Testing browser tiling function...")
            test_browser_tiling()
        elif sys.argv[1] == "control":
            print("Testing browser control function...")
            test_browser_control()
        elif sys.argv[1] == "advanced":
            print("Testing advanced browser control function...")
            test_browser_control_advanced()
        else:
            print("Usage: py -3 bot.py [test|control|advanced]")
    else:
        main()


