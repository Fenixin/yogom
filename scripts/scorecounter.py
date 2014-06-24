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

from tryengine.constants import WHITE, BLACK
from tryengine.utils import Borg
from tryengine.sprites import TrySprite

# some needed info for the animations
glo = Borg()


class ScoreCounter(TrySprite):
    """ """
    def __init__(self, **obj):
        # Text:
        self.font = glo.emulator_font
        self.size = 10
        self.layers = [('normal', {'color':WHITE}),]
        self.bg_color = BLACK
        self.bg_transparent = True

        # Init the image and the parent
        image = self.font.render(self.text, self.size, self.bg_color, self.bg_transparent, self.layers)
        TrySprite.__init__(self, image, obj['x'], obj['y'], image.get_rect())

        # minimum stuff tu be a mob
        self.killable = False
        self.hostile = False

    @property
    def text(self):
        text = "SCORE: {0}".format(glo.score)
        return text

    def update(self, platforms, new_sprites_group, player):
        self.dirty = 1
        self.player = player
        self.image.fill(BLACK)
        # Render the text
        self.image = self.font.render(self.text, self.size, self.bg_color, self.bg_transparent, self.layers)

