from ..net.model import ViTSTRTransducer
import torch
import albumentations as A
import numpy as np
import plotly.io as pio
import plotly.express as px
from albumentations.pytorch import ToTensorV2
from torch.utils.data import DataLoader
from PIL import Image

pio.renderers.default = 'png'
pio.templates.default = 'plotly_dark'

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
# Mean and std used while training
MEAN = [0]
STD = [1]
RESIZE = dict(height=224, width=224)
# Transforms for evaluation
TRANSFORMS_EVAL = A.Compose([
    A.Resize(**RESIZE),
    A.Normalize(mean=MEAN, std=STD),
    ToTensorV2()
])

class Predictor:
    def __init__(self) -> None:
        """Aux class to draw images with predicted caption"""
        self.inv_normalizer = A.Normalize(
            mean=[-m/s for m, s in zip(MEAN, STD)],
            std=[1/s for s in STD]
        )
        self.transforms = TRANSFORMS_EVAL
    
    def caption_dataloader(self, dataloader: DataLoader, model: ViTSTRTransducer, n_samples=5) -> None:
        """Draw n samples from given dataloader with predicted caption

        Args:
            `dataloader` (`DataLoader`): dataloader with pairs (image, target_caption)
            `model` (`Model`): model to predict caption
            `n_samples` (`int`, optional): number of samples to draw with predicted caption. Defaults to `5`.
        """
        iter_loader = iter(dataloader)
        for _ in range(n_samples):
            img, target = next(iter_loader)
            processed_img = img[0].unsqueeze(0) # [B,C, H, W]
            target = target[0]
            orig_img = self.inv_normalizer(image=processed_img.cpu().numpy())['image'][0, 0, ...] # [H, W]
            self._show_img_with_caption(processed_img, orig_img, model, target)
            
    def caption_single_image(self, path: str, model: ViTSTRTransducer, show_img) -> str:
        """Draw image from path with predicted caption

        Args:
            `path` (`str`): path to image
            `model` (`Model`): model to predict caption

        Returns:
            `output` (`str`): predicted caption
        
        Raises:
            `ValueError`: wrong image path
        """
        try:
            orig_img = np.array(Image.open(path).convert('L')) # [H, W]
        except:
            raise ValueError(f'Wrong image path: {path}')
        processed_img = self.transforms(image=orig_img)['image'].unsqueeze(0) # [1, H, W]
        return self._show_img_with_caption(processed_img, orig_img, model, show_img=show_img)
        
    def _show_img_with_caption(
        self, 
        processed_img: torch.Tensor, 
        orig_img: np.ndarray, 
        model: ViTSTRTransducer,
        show_img: bool,
        target=None,
    ) -> str:
        """Aux func to draw image and print caption

        Args:
            `processed_img` (`torch.Tensor`): transformed image of shape `[C, H, W]`
            `orig_img` (`np.ndarray`): original image of shape `[H, W, C]`
            `model` (`Model`): model to predict caption
            
        Returns:
            `prediction` (`str`): predicted caption
        """
        prediction = model.predict(processed_img[0])
        prediction = model.vocab.decode_word(prediction)
        if show_img:
            print(f'Predicted caption: {prediction}')
            if target is not None:
                target = model.vocab.decode_word(target)
                print(f'Target caption: {target}')
            px.imshow(
                orig_img, 
                color_continuous_scale='gray'
            ).update_xaxes(
                visible=False
            ).update_yaxes(
                visible=False
            ).update_layout(
                coloraxis_showscale=False
            ).show()
        return prediction
        