from wand.image import Image
from wand.color import Color
import os

def convert_webp_to_png_icons(webp_filepath):
    """
    Converts a WebP file to multiple PNG icon files of different sizes,
    saving them in a folder with the same base name as the WebP file.

    Args:
        webp_filepath: The full path to the input WebP file.
    """

    # Define the sizes for the output icons
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (96, 96), (128, 128), (256, 256)]

    # Get the directory and base name of the input WebP file
    input_dir = os.path.dirname(webp_filepath)
    base_name = os.path.splitext(os.path.basename(webp_filepath))[0]

    # Create the output directory with the same base name
    output_dir = os.path.join(input_dir, base_name)
    os.makedirs(output_dir, exist_ok=True)

    try:
        with Image(filename=webp_filepath) as img:
            # Convert to PNG format with transparency
            img.format = 'png'
            img.background_color = Color('transparent')
            img.alpha_channel = 'activate'

            for width, height in sizes:
                with img.clone() as i:
                    # Resize the image, maintaining aspect ratio
                    i.transform(resize=f"{width}x{height}")

                    # Create the output file path
                    output_filename = f"icon_{width}.png"
                    output_path = os.path.join(output_dir, output_filename)

                    # Save the resized image as a PNG icon
                    i.save(filename=output_path)
                    print(f"Saved {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage:
input_webp_file= r"C:\Users\gordon\Downloads\board-icon.webp"  # Replace with the actual path to your WebP file

# Get the directory of the script
script_dir = os.path.dirname(os.path.realpath(__file__))

convert_webp_to_png_icons(input_webp_file)