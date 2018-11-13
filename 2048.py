#!/usr/bin/python3

# Choose a python env that has Pygame installed!

from __future__ import print_function

import pygame, sys
import random
from builtins import range
from copy import copy

from time import sleep

def color(val):
    return wavelength_to_rgb(700.0 - 20*val)

def cmp(a, b):
    return (a>b)-(a<b)

def wavelength_to_rgb(wavelength, gamma=0.8):

    '''This converts a given wavelength of light to an 
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 375 nm through 750 nm
    (800 THz through 400 THz).

    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    '''

    wavelength = float(wavelength)
    if wavelength >= 375 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 375)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0

    return (int(255*R), int(255*G), int(255*B))

### SETUP ###

SIZE = (4,4)
ANIMSPEED = 0.45
MAXITERS = int(max(SIZE)/ANIMSPEED) + 1
FPS = 60

#  colors:
BGCOLOR = (64,64,64)
EMPTYCOLOR = (0,0,0)
NUMCOLOR = (249,247,234)
HURRAY = (255,255,0)

UP = pygame.K_UP
DOWN = pygame.K_DOWN
LEFT = pygame.K_LEFT
RIGHT = pygame.K_RIGHT

TILESIZE = 100
BORDER = 16
BOARDX = SIZE[0] * (TILESIZE + BORDER) + BORDER
BOARDY = SIZE[1] * (TILESIZE + BORDER) + BORDER

tileColor = dict((i,color(i)) for i in range(21))

if len(sys.argv) > 2:
    SIZE = (int(sys.argv[1]), int(sys.argv[2]))



def pixel(vec):
    tilesize = TILESIZE + BORDER
    x = BORDER + vec[0] * tilesize
    y = BORDER + vec[1] * tilesize
    return (x,y)


class Tile(object):
    def __init__(self, col, row, val=0):
        self.pos = self.target = (col, row)
        self.val = self.targetval = val
        self.delta = None
        
    @property
    def str(self):
        prefix, p = divmod(self.val, 10)
        char = ''
        if prefix==1: char='k'
        elif prefix==2: char='M'
        elif prefix==3: char='G'
        return str(2**p) + char

    def update(self):
        if self.val!=self.targetval:
            self.val = self.targetval
            return (2**(self.val-1) if self.val!=0 else 0)
        return 0

    def move(self, v=ANIMSPEED):
        pos = self.pos
        tg = self.target

        if pos == tg:
            self.delta = None
            return True

        # first time: set delta
        if self.delta==None:
            self.delta = (v * cmp(tg[0], pos[0]), v * cmp(tg[1], pos[1]))

        if abs(tg[0]-pos[0] + tg[1] - pos[1]) < v:
            self.pos = self.target
            self.delta = None
            return True
        else:
            self.pos = (pos[0] + self.delta[0], pos[1] + self.delta[1])
            return False


    def draw(self):
        x, y = pixel(self.pos)
        size = TILESIZE
        if self.val!=self.targetval:
            off = BORDER/2
            x -= off
            y -= off
            size += 2*off

        tile = (x, y, size, size)
        DISPLAY.fill(tileColor[self.val], tile)

        textsize = tilefont.size(self.str)
        borderx = (TILESIZE - textsize[0])/2
        bordery = (TILESIZE - textsize[1])/3
        text = tilefont.render(self.str, True, NUMCOLOR)
        DISPLAY.blit(text, (x+borderx, y+bordery))


class Board(object):
    def __init__(self, ncols=4, nrows=4):
        self.ncols = ncols
        self.nrows = nrows
        self.tiles = []
        self.points = 0
        self.canUndo = False

    def getempty(self):
        empty = set(divmod(i, self.nrows) for i in range(self.ncols * self.nrows))
        empty -= set(t.pos for t in self.tiles)
        return list(empty)

    def rows(self, reverse=False):
        lines = [[] for i in range(self.nrows)]
        for t in self.tiles:
            lines[t.pos[1]].append(t)

        for line in lines:
            line.sort(key=lambda t:t.pos[0], reverse=reverse)
            yield line

    def cols(self, reverse=False):
        lines = [[] for i in range(self.ncols)]
        for t in self.tiles:
            lines[t.pos[0]].append(t)

        for line in lines:
            line.sort(key=lambda t:t.pos[1], reverse=reverse)
            yield line

    def add(self, num=1):
        empty = self.getempty()
        for i in range(num):
            if len(empty)==0:
                return False
            c, r = random.choice(empty)
            empty.remove((c,r))
            val = 1 if random.random() < 0.8 else 2
            self.tiles.append(Tile(c, r, val))
            self.points += 2**val
        return True

    def move(self, key):
        self.prevtiles = [copy(t) for t in self.tiles]
        self.prevpoints = self.points
        self.canUndo = True
        self.settarget(key)

        # animation
        allready = False
        while not allready:
            #allready = all(t.move() for t in self.tiles) # gives bumpy performance?
            allready = True
            for t in self.tiles:
                allready &= t.move()

            self.draw()

        hurray = None
        for t in self.tiles:
            points = t.update()
            if points>511:
                hurray = t.str

        if hurray:
            self.draw()
            self.hurray('Hurray! '+hurray)
            sleep(1)
            

        self.tiles = [t for t in self.tiles if t.val!=0]
        num = self.ncols*self.nrows // 16
        OK = self.add(num)
        print(self.points, 'points')
        return OK

    def undo(self):
        if self.canUndo:
            self.tiles = self.prevtiles
            self.points = self.prevpoints
            self.canUndo = False
            print(self.points, 'points')
            self.draw()


    def settarget(self, key):
        if key==UP:
            lines = self.cols(reverse=False)
            coord = lambda t, idx: (t.pos[0], idx) 
        elif key==DOWN:
            lines = self.cols(reverse=True)
            coord = lambda t, idx: (t.pos[0], self.nrows-1-idx) 
        elif key==LEFT:
            lines = self.rows(reverse=False)
            coord = lambda t, idx: (idx, t.pos[1]) 
        elif key==RIGHT:
            lines = self.rows(reverse=True)
            coord = lambda t, idx: (self.ncols-1-idx, t.pos[1]) 
        else:
            print('Unknown Key:', key)
            return
        
        for line in lines:
            tprev = None
            idx = 0
            for tile in line:
                if tprev and tprev.val==tile.val:
                    # move this tile and delete it later
                    tile.target = tprev.target
                    tprev.targetval += 1
                    tile.targetval = 0
                    tprev = None
                else:
                    tile.target = coord(tile, idx)
                    tprev = tile
                    idx += 1

    def draw(self):
        DISPLAY.fill(BGCOLOR)
        tilesize = TILESIZE + BORDER
        for i in range(self.ncols):
            for j in range(self.nrows):
                rect = (BORDER + i*tilesize, 
                        BORDER + j*tilesize,
                        TILESIZE,
                        TILESIZE)
                DISPLAY.fill(EMPTYCOLOR, rect)

        #draw the tiles
        for t in self.tiles:
            t.draw()

        s = '                      2048    % 6d points!' %self.points
        pygame.display.set_caption(s)
        pygame.display.update()
        clock.tick(FPS)

    def hurray(self, s):
        font = pygame.font.SysFont("Marker Felt", 96)
        textsize = font.size(s)
        borderx = (BOARDX - textsize[0]) // 2
        bordery = (BOARDY - textsize[1]) // 2
        text = font.render(s, True, HURRAY)
        DISPLAY.blit(text, (borderx, bordery))
        pygame.display.update()
        clock.tick(FPS)

    def gameover(self):
        font = pygame.font.SysFont("Impact", 80)
        s = "Game Over!"
        textsize = font.size(s)
        borderx = (BOARDX - textsize[0]) // 2
        bordery = (BOARDY - textsize[1]) // 2
        text = font.render(s, True, (249,247,234))
        DISPLAY.blit(text, (borderx, bordery))

        pygame.display.update()
        clock.tick(FPS)
        sleep(3)

        for t in self.tiles:
            t.target = (t.pos[0], self.ncols+1)

        # animation
        ready = False
        while not ready:
            ready = True
            for t in self.tiles:
                ready &= t.move(v=0.03)
            self.draw()
            DISPLAY.blit(text, (borderx, bordery))



### PYGAME ###

pygame.init()
tilefont = pygame.font.SysFont("Helvetica Bold", 72)
clock = pygame.time.Clock()
DISPLAY = pygame.display.set_mode((BOARDX, BOARDY))
pygame.display.set_caption('2048')

### GAME ###


board = Board(SIZE[0], SIZE[1])
board.add(int(SIZE[0]*SIZE[1] // 8))
board.draw()

OK = True
ctrl = False
while OK:
    ev = pygame.event.wait()
    if ev.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    elif ev.type==pygame.KEYUP and ev.key in (UP,DOWN, LEFT, RIGHT):
        OK = board.move(ev.key)
        board.draw()
        #pygame.display.update()
        #clock.tick(FPS)
    elif ev.type==pygame.KEYDOWN:
        if ev.key in (306, 309, 310): #ctrl, cmd key
            ctrl = True
        if ctrl and ev.key==pygame.K_z:
            board.undo()
    elif ev.type==pygame.KEYUP:
        if ev.key in (306, 309, 310): #ctrl, cmd key
            ctrl = False

print('game over!')
board.gameover()

sleep(3)


