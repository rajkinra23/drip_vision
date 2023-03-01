import os
import torch
import clip
import numpy as np

from models.efficient_det_model import MODEL_CHECKPOINTS_DIR, EfficientDetModel
from PIL import Image

# Wrapper class to use for inferencing at run time
class EfficientDetAPI():
    def __init__(self):
        ckpt_file = os.listdir(MODEL_CHECKPOINTS_DIR)[-1]
        ckpt_file_path = os.path.join(MODEL_CHECKPOINTS_DIR, ckpt_file)
        print(f"Using checkpoint: f{ckpt_file_path}")
        model = EfficientDetModel.load_from_checkpoint(ckpt_file_path)
        model.eval()
        self.model = model

    def detect(self, jpeg_image):
        image = Image.open(jpeg_image).convert("RGB")
        boxes, labels, _ = self.model.predict([image])
        boxes = torch.tensor(boxes[0])
        labels = labels[0]
        clothing_images = []
        for box in boxes:
            cropped_image = image.crop((int(val) for val in box))
            clothing_images.append(cropped_image)
        return clothing_images

# Wrapper class for CLIP
class ClipAPI():
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        clip_model, preprocess = clip.load("ViT-B/32", device=self.device)
        self.clip_model = clip_model
        self.preprocess = preprocess

    def rank_labels(self, image, labels):
        image = self.preprocess(image).unsqueeze(0).to(self.device)
        text = clip.tokenize(list(labels.values())).to(self.device)
        with torch.no_grad():
            logits_per_image, _ = self.clip_model(image, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        return np.argmax(probs), probs.max()