from box import Timer
timer = Timer()
from box import handler, ic, ib , rel2abs, markup
import time
import glob
import re
import json
import hashlib
import os
from pathlib import Path
import numpy as np
import cv2

# Configuration
CACHE_DIR = "cache/ocr_results"
USE_CACHE = True  # Feature flag for caching

def get_image_hash(image_path):
    """Generate a hash for the image file"""
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_cache_path(image_hash):
    """Get the path for the cached results"""
    # Create cache directory if it doesn't exist
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{image_hash}.json")

def save_to_cache(image_hash, result):
    """Save OCR results to cache"""
    cache_path = get_cache_path(image_hash)
    with open(cache_path, 'w') as f:
        json.dump(result, f)

def load_from_cache(image_hash):
    """Load OCR results from cache"""
    cache_path = get_cache_path(image_hash)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None

def parse_raw(image_path):
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=True)
    result = ocr.ocr(image_path, cls=True)
    lines = [line[1][0] for line in result]
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line)

def pretty_print_box(box):
    # box sample: [[[138.0, 36.0], [462.0, 36.0], [462.0, 77.0], [138.0, 77.0]]
    (top_left, top_right, bottom_right, bottom_left) = box
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = box

    x_min = min(x1, x2, x3, x4)
    x_max = max(x1, x2, x3, x4)
    y_min = min(y1, y2, y3, y4)
    y_max = max(y1, y2, y3, y4)

    # Validation checks
    assert x_min < x_max, f"Invalid x coordinates: min ({x_min}) >= max ({x_max})"
    assert y_min < y_max, f"Invalid y coordinates: min ({y_min}) >= max ({y_max})"
    
    # Additional geometric checks
    assert abs(y1 - y2) < (y_max - y_min), "Top edge is not roughly horizontal"
    assert abs(y3 - y4) < (y_max - y_min), "Bottom edge is not roughly horizontal"
    assert abs(x1 - x4) < (x_max - x_min), "Left edge is not roughly vertical"
    assert abs(x2 - x3) < (x_max - x_min), "Right edge is not roughly vertical"

    pretty_string_flat = {
        "left": x_min,
        "right": x_max,
        "top": y_min,
        "bottom": y_max,
        "top_left": (x1, y1),
        "top_right": (x2, y2),
        "bottom_right": (x3, y3),
        "bottom_left": (x4, y4),
    }
    
    print(f"{box} => {pretty_string_flat}")

def get_central_box(image_path, use_cache=USE_CACHE):
    """Extract the central participants table region"""
    from PIL import Image
    
    # Get image dimensions
    dimensions = get_image_height_and_width(image_path)
    center_x = dimensions["width"] / 2
    print(f"Image center x={center_x}")
    
    result = perform_ocr(image_path)
    
    # Find all occurrences of "Participants" (case insensitive)
    participant_boxes = []
    for line in result[0]:  # result[0] contains all text lines
        box = line[0]
        text = line[1][0]
        if "participants" in text.lower():
            x_center = sum(point[0] for point in box) / len(box)  # Average x coordinate
            distance_from_center = abs(x_center - center_x)
            box_str = f"'{text}' at x={x_center:.1f}, distance={distance_from_center:.1f}"
            participant_boxes.append((box, x_center, distance_from_center, box_str))
    
    # Find all occurrences of player
    player_boxes = []
    for line in result[0]:
        box = line[0]
        text = line[1][0]
        if "player" in text.lower():
            left_x = min(point[0] for point in box)
            box_str = f"'{text}' at x={left_x:.1f}"
            player_boxes.append((box, left_x, box_str))
    
    # Find all occurrences of member/leader/officer
    role_boxes = []
    for line in result[0]:
        box = line[0]
        text = line[1][0].lower()
        if any(role in text for role in ["member", "leader", "officer"]):
            bottom_y = max(point[1] for point in box)
            right_x = max(point[0] for point in box)
            box_str = f"'{text}' at y={bottom_y:.1f}, x={right_x:.1f}"
            role_boxes.append((box, bottom_y, right_x, box_str))
    
    # Print candidates (in original order)
    print("\nParticipant candidates:")
    selected_participant = min(participant_boxes, key=lambda x: x[2]) if participant_boxes else None
    assert selected_participant is not None, "No participant boxes found"
    for box, x_center, distance, box_str in participant_boxes:
        if box == selected_participant[0]:  # Selected one
            print(markup(f"[green]→ {box_str}[/]"))
        else:
            print(f"  {box_str}")
    
    print("\nPlayer candidates:")
    selected_player = min(player_boxes, key=lambda x: x[1]) if player_boxes else None
    assert selected_player is not None, "No player boxes found"
    for box, left_x, box_str in player_boxes:
        if box == selected_player[0]:  # Selected one (leftmost)
            print(markup(f"[green]→ {box_str}[/]"))
        else:
            print(f"  {box_str}")
            
    print("\nRole candidates:")
    selected_role = max(role_boxes, key=lambda x: x[1]) if role_boxes else None
    assert selected_role is not None, "No role boxes found"
    for box, bottom_y, right_x, box_str in role_boxes:
        if box == selected_role[0]:  # Selected one (bottom-most)
            print(markup(f"[green]→ {box_str}[/]"))
        else:
            print(f"  {box_str}")
    
    # Process results
    if participant_boxes and role_boxes and player_boxes:
        # Get top from middle participant
        middle_box = selected_participant[0]
        top = min(point[1] for point in middle_box)
        
        # Get bottom and right from lowest role text
        bottom_box, bottom_y, right_x, _ = selected_role
        
        # Get left from leftmost player text
        left_box = selected_player[0]
        left = min(point[0] for point in left_box)
        
        # Add padding
        bottom_padding = 50
        right_padding = 30
        left_padding = -30  # Negative to extend left
        bottom = bottom_y + bottom_padding
        right = right_x + right_padding
        left = left + left_padding
        
        # Open and crop the image
        img = Image.open(image_path)
        # Crop using all coordinates
        cropped = img.crop((left, top, right, bottom))
        output_path = "cache/central_box.jpg"
        cropped.save(output_path)
        print(f"\nSaved central box to {output_path} (top={top:.1f}, bottom={bottom:.1f}, left={left:.1f}, right={right:.1f})")
        
        return output_path
    
    return None

def perform_ocr(image_path, use_cache=USE_CACHE):
    """Perform OCR on an image with optional caching"""
    if use_cache:
        # Try to load from cache first
        image_hash = get_image_hash(image_path)
        cached_result = load_from_cache(image_hash)
        if cached_result is not None:
            print("Using cached OCR results")
            return cached_result

        # No cache found, perform OCR and cache results
        print("No cache found, running OCR")
        result = _run_ocr(image_path)
        save_to_cache(image_hash, result)
        return result
    
    # Cache disabled
    print("Cache disabled, running OCR")
    return _run_ocr(image_path)

def _run_ocr(image_path):
    """Internal function to run PaddleOCR"""
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    return ocr.ocr(image_path, cls=True)

def parse_total_damage_image(image_path, use_cache=USE_CACHE):
    """Parse the total damage image into table data"""
    result = perform_ocr(image_path)
    
    # Initialize data
    rows = {}  # Dictionary to store rows by y-coordinate
    y_padding = 30  # Pixels to pad above and below rank y-coordinate
    header_y = None  # Store header row y-coordinate
    
    # First pass: find all rank positions and header
    rank_positions = []
    for line in result[0]:
        box = line[0]
        text = line[1][0]
        y_coord = max(point[1] for point in box)
        x_coord = min(point[0] for point in box)
        
        if text.lower() in ["rank", "member", "leader", "officer"]:
            print(f"\nFound rank '{text}' at x={x_coord:.1f}, y={y_coord:.1f}")
            if text.lower() == "rank":  # This is the header row
                header_y = y_coord
            else:
                rank_positions.append(y_coord)
    
    # Second pass: assign text to rows based on y-coordinate proximity
    header_parts = {}  # Store header parts by x-coordinate
    avatar_of_found = False  # Flag to track if we've handled "Avatar of Destiny"
    
    for line in result[0]:
        box = line[0]
        text = line[1][0]
        
        # Get box coordinates
        y_bottom = max(point[1] for point in box)
        y_top = min(point[1] for point in box)
        x_left = min(point[0] for point in box)
        
        # Handle header row specially
        if abs(y_bottom - header_y) <= y_padding:
            # Handle "Avatar of Destiny" special case
            header_parts[x_left] = text
            continue
        
        # Find closest rank position
        for rank_y in rank_positions:
            if (rank_y - y_padding) <= y_bottom <= (rank_y + y_padding):
                if rank_y not in rows:
                    rows[rank_y] = []
                rows[rank_y].append((x_left, text))
                print(f"  Adding '{text}' (y={y_top:.1f}-{y_bottom:.1f}) to row at y={rank_y:.1f}")
                break
    
    # Print header
    header_texts = [text for _, text in sorted(header_parts.items())]
    print("\nHeader row:")
    print(" | ".join(header_texts))
    
    # Print data rows
    print("\nData rows:")
    for rank_y in sorted(rows.keys()):
        # Sort by x coordinate
        sorted_row = sorted(rows[rank_y], key=lambda x: x[0])
        texts = [item[1] for item in sorted_row]
        print(f"Row at y={rank_y:.1f}: {' | '.join(texts)}")

def get_image_height_and_width(image_path):
    from PIL import Image
    image = Image.open(image_path)
    width, height = image.size
    return { "height": height, "width": width }

def single_image_runner(image_path, use_cache=USE_CACHE):
    print(image_path)
    height_and_width = get_image_height_and_width(image_path)
    print(height_and_width)
    success = False

    cropped_image_path = get_central_box(image_path)
    assert cropped_image_path is not None, "Failed to extract central box"
    height_and_width = get_image_height_and_width(image_path)
    print("cropped", height_and_width)

    parse_total_damage_image(cropped_image_path, use_cache)

def main():
    image_path = "assets/total_dmgs/Screenshot_2024-10-09-02-10-01-903_com.devsisters.ck.jpg"
    single_image_runner(image_path)
    print(markup("[green bold]Done.[/]"))

if __name__ == "__main__":
    with handler():
        main()

# run.vim: term ++rows=100 python %
