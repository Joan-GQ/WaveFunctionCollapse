from __future__ import annotations
from ast import Dict
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
import random
import numpy as np

# TODO: Move this to fmatrix
########################################################################

def get_image(n:int):
    return load_image(f'./tiles-new/tile_{n}.png')

def display_matrix(m:Matrix):
    size = m.size
    canvas = Image.new(size=(7*size,7*size), mode='RGB')
    for i in range(0,size):
        for j in range(0,size):
            canvas.paste(get_image(m[j,i]), (i*7,j*7))
    plt.grid(False)
    plt.imshow(canvas)

def save_matrix(n:int, m:Matrix):
    with open(f'./progress/state-{n}.py','w') as fp:
        fp.write(str(m.rows()).replace('], ','],\n '))
        
    size = m.size
    canvas = Image.new(size=(7*size,7*size), mode='RGB')
    for i in range(0,size):
        for j in range(0,size):
            canvas.paste(get_image(m[j,i]), (i*7,j*7))
    
    canvas.save(f'./progress/state-{n}.png')

def find_matrix_center(matrix:Matrix):
    if matrix.size % 2 != 0:
        return (matrix.size//2,)*2
    else:
        raise Exception("Non odd sized matrix")

########################################################################

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


class Board:
    def __init__(self, tile_options:List[Dict]):
        # TODO: Change fixed size of 5x5
        self.__m__ = np.tile(-1, (5,5)).tolist()
        self.__m__ = Matrix(self.__m__)
        self.__options__ = tile_options
    
    def global_decision_space(self) -> List[int]:
        return list(range(len(self.__options__)))
    
    def cell_decision_space(self, pos:Tuple[int,int]) -> List[Set[int]]:
        if pos[0] not in range(self.__m__.size) or pos[1] not in range(self.__m__.size):
            cell = -1
        else:
            cell = self.__m__[pos]

        if cell == -1:
            return [set(self.global_decision_space()),
                    set(self.global_decision_space()),
                    set(self.global_decision_space()),
                    set(self.global_decision_space())]

        up_decision    = self.__options__[cell]['connections'][0]
        right_decision = self.__options__[cell]['connections'][1]
        down_decision  = self.__options__[cell]['connections'][2]
        left_decision  = self.__options__[cell]['connections'][3]

        up_decision    = set(up_decision)
        right_decision = set(right_decision)
        down_decision  = set(down_decision)
        left_decision  = set(left_decision)

        return [up_decision, right_decision, down_decision, left_decision]
    
    def local_decision_space(self, pos:Tuple[int,int]) -> Set[int]:
        y, x = pos
        up_pos    = (y-1, x+0)
        right_pos = (y+0, x+1)
        down_pos  = (y+1, x+0)
        left_pos  = (y+0, x-1)

        down_neighbour_constraint  = self.cell_decision_space(pos=down_pos)[0]
        left_neighbour_constraint  = self.cell_decision_space(pos=left_pos)[1]
        up_neighbour_constraint    = self.cell_decision_space(pos=up_pos)[2]
        right_neighbour_constraint = self.cell_decision_space(pos=right_pos)[3]

        lds = set(self.global_decision_space())
        lds &= down_neighbour_constraint
        lds &= left_neighbour_constraint
        lds &= up_neighbour_constraint
        lds &= right_neighbour_constraint

        return lds


    def collapse(self, pos:Tuple[int,int], decision_space:List[int]=None):
        if pos[0] not in  range(self.__m__.size) or pos[1] not in range(self.__m__.size):
            raise Exception("Invalid position")

        cell = self.__m__[pos]

        if cell != -1: # Collapsed cell
            return self
        else: # Uncollapsed cell
            #choice = random.choice(decision_space)
            if decision_space == None:
                choice = random.choice(list(self.local_decision_space(pos)))
            else:
                choice = random.choice(list(decision_space))
            
            self.__m__.setAt(pos = pos,
                            n    = choice)
            return self

    @DeprecationWarning
    def collapse_center(self, initial_decisions:List[int]):
        #return self.collapse(pos = find_matrix_center(self.__m__), decision_space = initial_decisions)
        pos = find_matrix_center(self.__m__)
        if pos[0] > self.__m__.size or pos[1] > self.__m__.size:
            raise Exception("Invalid position")

        cell = self.__m__[pos]

        if cell != -1: # Collapsed cell
            return self
        else: # Uncollapsed cell
            #choice = random.choice(decision_space)
            choice = random.choice(initial_decisions)
            self.__m__.setAt(pos = pos,
                            n    = choice)
            return self
    
    @DeprecationWarning
    def collapse_neighbours(self, pos:Tuple[int,int]):
        cell = self.__m__[pos]
        if cell == -1:
            raise Exception("Cannot collapse neighbours of non-collapsed cell.")
        
        # TODO: fix fmatrix reverse coordinates
        y, x = pos
        up_pos    = (y-1, x+0)
        right_pos = (y+0, x+1)
        down_pos  = (y+1, x+0)
        left_pos  = (y+0, x-1)

        # up_decision    = self.__options__[cell]['connections'][0]
        # right_decision = self.__options__[cell]['connections'][1]
        # down_decision  = self.__options__[cell]['connections'][2]
        # left_decision  = self.__options__[cell]['connections'][3]

        up_decision    = self.local_decision_space(up_pos)
        right_decision = self.local_decision_space(right_pos)
        down_decision  = self.local_decision_space(down_pos)
        left_decision  = self.local_decision_space(left_pos)

        self.collapse(pos=up_pos,    decision_space = up_decision)
        self.collapse(pos=right_pos, decision_space = right_decision)
        self.collapse(pos=down_pos,  decision_space = down_decision)
        self.collapse(pos=left_pos,  decision_space = left_decision)
        return self
    

