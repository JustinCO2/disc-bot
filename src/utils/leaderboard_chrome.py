from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
from jinja2 import Environment, FileSystemLoader
from selenium.webdriver.common.by import By
import time
import sys
from box import markup
import platform

def get_player_stats(guild_data):
    def format_number(n):
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        if n >= 1_000:
            return f"{n/1_000:.2f}K"
        return str(n)

    # Convert guild member data to sorted list of player stats
    player_stats = []
    for player, data in guild_data['members'].items():
        damages = data['damages']
        total_damage = damages['rvd'] + damages['aod'] + damages['la']
        player_stats.append({
            "name": player,
            "rvd": format_number(damages['rvd']),
            "aod": format_number(damages['aod']),
            "la": format_number(damages['la']),
            "total": format_number(total_damage),
            "total_num": total_damage
        })
    
    # Sort by total damage descending (need to convert back to number first)
    player_stats.sort(key=lambda x: x["total_num"], reverse=True)
    # delete total_num
    for player in player_stats:
        del player["total_num"]
    
    if len(player_stats) < 30:
        remaining_players = 30 - len(player_stats)
        player_stats += [{ "name": "Player {player_number}".format(player_number=remaining_players + i - 1), "rvd": 0, "aod": 0, "la": 0, "total": 0 } for i in range(30 - len(player_stats))]
    return player_stats

def create_damage_board(guild_name, guild_data):
    player_stats = get_player_stats(guild_data)

    # Setup Jinja environment
    env = Environment(loader=FileSystemLoader('assets'))
    template = env.get_template('template.html')

    # Render template
    html_content = template.render(
        guild_name=guild_name,
        players=player_stats
    )

    # Save rendered template
    html_path = f"leaderboard_{guild_name}.html"
    with open(html_path, 'w') as file:
        file.write(html_content)

    # Chrome setup
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--force-device-scale-factor=2.0')  # Increase resolution

    if platform.system() == 'Windows':
        path_to_chromedriver = "bin/chromedriver.exe"
        path_to_chrome = "bin/chrome-headless-shell-win64/chrome-headless-shell.exe"
    elif platform.system() == 'Linux':
        path_to_chromedriver = "bin/chromedriver"
        path_to_chrome = "bin/chrome-headless-shell-linux64/chrome-headless-shell"
    else:
        raise Exception("Unsupported platform")

    # Check if files are executable

    if any(not os.access(path, os.X_OK) for path in [path_to_chromedriver, path_to_chrome]):
        print()
        print(markup("[bold red]PERMISSION ERROR[/] Some files are not executable. Please run:"))
        print()
    for path in [path_to_chromedriver, path_to_chrome]:
        if not os.access(path, os.X_OK):
            print("    " + markup(f"[bold yellow]chmod +x {path}[/]"))
    if any(not os.access(path, os.X_OK) for path in [path_to_chromedriver, path_to_chrome]):
        sys.exit(1)

    chrome_options.binary_location = path_to_chrome
    service = webdriver.ChromeService(path_to_chromedriver)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # driver.set_window_size(3000,800)
    # driver.execute_script("document.body.style.zoom='250%'")

    driver.get(f'file://{os.path.abspath(html_path)}')
    driver.maximize_window()

    # wait for the page to load
    while True:
        script = '''return document.fonts.status;'''
        loaded = driver.execute_script(script)
        if loaded == 'loaded':
            print('All fonts loaded')
            break
        print('Fonts still loading')
        time.sleep(.5)

    screenshot_path = f"leaderboard_{guild_name}.png"

    selector = "body"
    element = driver.find_element(By.CSS_SELECTOR, selector)
    # element.screenshot(screenshot_path)

    driver.set_window_size(element.size['width'], element.size['height'])
    driver.save_screenshot(screenshot_path)
    
    # Clean up
    driver.quit()
    
    return screenshot_path, html_path

# Test
if __name__ == "__main__":
    import json
    
    with open('data/guilds.json', 'r') as f:
        guilds_data = json.load(f)
    
    screenshot_path, html_path = create_damage_board("StarCookiez", guilds_data["StarCookiez"])
    print(f"Screenshot saved as: {screenshot_path}")
    print(f"HTML file saved as: {html_path}")
