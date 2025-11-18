import os
import logging
import webbrowser
import tkinter as tk

from dotenv import load_dotenv
import discord
from discord import app_commands, scheduled_event


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


@client.tree.command(name="sync", description="Sync slash commands (removes old duplicates)")
async def sync(interaction: discord.Interaction) -> None:
    """Manually sync slash commands to Discord"""
    # Check if command is used in allowed channel
    if not is_allowed_channel(interaction):
        await interaction.response.send_message(
            "❌ This command can only be used in the #crr-bot-test channel.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        guild_id_env = os.getenv("DISCORD_GUILD_ID")
        
        # First, sync globally to ensure global commands are up to date
        synced_global = await client.tree.sync()
        logging.info(f"Synced {len(synced_global)} command(s) globally")
        
        # Then sync to guild if guild_id is set
        if guild_id_env:
            guild_id = int(guild_id_env)
            guild = discord.Object(id=guild_id)
            client.tree.copy_global_to(guild=guild)
            synced_guild = await client.tree.sync(guild=guild)
            logging.info(f"Synced {len(synced_guild)} command(s) to guild {guild_id}")
            await interaction.followup.send(
                f"✅ Synced {len(synced_global)} global and {len(synced_guild)} guild command(s).",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"✅ Synced {len(synced_global)} command(s) globally.",
                ephemeral=True
            )
    except Exception as e:
        logging.error(f"Error syncing commands: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ Error syncing commands: {str(e)}",
            ephemeral=True
        )


def get_presets() -> dict:
    """Returns the presets dictionary"""
    return {
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
        ],
        "ow_my_balls": [
            {"type": "plextv", "query": "https://www.google.com"},
            {"type": "plextv", "query": "https://www.youtube.com"},
            {"type": "plextv", "query": "Hot Ones"},
            {"type": "plextv", "query": "https://www.github.com"}
        ],
        "sports_bar": [
            {"type": "plextv", "query": "https://www.google.com"},
            {"type": "plextv", "query": "https://www.youtube.com"},
            {"type": "plextv", "query": "Hot Ones"},
            {"type": "plextv", "query": "https://www.github.com"}
        ],
        "christmas": [
            {"type": "plextv", "query": "hallmark movies & more"},
            {"type": "plextv", "query": "sweet escapes"},
            {"type": "plextv", "query": "stingray holidayscapes"},
            {"type": "plextv", "query": "The Great Christmas Light Fight on Places & Spaces"}
        ],
        "funny": [
            {"type": "plextv", "query": "always funny"},
            {"type": "plextv", "query": "always funny"},
            {"type": "plextv", "query": "always funny"},
            {"type": "plextv", "query": "always funny"}
        ],
        "vehicles": [
            {"type": "plextv", "query": "top gear"},
            {"type": "plextv", "query": "monster jam"},
            {"type": "plextv", "query": "hot wheels action"},
            {"type": "plextv", "query": "ice road truckers"}
        ],
        "joey": [
            {"type": "plextv", "query": "hot wheels action"},
            {"type": "plextv", "query": "monster jam"},
            {"type": "plextv", "query": "kidoodle tv"},
            {"type": "plextv", "query": "pbs retro"}
        ]
    }


async def preset_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete function for preset parameter"""
    try:
        presets_dict = get_presets()
        preset_names = list(presets_dict.keys())
        
        # If no current input, return all presets; otherwise filter
        if not current:
            choices = [app_commands.Choice(name=preset, value=preset) for preset in preset_names]
        else:
            current_lower = current.lower()
            choices = [
                app_commands.Choice(name=preset, value=preset)
                for preset in preset_names
                if current_lower in preset.lower()
            ]
        return choices[:25]  # Discord limits to 25 choices
    except Exception as e:
        logging.error(f"Error in preset_autocomplete: {e}", exc_info=True)
        # Return empty list on error
        return []


@client.tree.command(name="watch", description="Change windows to preset")
@app_commands.describe(preset="Each preset will open 4 windows in a tiled arrangement")
@app_commands.autocomplete(preset=preset_autocomplete)
async def watch(interaction: discord.Interaction, preset: str) -> None:
    # Log the received preset value immediately
    logging.info(f"Watch command called with preset: '{preset}' (type: {type(preset)}, length: {len(preset) if preset else 0})")
    
    # Check if command is used in allowed channel
    if not is_allowed_channel(interaction):
        await interaction.response.send_message(
            "❌ This command can only be used in the #crr-bot-test channel.",
            ephemeral=True
        )
        return
    
    # Defer the response since this might take a moment
    await interaction.response.defer()
    
    try:
        logging.info(f"Watch command received: preset={preset}")
        # Import the function to update windows
        import asyncio
        import concurrent.futures
        
        # Run the window update in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, update_windows_to_preset, preset)
        
        logging.info(f"Watch command result: {result}")
        
        if result:
            await interaction.followup.send(
                f"✅ Windows updated to preset: **{preset}**"
            )
        else:
            await interaction.followup.send(
                f"❌ Failed to update windows. Preset '{preset}' may not exist or an error occurred."
            )
    except Exception as e:
        logging.error(f"Error in watch command: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ Error: {str(e)}"
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
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        logging.info(f"Searching Plex TV for: {search_query}")
        
        # Always navigate to about:blank first to reset the state and clear any overlays
        # This is necessary to ensure we can change window content, especially when updating existing windows
        driver.get("about:blank")
        time.sleep(1)
        
        # Now navigate to Plex TV
        driver.get("https://app.plex.tv/desktop/#!/live-tv")
        time.sleep(5)
        
        # Find the search input
        search_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "quickSearchInput"))
        )
        
        # Wait for search input to be interactable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "quickSearchInput"))
        )
        
        # Clear any existing text and type the search query
        try:
            search_input.clear()
        except Exception:
            # If clear fails, try selecting all and deleting
            search_input.send_keys(Keys.CONTROL + "a")
            search_input.send_keys(Keys.DELETE)
        
        search_input.send_keys(search_query)
        
        # Wait for search results to appear
        time.sleep(3)
        
        # Look for the first search result row first
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".SearchResultListRow-container-eOnSD1"))
        )
        
        # Now look for a play button WITHIN the first result row only
        try:
            # Try to find play button within the first result element
            play_button = first_result.find_element(By.CSS_SELECTOR, 'button[aria-label="Play"]')
            play_button.click()
            logging.info(f"Clicked play button for '{search_query}'")
            return
        except Exception:
            # Play button not found, fall back to clicking the first result (this is expected)
            pass
        
        # Fallback: Click the first search result
        first_result.click()
        logging.info(f"Clicked on '{search_query}' search result")
        
    except Exception as e:
        logging.error(f"Error during Plex search: {e}", exc_info=True)


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


def update_windows_to_preset(preset: str) -> bool:
    """Update existing 4 windows to show a new preset, or open them if they don't exist"""
    global active_drivers
    
    logging.info(f"update_windows_to_preset called with preset: {preset}")
    logging.info(f"Current active_drivers count: {len(active_drivers)}")
    
    # Check if we have 4 windows open, if not, open them
    if len(active_drivers) != 4:
        logging.info(f"Windows not open (found {len(active_drivers)}), opening new windows with preset: {preset}")
        try:
            # Open windows using the existing function (keep_alive=False so it returns immediately)
            test_browser_control_advanced(preset, keep_alive=False)
            # Wait a moment for windows to open
            import time
            time.sleep(3)
            # Check again if windows are now open
            if len(active_drivers) != 4:
                logging.error(f"Failed to open windows. Found {len(active_drivers)} windows.")
                return False
            logging.info(f"Successfully opened {len(active_drivers)} windows")
            return True
        except Exception as e:
            logging.error(f"Error opening windows: {e}", exc_info=True)
            return False
    
    # Get the presets using the shared function
    presets = get_presets()
    
    if preset not in presets:
        logging.error(f"Unknown preset: {preset}")
        return False
    
    items = presets[preset]
    
    if len(items) != 4:
        logging.error(f"Preset must have exactly 4 items, found {len(items)}")
        return False
    
    logging.info(f"Updating windows to preset: {preset}")
    
    # Update each window
    for i, (driver, item) in enumerate(zip(active_drivers, items)):
        try:
            # Check if driver is still valid
            try:
                driver.current_url  # Verify driver is still active
            except Exception as e:
                logging.error(f"Window {i+1} driver is invalid: {e}")
                return False
            
            if item["type"] == "URL":
                import time
                # Navigate to about:blank first to reset state
                try:
                    driver.get("about:blank")
                    time.sleep(1)
                except Exception:
                    pass
                # Now navigate to the target URL
                try:
                    # Try normal navigation first
                    driver.get(item["query"])
                    time.sleep(2)  # Wait for page to load
                except Exception as nav_error:
                    # If normal navigation fails (e.g., app mode), try JavaScript
                    try:
                        driver.execute_script(f"window.location.href = '{item['query']}';")
                        time.sleep(3)  # Wait for navigation
                    except Exception as js_error:
                        logging.error(f"Navigation failed for window {i+1}: {js_error}")
                        raise
                # Mute audio for windows after the first one
                if i > 0:
                    import time
                    time.sleep(1)
                    try:
                        driver.execute_script("""
                            document.querySelectorAll('audio, video').forEach(function(media) {
                                media.muted = true;
                                media.volume = 0;
                            });
                            var observer = new MutationObserver(function(mutations) {
                                document.querySelectorAll('audio, video').forEach(function(media) {
                                    if (!media.muted) {
                                        media.muted = true;
                                        media.volume = 0;
                                    }
                                });
                            });
                            observer.observe(document.body, { childList: true, subtree: true });
                        """)
                    except:
                        pass
            elif item["type"] == "plextv":
                plex_search_and_watch(driver, item["query"])
                # Mute audio for windows after the first one
                if i > 0:
                    import time
                    time.sleep(2)
                    try:
                        driver.execute_script("""
                            document.querySelectorAll('audio, video').forEach(function(media) {
                                media.muted = true;
                                media.volume = 0;
                            });
                            var observer = new MutationObserver(function(mutations) {
                                document.querySelectorAll('audio, video').forEach(function(media) {
                                    if (!media.muted) {
                                        media.muted = true;
                                        media.volume = 0;
                                    }
                                });
                            });
                            observer.observe(document.body, { childList: true, subtree: true });
                        """)
                    except:
                        pass
            
            # Small delay between window updates to avoid overwhelming the system
            import time
            time.sleep(0.5)
            
        except Exception as e:
            logging.error(f"Error updating window {i+1}: {e}", exc_info=True)
            return False
    
    # Final verification - check that all windows are still valid
    for i, driver in enumerate(active_drivers):
        try:
            driver.current_url  # Verify driver is still active
        except Exception as e:
            logging.error(f"Window {i+1} is invalid after update: {e}")
            return False
    
    logging.info(f"Successfully updated all windows to preset: {preset}")
    return True


def test_browser_control_advanced(preset="default", keep_alive=True) -> None:
    """Test function to open and control browser windows with tracking"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time
        
        print(f"Testing advanced browser control with preset: {preset}")
        
        # Get the presets using the shared function
        presets = get_presets()
        
        # Get the preset configuration
        if preset not in presets:
            print(f"Unknown preset: {preset}")
            print(f"Available presets: {', '.join(presets.keys())}")
            return
            
        items = presets[preset]
        
        print(f"Using preset '{preset}' with {len(items)} items")
        
        drivers = []
        
        # Get actual screen dimensions dynamically
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        
        # Calculate window dimensions (2x2 grid) - exactly half the screen
        window_width = screen_width // 2
        window_height = screen_height // 2
        
        print(f"Screen resolution: {screen_width}x{screen_height}")
        print(f"Window size: {window_width}x{window_height}")
        print("Opening 4 browser windows...")
        
        # Open each browser window and track it
        for i, item in enumerate(items):
            try:
                # Calculate position (2x2 grid) - no gaps, starting from top-left corner
                # Top-left: (0, 0)
                # Top-right: (window_width, 0)
                # Bottom-left: (0, window_height)
                # Bottom-right: (window_width, window_height)
                x = (i % 2) * window_width
                # Move all windows up by 8px, and bottom row windows up by additional 8px (total 16px)
                y = (i // 2) * window_height - 8 - (8 if (i // 2) == 1 else 0)
                
                # Configure Chrome options for each window (app mode removes toolbars/tabs)
                chrome_options = Options()
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Use user's Chrome profile to maintain login sessions
                # Use a simpler approach: copy only cookies to temp directories
                import os
                import tempfile
                import shutil
                # On Windows, Chrome user data is typically in AppData\Local\Google\Chrome\User Data
                chrome_user_data = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data')
                default_profile = os.path.join(chrome_user_data, 'Default')
                
                if os.path.exists(default_profile):
                    # Create a temporary user data directory for this window
                    temp_user_data = os.path.join(tempfile.gettempdir(), f'chrome_user_data_{i}')
                    temp_default_profile = os.path.join(temp_user_data, 'Default')
                    
                    # Copy essential files to maintain login sessions
                    # Always copy to ensure we have the latest cookies/storage
                    os.makedirs(temp_user_data, exist_ok=True)
                    os.makedirs(temp_default_profile, exist_ok=True)
                    try:
                        # Copy essential files for login sessions (always copy to get latest)
                        essential_files = ['Cookies', 'Preferences', 'Login Data', 'Web Data']
                        for file_name in essential_files:
                            src_file = os.path.join(default_profile, file_name)
                            if os.path.exists(src_file):
                                dst_file = os.path.join(temp_default_profile, file_name)
                                try:
                                    shutil.copy2(src_file, dst_file)
                                except Exception as e:
                                    # File might be locked, try again or skip
                                    pass
                        
                        # Copy Local Storage directory (contains localStorage data for sites)
                        local_storage_src = os.path.join(default_profile, 'Local Storage')
                        if os.path.exists(local_storage_src):
                            local_storage_dst = os.path.join(temp_default_profile, 'Local Storage')
                            # Remove existing and copy fresh
                            if os.path.exists(local_storage_dst):
                                shutil.rmtree(local_storage_dst, ignore_errors=True)
                            try:
                                shutil.copytree(local_storage_src, local_storage_dst, 
                                              ignore=shutil.ignore_patterns('*.log', 'LOCK'))
                            except Exception:
                                pass
                        
                        # Copy Session Storage directory (contains sessionStorage data)
                        session_storage_src = os.path.join(default_profile, 'Session Storage')
                        if os.path.exists(session_storage_src):
                            session_storage_dst = os.path.join(temp_default_profile, 'Session Storage')
                            # Remove existing and copy fresh
                            if os.path.exists(session_storage_dst):
                                shutil.rmtree(session_storage_dst, ignore_errors=True)
                            try:
                                shutil.copytree(session_storage_src, session_storage_dst,
                                              ignore=shutil.ignore_patterns('*.log', 'LOCK'))
                            except Exception:
                                pass
                        
                        # Copy IndexedDB directory (many modern apps use this for auth tokens)
                        indexeddb_src = os.path.join(default_profile, 'IndexedDB')
                        if os.path.exists(indexeddb_src):
                            indexeddb_dst = os.path.join(temp_default_profile, 'IndexedDB')
                            # Remove existing and copy fresh
                            if os.path.exists(indexeddb_dst):
                                shutil.rmtree(indexeddb_dst, ignore_errors=True)
                            try:
                                shutil.copytree(indexeddb_src, indexeddb_dst,
                                              ignore=shutil.ignore_patterns('*.log', 'LOCK', '*.tmp'))
                            except Exception:
                                pass
                    except Exception as e:
                        # If copy fails, just use the temp directory (will be fresh profile)
                        print(f"Warning: Could not copy profile data: {e}")
                    
                    chrome_options.add_argument(f'--user-data-dir={temp_user_data}')
                    chrome_options.add_argument(f'--profile-directory=Default')
                # If Chrome user data doesn't exist, continue without it (will use default profile)
                
                # Determine the initial URL for app mode
                # For URL types, use the target URL directly in --app to maintain app mode
                # For Plex TV, use the Plex TV URL directly in --app to maintain app mode
                if item["type"] == "URL":
                    initial_url = item["query"]
                elif item["type"] == "plextv":
                    initial_url = "https://app.plex.tv/desktop/#!/live-tv"
                else:
                    initial_url = "about:blank"
                
                # Use app mode to remove toolbars and tab bar
                chrome_options.add_argument(f"--app={initial_url}")
                # Additional flags to remove UI elements and ensure clean window
                chrome_options.add_argument("--disable-infobars")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-notifications")
                chrome_options.add_argument("--disable-features=TranslateUI")
                # Remove address bar and other UI elements
                chrome_options.add_argument("--hide-scrollbars")
                # Only mute audio for windows after the first one (index 0)
                if i > 0:
                    chrome_options.add_argument("--mute-audio")
                # Try to force app mode by disabling features that show UI
                chrome_options.add_argument("--disable-features=BrowserSwitcherUI")
                chrome_options.add_argument("--disable-features=ChromeWhatsNewUI")
                
                # Create a new driver instance for each window
                driver = webdriver.Chrome(options=chrome_options)
                
                # On Windows, we need to account for window decorations (title bar, borders)
                # Use negative offsets and size adjustments to eliminate gaps between windows
                # Windows typically has ~8px window frame, so we need to overlap windows slightly
                border_offset = -8
                horizontal_overlap = 12  # Horizontal overlap (increased by 2px from 10px)
                vertical_overlap = 8  # Vertical overlap (reduced by 4px from 10px)
                
                # Adjust position: negative offset for left/top edges
                # For right column, also offset to overlap with left column
                adjusted_x = x + border_offset if x == 0 else (x - horizontal_overlap if x == window_width else x)
                # Calculate adjusted_y based on original position (before -8 offset)
                original_y = (i // 2) * window_height
                if original_y == 0:  # Top row
                    adjusted_y = y + border_offset
                elif original_y == window_height:  # Bottom row
                    adjusted_y = y - vertical_overlap
                else:
                    adjusted_y = y
                
                # Adjust size: add extra width/height to fill gaps
                adjusted_width = window_width
                adjusted_height = window_height
                
                # Width adjustments (horizontal)
                if x == 0:  # Left edge - extend right to fill gap
                    adjusted_width += horizontal_overlap
                elif x + window_width == screen_width:  # Right edge - extend to fill screen (needs more to cover gap)
                    adjusted_width += horizontal_overlap + 10  # Extra 10px to ensure it reaches the edge and covers window frame
                elif x == window_width:  # Right column (middle) - extend right to overlap with left column
                    adjusted_width += horizontal_overlap
                
                # Height adjustments (vertical)
                if y == 0:  # Top edge - extend down to fill gap
                    adjusted_height += vertical_overlap
                elif y + window_height == screen_height:  # Bottom edge - extend to fill screen
                    adjusted_height += vertical_overlap
                elif y == window_height:  # Bottom row (middle) - extend down to overlap with top row
                    adjusted_height += vertical_overlap
                
                # Set window position and size, accounting for borders
                driver.set_window_rect(adjusted_x, adjusted_y, adjusted_width, adjusted_height)
                
                # Force the window to the exact position (sometimes Chrome doesn't respect the first call)
                time.sleep(0.2)
                driver.set_window_rect(adjusted_x, adjusted_y, adjusted_width, adjusted_height)
                
                # Handle different types of items
                if item["type"] == "URL":
                    # URL is already loaded via --app flag, just wait for it to load
                    time.sleep(2)  # Wait for page to load
                    # If this window should be muted (i > 0), mute all audio elements
                    if i > 0:
                        try:
                            driver.execute_script("""
                                // Mute all audio and video elements
                                document.querySelectorAll('audio, video').forEach(function(media) {
                                    media.muted = true;
                                    media.volume = 0;
                                });
                                // Also mute any new media elements that get added
                                var observer = new MutationObserver(function(mutations) {
                                    document.querySelectorAll('audio, video').forEach(function(media) {
                                        if (!media.muted) {
                                            media.muted = true;
                                            media.volume = 0;
                                        }
                                    });
                                });
                                observer.observe(document.body, { childList: true, subtree: true });
                            """)
                        except:
                            pass
                elif item["type"] == "plextv":
                    # For Plex TV, navigate to Plex and search
                    plex_search_and_watch(driver, item["query"])
                    # If this window should be muted (i > 0), mute all audio elements
                    if i > 0:
                        try:
                            time.sleep(2)  # Wait a bit for media to load
                            driver.execute_script("""
                                // Mute all audio and video elements
                                document.querySelectorAll('audio, video').forEach(function(media) {
                                    media.muted = true;
                                    media.volume = 0;
                                });
                                // Also mute any new media elements that get added
                                var observer = new MutationObserver(function(mutations) {
                                    document.querySelectorAll('audio, video').forEach(function(media) {
                                        if (!media.muted) {
                                            media.muted = true;
                                            media.volume = 0;
                                        }
                                    });
                                });
                                observer.observe(document.body, { childList: true, subtree: true });
                            """)
                        except:
                            pass
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
        
        # Keep the function running to prevent garbage collection (only if keep_alive is True)
        if keep_alive:
            print("Press Ctrl+C to exit (windows will stay open)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nExiting... Windows will remain open.")
        else:
            print("Windows opened successfully (keep_alive=False, returning immediately)")
                
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
            preset = sys.argv[2] if len(sys.argv) > 2 else "default"
            print(f"Testing browser control function with preset: {preset}")
            test_browser_control_advanced(preset)
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


