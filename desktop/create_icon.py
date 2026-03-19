"""
Generate the VetCoreSoft application icon (.ico) for the Windows exe and shortcut.

Uses Pillow to draw a simple but professional icon:
  - Blue circle background (VetCoreSoft brand color #0d6efd)
  - White cross/plus symbol (veterinary/medical)
  - Multiple sizes for Windows (16, 32, 48, 64, 128, 256)

Run: python create_icon.py
Output: vetcoresoft.ico
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon(output_path='vetcoresoft.ico'):
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Blue circle background (#0d6efd)
        margin = max(1, size // 16)
        draw.ellipse(
            [margin, margin, size - margin - 1, size - margin - 1],
            fill=(13, 110, 253, 255)
        )

        # White cross (medical/vet symbol)
        cx, cy = size // 2, size // 2
        arm_w = max(2, size // 6)       # half-width of each arm
        arm_len = max(4, size // 3)     # half-length of each arm

        # Vertical bar
        draw.rectangle(
            [cx - arm_w, cy - arm_len, cx + arm_w, cy + arm_len],
            fill=(255, 255, 255, 255)
        )
        # Horizontal bar
        draw.rectangle(
            [cx - arm_len, cy - arm_w, cx + arm_len, cy + arm_w],
            fill=(255, 255, 255, 255)
        )

        images.append(img)

    # Save as multi-size ICO
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"  [OK] Icon generated: {output_path}")


if __name__ == '__main__':
    create_icon()
