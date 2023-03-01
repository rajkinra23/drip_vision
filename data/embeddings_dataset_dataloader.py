"""Util for loading data from the embeddings dataset
"""
import os
import random
from PIL import Image

# Directories
ROOT = "/home/rajkinra23/git/drip_vision/data/scraped_dataset/"
TRAIN_DIR = os.path.join(ROOT, "train")
TEST_DIR = os.path.join(ROOT, "test")

# Util to select a random image. Useful for visualizing detections
def random_test_image():
    product_ids = os.listdir(TEST_DIR)
    pid = random.choice(product_ids)
    pid_image_bucket = os.path.join(TEST_DIR, pid)
    image = random.choice(os.listdir(pid_image_bucket))
    image_full_path = os.path.join(pid_image_bucket, image)
    return Image.open(image_full_path).convert("RGB")
