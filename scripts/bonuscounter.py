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

from pygame import Rect

from tryengine.constants import *
from tryengine.utils import Borg
from tryengine.sprites import TrySprite

# animations info
frame_size = (24,22)

directory = "data"
ss_dir = "data/spritesheets/"

# some needed info for the animations
glo = Borg()

bonus_text_coords = (16, 13)

class BonusCounter(TrySprite):
    """ """
    def __init__(self, **obj):
        
        # Colors to set when the match/bonus is low
        self.hig_score = 5000
        self.hig_color = SKY
        self.med_score = 2000
        self.med_color = PURPLE
        self.low_score = 1000
        self.low_color = RED
        self.index_layer_normal = 0

        # Font
        self.font = glo.emulator_font
        self.font_size = 10
        self.bg_color = VIOLET
        self.bg_transparent = True
        self.color = WHITE
        self.layers = [
#           ('external_border',{'width':1, 'color':BLACK}),
#             ('shadows',{'positions_and_colors':[((2,-2),BLUE),((1,-1),RED)]}),
            ('normal',{'color':WHITE}),#
#               ('internal_border', {'color':(GREEN)}),
              ]

        sp = glo.spritesheet
        spritesheet = sp
        self.bonus_frame = spritesheet.subsurface(Rect(16*8, 144, 16* 4, 16*2)).copy()
        
        # Just to get the first image
        self.update(None, None, None)
        TrySprite.__init__(self, self.image, obj['x'], obj['y'], self.image.get_rect())

        # minimum stuff to be a mob
        self.killable = False
        self.hostile = False

    def update(self, platforms, new_sprites_group, player):
        text_image = self.text_image
        self.image = self.bonus_frame.copy()
        self.image.blit(text_image, bonus_text_coords)

        if glo.bonus <= self.low_score:
            color = self.low_color
        elif glo.bonus < self.med_score:
            color = self.med_color
        elif glo.bonus < self.hig_score:
            color = self.hig_color
        self.layers[self.index_layer_normal][1]['color'] = color

    @property
    def text_image(self):
        text = self.text
        text_image = self.font.render(text, self.font_size, self.bg_color, self.bg_transparent, self.layers)
        text_image.set_colorkey(self.bg_color)
        return text_image

    @property
    def text(self):
        return "{0: >4}".format(glo.bonus if glo.bonus > 0 else 0)
