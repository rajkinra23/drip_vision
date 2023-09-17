#!/usr/bin/env python
# coding: utf-8

# Parent directory import
import sys
sys.path.append('/home/rajkinra23/git/drip_vision/')

import requests
import re
import time

from bs4 import BeautifulSoup
from collections import defaultdict
from data.scraping_pipeline_plugin import ScrapingPipelineAbstractClass

# Constants
COOKIES = {
    'audience': 'audiences=',
    'rfx-forex-rate': 'currencyCode=USD&exchangeRate=1&quoteId=0',
    'internationalshippref': 'preferredcountry=US&preferredcurrency=USD&preferredcountryname=United%20States',
    'no-track': 'ccpa=false',
    'nordstrom': 'bagcount=0&firstname=&ispinned=False&isSocial=False&shopperattr=||0|False|-1&shopperid=a5da7973f3244fcb969a8d2f966950a9&USERNAME=',
    'nui': 'firstVisit=2023-07-10T04%3A42%3A22.280Z&geoLocation=&isModified=false&lme=false',
    'shoppertoken': 'shopperToken=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhNWRhNzk3M2YzMjQ0ZmNiOTY5YThkMmY5NjY5NTBhOSIsImF1ZCI6Imd1ZXN0IiwiaXNzIjoibm9yZHN0cm9tLWd1ZXN0LWF1dGgiLCJleHAiOjIwMDQ1ODMzNDIsInJlZnJlc2giOjE2ODg5Nzg1NDIsImp0aSI6IjI1NTJlMzJlLWYyNjQtNDAzOC05ZWQ3LTM4NzkwZGE3Njc4NSIsImlhdCI6MTY4ODk2NDE0Mn0.ZWx1sqUbBxlg6-jEREBS2FkfDqRsY19NbgTijVUB5TQ3i9o0Hp3VTH3j_kPmhWEghaBHABf85QP69txGvUUV5QCtiy8acLMxdjJ8kiO0qMY68jf7D1RFMVYsd7cd34iuSiWlkPYiavXdwQNstvczvA9-xanvfdcaH0lUOb_bddPFa26VCz5sHFYqrPpAyOFzwIg2c5paRag0C2tJU2w3Vno2KEqpd77kcZaXfM2P6aZoOr2SnUHv1DJHRtQNbthABN44vYY6n6UyG7Evrd9bOoHIFK19nJ0Fkv3zdXnfzJn4l6sHBuLcFUz_vIm-mz4-XCvV_bVLZTIdQ2OkwJlQRmI9B6PVvC_DxhtVm4_53xjAtPXuAS3eewcT1fqWq3bDpQtj4HTKL5Ded_YlMgxkTp4z46qjWiDGGP1a_MvKrjvSrvS1D9to5zH-UwxuQVRk6JpnapIR0SGcbiiDZfTeV2ah3Qcn2nvuPJZir6mjT_tRJquqNL6xX3uBMQNQXMA_0u7xdwRI3BnomxSa_znE_BF_aPR9KTGu7BoKDfjW4rIjhHDPUyk4khSDwEzt13HEN3B6sNXSVpaajt8bxfDIc0qH26hbB_5Iv_xFa55ba3CWBfzbyXjQqELP_oPxFLk-hTc8zvxJeZjBWEnS1ucdueZHnqQdQsBnwVxS0AalXfM',
    'usersession': 'CookieDomain=nordstrom.com&SessionId=87e1d63d-d236-47af-9904-4bb8619609b7',
    'experiments': 'ExperimentId=83f606f8-01d8-432c-b1f0-08281fca1c15',
    'Bd34bsY56': 'A3WUGz6JAQAAVXWEW1-iIjLHeTMONobpCfoy04GGv_66jjJ8nGPsHxhB-hzFARgFg2euchZ2wH8AAEB3AAAAAA==',
    'Ad34bsY56': 'A1mOGz6JAQAAibJUhrW579lEbdnfu_i0yV3b5PUdgFKHNQzF92yLksW9gOB2ARgFg2euchZ2wH8AAEB3AAAAAA|1|1|13db72f44826b1ae3d583acf73652750a00af2ee',
    '_uetsid': '2c8014001edc11eea8b147be3dccdfd5',
    '_uetvid': '2c803e601edc11eeba7ed947785f8736',
    '_gid': 'GA1.2.790257730.1688964148',
    '_gat_UA-107105548-20': '1',
    'client': 'viewport=2_SMALL',
    '_gcl_au': '1.1.2004934057.1688964149',
    '_gat_UA-107105548-1': '1',
    'n.com_shopperId': 'a5da7973f3244fcb969a8d2f966950a9',
    'ftr_blst_1h': '1688964150727',
    '_ga_11111111': 'GS1.1.1688964150.1.0.1688964150.0.0.0',
    '_ga': 'GA1.1.1565654462.1688964148',
    '_ga_XWLT9WQ1YB': 'GS1.1.1688964150.1.0.1688964150.60.0.0',
    '_scid': 'f86ded14-9bc1-41a2-b531-8843d95a2f09',
    '_scid_r': 'f86ded14-9bc1-41a2-b531-8843d95a2f09',
    'mp_nordstrom_com_mixpanel': '%7B%22distinct_id%22%3A%20%221893e1bb83b47c-031684712dbec8-26031b51-144000-1893e1bb83cc06%22%2C%22bc_persist_updated%22%3A%201688964151357%7D',
    'bc_invalidateUrlCache_targeting': '1688964151426',
    'FPLC': 'VbUZINxDW1bL7Ic0pL7e%2F%2Ff8OBEZHL4GtoL83hsd9rR5DxkDeBWuHLnrxlIc0d49DuDvbKSlpphOE4EYPSK4VJF3Nh2SjUOkjTJVPYFwsKAbtiBAj0dvP%2FXK%2BeahHQ%3D%3D',
    'FPID': 'FPID2.2.N4z2KLfb8StSQZSBhWifF2jU1tQmkhKOjHYwuXIiwx4%3D.1688964148',
    '_tt_enable_cookie': '1',
    '_ttp': 'db4_SZkUdpnxwd8ly9aeRhOVjoK',
    '_pin_unauth': 'dWlkPU5EWTBNbU16TVRBdFpqbGxaaTAwTVRjMkxXRTFPRE10TVdSalpqUmlNV000T1dRdw',
    'bluecoreNV': 'true',
    '_sctr': '1%7C1688886000000',
    'storemode': 'version=4&postalCode=&selectedStoreIds=&storesById=&localMarketId=&localMarketsById=',
    'session': 'FILTERSTATE=&RESULTBACK=&RETURNURL=http%3A%2F%2Fshop.nordstrom.com&SEARCHRETURNURL=http%3A%2F%2Fshop.nordstrom.com&FLSEmployeeNumber=&FLSRegisterNumber=&FLSStoreNumber=&FLSPOSType=&gctoken=&CookieDomain=&IsStoreModeActive=0&',
    'storeprefs': '|100|||2023-07-10T04:42:38.630Z',
    'forterToken': '9e3226e80a7e42ce98b0e6ef27dbc445_1688964146438__UDF43-m4_17ck',
    'trx': '5324002432795793452',
    '_imp_apg_r_': '%7B%22c%22%3A%20%22QVVBbzQ5VGZQTU1mS25DTA%3D%3DCrhmzovT1StQ44o_FrZAjjzkcl96dXJEeZNjmu37KpUt-Nq3l5FjN7ssRDACHTi1cEhe7mMyehkHAG-K05LHOYZQ3thZb0DHBcqybLES6VfuX-jBPw%3D%3D%22%2C%20%22dc%22%3A%200%2C%20%22mf%22%3A%200%7D',
}

HEADERS = {
    'authority': 'www.nordstrom.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,es;q=0.8',
    'cache-control': 'max-age=0',
    # 'cookie': 'audience=audiences=; rfx-forex-rate=currencyCode=USD&exchangeRate=1&quoteId=0; internationalshippref=preferredcountry=US&preferredcurrency=USD&preferredcountryname=United%20States; no-track=ccpa=false; nordstrom=bagcount=0&firstname=&ispinned=False&isSocial=False&shopperattr=||0|False|-1&shopperid=a5da7973f3244fcb969a8d2f966950a9&USERNAME=; nui=firstVisit=2023-07-10T04%3A42%3A22.280Z&geoLocation=&isModified=false&lme=false; shoppertoken=shopperToken=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhNWRhNzk3M2YzMjQ0ZmNiOTY5YThkMmY5NjY5NTBhOSIsImF1ZCI6Imd1ZXN0IiwiaXNzIjoibm9yZHN0cm9tLWd1ZXN0LWF1dGgiLCJleHAiOjIwMDQ1ODMzNDIsInJlZnJlc2giOjE2ODg5Nzg1NDIsImp0aSI6IjI1NTJlMzJlLWYyNjQtNDAzOC05ZWQ3LTM4NzkwZGE3Njc4NSIsImlhdCI6MTY4ODk2NDE0Mn0.ZWx1sqUbBxlg6-jEREBS2FkfDqRsY19NbgTijVUB5TQ3i9o0Hp3VTH3j_kPmhWEghaBHABf85QP69txGvUUV5QCtiy8acLMxdjJ8kiO0qMY68jf7D1RFMVYsd7cd34iuSiWlkPYiavXdwQNstvczvA9-xanvfdcaH0lUOb_bddPFa26VCz5sHFYqrPpAyOFzwIg2c5paRag0C2tJU2w3Vno2KEqpd77kcZaXfM2P6aZoOr2SnUHv1DJHRtQNbthABN44vYY6n6UyG7Evrd9bOoHIFK19nJ0Fkv3zdXnfzJn4l6sHBuLcFUz_vIm-mz4-XCvV_bVLZTIdQ2OkwJlQRmI9B6PVvC_DxhtVm4_53xjAtPXuAS3eewcT1fqWq3bDpQtj4HTKL5Ded_YlMgxkTp4z46qjWiDGGP1a_MvKrjvSrvS1D9to5zH-UwxuQVRk6JpnapIR0SGcbiiDZfTeV2ah3Qcn2nvuPJZir6mjT_tRJquqNL6xX3uBMQNQXMA_0u7xdwRI3BnomxSa_znE_BF_aPR9KTGu7BoKDfjW4rIjhHDPUyk4khSDwEzt13HEN3B6sNXSVpaajt8bxfDIc0qH26hbB_5Iv_xFa55ba3CWBfzbyXjQqELP_oPxFLk-hTc8zvxJeZjBWEnS1ucdueZHnqQdQsBnwVxS0AalXfM; usersession=CookieDomain=nordstrom.com&SessionId=87e1d63d-d236-47af-9904-4bb8619609b7; experiments=ExperimentId=83f606f8-01d8-432c-b1f0-08281fca1c15; Bd34bsY56=A3WUGz6JAQAAVXWEW1-iIjLHeTMONobpCfoy04GGv_66jjJ8nGPsHxhB-hzFARgFg2euchZ2wH8AAEB3AAAAAA==; Ad34bsY56=A1mOGz6JAQAAibJUhrW579lEbdnfu_i0yV3b5PUdgFKHNQzF92yLksW9gOB2ARgFg2euchZ2wH8AAEB3AAAAAA|1|1|13db72f44826b1ae3d583acf73652750a00af2ee; _uetsid=2c8014001edc11eea8b147be3dccdfd5; _uetvid=2c803e601edc11eeba7ed947785f8736; _gid=GA1.2.790257730.1688964148; _gat_UA-107105548-20=1; client=viewport=2_SMALL; _gcl_au=1.1.2004934057.1688964149; _gat_UA-107105548-1=1; n.com_shopperId=a5da7973f3244fcb969a8d2f966950a9; ftr_blst_1h=1688964150727; _ga_11111111=GS1.1.1688964150.1.0.1688964150.0.0.0; _ga=GA1.1.1565654462.1688964148; _ga_XWLT9WQ1YB=GS1.1.1688964150.1.0.1688964150.60.0.0; _scid=f86ded14-9bc1-41a2-b531-8843d95a2f09; _scid_r=f86ded14-9bc1-41a2-b531-8843d95a2f09; mp_nordstrom_com_mixpanel=%7B%22distinct_id%22%3A%20%221893e1bb83b47c-031684712dbec8-26031b51-144000-1893e1bb83cc06%22%2C%22bc_persist_updated%22%3A%201688964151357%7D; bc_invalidateUrlCache_targeting=1688964151426; FPLC=VbUZINxDW1bL7Ic0pL7e%2F%2Ff8OBEZHL4GtoL83hsd9rR5DxkDeBWuHLnrxlIc0d49DuDvbKSlpphOE4EYPSK4VJF3Nh2SjUOkjTJVPYFwsKAbtiBAj0dvP%2FXK%2BeahHQ%3D%3D; FPID=FPID2.2.N4z2KLfb8StSQZSBhWifF2jU1tQmkhKOjHYwuXIiwx4%3D.1688964148; _tt_enable_cookie=1; _ttp=db4_SZkUdpnxwd8ly9aeRhOVjoK; _pin_unauth=dWlkPU5EWTBNbU16TVRBdFpqbGxaaTAwTVRjMkxXRTFPRE10TVdSalpqUmlNV000T1dRdw; bluecoreNV=true; _sctr=1%7C1688886000000; storemode=version=4&postalCode=&selectedStoreIds=&storesById=&localMarketId=&localMarketsById=; session=FILTERSTATE=&RESULTBACK=&RETURNURL=http%3A%2F%2Fshop.nordstrom.com&SEARCHRETURNURL=http%3A%2F%2Fshop.nordstrom.com&FLSEmployeeNumber=&FLSRegisterNumber=&FLSStoreNumber=&FLSPOSType=&gctoken=&CookieDomain=&IsStoreModeActive=0&; storeprefs=|100|||2023-07-10T04:42:38.630Z; forterToken=9e3226e80a7e42ce98b0e6ef27dbc445_1688964146438__UDF43-m4_17ck; trx=5324002432795793452; _imp_apg_r_=%7B%22c%22%3A%20%22QVVBbzQ5VGZQTU1mS25DTA%3D%3DCrhmzovT1StQ44o_FrZAjjzkcl96dXJEeZNjmu37KpUt-Nq3l5FjN7ssRDACHTi1cEhe7mMyehkHAG-K05LHOYZQ3thZb0DHBcqybLES6VfuX-jBPw%3D%3D%22%2C%20%22dc%22%3A%200%2C%20%22mf%22%3A%200%7D',
    'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
}

ROOT =  "https://www.nordstrom.com/browse/men/clothing?page={}"
NUM_PAGES = 2

class NordstromScrapingPipeline(ScrapingPipelineAbstractClass):
    def __init__(self, labels=None):
        super(NordstromScrapingPipeline, self).__init__(labels)

    def desired_image_classes(self):
        return (0, )
    
    def generate_image_metadata(self):
        # Map from product_id to image urls
        product_id_image_url_map = defaultdict(list)

        # Iterate over pages
        for page in range(NUM_PAGES):
            # Build URL
            url = ROOT.format(page)

            # Log URL
            print("Generating image metadata for url {}".format(url))

            # Iterate over all the image tiles in the page
            resp = requests.get(url, cookies=COOKIES, headers=HEADERS)
            soup = BeautifulSoup(resp.content, 'html.parser')
            images = list(soup.findAll('div', attrs={'class': 'NMGaP'}))
            for image in images:
                tile = image.img
                src = tile["src"]
                product_id = src.split("/")[-1].split(".")[0]
                product_id_image_url_map[product_id].append(src)

            # Sleep to avoid ddos
            time.sleep(5)

        # Return map
        return product_id_image_url_map

if __name__ == '__main__':
    labels = ("clothing", "not clothing")
    pipeline = NordstromScrapingPipeline(labels=labels)
    pipeline.run()