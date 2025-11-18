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

# Global variable to keep browser drivers alive
active_drivers = []


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


def plex_search_and_watch(driver, search_query: str) -> None:
    """Function to search for a show on Plex TV and click the first result using existing driver"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        print(f"Searching Plex TV for: {search_query}")
        
        # Navigate to Plex TV
        print("Navigating to Plex TV...")
        driver.get("https://app.plex.tv/desktop/#!/live-tv")
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(10)
        
        # Find the search input
        print("Looking for search input...")
        search_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "quickSearchInput"))
        )
        
        print(f"Found search input, typing '{search_query}'...")
        
        # Clear any existing text and type the search query
        search_input.clear()
        search_input.send_keys(search_query)
        
        # Wait 5 seconds for search results to appear
        print("Waiting 5 seconds for search results...")
        time.sleep(5)
        
        # Look for the first search result
        print("Looking for first search result...")
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".SearchResultListRow-container-eOnSD1"))
        )
        
        print("Found first search result, clicking it...")
        first_result.click()
        
        print(f"SUCCESS: Clicked on '{search_query}' search result!")
        
    except Exception as e:
        print(f"Error during Plex search: {e}")


def test_plex_search() -> None:
    """Test function to search for 'Hot Ones' on Plex TV and click the first result"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        import time
        
        print("Testing Plex TV search for 'Hot Ones'...")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to Plex TV
            print("Navigating to Plex TV...")
            driver.get("https://app.plex.tv/desktop/#!/live-tv")
            
            # Wait for page to load
            print("Waiting for page to load...")
            time.sleep(3)
            
            # Debug: Print page title and URL
            print(f"Page title: {driver.title}")
            print(f"Current URL: {driver.current_url}")
            
            # Find the search input
            print("Looking for search input...")
            search_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "quickSearchInput"))
            )
            
            print("Found search input, typing 'hot ones'...")
            
            # Clear any existing text and type "hot ones"
            search_input.clear()
            search_input.send_keys("hot ones")
            
            # Wait 5 seconds for search results to appear
            print("Waiting 2 seconds for search results...")
            time.sleep(2)
            
            # Look for the first search result
            print("Looking for first search result...")
            first_result = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".SearchResultListRow-container-eOnSD1"))
            )
            
            print("Found first search result, clicking it...")
            first_result.click()
            
            print("SUCCESS: First search result clicked!")
            
            # Take a screenshot after clicking
            driver.save_screenshot("plex_search_success.png")
            print("Screenshot saved as plex_search_success.png")
            
            # Keep window open for inspection
            print("Window will stay open for 30 seconds for inspection...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Error during Plex search: {e}")
            driver.save_screenshot("plex_search_error.png")
            print("Error screenshot saved as plex_search_error.png")
            
        finally:
            print("Closing browser...")
            driver.quit()
            
    except ImportError:
        print("ERROR: Selenium not installed. Install with: py -3 -m pip install selenium")
    except Exception as e:
        print(f"ERROR: Plex search failed: {e}")


def test_browser_control_advanced(preset="default") -> None:
    """Test function to open and control browser windows with tracking"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time
        
        print(f"Testing advanced browser control with preset: {preset}")
        
        # Define presets
        presets = {
            "default": [
                {"type": "URL", "query": "https://www.google.com"},
                {"type": "URL", "query": "https://www.youtube.com"},
                {"type": "URL", "query": "https://www.github.com"},
                {"type": "URL", "query": "https://www.stackoverflow.com"}
            ],
            "social": [
                {"type": "URL", "query": "https://www.facebook.com"},
                {"type": "URL", "query": "https://www.twitter.com"},
                {"type": "URL", "query": "https://www.instagram.com"},
                {"type": "URL", "query": "https://www.linkedin.com"}
            ],
            "work": [
                {"type": "URL", "query": "https://www.gmail.com"},
                {"type": "URL", "query": "https://www.calendar.google.com"},
                {"type": "URL", "query": "https://www.drive.google.com"},
                {"type": "URL", "query": "https://www.meet.google.com"}
            ],
            "news": [
                {"type": "URL", "query": "https://www.bbc.com"},
                {"type": "URL", "query": "https://www.cnn.com"},
                {"type": "URL", "query": "https://www.reuters.com"},
                {"type": "URL", "query": "https://www.npr.org"}
            ],
            "entertainment": [
                {"type": "URL", "query": "https://www.netflix.com"},
                {"type": "URL", "query": "https://www.youtube.com"},
                {"type": "URL", "query": "https://www.twitch.tv"},
                {"type": "URL", "query": "https://www.hulu.com"}
            ],
            "development": [
                {"type": "URL", "query": "https://www.github.com"},
                {"type": "URL", "query": "https://www.stackoverflow.com"},
                {"type": "URL", "query": "https://www.dev.to"},
                {"type": "URL", "query": "https://www.codepen.io"}
            ],
            "plex_test": [
                {"type": "URL", "query": "https://www.google.com"},
                {"type": "URL", "query": "https://www.youtube.com"},
                {"type": "plextv", "query": "Hot Ones"},
                {"type": "URL", "query": "https://www.github.com"}
            ]
        }
        
        # Get the preset configuration
        if preset not in presets:
            print(f"Unknown preset: {preset}")
            print(f"Available presets: {', '.join(presets.keys())}")
            return
            
        items = presets[preset]
        
        print(f"Using preset '{preset}' with {len(items)} items")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        drivers = []
        
        print("Opening 4 browser windows...")
        
        # Open each browser window and track it
        for i, item in enumerate(items):
            try:
                # Create a new driver instance for each window
                driver = webdriver.Chrome(options=chrome_options)
                
                # Position the window first (2x2 grid)
                screen_width = 1920  # You can get this dynamically
                screen_height = 1080
                window_width = screen_width // 2
                window_height = screen_height // 2
                
                x = (i % 2) * window_width
                y = (i // 2) * window_height
                
                driver.set_window_position(x, y)
                driver.set_window_size(window_width, window_height)
                
                # Handle different types of items
                if item["type"] == "URL":
                    driver.get(item["query"])
                    url = item["query"]
                elif item["type"] == "plextv":
                    # For Plex TV, use the same driver but navigate to Plex
                    plex_search_and_watch(driver, item["query"])
                    url = f"Plex TV - {item['query']}"
                else:
                    print(f"Unknown item type: {item['type']}")
                    continue
                
                drivers.append(driver)
                print(f"Opened window {i+1}: {url} at position ({x}, {y})")
                time.sleep(1)
                
            except Exception as e:
                print(f"Failed to open window {i+1}: {e}")
        
        print(f"\nSuccessfully opened {len(drivers)} windows!")
        print("Windows are now open and ready to use!")
        print("They will remain open until you manually close them.")
        
        # Keep the drivers alive by storing them globally
        global active_drivers
        active_drivers = drivers
        
        # Keep the function running to prevent garbage collection
        print("Press Ctrl+C to exit (windows will stay open)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting... Windows will remain open.")
                
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
            preset = sys.argv[2] if len(sys.argv) > 2 else "default"
            print(f"Testing advanced browser control function with preset: {preset}")
            test_browser_control_advanced(preset)
        elif sys.argv[1] == "plex":
            print("Testing Plex TV search...")
            test_plex_search()
        else:
            print("Usage: py -3 bot.py [test|control|advanced [preset]|plex]")
            print("Available presets: default, social, work, news, entertainment, development, plex_test")
    else:
        main()


