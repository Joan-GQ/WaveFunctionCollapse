import os
import PIL
from PIL import Image
import pathlib

upscale = 25
tiles = []
pathlib.Path('./big').mkdir(parents=True, exist_ok=True)
for tile in os.listdir('./'):
    filename = f'./{tile}'
    if filename[-3:] == 'png':
        image = Image.open(filename)
        image = image.resize((image.width*upscale,image.height*upscale), resample=Image.NEAREST)
        image.save(f'./big/{tile}.png')