from dataclasses import dataclass
from datetime import datetime
from typing import List
import uuid

@dataclass
class Product:
    product_id: str
    image_urls: List[str]
    clothing_type: str
    downloaded_images: List[str]
    uploaded_date: datetime

