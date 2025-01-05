import sys
from box import Timer
timer = Timer()
from box import handler, ic, ib , rel2abs, markup
import os
import platform
from unzip_url import unzip_url

def test_chromedriver_via_selenium(path_to_chromedriver, path_to_chrome):

    print(markup("[bold blue]TEST[/] [bold magenta]GET[/] [yellow]https://www.google.com[/]"))

    if any(not os.access(path, os.X_OK) for path in [path_to_chromedriver, path_to_chrome]):
        print()
        print(markup("[bold red]PERMISSION ERROR[/] Some files are not executable. Please run:"))
        print()
    for path in [path_to_chromedriver, path_to_chrome]:
        if not os.access(path, os.X_OK):
            print("    " + markup(f"[bold yellow]chmod +x {path}[/]"))
    if any(not os.access(path, os.X_OK) for path in [path_to_chromedriver, path_to_chrome]):
        sys.exit(1)

    from selenium import webdriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')

    chrome_options.binary_location = path_to_chrome
    service = webdriver.ChromeService(path_to_chromedriver)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get("https://www.google.com")

    title = driver.title
    print(f"Page title: {driver.title}")
    driver.quit()

    if title == "Google":
        print(markup("[bold green]PASSED[/]"))

def setup_chrome_testing_binaries():

    cwd = os.getcwd()
    bin_path = os.path.join(cwd, 'bin')
    if not os.path.exists(bin_path):
        os.makedirs(bin_path)
        print(f"Created {bin_path}")

    if platform.system() == 'Linux':
        os_name = 'linux64'
        binary_extension = ''
    elif platform.system() == 'Windows':
        os_name = "win64"
        binary_extension = '.exe'
    else:
        raise Exception(f"Unsupported platform: {platform.system()}")

    chromdriver_url = f"https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.76/{os_name}/chromedriver-{os_name}.zip"
    chrome_headless_shell_url = f"https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.76/{os_name}/chrome-headless-shell-{os_name}.zip"
    chromedriver_select_path = f"chromedriver-{os_name}/chromedriver" + binary_extension
    chrome_headless_shell_select_path = f"chrome-headless-shell-{os_name}/"

    # path_to_chromedriver = unzip_url(chromdriver_url, select="chromedriver-linux64/chromedriver", out_dir=bin_path)
    path_to_chromedriver = unzip_url(chromdriver_url, select=chromedriver_select_path, out_dir=bin_path)
    # path_to_chrome_directory = unzip_url(chrome_headless_shell_url, select="chrome-headless-shell-linux64/", out_dir=bin_path)
    path_to_chrome_directory = unzip_url(chrome_headless_shell_url, select=chrome_headless_shell_select_path, out_dir=bin_path)

    if path_to_chromedriver is None:
        raise Exception(f"Failed to download chromedriver: {chromdriver_url}")
    if path_to_chrome_directory is None:
        raise Exception(f"Failed to download chrome-headless-shell: {chrome_headless_shell_url}")

    path_to_chrome = os.path.join(path_to_chrome_directory, "chrome-headless-shell" + binary_extension)

    if platform.system() == 'Linux':
        os.chmod(path_to_chromedriver, 0o755)
        os.chmod(path_to_chrome, 0o755)

    print(f"Downloaded chromedriver to {path_to_chromedriver}")
    print(f"Downloaded chrome-headless-shell to {path_to_chrome}")

    return path_to_chromedriver, path_to_chrome

def main():
    path_to_chromedriver, path_to_chrome = setup_chrome_testing_binaries()
    print()
    test_chromedriver_via_selenium(path_to_chromedriver, path_to_chrome)

if __name__ == "__main__":
    main()
