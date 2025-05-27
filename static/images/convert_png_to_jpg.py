from PIL import Image
import os

# static/images 폴더 안에 있는 .png 파일들을 .jpg로 변환
image_dir = os.path.join(os.getcwd(), "static", "images")  # 현재 경로 기준
for file in os.listdir(image_dir):
    if file.endswith(".png"):
        file_path = os.path.join(image_dir, file)
        img = Image.open(file_path)
        new_file = file.replace(".png", ".jpg")
        new_file_path = os.path.join(image_dir, new_file)
        rgb_img = img.convert("RGB")
        rgb_img.save(new_file_path)
        print(f"Converted {file} to {new_file}")
