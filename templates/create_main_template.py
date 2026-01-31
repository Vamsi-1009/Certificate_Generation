from PIL import Image, ImageDraw
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def generate_base_template():
    width, height = config.CERT_SIZE
    # Create white canvas
    template = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(template)
    
    # Draw KIET Blue Sidebar (30% width for the ID Card area)
    sidebar_width = int(width * 0.3)
    draw.rectangle([0, 0, sidebar_width, height], fill=config.COLORS['KIET_BLUE'])
    
    # Draw a gold accent line
    draw.rectangle([sidebar_width, 0, sidebar_width + 30, height], fill=config.COLORS['GOLD'])
    
    # Save the template
    output_path = config.PATHS["TEMPLATE"]
    template.save(output_path, quality=100)
    print(f"✅ Professional template generated at: {output_path}")

if __name__ == "__main__":
    generate_base_template()
