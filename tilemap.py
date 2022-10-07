from collections import deque
from pixels import *
from fmatrix import *
import numpy as np
import json

direction2vector = [(-1,0), (0, 1), (1,0), (0,-1)]

tiles = []
with open('tile-connections.json', 'r') as fp:
    tiles = json.load(fp=fp)

b = Board(tiles)
display_matrix(b.__m__)

initial_decision_space = [8,15,16,21,28,32,38,39,48,51,63,64,65]
center = find_matrix_center(b.__m__)
b.collapse(center, decision_space = initial_decision_space)
display_matrix(b.__m__)

already_visited = set()
queue = deque()
queue.appendleft((2,2))
while len(queue) != 0:
    cell = queue.popleft()
    #print(cell)
    if (cell[0] in range(b.__m__.size) and cell[1] in range(b.__m__.size)) and (cell not in already_visited):
        road_decision_space = set(b.local_decision_space(cell)) - set(initial_decision_space)
        road_decision_space = list(road_decision_space)
        b.collapse(cell, decision_space=road_decision_space)
        already_visited.add(cell)

        cell_value = b.__m__[cell]
        tile = tiles[cell_value]
        sockets = tile['sockets']
        new_q = [tuple(np.add(direction2vector[i],cell)) for i,x in enumerate(sockets) if 'C' in x]
        queue.extend(new_q)


save_matrix(99, b.__m__)