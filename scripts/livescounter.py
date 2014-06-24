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
from pygame.transform import scale 

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

class LivesCounter(TrySprite):
    """ """
    def __init__(self, **obj):
        
        # Live image
        ss_dir = "data/spritesheets/"
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)
        
        spritesheet = image_loader(filename)
        live_image = spritesheet.subsurface(pygame.Rect(0,0, 24, 24))
        self.live_image = pygame.transform.scale(live_image, (12,12))
        
        self.text = "LIVES:"
        image = self.get_lives_image(self.text, glo.lives, self.live_image)
        TrySprite.__init__(self, image, obj['x'], obj['y'], image.get_rect())

        # Blinking effect
        self.blinks = 5
        # Half of them on half off
        self.updates_per_blink = 10
        self.updates_blinking = self.blinks * self.updates_per_blink
        self.blink_update_counter = 0
        self.blinking = False
        self.current_lives = glo.lives
        self.lives_in_counter = glo.lives
        self.lives_pos_offset = (0, 2)

        # Minimun stuff needed to be updated in the same group as mobs
        self.killable = False
        self.hostile = False
        self.last_lives = 0

    def update(self, platforms, new_sprites_group, player):
        
        final_lives = None
        
        # Check if we have to blink
        if self.current_lives != glo.lives:
            #~ print "Lives changed! Time to blink!"
            self.last_lives = self.current_lives
            self.current_lives = glo.lives
            self.blinking = True
            self.blink_update_counter = 0
        
        if self.blinking:
            first_period = True if (self.blink_update_counter % self.updates_per_blink) / (self.updates_per_blink / 2) else False
            self.blink_update_counter += 1
            if self.blink_update_counter == self.updates_blinking:
                self.blinking = False
            if first_period:
                final_lives = self.current_lives
            else:
                final_lives = self.last_lives
            #~ print "Blinking: final_lives = ", final_lives, "; first_period = ", first_period, "; blink_update_counter = ", self.blink_update_counter
        else:
            final_lives = glo.lives
        
        if final_lives != self.lives_in_counter:
            #~ print "Updating image!"
            self.lives_in_counter = final_lives
        # Update it every frame...
        self.image = self.get_lives_image(self.text, final_lives, scale(player.image,(12,12)), 3, self.lives_pos_offset)

    def get_lives_image(self, text, num_lives, live_image, separation = 3, lives_pos_offset = (0,0)):
        loffset = lives_pos_offset
        y_pos_text = 2
        w_text, h_text = font.size(text)
        text_image = font.render(text, False, WHITE, BLACK)
        w_image, h_image = live_image.get_size()
        
        w = w_text + separation * num_lives + num_lives * w_image
        h = w_text if w_text > w_image else w_image
        
        image = pygame.Surface((w,h), pygame.HWSURFACE, pygame.display.get_surface())
        image.set_colorkey(BLACK)
        
        image.blit(text_image, (0,y_pos_text))
        for i in xrange(num_lives):
            
            image.blit(live_image, (w_text + separation * (1 + i) + w_image * i + loffset[0], loffset[1]))
        
        return image
