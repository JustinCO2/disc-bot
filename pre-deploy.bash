sudo apt-get update
xargs -a dependencies.txt sudo apt-get install -y
python src/utils/setup_chrome_testing_binaries.py
# chmod +x bin/chromedriver
# chmod +x bin/chrome-headless-shell-linux64/chrome-headless-shell
