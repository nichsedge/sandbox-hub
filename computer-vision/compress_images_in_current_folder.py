import os
from PIL import Image


def compress_images_in_current_folder(quality=50):
    current_folder = os.getcwd()

    for filename in os.listdir(current_folder):
        if filename.lower().endswith(("png", "jpg", "jpeg", "bmp", "gif", "tiff")):
            img_path = os.path.join(current_folder, filename)
            img = Image.open(img_path)

            # Compress and save the image
            output_path = os.path.join(current_folder, f"compress_{filename}")
            img.save(output_path, optimize=True, quality=quality)

            print(f"Compressed and saved: {output_path}")


# Run the function
compress_images_in_current_folder()
