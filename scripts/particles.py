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

from pygame import Surface, Rect, draw

from tryengine.sprites import TrySprite
from tryengine.constants import *
from tryengine.utils import Borg, Timer

from tryengine.particles import TryParticle, FadeOutParticle ,\
    RandomSpeedParticle, ColorParticle, TextParticle, FunctionSpeedParticle,\
    RotatingPaletteParticle, AnimatedParticle

glo = Borg()


class RandColorParticle(TryParticle, FadeOutParticle, RandomSpeedParticle, ColorParticle):
    def __init__(self, **kwargs):
        TryParticle.__init__(self, **kwargs)
        FadeOutParticle.__init__(self, **kwargs)
        RandomSpeedParticle.__init__(self,**kwargs)
#         RotatingPaletteParticle.__init__(self)
        ColorParticle.__init__(self,**kwargs)

    def custom_update_actions(self, platforms, new_sprites_group, player):
        pass


class RandImageParticle(TryParticle, FadeOutParticle, RandomSpeedParticle):
    def __init__(self, **kwargs):
        TryParticle.__init__(self, **kwargs)
        FadeOutParticle.__init__(self, **kwargs)
        RandomSpeedParticle.__init__(self,**kwargs)


class AnimatedRandParticle(TryParticle, FadeOutParticle, RandomSpeedParticle, AnimatedParticle):
    def __init__(self, **kwargs):
        TryParticle.__init__(self, **kwargs)
        FadeOutParticle.__init__(self, **kwargs)
        RandomSpeedParticle.__init__(self,**kwargs)
        AnimatedParticle.__init__(self, **kwargs)


class SimpleAnimatedParticle(TryParticle, AnimatedParticle):
    def __init__(self, **kwargs):
        TryParticle.__init__(self, **kwargs)
        AnimatedParticle.__init__(self, **kwargs)


class Sparkle(TryParticle, FadeOutParticle, RandomSpeedParticle):
    def __init__(self, x, y, **kwargs):
        img = Surface((50,50))
        img = img.convert()
        img.fill(PINK_TRANSPARENT)
        img.set_colorkey(PINK_TRANSPARENT)
        col_rect = Rect(24,24,2,2)
        TryParticle.__init__(self, x=x, y=y, gravity = 0.5, has_gravity=True, image = img, col_rect=col_rect, life_time=100, collides=True)
        FadeOutParticle.__init__(self, fade_out_time = 30, life_time = 30)
        RandomSpeedParticle.__init__(self, max_speed = 10, delta_ang = 360, min_speed=5)

    def custom_update_actions(self, platforms, new_sprites_group, player):
        self.image.fill(PINK_TRANSPARENT)
        points = map(self.global2local, self._last_positions)
        draw.lines(self.image, WHITE, False, points, 1)

    def global2local(self, coords):
        offset = -self.rect[0] + self.col_rect[0],-self.rect[1] + self.col_rect[1]
#         offset = 0,0
        return -self.rect[0] + coords[0] + offset[0], -self.rect[1] + coords[1] + offset[1]


class ScoreText(TryParticle, FadeOutParticle, TextParticle, FunctionSpeedParticle):
    def __init__(self, **kwargs):
        TryParticle.__init__(self, **kwargs)
        FadeOutParticle.__init__(self, **kwargs)
        TextParticle.__init__(self, **kwargs)
        FunctionSpeedParticle.__init__(self, **kwargs)


class RotatingPaletteScoreText(ScoreText, RotatingPaletteParticle):
    def __init__(self, **kwargs):
        ScoreText.__init__(self, **kwargs)
        self.image = self.image.convert(8)
        RotatingPaletteParticle.__init__(self, **kwargs)


class CoveringSprite(TrySprite):
    def __init__(self, image, x, y, col_rect):
        self.smooth_kill = False
        TrySprite.__init__(self, image, x, y, col_rect)
        
    def update(self, *args):
        if self.smooth_kill:
            alpha = self.image.get_alpha()
            if alpha == 0:
                self.kill()
            else:
                self.image.set_alpha(alpha -5)


class FlickeringSprite(TrySprite):
    def __init__(self, image, x, y, col_rect, timer = 1):
        TrySprite.__init__(self, image, x, y, col_rect)
        
        self.timer = Timer(timer)
        
    def update(self, *args):
        
        if self.timer.finished:
            self.timer.reset()
            alpha = self.image.get_alpha()
            if alpha == 0:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(0)
