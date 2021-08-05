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

ROOT = 'https://www.saksfifthavenue.com/Men/Apparel/T-Shirts/shop/_/N-52kmqv/Ne-6lvnb5?FOLDER%3C%3Efolder_id=2534374306652711&Nao={}'
OFFSETS = [0, 150, 300, 450, 600]

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
def get_metadata(s):
    print(len(s.contents))
    return s.contents[-2].contents[5].contents[18].contents[1].contents[9].find('script',
                                                                                   type='application/json').text


# Get the shirt link from
def get_image_links(shirt_link):
    # Curl the page and parse into bs4.
    resp = requests.get(shirt_link, headers=AGENT)
    soup = BeautifulSoup(resp.content, 'html.parser')

    # Get the json metadata div from the soup.
    metadata = json.loads(get_metadata(soup))

    # Navigate through the json for the shirt links in the media construction.
    images = metadata.get('ProductDetails').get('main_products')[0].get('media').get('images')

    # Build the links from the images.
    root = "https://image.s5a.com/is/image/saks/{}"
    links = []
    for image in images:
        links.append(root.format(image))

    # Return the links
    return links


# Write a single image to disk
def write_image_to_disk(image_url, dst):
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


# Write a set of images
def write_image_set_to_disk(image_set, root="/home/rajkinra23/git/drip_vision/data_pipeline/dataset"):
    # Create the directory for the image set, if it doesn't already exist.
    image_id = image_set[0].split('/')[-1]
    image_set_root = os.path.join(root, image_id)
    if not os.path.isdir(image_set_root):
        os.mkdir(image_set_root)

        # Write images to the root
        for image_url in image_set:
            img = "{}.jpg".format(image_url.split('/')[-1])
            dst = os.path.join(image_set_root, img)
            write_image_to_disk(image_url, dst, image_set_root)

        # Return that we wrote images
        return True

    # Otherwise, we skip.
    else:
        return False


# Multithreaded pipeline to actually grab the shirt images.
def pipeline():
    # Build shirt links
    links = build_shirt_links()
    print("Found {} shirts.".format(len(links)))

    # Get the image links
    image_links = []
    for link in links[:1]:
        print(link)
        image_links.append(get_image_links(link))

    # Multithread image download. Control batch size so we don't ddos the server (it will also kick us out if the
    # number of RPC's is too high.
    batch_size = 10
    thread_pool = mp.Pool(batch_size)

    # For each batch, use starmap. Run the image grep
    num_batches = len(image_links)//batch_size
    batch_ctr = 0

    print("Processing {} batches.".format(num_batches))
    # for i in range(0, len(image_links), batch_size):
    #     # Process batch
    #     batch = image_links[i:i+batch_size]
    #     results = thread_pool.starmap(write_image_set_to_disk, batch)
    #     thread_pool.close()
    #     thread_pool.join()
    #
    #     # Log the progress
    #     print("Finished downloading batch {} of {}".format(batch_ctr, num_batches))
    #     batch_ctr += 1
    #
    #     # Sleep to not ddos. Let's sleep 5 seconds between batches.
    #     time.sleep(5)


if __name__ == '__main__':
    pipeline()



