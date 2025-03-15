import os

categories = ["minor", "moderate", "major"]
dataset_path = "dataset"

# Create the dataset folder
if not os.path.exists(dataset_path):
    os.makedirs(dataset_path)

# Create category folders inside dataset/
for category in categories:
    category_path = os.path.join(dataset_path, category)
    if not os.path.exists(category_path):
        os.makedirs(category_path)

print("Folders created successfully!")
