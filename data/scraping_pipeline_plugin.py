"""
Given a function to scrape image urls, this class serves as a pipeline which runs the image urls
through our model api to sanity check items, crops the images, and writes to disk.
"""

import requests
import os
import shutil
import dataclasses

from models import model_api
from datetime import datetime
from data_loaders import LABELS as classification_labels
from data.mongo.schema import Product
from data.mongo.mongo_client import MongoInterface

class ScrapingPipelineAbstractClass():
    def __init__(self, labels):
        # Initialize model API's
        self.detector = model_api.EfficientDetAPI()
        self.classifier = model_api.ClipAPI()
        self.dataset_root = "/home/rajkinra23/git/drip_vision/data/scraped_product_images/"
        self.tmp_root = "/tmp/scraped_dataset/"

        # Create the tmp root if it doesn't exist (since this can get deleted by os manager)
        if not os.path.exists(self.tmp_root):
            os.mkdir(self.tmp_root)

        # Class labels for this scraper; default to the classification labels
        # in the deepfashion dataset, but probably best to supply it. 
        self.labels = labels

        # Init mongo interface
        self.mongo = MongoInterface()

    def generate_image_metadata(self):
        """This function should return a map from some kind of id associated
        with the item, and a list of images of the item

        :return: map str --> list[str]
        """
        raise NotImplementedError
    
    def desired_image_classes(self):
        """Function that returns which image classes are being mined for in this
        scraping pipeline
        """
        raise NotImplementedError
    
    def download(self, product_id, image_urls, overwrite=False):
        """Given a map of product ids to a list of image urls, verify the presence
        of clothes using model api, and download to disk. The rough pipeline

        1) Write all the images to a temp directory
        2) Iterate over images
        3) For each image, detect if there are any clothes, and verify
           these clothes are the intended image class
        4) If so, write the image to the permanent image directory
        """
        # Directory where images are permanently written, if they contain clothes
        image_directory = os.path.join(self.dataset_root, product_id)

        # Temporary directory to write images before passing through model API for verification
        # Create this if it does not exist
        tmp_image_directory = os.path.join(self.tmp_root, product_id)
        if not os.path.exists(tmp_image_directory):
            os.mkdir(tmp_image_directory)

        # If the directory exists, but we're overwriting, proceed. If the directory
        # doesn't exist, create. Otherwise, return
        if os.path.exists(image_directory):
            if overwrite:
                print("Product id {} already written".format(product_id))
                return
        os.mkdir(image_directory)

        # Write each image to the tmp directory
        counter = 0
        for image_url in image_urls:
            # Check if the image was retrieved successfully, otherwise log a failure.
            r = requests.get(image_url, stream = True)
            if r.status_code == 200:
                # Get the raw image data via requests
                r.raw.decode_content = True

                # Compute image name using the counter
                image_name = f"{product_id}_A{counter}.jpg"
                
                # Write to tmp directory
                temp_image_path = os.path.join(tmp_image_directory, image_name)
                with open(temp_image_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

                # Increment counter
                counter += 1

                # Run image through detector to find clothes
                cropped_images = self.detector.detect(temp_image_path)

                # Iterate through detected images. If we find images, add to the 
                # image paths container and write to disk.
                image_paths = []
                for i, image in enumerate(cropped_images):
                    image_class, c = self.classifier.rank_labels(image, self.labels)
                    if image_class in self.desired_image_classes() and c >= 0.6:
                        image_name = os.path.split(temp_image_path)[-1]
                        filename, extension = image_name.split(".")
                        image_name = ".".join((f"{filename}_{i}", extension))
                        image_path = os.path.join(image_directory, image_name)
                        print("Writing: {}".format(image_path))
                        image.save(image_path)
                        image_paths.append(image_path)

                # Upload product to mongodb metadata
                product = Product(
                    product_id=product_id,
                    image_urls=image_urls,
                    clothing_type="top",
                    downloaded_images=image_paths,
                    uploaded_date=datetime.now()
                )
                self.mongo.insert_product(dataclasses.asdict(product))

            else:
                print("Could not retrieve image at url: {}".format(image_url))

    def run(self):
        """Run the image downloading pipeline, end to end.
        """
        # Get a map from product id to urls
        product_id_image_url_map = self.generate_image_metadata()

        # For each product id, download images
        for product_id, image_urls in product_id_image_url_map.items():
            self.download(product_id, image_urls, overwrite=True)