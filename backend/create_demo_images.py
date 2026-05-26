from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("demo_images", exist_ok=True)

img1 = Image.new("RGB", (400, 400), "white")
d1 = ImageDraw.Draw(img1)
d1.polygon([(200, 50), (350, 300), (50, 300)], fill="black", outline="black")
img1.save("demo_images/star.png")

img2 = Image.new("RGB", (400, 400), "white")
d2 = ImageDraw.Draw(img2)
d2.text((50, 150), "HELLO", fill="black")
img2.save("demo_images/text.png")

img3 = Image.new("RGB", (400, 400), "white")
d3 = ImageDraw.Draw(img3)
d3.ellipse([100, 100, 300, 300], fill="red", outline="darkred", width=3)
d3.ellipse([150, 150, 250, 250], fill="white")
img3.save("demo_images/circle.png")

print("Demo images created")
