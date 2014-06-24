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
from tryengine.utils import image_loader
from tryengine.animation import UpdateAnimationPlayer, Animation
from tryengine.sprites import TrySprite

# animations info
frame_size = (24,24)

directory = "data"
ss_dir = "data/spritesheets/"

# some needed info for the animations
max_speed = 0.
updates_per_frame = 4


class MatchCounter(TrySprite):
    """ The sprite representing the player. """
    def __init__(self, **obj):
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        spritesheet = image_loader(filename)
        # Fire animation:
        self.match = spritesheet.subsurface(pygame.Rect(0,5*24, 4*24, 24))
        self.burnt_match = spritesheet.subsurface(pygame.Rect(4*24,5*24, 4*24, 24))

        # sprites 16x16 size in (0,144)
        self.fire = spritesheet.subsurface(pygame.Rect(8*16,144 + 16*2, 4*16, 16))
        self.fire_a = UpdateAnimationPlayer(Animation(self.fire, (16,16), False), updates_per_frame)

        # Call the parent's constructor
        TrySprite.__init__(self, self.match.copy(), obj['x'], obj['y'], self.match.get_rect())
        
        # Will get coordinates from here
        self.camera = None
        
        # Add himself in the mobs and render groups
        #~ player.properly_add_ontop(self)
        
        self.player = None
        
        self.x_size = self.image.get_size()[0]

        # minimum stuff tu be a mob
        self.killable = False
        self.hostile = False

    def update(self, platforms, new_sprites_group, player):
        self.dirty = 1
        self.player = player
        self.image.fill(PINK_TRANSPARENT)
        # This must be a number between 100.0 and - inifinite
        amount_of_fire = self.player.lit
        min_x = 20
        if amount_of_fire >= 0:
            # -20 offset, -8 center of flame
            x_coord = 20 + int((self.x_size - 20 - 8) * amount_of_fire / 100.)

            match_rect = self.match.get_rect()
            match_rect.width = x_coord
            self.image.blit(self.match, (0,0), match_rect)
            
            burnt_rect = pygame.Rect(x_coord, 0, self.burnt_match.get_size()[0] - x_coord, 24)
            self.image.blit(self.burnt_match, (x_coord, 0), burnt_rect)
            
            f = self.fire_a.get_next_frame()
            self.image.blit(f,(x_coord - 8,4))
        else:
            self.image = self.burnt_match.copy()
