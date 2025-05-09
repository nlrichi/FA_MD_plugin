import base64

# Convert the images to base64
with open("testImg3.jpg", "rb") as image_file:
    image1_base64 = base64.b64encode(image_file.read()).decode('utf-8')

with open("testImg4.jpg", "rb") as image_file:
    image2_base64 = base64.b64encode(image_file.read()).decode('utf-8')

# Print the formatted strings for Postman
print(f"data:image/jpeg;base64,{image1_base64}")
print("---")
print(f"data:image/jpeg;base64,{image2_base64}")