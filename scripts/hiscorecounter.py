#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   This file is part of You only get one! (match).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from os.path import join, split

import pygame

from tryengine.constants import *
from tryengine.utils import Borg, image_loader
from tryengine.sprites import TrySprite

# animations info
frame_size = (24,24)

directory = "data"
ss_dir = "data/spritesheets/"

# some needed info for the animations
glo = Borg()

# lets render some text
emulator_file = "fonts/Emulator.ttf"
font = pygame.font.Font(emulator_file, 10)


class HiScoreCounter(TrySprite):
    """ """
    def __init__(self, **obj):
        text = "SCORE: {0}".format(glo.lives)
        image = font.render(text, False, WHITE, BLACK)
        TrySprite.__init__(self, image, obj['x'], obj['y'], image.get_rect())
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        spritesheet = image_loader(filename)

        # Will get coordinates from here
        self.camera = None

        # minimum stuff tu be a mob
        self.killable = False
        self.hostile = False

    def update(self, platforms, new_sprites_group, player):
        self.dirty = 1
        self.player = player
        self.image.fill(BLACK)
        # Render the text
        if glo.score > glo.hiscore:
            glo.hiscore = glo.score
        text = "HI: {0}".format(glo.hiscore)
        self.image = font.render(text, False, WHITE, BLACK)
        self.image.set_colorkey(BLACK)


