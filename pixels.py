from __future__ import annotations
from numpy import outer

from webcolors import hex_to_rgb, CSS3_HEX_TO_NAMES
from typing import Set, List, Tuple
from PIL import Image
import copy

from pixels import *
from fmatrix import Matrix
from matplotlib import pyplot as plt
from collections import deque
from base64 import b64encode

def ib64(n:int):
    return b64encode(f'{abs(n):02x}'.encode()).decode().upper().replace('=','')

def load_image(path:str) -> Image.Image:
    return Image.open(path)

def closest_colour(requested_colour):
    min_colours = {}
    for key, name in CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

class Color:
    def __init__(self, rgb:Tuple[int,int,int]):
        self.r, self.g, self.b = rgb
        self.name = closest_colour(rgb)
        self.alias = self.name[0].lower()
    
    def asTuple(self):
        return (self.r, self.g, self.b)
    
    def asHex(self):
        return str('#%02x%02x%02x' % (self.r, self.g, self.b)).upper()

    def __repr__(self):
        return f'{self.alias}{self.asHex()}'

    def __hash__(self):
        return hash(self.asHex())

    def __eq__(self, other):
        return self.asHex() == other.asHex()

def get_pixels(image:Image.Image) -> List[List[Tuple[int,int,int]]]:
    pixels = []
    for y in range(image.height):
        row = []
        for x in range(image.width):
            pixel = image.getpixel((x,y))[:-1]
            pixel = Color(rgb=pixel)
            row.append(pixel)
        pixels.append(row)
    return pixels

class Tile:
    def __init__(self, image: str):
        self.image = load_image(image)
        self.name = image.split('/')[-1]
        self.pixels = Matrix(get_pixels(self.image))
        self.colors = set(self.pixels.flat())

        self.sockets = [
            [], # UP
            [], # RIGHT
            [], # DOWN
            []  # LEFT
        ]

        rows = self.pixels.rows()
        cols = self.pixels.columns()

        self.sockets[0] = rows[0]
        self.sockets[1] = cols[len(cols)-1]
        self.sockets[2] = rows[len(rows)-1]
        self.sockets[3] = cols[0]

    def display(self):
        plt.axis('off')
        plt.imshow(self.image)
    
    def __repr__(self):
        self.display()
        return f'<Tile {ib64(hash(self))}>'

    def rotateOneClockwise(self):
        self.image = self.image.rotate(-90)
        self.pixels = Matrix(get_pixels(self.image))
        
        dequeue = deque(self.sockets)
        dequeue.rotate(1)
        self.sockets = list(dequeue)

        return self

    def rotate(self, n:int = 1): # ALWAYS CLOCKWISE
        for i in range(n):
            self.rotateOneClockwise()
        return self
    
    def __hash__(self):
        return hash(self.pixels)
    
    def __eq__(self, other):
        return hash(self) == hash(other) 
    
    def copy(self):
        return copy.copy(self)

    def rotations(self) -> Set[Tile]:
        output = set()
        for i in range(4):
            rotation = self.rotate(1).copy()
            output.add(rotation)
        return list(output)

    def global_sockets(self, colorset:Set[Color]) -> List[List]:
        output = ['','','','']
        for i,socket in enumerate(self.sockets):
            for color in socket:
                for ref in colorset:
                    if color == ref:
                        output[i] += ref.alias

        return output

    def asDict(self) -> dict:
        output = {'name': self.name, 'sockets': self.sockets}
        return output
    
    def asGlobalDict(self, colorset:set) -> dict:
        output = {'name': self.name, 'sockets': self.global_sockets(colorset=colorset)}
        return output

class SimplifiedTile:
    def __init__(self, name:str, sockets:List[str,str,str,str]):
        self.name = name
        self.sockets = sockets
        self.connections: List[List[str]] = []
    
    def connects(self, other) -> List[bool,bool,bool,bool]:
        return [
            self.sockets[0] == other.sockets[2][::-1],
            self.sockets[1] == other.sockets[3][::-1],
            self.sockets[2] == other.sockets[0][::-1],
            self.sockets[3] == other.sockets[1][::-1],
        ]

    def asDict(self):
        obj = {
            'name':self.name,
            'sockets':self.sockets,
            'connections': [[],[],[],[]]
        }

        for i,connection in enumerate(self.connections):
            for tile in connection:
                number = int(tile.name.split('_')[1][:-4])
                obj['connections'][i].append(number)
        
        return obj