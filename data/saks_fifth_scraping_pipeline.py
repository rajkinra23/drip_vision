#!/usr/bin/env python
# coding: utf-8

# Parent directory import
import sys
sys.path.append('/home/rajkinra23/git/drip_vision/')

import requests
import re
import requests
import time

from bs4 import BeautifulSoup
from collections import defaultdict
from data.scraping_pipeline_plugin import ScrapingPipelineAbstractClass

# Constants
ROOT = 'https://www.saksfifthavenue.com/c/men/apparel/{}?start={}'
PAGE_SIZE = 24
CATEGORIES = (
    "coats-jackets",
    "dress-shirts",
    "polos",
    "sweaters",
)
DATASET_ROOT_DESTINATION = "/home/rajkinra23/git/drip_vision/data/scraped_dataset/"
DATASET_TMP_DESTINATION = "/tmp/scraped_dataset/"

# Headers
AGENT = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"}


class SaksFifthScrapingPipeline(ScrapingPipelineAbstractClass):
    def __init__(self, labels=None):
        super(SaksFifthScrapingPipeline, self).__init__(labels)

    def desired_image_classes(self):
        return (0, )
    
    def generate_image_metadata(self):
        # Build set of product page links
        links = set()
        for category in CATEGORIES:
            offset = 0
            process = True
            while process:
                # Build URL
                url = ROOT.format(category, offset)

                # Log URL
                print("Generating image metadata for url {}".format(url))

                # Generate page links using soup and requests. If there are no links, 
                # break from this category to move to the next one.
                resp = requests.get(url, headers=AGENT)
                soup = BeautifulSoup(resp.content, 'html.parser')
                page_links = soup.findAll('a', attrs={'href': re.compile("/product"), 'class': 'link'})
                if len(page_links) == 0:
                    process = False
                for link in page_links:
                    l = link.get('href')
                    if 'product' in l:
                        links.add(f"https://www.saksfifthavenue.com/{l}")

                # Increment offset
                offset += PAGE_SIZE

                # Sleep to avoid ddos
                time.sleep(5)
            
        # Convert links into a list for indexing
        links = list(links)

        # Map from product_id to image urls
        product_id_image_url_map = defaultdict(list)

        # Iterate over links, and get images. Sleep after every 10 fetches to avoid ddosing
        batch_ctr = 0
        for i, link in enumerate(links):
            # Optionally sleep
            if i % 10 == 0:
                print("{} batches done".format(batch_ctr))
                batch_ctr += 1
                time.sleep(5)

            # Craft and get request
            resp = requests.get(link, headers=AGENT)
            soup = BeautifulSoup(resp.content, 'html.parser')

            # For each link, populate metadata
            for link in soup.find_all('div', {"class": "primary-image"}):
                for image in link.findAll('img'):
                    try:
                        product_id = image.attrs["data-adobelaunchfullsizeimageproductid"]
                        image_url = image.attrs["src"]
                        product_id_image_url_map[product_id].append(image_url)
                    except Exception as e:
                        print("Error processing image {}: {}".format(
                            image, e
                        ))

        # Return map
        return product_id_image_url_map

if __name__ == '__main__':
    labels = ("a picture of a mens top clothing", "a picture of a mens bottom clothing")
    pipeline = SaksFifthScrapingPipeline(labels=labels)
    pipeline.run()