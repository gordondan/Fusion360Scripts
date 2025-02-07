#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(
        description="Generate Fusion 360 icon files using ImageMagick."
    )
    parser.add_argument(
        "input_image",
        help="Path to the starting image file (e.g., a PNG file)."
    )
    parser.add_argument(
        "destination",
        nargs="?",
        default="./resources",
        help="Destination directory for the output icons (default: ./resources)"
    )
    args = parser.parse_args()

    input_image = args.input_image
    dest_dir = args.destination

    # Verify the input image exists.
    if not os.path.isfile(input_image):
        print(f"Error: Input image file '{input_image}' not found.")
        sys.exit(1)

    # Create the destination directory if it doesn't exist.
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
            print(f"Created destination directory: {dest_dir}")
        except Exception as e:
            print(f"Error: Could not create destination directory '{dest_dir}'.\n{e}")
            sys.exit(1)

    # Define the icon files and their target sizes.
    # Fusion 360 typically expects at least a small and a large icon, along with optional @2x (retina) versions.
    icons = [
        ("SmallIcon.png", "16x16"),
        ("SmallIcon@2x.png", "32x32"),
        ("LargeIcon.png", "32x32"),
        ("LargeIcon@2x.png", "64x64")
    ]

    # Process each icon using ImageMagick.
    for filename, size in icons:
        output_path = os.path.join(dest_dir, filename)
        # Build the ImageMagick command.
        # Using the "magick" command which is standard for recent ImageMagick installations.
        cmd = ["magick", "convert", input_image, "-resize", size, output_path]
        print(f"Generating {filename} ({size}) ...")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as err:
            print(f"Error: Failed to generate {filename}.")
            print("Command:", " ".join(cmd))
            sys.exit(1)

    print(f"Icon files generated successfully in: {os.path.abspath(dest_dir)}")

if __name__ == "__main__":
    main()
