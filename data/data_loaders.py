"""
This file contains pytorch data loaders for train, test, and validation data sets.
This dataset will be fed into efficient det.
Guide: https://medium.com/data-science-at-microsoft/training-efficientdet-on-custom-data-with-pytorch-lightning-using-an-efficientnetv2-backbone-1cdf3bd7921f
"""

# Imports
import albumentations as A
from albumentations.pytorch.transforms import ToTensorV2
from albumentations.core.bbox_utils import check_bbox
from detecto import visualize
from torch.optim import lr_scheduler
from torch.autograd import Variable
from torchvision import datasets, models, transforms
from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader, Dataset
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import torchvision
import matplotlib.pyplot as plt
import time
import os
import numpy as np
import json

from PIL import Image
from dataclasses import dataclass

# Labels
LABELS = {
    0: "short sleeve top",
    1: "long sleeve top",
    2: "short_sleeve outwear",
    3: "long sleeve outwear",
    4: "vest",
    5: "sling",
    6: "shorts",
    7: "trousers",
    8: "skirt",
    9: "short sleeve dress",
    10: "long sleeve dress",
    11: "vest dress",
    12: "sling dress",
}
LABEL_TO_CLASS = {}
for k, v in LABELS.items():
    LABEL_TO_CLASS[v] = k 

# Data locations
ROOT = "/home/rajkinra23/git/drip_vision/data/deepfashion/"
TRAIN = os.path.join(ROOT, "train")
TEST = os.path.join(ROOT, "test")
VALIDATION = os.path.join(ROOT, "validation")
DRY_RUN_TRAIN = os.path.join(ROOT, "dry_run_train")
DRY_RUN_VALIDATION = os.path.join(ROOT, "dry_run_validation")

# Helper to get the label
def get_label(label_name):
    return LABEL_TO_CLASS[label_name]

# Transforms at train time
def get_train_transforms(target_img_size=512):
    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.Resize(height=target_img_size, width=target_img_size, p=1),
            A.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ToTensorV2(p=1),
        ],
        p=1.0,
        bbox_params=A.BboxParams(
            format="pascal_voc", min_area=0, min_visibility=0, label_fields=["labels"]
        ),
    )

# Transforms at inference time
def get_valid_transforms(target_img_size=512):
    return A.Compose(
        [
            A.Resize(height=target_img_size, width=target_img_size, p=1),
            A.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ToTensorV2(p=1),
        ],
        p=1.0,
        bbox_params=A.BboxParams(
            format="pascal_voc", min_area=0, min_visibility=0, label_fields=["labels"]
        ),
    )

# Util for area of a box, make sure that it's not 0
def area(box):
    x_a, y_a, x_b, y_b = box
    area = (y_b - y_a) * (x_b - x_a)
    return area  

# Util for the area adjusted to image size
def relative_box(box, w, h):
    x_a, y_a, x_b, y_b = box
    x_a /= w
    x_b /= w
    y_a /= h
    y_b /= h
    box = (x_a, y_a, x_b, y_b)
    return box

class DeepFashionDatasetAdaptor:
    def __init__(self, root):
        # Root directory
        self.root = root
        
        # Load the images and the annotations
        self.image_root = os.path.join(root, "image")
        self.annos_root = os.path.join(root, "annos")
        self.images = list(sorted(os.listdir(self.image_root)))
        self.annotations = list(sorted(os.listdir(self.annos_root)))

    def __len__(self) -> int:
        return len(self.images)

    def get_image_and_labels_by_idx(self, index):
        # Get the image and correpsonding annotations
        img_path = os.path.join(self.image_root, self.images[index])
        anno_path = os.path.join(self.annos_root, self.annotations[index])
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        anno = json.load(open(anno_path))

        # Get the bounding box and label for each item
        boxes = []
        for k in anno:
            if k.startswith('item'):
                item = anno[k]
                box = item.get('bounding_box')

                # Round the box to be smaller than the image if it overfills 
                # This is a labeling error.
                if box[2] > w:
                    print("X label box too big! Cropping")
                    box[2] = min(box[2], w)
                if box[3] > h:
                    print("Y label box too big! Cropping")
                    box[3] = min(box[3], h)

                # Add the box if the area is non - zero
                if area(box) > 0:
                    boxes.append(box)

        # Class labels are 1 for everything
        class_labels = np.ones(len(boxes))

        # Return everything. But train on just 1 label for clothes.
        return img, torch.tensor(boxes), class_labels, index
    
    def show_image(self, index):
        # Get image, boxes, and labels
        image, bboxes, class_labels, image_id = self.get_image_and_labels_by_idx(index)

        # Convert labels to the string representation for display
        labels = ['item' for label in class_labels]
        print(bboxes, labels, image.size)
        visualize.show_labeled_image(image, bboxes, labels)
        
# Class definition for the efficient det dataset
class EfficientDetDataset(Dataset):
    def __init__(
        self, dataset_adaptor, transforms=get_valid_transforms()
    ):
        self.ds = dataset_adaptor
        self.transforms = transforms

    def __getitem__(self, index):
        (
            image,
            pascal_bboxes,
            class_labels,
            image_id,
        ) = self.ds.get_image_and_labels_by_idx(index)

        sample = {
            "image": np.array(image, dtype=np.float32),
            "bboxes": pascal_bboxes,
            "labels": class_labels,
        }

        sample = self.transforms(**sample)
        sample["bboxes"] = np.array(sample["bboxes"])
        image = sample["image"]
        labels = sample["labels"]

        _, new_h, new_w = image.shape
        sample["bboxes"][:, [0, 1, 2, 3]] = sample["bboxes"][
            :, [1, 0, 3, 2]
        ]  # convert to yxyx

        target = {
            "bboxes": torch.as_tensor(sample["bboxes"], dtype=torch.float32),
            "labels": torch.as_tensor(labels),
            "image_id": torch.tensor([image_id]),
            "img_size": (new_h, new_w),
            "img_scale": torch.tensor([1.0]),
        }

        return image, target, image_id

    def __len__(self):
        return len(self.ds)

class EfficientDetDataset(Dataset):
    def __init__(
        self, dataset_adaptor, transforms=get_valid_transforms()
    ):
        self.ds = dataset_adaptor
        self.transforms = transforms

    def __getitem__(self, index):
        (
            image,
            pascal_bboxes,
            class_labels,
            image_id,
        ) = self.ds.get_image_and_labels_by_idx(index)

        sample = {
            "image": np.array(image, dtype=np.float32),
            "bboxes": pascal_bboxes,
            "labels": class_labels,
        }

        sample = self.transforms(**sample)
        sample["bboxes"] = np.array(sample["bboxes"])
        image = sample["image"]
        labels = sample["labels"]

        _, new_h, new_w = image.shape
        sample["bboxes"][:, [0, 1, 2, 3]] = sample["bboxes"][
            :, [1, 0, 3, 2]
        ]  # convert to yxyx

        target = {
            "bboxes": torch.as_tensor(sample["bboxes"], dtype=torch.float32),
            "labels": torch.as_tensor(labels),
            "image_id": torch.tensor([image_id]),
            "img_size": (new_h, new_w),
            "img_scale": torch.tensor([1.0]),
        }

        return image, target, image_id

    def __len__(self):
        return len(self.ds)

# Lightning datamodule
class EfficientDetDataModule(LightningDataModule):
    def __init__(self,
                train_dataset_adaptor,
                validation_dataset_adaptor,
                train_transforms=get_train_transforms(target_img_size=512),
                valid_transforms=get_valid_transforms(target_img_size=512),
                num_workers=4,
                batch_size=8):     
        self.train_ds = train_dataset_adaptor
        self.valid_ds = validation_dataset_adaptor
        self.train_tfms = train_transforms
        self.valid_tfms = valid_transforms
        self.num_workers = num_workers
        self.batch_size = batch_size
        super().__init__()

    def train_dataset(self) -> EfficientDetDataset:
        return EfficientDetDataset(
            dataset_adaptor=self.train_ds, transforms=self.train_tfms
        )

    def train_dataloader(self) -> DataLoader:
        train_dataset = self.train_dataset()
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            pin_memory=True,
            drop_last=True,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn,
        )
        return train_loader

    def val_dataset(self) -> EfficientDetDataset:
        return EfficientDetDataset(
            dataset_adaptor=self.valid_ds, transforms=self.valid_tfms
        )

    def val_dataloader(self) -> DataLoader:
        valid_dataset = self.val_dataset()
        valid_loader = torch.utils.data.DataLoader(
            valid_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            pin_memory=True,
            drop_last=True,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn,
        )
        return valid_loader
    
    @staticmethod
    def collate_fn(batch):
        images, targets, image_ids = tuple(zip(*batch))
        images = torch.stack(images)
        images = images.float()

        boxes = [target["bboxes"].float() for target in targets]
        labels = [target["labels"].float() for target in targets]
        img_size = torch.tensor([target["img_size"] for target in targets]).float()
        img_scale = torch.tensor([target["img_scale"] for target in targets]).float()

        annotations = {
            "bbox": boxes,
            "cls": labels,
            "img_size": img_size,
            "img_scale": img_scale,
        }

        return images, annotations, targets, image_ids