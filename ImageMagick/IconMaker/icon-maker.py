from wand.image import Image
from wand.color import Color
import os
import tempfile

def convert_webp_to_png_icons(webp_filepath):
    """
    Converts a WebP file to an intermediate PNG, then to multiple PNG icon files of different sizes,
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

    # Create a temporary file for the intermediate PNG
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_png:
        temp_png_path = tmp_png.name

        try:
            # First, convert WebP to a temporary PNG file
            with Image(filename=webp_filepath) as img:
                img.format = 'png'
                img.background_color = Color('transparent')
                if not img.alpha_channel:
                    img.alpha_channel = 'activate'  # Ensure alpha channel
                img.save(filename=temp_png_path)
                print(f"Saved temporary PNG: {temp_png_path}")

            # Then, create icons from the temporary PNG
            with Image(filename=temp_png_path) as img:
                for width, height in sizes:
                    with img.clone() as i:
                        i.transform(resize=f"{width}x{height}")

                        if i.width == 0 or i.height == 0:
                            print(f"Warning: Image has invalid dimensions after resizing to {width}x{height}. Skipping.")
                            continue

                        output_path = os.path.join(output_dir, f"icon_{width}.png")
                        i.save(filename=output_path)
                        print(f"Saved {output_path}")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Clean up the temporary PNG file
            os.remove(temp_png_path)
            print(f"Deleted temporary file: {temp_png_path}")

# Example usage:
input_webp_file = r"C:\Users\gordon\Downloads\board-icon.webp"  # Replace with the actual path to your WebP file
convert_webp_to_png_icons(input_webp_file)