from box import Timer

from src.utils.preprocess_damage_image import binarize_and_save_image, sharpen_and_save_image
timer = Timer()
from box import handler, ic, ib, rel2abs, markup
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
        if any(x in line.lower() for x in ["total damage", "totaldamage", "tota/damage", "tota damage"]):
            try:
                # Split on either ':' or any non-digit character
                damage_parts = re.split(r'[^0-9,]', line)
                # Take the last part that contains digits
                damage_str = next((part for part in reversed(damage_parts) if any(c.isdigit() for c in part)), '')
                if damage_str:
                    damage = int(damage_str.replace(",", ""))
            except:
                continue
    
    return {
        "boss": boss,
        "level": level,
        "damage": damage
    }

def parse_image_verbose(image_path):
    ocr = PaddleOCR(
        use_angle_cls=True, 
        lang='en',
        show_log=True
    )
    result = ocr.ocr(image_path, cls=True)
    for idx in range(len(result)):
        print(f"Predictor {idx + 1}")
        res = result[idx]
        for line in res:
            print(line)
        print()

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
    image_path = 'assets/36_highres.webp'
    parse_image(image_path)
    print()
    return


    # exclude_paths = [ "assets/guild_dmgs_from_max/13.webp", "assets/guild_dmgs_from_max/14.webp", "assets/guild_dmgs_from_max/18.webp", "assets/guild_dmgs_from_max/27.webp", "assets/guild_dmgs_from_max/29.webp", "assets/guild_dmgs_from_max/30.webp", "assets/guild_dmgs_from_max/31.webp", "assets/guild_dmgs_from_max/32.webp", "assets/guild_dmgs_from_max/33.webp", "assets/guild_dmgs_from_max/35.webp", "assets/guild_dmgs_from_max/36.webp", "assets/guild_dmgs_from_max/37.webp", "assets/guild_dmgs_from_max/38.webp", "assets/guild_dmgs_from_max/42.webp", "assets/guild_dmgs_from_max/43.webp", "assets/guild_dmgs_from_max/44.webp", "assets/guild_dmgs_from_max/45.webp", "assets/guild_dmgs_from_max/46.webp", "assets/guild_dmgs_from_max/48.webp", "assets/guild_dmgs_from_max/50.webp" ]
    # paths = [path for path in paths if path not in exclude_paths]

    paths = sorted(glob.glob('assets/guild_dmgs_from_max/*'), key=lambda x: int(x.split('/')[-1].split('.')[0]))
    # Kpaths = [ "assets/guild_dmgs_from_max/14.webp", "assets/guild_dmgs_from_max/27.webp" ]
    for path in paths:
        print(path)
        stats = parse_image(path)
        if any(value is None for value in stats.values()):
            none_keys = [key for key, value in stats.items() if value is None]
            if none_keys == [ 'level' ]:
                print(markup("[yellow][bold]WARNING[/] [yellow]Found a 'None' value in stats for keys: {}.[/] ({})".format(none_keys, path)))
            else:
                print(markup("[red][bold]ERROR[/] [red]Found a 'None' value in stats for keys: {}.[/] ({})".format(none_keys, path)))
        print()
    print(markup("[green][bold]Done![/]"))

if __name__ == "__main__":
    with handler():
        main()

# run.vim: term ++rows=100 python %
