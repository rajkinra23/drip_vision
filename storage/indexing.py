# Start connecting to redis to get storage
# Reference doc - https://github.com/RedisAI/vecsim-demo/blob/master/VisualSearch1k.ipynb

import numpy as np
import random
import numpy as np
import pandas as pd
import time
import clip
import torch
import os
from redis import Redis
from redis.commands.search.field import VectorField
from redis.commands.search.field import TextField
from redis.commands.search.field import TagField
from redis.commands.search.query import Query
from PIL import Image

PRODUCT_IMAGE_VECTOR_FIELD = 'product_image_vector'
ITEM_NAME_FIELD = "item_name"
IMAGE_VECTOR_DIMENSION = 512

# Clip model init
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)

# Util to get the embedding for an image
def get_embedding(image):
    image_input = clip_preprocess(Image.open(image)).unsqueeze(0).to(device)
    image_features = clip_model.encode_image(image_input)
    return image_features

# Util function to create hnsw index
def create_hnsw_index(r, name, vector_dimensions=512):
    try:
        schema = []
        schema.append(VectorField(name, "HNSW", {"TYPE": "FLOAT32", "DIM": vector_dimensions, "DISTANCE_METRIC": "L2"}))
        schema.append(TextField("item_name"))
        r.ft().create_index(schema)
    except Exception as e:
        print("Creating index failed; it probably exists?")
        print("Exception: {}".format(e))
    
# Run indexing on all images
def run_indexing(r):
    # Populate image set
    train_dir = "/home/rajkinra23/git/drip_vision/data/embeddings_dataset/train/"
    image_ids = set(os.listdir(train_dir))
    m = {}
    images = []
    for image_id in image_ids:
        root = os.path.join(train_dir, image_id)
        for image in os.listdir(root):
            images.append(os.path.join(root, image))
            m[os.path.join(root, image)] = image_id

    # Write images to redis
    # Write data to redis
    for image in images:
        embedding = get_embedding(image).cpu().detach().numpy().astype(np.float32).tobytes()
        key = image
        product_id = m[image]
        item_metadata = {
            PRODUCT_IMAGE_VECTOR_FIELD: embedding,
            ITEM_NAME_FIELD: product_id
        }
        r.hset(key, mapping=item_metadata)

if __name__ == "__main__":
    # Create redis connection
    r = Redis(host = 'localhost', port = 6379)
    
    # Create the hnsw index
    create_hnsw_index(r, PRODUCT_IMAGE_VECTOR_FIELD, IMAGE_VECTOR_DIMENSION)

    # Load vectors
    run_indexing(r)