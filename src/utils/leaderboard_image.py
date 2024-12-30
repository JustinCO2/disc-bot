from PIL import Image, ImageDraw, ImageFont
import json

def create_damage_board(guild_name):
    # Load JSON data
    with open('data/guilds.json', 'r') as f:
        data = json.load(f)
    
    # Get guild members and their damages
    members = data[guild_name]['members']
    
    # Convert to list and sort by LA damage
    member_list = []
    max_name_length = 0
    max_rvd_length = len("RVD")
    max_aod_length = len("AOD")
    max_la_length = len("LA")
    max_total_length = len("Total")

    for name, info in members.items():
        max_name_length = max(max_name_length, len(name))
        damages = info['damages']
        total = (damages['rvd'] + damages['aod'] + damages['la']) / 1_000_000_000
        
        # Calculate max lengths for each column including the "B" suffix
        rvd = f"{damages['rvd'] / 1_000_000_000:.2f}B"
        aod = f"{damages['aod'] / 1_000_000_000:.2f}B"
        la = f"{damages['la'] / 1_000_000_000:.2f}B"
        total_str = f"{total:.2f}B"
        
        max_rvd_length = max(max_rvd_length, len(rvd))
        max_aod_length = max(max_aod_length, len(aod))
        max_la_length = max(max_la_length, len(la))
        max_total_length = max(max_total_length, len(total_str))
        
        member_list.append({
            'name': name,
            'rvd': damages['rvd'] / 1_000_000_000,
            'aod': damages['aod'] / 1_000_000_000,
            'la': damages['la'] / 1_000_000_000,
            'total': total
        })
    
    # Sort by LA damage descending
    member_list.sort(key=lambda x: x['la'], reverse=True)
    
    # Image settings
    width = 600
    row_height = 20
    top_padding = 80     # Space for title, header, and separator
    bottom_padding = 20  # Space after the last row
    height = top_padding + (len(member_list) * row_height) + bottom_padding  # Dynamic height with padding
    background_color = (25, 25, 25)
    background_color = (255, 255, 255)
    text_color = (255, 255, 255)
    header_color = (255, 255, 255)
    text_color = (0, 0, 0)
    header_color = (0, 0, 0)
    
    # Create image with antialiasing
    img = Image.new('RGB', (width, height), background_color)
    img = img.convert('L').convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Try to load font (use Inter font from assets)
    try:
        # SourceCodePro: [b'ExtraLight', b'Light', b'Regular', b'Medium', b'SemiBold', b'Bold', b'ExtraBold', b'Black']
        font = ImageFont.truetype("assets/SourceCodePro-VariableFont_wght.ttf", 20)
        font.set_variation_by_name("Regular")

        bold_font = ImageFont.truetype("assets/SourceCodePro-VariableFont_wght.ttf", 20)
        bold_font.set_variation_by_name("Bold")
    except:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
        print("Failed to load Inter font, using default font")
    # Draw title
    draw.text((20, 10), f"{guild_name} DMG Board", fill=text_color, font=font, stroke_width=0)
    
    # Draw header
    header = f"{'#':<2}   {'Name':<{max_name_length}}  {'RVD':<{max_rvd_length-1}} {'AOD':<{max_aod_length-1}} {'LA':<{max_la_length-1}} {'Total':<{max_total_length-1}}"
    draw.text((20, 40), header, fill=header_color, font=bold_font, stroke_width=0)
    draw.text((20, 60), "─" * (max_name_length + max_rvd_length + max_aod_length + max_la_length + max_total_length + 8), fill=header_color, font=font, stroke_width=0)
    
    # Draw member rows
    y = 80
    for i, member in enumerate(member_list, 1):
        row = f"{i:>2} {member['name']:<{max_name_length}}  {member['rvd']:>{max_rvd_length-1}.2f}B {member['aod']:>{max_aod_length-1}.2f}B {member['la']:>{max_la_length-1}.2f}B {member['total']:>{max_total_length-1}.2f}B"
        draw.text((20, y), row, fill=text_color, font=font, stroke_width=0)
        y += 20
    
    return img

# Create and save the image
img = create_damage_board("StarCookiez")
img.save("damage_board.png")
print("Done")
