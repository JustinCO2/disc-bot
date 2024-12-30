from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
import os
from box import rel2abs, ic

def find(filename):
    self_path = os.getcwd()
    path = None
    count = 0
    paths = []
    for root, dirs, files in os.walk(self_path):
        for file in files:
            if file == filename:
                path = os.path.join(root, file)
                count += 1
                paths.append(path)
    if count > 1:
        ic(paths)
        raise Exception(f"Multiple files found: {filename} ({count})")
    return path

def ensure_chromedriver():
    if os.path.exists("bin/chromedriver"):
        print("Chromedriver already installed")
        print("bin/chromedriver")
        return
    import requests
    import zipfile
    download_url = "https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.76/linux64/chromedriver-linux64.zip"
    response = requests.get(download_url)
    print("wget", download_url)
    if not os.path.exists("bin"):
        os.makedirs("bin", exist_ok=True)
        print("mkdir bin")

    current_dir = os.getcwd()
    os.chdir("bin")
    print("cd bin")

    with open("chromedriver-linux64.zip", "wb") as f:
        f.write(response.content)
    with zipfile.ZipFile("chromedriver-linux64.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
    print("unzip chromedriver-linux64.zip")

    os.remove("chromedriver-linux64.zip")
    print("rm chromedriver-linux64.zip")

    chromedriver_path = find("chromedriver")
    assert chromedriver_path

    os.rename(chromedriver_path, "chromedriver")
    print(f"mv {chromedriver_path} chromedriver")

    print("Set chromedriver executable")

    os.chmod("chromedriver", 0o755)
    print("chmod +x chromedriver")

    os.chdir(current_dir)
    print("cd", current_dir)

    if not find("chromedriver"):
        raise Exception("Failed to install chromedriver")

    print("bin/chromedriver")

ensure_chromedriver()
