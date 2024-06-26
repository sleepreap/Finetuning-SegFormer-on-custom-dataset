import pytorch_lightning as pl
import torch
from pathlib import Path
torch.set_float32_matmul_precision("medium")
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from segformer import  (SegformerFinetuner, 
                        SegmentationDataModule, 
                        DATASET_DIR, 
                        BATCH_SIZE, 
                        NUM_WORKERS, 
                        ID2LABEL, 
                        LEARNING_RATE)
from torch import nn
import numpy as np
import matplotlib.pyplot as plt
import argparse
from tqdm import tqdm
from colorPalette import color_palette, apply_palette

def dataset_predictions(dataloader):
    pred_set = []
    for batch in tqdm(dataloader, desc="Doing predictions"):
        images, labels = batch['pixel_values'], batch['labels']
        outputs = model(images, labels)
        loss, logits = outputs[0], outputs[1]
        upsampled_logits = nn.functional.interpolate(
            logits,
            # Size of original image is 640x640
            size=labels.shape[-2:],
            mode="bilinear",
            align_corners=False
        )
        predicted_mask = upsampled_logits.argmax(dim=1).numpy()
        # Extend the pred_set list with each image in the batch
        for image in predicted_mask:
            pred_set.append(image)
    return pred_set


def savePredictions(pred_set, save_path):
    palette = color_palette()
    for i, image in enumerate(tqdm(pred_set, desc="Saving predictions")):
        file_name = f"result_{i}"
        colored_image = apply_palette(image, palette)
        plt.imshow(colored_image)
        plt.axis('off')  # Turn off axis numbers and ticks
        file_path = os.path.join(save_path, f"{file_name}.png")
        plt.savefig(file_path, bbox_inches='tight')
        plt.close()  # Close the figure to free memory
        
    print("Predictions saved")


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
    '--model_path',
    type=str,
    default='',
    help="Enter the path of your model.ckpt file"
    )
    parser.add_argument(
    '--save_path',
    type=str,
    default='',
    help="enter the path to save your images"
    )

    args = parser.parse_args()
    model_path = os.path.join( '..', args.model_path)
    save_path = os.path.join( '..', args.save_path)
  
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        
    data_module = SegmentationDataModule(dataset_dir=DATASET_DIR, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
    model = SegformerFinetuner.load_from_checkpoint(model_path,id2label=ID2LABEL, lr=LEARNING_RATE)
    model.eval()

    data_module.setup(stage='test')
    test_dataloader = data_module.test_dataloader()
    pred_set= dataset_predictions(test_dataloader)
    savePredictions(pred_set, save_path)
        
    
