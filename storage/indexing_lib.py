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

from models import model_api

PRODUCT_IMAGE_VECTOR_FIELD = 'product_image_vector'
ITEM_NAME_FIELD = "item_name"
IMAGE_VECTOR_DIMENSION = 512

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

# Indexer class
class Indexer():
    def __init__(self, directory):
        # Create redis connection
        self.r = Redis(host = 'localhost', port = 6379)
        
        # Create the vector index
        create_hnsw_index(self.r, PRODUCT_IMAGE_VECTOR_FIELD, IMAGE_VECTOR_DIMENSION)

        # Root directory for the images being indexed on
        self.root_dir = directory
    
    # Run indexing on all images in the specified directory
    def run_indexing(self):
        # Clip API
        clip_api = model_api.ClipAPI()

        # Populate image set
        image_ids = set(os.listdir(self.root_dir))
        m = {}
        images = []
        for image_id in image_ids:
            root = os.path.join(self.root_dir, image_id)
            for image in os.listdir(root):
                images.append(os.path.join(root, image))
                m[os.path.join(root, image)] = image_id

        # Extract the set of existing keys
        key_set = set(self.r.keys())

        # Write images to redis, if the key isn't already written
        for image in images:
            key = image
            if bytes(key, 'utf-8') not in key_set:
                print("Indexing {}".format(key))
                embedding = clip_api.get_embedding(image).cpu().detach().numpy().astype(np.float32).tobytes()
                product_id = m[image]
                item_metadata = {
                    PRODUCT_IMAGE_VECTOR_FIELD: embedding,
                    ITEM_NAME_FIELD: product_id
                }
                self.r.hset(key, mapping=item_metadata)
                print("Indexed {}".format(key))