#!/usr/bin/env python
# coding: utf-8

import requests
import os
import re
import json
import requests
import shutil
import time
import multiprocessing as mp

from bs4 import BeautifulSoup, SoupStrainer

ROOT = 'https://www.saksfifthavenue.com/c/men/apparel/t-shirts?start={}&sz=24'
OFFSETS = list(range(0, 900, 96))

# Headers
AGENT = {"user-agent":
             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"}


# Function to get all of the shirt links.
def build_shirt_links():
    shirt_links = set()
    for offset in OFFSETS:
        url = ROOT.format(offset)
        resp = requests.get(url, headers=AGENT)
        soup = BeautifulSoup(resp.content, 'html.parser')
        for link in soup.findAll('a', attrs={'href': re.compile("/product")}):
            l = link.get('href')
            if 'product' in l:
                shirt_links.add(f"https://www.saksfifthavenue.com/{l}")
    return list(shirt_links)


# Get the metadata per shirt entry
def get_metadata(soup):
    metadata = soup.find('script', attrs={"type": "application/ld+json"})

    # Find the product code
    page_data = soup.find('script', attrs={"type": "text/javascript"})
    page_data = page_data.string.split("=")[1][:-2]

    # Find the final closing brace of the first complete json
    s = metadata.contents[0]
    left = s.index("{")
    ctr = 1
    index = left + 1
    right = None
    while index < len(s) and ctr != 0:
        if s[index] == "{":
            ctr += 1
        elif s[index] == "}":
            ctr -= 1
            right = index
        index += 1
    return s[left:right + 1], page_data

# Get the shirt link from the product page.
def get_image_links(shirt_link):
    # Curl the page and parse into bs4.
    shirt_link = f"https://www.saksfifthavenue.com/{shirt_link}"
    resp = requests.get(shirt_link, headers=AGENT)
    soup = BeautifulSoup(resp.content, 'html.parser')

    # Get the json metadata div from the soup.
    metadata, product_metadata = get_metadata(soup)
    metadata_js = json.loads(metadata)
    product_metadata_js = json.loads(product_metadata)

    # Navigate through the json for the shirt links in the media construction.
    images = metadata_js.get("image")
    product_id = product_metadata_js.get("products")[0].get("code")
    return (images, product_id)


def write_image_to_disk(image_url, dst, root):
    # Set up the image URL and filename
    filename = image_url.split("/")[-1]

    # Open the url image, set stream to True, this will return the stream content.
    r = requests.get(image_url, stream=True)

    # Check if the image was retrieved successfully
    if r.status_code == 200:

        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True

        # Open a local file with wb ( write binary ) permission.
        with open(dst, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    else:
        print('Image Couldn\'t be retreived')


def write_image_set_to_disk(image_set, product_id, dry_run=False):
    # Declare root for all images
    root = "/home/rajkinra23/git/drip_vision/data_pipeline/dataset/"

    # Create the directory for the image set, if it doesn't already exist.
    image_set_root = os.path.join(root, product_id)
    if not os.path.exists(image_set_root):

        # Write image root dir.
        print("Writing images to: {}".format(image_set_root))
        if not dry_run:
            os.mkdir(image_set_root)

        # Write images
        counter = 0
        for image_url in image_set:
            img = f"{product_id}_A{counter}.jpg"
            dst = os.path.join(image_set_root, img)
            if not dry_run:
                write_image_to_disk(image_url, dst, image_set_root)
            counter += 1

        # Return that we wrote images
        return True

    # Otherwise, we skip.
    else:
        print("Images already written to: {}".format(image_set_root))
        return False


# Multithreaded pipeline to actually grab the shirt images.
def pipeline():
    # Build shirt links
    links = build_shirt_links()
    print("Found {} shirts.".format(len(links)))

    # Get the image links and product ids. Multithreaded to avoid DDOS
    batch_size = 100
    batch_ctr = 0
    num_batches = len(links) // batch_size
    image_download_args = []

    # Multithreaded link getter
    for i in range(0, len(links), batch_size):
        thread_pool = mp.Pool(batch_size)
        batch = [(arg,) for arg in links[i:i+batch_size]]
        results = thread_pool.starmap(get_image_links, batch)
        thread_pool.close()
        thread_pool.join()
        image_download_args += results

        # Log the progress
        batch_ctr += 1
        print("Finished getting links for batch {} of {}".format(batch_ctr, num_batches))

        # Sleep to not ddos. Let's sleep 5 seconds between batches.
        time.sleep(5)

    print(f"{len(image_download_args)} args prepared")

    # Multithread image download. Control batch size so we don't ddos the server (it will also kick us out if the
    # number of RPC's is too high.
    batch_size = 100

    # For each batch, use starmap. Run the image download
    num_batches = len(image_download_args)//batch_size
    batch_ctr = 0

    print("Processing {} batches.".format(num_batches))
    for i in range(0, len(image_download_args), batch_size):
        # Process batch
        thread_pool = mp.Pool(batch_size)
        batch = image_download_args[i:i+batch_size]
        thread_pool.starmap(write_image_set_to_disk, batch)
        thread_pool.close()
        thread_pool.join()

        # Log the progress
        batch_ctr += 1
        print("Finished downloading batch {} of {}".format(batch_ctr, num_batches))

        # Sleep to not ddos. Let's sleep 5 seconds between batches.
        time.sleep(5)


if __name__ == '__main__':
    pipeline()



