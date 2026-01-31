from PIL import Image, ImageOps, ImageDraw, ImageFilter
import os
import config

def prepare_student_photo(photo_path, size=(400, 400)):
    """Creates a circular student photo with a border."""
    if not os.path.exists(photo_path):
        # Create a placeholder if photo is missing
        img = Image.new('RGBA', size, (200, 200, 200, 255))
    else:
        img = Image.open(photo_path).convert("RGBA")
        img = ImageOps.fit(img, size, centering=(0.5, 0.5))
    
    # Create circular mask
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    output = Image.new('RGBA', size, (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    
    # Add a subtle gold border around the circle
    draw_border = ImageDraw.Draw(output)
    draw_border.ellipse((0, 0) + size, outline=config.COLORS['GOLD'], width=10)
    
    return output

def add_lanyard_effect(cert_image, pos_card):
    """Draws a lanyard/strap to simulate a hanging ID card."""
    draw = ImageDraw.Draw(cert_image)
    # Drawing two lines representing the strap hanging from the top
    strap_color = (40, 40, 40) # Dark Grey/Black strap
    draw.line([(pos_card[0] + 150, 0), (pos_card[0] + 250, pos_card[1])], fill=strap_color, width=15)
    draw.line([(pos_card[0] + 450, 0), (pos_card[0] + 350, pos_card[1])], fill=strap_color, width=15)
    return cert_image
