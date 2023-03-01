#!/usr/bin/env python
# coding: utf-8

# Parent directory import
import sys
sys.path.append('/home/rajkinra23/git/drip_vision/')

import requests
import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

from data.scraping_pipeline_plugin import ScrapingPipelineAbstractClass

# Constants
ROOT = 'https://www.saksfifthavenue.com/c/men/apparel/t-shirts?start={}&sz=24'
OFFSETS = list(range(0, 900, 96))
DATASET_ROOT_DESTINATION = "/home/rajkinra23/git/drip_vision/data/scraped_dataset/"
DATASET_TMP_DESTINATION = "/tmp/scraped_dataset/"

# Headers
AGENT = {"user-agent":
             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"}


class SaksFifthScrapingPipeline(ScrapingPipelineAbstractClass):
    def __init__(self):
        super(SaksFifthScrapingPipeline, self).__init__()

    def desired_image_classes(self):
        return (0, 1, 2, 3, 4)
    
    def generate_image_metadata(self):
        # Build set of product page links
        shirt_links = set()
        for offset in OFFSETS:
            url = ROOT.format(offset)
            resp = requests.get(url, headers=AGENT)
            soup = BeautifulSoup(resp.content, 'html.parser')
            for link in soup.findAll('a', attrs={'href': re.compile("/product")}):
                l = link.get('href')
                if 'product' in l:
                    shirt_links.add(f"https://www.saksfifthavenue.com/{l}")
        shirt_links = list(shirt_links)

        # Map from product_id to image urls
        product_id_image_url_map = defaultdict(list)

        # Iterate over links, and get images
        for shirt_link in shirt_links[:1]:
            resp = requests.get(shirt_link, headers=AGENT)
            soup = BeautifulSoup(resp.content, 'html.parser')

            # For each link, populate metadata
            for link in soup.find_all('div', {"class": "primary-image"}):
                for image in link.findAll('img'):
                    product_id = image.attrs["data-adobelaunchfullsizeimageproductid"]
                    image_url = image.attrs["src"]
                    product_id_image_url_map[product_id].append(image_url)

        # Return map
        return product_id_image_url_map

if __name__ == '__main__':
    pipeline = SaksFifthScrapingPipeline()
    pipeline.run()