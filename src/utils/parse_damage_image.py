from box import Timer
timer = Timer()
from box import handler, ic, ib, rel2abs
from paddleocr import PaddleOCR
import time
import glob
import re

def should_print_line(line):
    line = line.lower()
    keywords = "Living Abyss Red Velvet Dragon Avatar Of Destiny Lv Total Damage".lower().split()
    if any(keyword in line for keyword in keywords):
        return True
    return False

def parse_damage_stats(lines):
    BOSS_NAMES = [
        "Living Abyss",
        "Avatar of Destiny",
        "Red Velvet Dragon"
    ]
    
    boss = None
    level = None
    damage = None
    
    for line in lines:
        line = line.strip()
        # Check for boss name
        for boss_name in BOSS_NAMES:
            if boss_name.lower() in line.lower() and "Lv." not in line and "HP" not in line:
                boss = boss_name
                break
                
        # Handle various level formats
        if any(x in line for x in ["Lv.", "LV.", "Lv ", "LV "]):
            try:
                # Extract numbers from the line
                numbers = re.findall(r'\d+', line)
                if numbers:
                    level = int(numbers[0])
            except:
                continue
                
        # Handle various damage formats
        if any(x in line.lower() for x in ["total damage", "totaldamage"]):
            try:
                # Remove any non-numeric characters except commas
                damage_str = ''.join(c for c in line.split(":")[-1] if c.isdigit() or c == ',')
                damage = int(damage_str.replace(",", ""))
            except:
                continue
    
    return {
        "boss": boss,
        "level": level,
        "damage": damage
    }


def parse_image(image_path):
    start_time = time.time()
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False) # need to run only once to download and load model into memory
    result = ocr.ocr(image_path, cls=True)
    lines = []
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            if not should_print_line(line[1][0]):
                continue
            text, confidence = line[-1]
            lines.append(text)
    print(lines)
    stats = parse_damage_stats(lines)
    print(stats)
    time_taken = time.time() - start_time
    print(f"Time taken: {time_taken:.2f}s")
    return stats

def main():
    # image_path = 'assets/living-abyss-damage-sample.png'
    # parse_image(image_path)
    paths = sorted(glob.glob('assets/guild_dmgs/*'))
    for path in paths:
        print(path)
        parse_image(path)
        print()

if __name__ == "__main__":
    with handler():
        main()

# run.vim: term ++rows=100 python %
