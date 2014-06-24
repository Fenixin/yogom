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

from pygame import Surface, Rect, mask

from tryengine.sprites import TryMovingSprite
from tryengine.constants import *
from tryengine.utils import Borg, Timer

glo = Borg()


class TextSprite(TryMovingSprite):
    def __init__(self, font_render, text, color, background=(0,0,0), antialias = False, x = 0, y = 0, bg_transparent = True ):
        """ Background is transparent by defualt. """
        
        # Render the image
        self.font = font_render
        self._text = text
        self.antialias = antialias
        self.background = background
        self.color = color
        self.bg_transparent = bg_transparent
        img = self.render(text)
        if bg_transparent:
            img.set_colorkey(background)
        
        TryMovingSprite.__init__(self, img, x, y, img.get_rect())
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = value
        self.image = self.render(value)
        self.rect = Rect((self.rect[0], self.rect[1]), self.image.get_rect()[2:])
        self.col_rect = self.rect.copy()
        self.mask = mask.from_surface(self.image)
        self.create_feet()
        
    def render(self, text):
        """ Renders the text using the options first used. """
        img = self.font.render(text, self.antialias, self.color, self.background)
        return img


class NewTextSprite(TryMovingSprite):
    def __init__(self, font_render, text, size,
                 bg_color, layers, x=0, y=0, 
                 bg_transparent=True):
        """ Background is transparent by defualt. """
        
        # Render the image
        self.font = font_render
        self._text = text
        self.size = size
        self.background = bg_color
        self.bg_transparent = bg_transparent
        self.layers = layers
        
        img = self._render(text)
        
        TryMovingSprite.__init__(self, img, x, y, img.get_rect())
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = value
        self.image = self._render(value)
        self.rect = Rect((self.rect[0], self.rect[1]), self.image.get_rect()[2:])
        self.col_rect = self.rect.copy()
        self.mask = mask.from_surface(self.image)
        self.create_feet()
        
    def _render(self, text):
        """ Renders text using stored options """
        img = self.font.render(self.text, self.size, self.background, self.bg_transparent, self.layers)
        return img


class MultiLineTextSprite(TryMovingSprite):

    A_LEFT = 0
    A_CENTER = 1
    A_RIGHT = 2

    def __init__(self, font_render, text, size, background, layers,
                 x=0, y=0, align=1, line_spacer=0, bg_transparent=True ):
        """ Background is transparent by defualt. 
        
        align:
        0 - left
        1 - center
        2 - right
        
        """

        # Render the image
        self.font = font_render
        self._text = text
        self.size = size
        self.background = background
        self.bg_transparent = bg_transparent
        self.align = align
        self.line_spacer = line_spacer
        self.layers = layers
        
        img = self.render(text)
        if bg_transparent:
            img.set_colorkey(background)

        TryMovingSprite.__init__(self, img, x, y, img.get_rect())

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.image = self.render(value)
        self.rect = Rect((self.rect[0], self.rect[1]), self.image.get_rect()[2:])
        self.col_rect = self.rect.copy()
        self.mask = mask.from_surface(self.image)
        self.create_feet()

    def _calculate_image_size(self, font_render, text, size, line_spacer, layers):
        lines = text.splitlines()
        ls = line_spacer
        xs = 0
        ys = 0
        for l in lines:
            w, h = font_render.size(l, size, layers)
            xs = max(xs, w)
            ys += h + ls
        
        # Don't put a line spacer for one line text
        if len(lines) == 1:
            ys -= ls
        return xs, ys

    def render(self, text):
        """ Renders the text using the options first used. """

        lines = text.splitlines()
        img = Surface(self._calculate_image_size(self.font, 
                             self.text, self.size, self.line_spacer, self.layers))
        if self.bg_transparent:
            img.set_colorkey(self.background)
        full_rect = img.get_rect()
        
        y = 0
        for l in lines:
            r = self.font.render(l, self.size, self.background, self.bg_transparent, self.layers)
            r_rect = r.get_rect()
            if self.bg_transparent:
                r.set_colorkey(self.background)
            if self.align == self.A_CENTER:
                x = self._center_rect_inside_rect(r_rect, full_rect)
            elif self.align == self.A_LEFT:
                x = 0
            elif self.align == self.A_RIGHT:
                x = full_rect[3] - r_rect[3]
            img.blit(r, (x, y))
            y += self.line_spacer + r_rect[3]
        
        return img
            
    def _center_rect_inside_rect(self, rect1, rect2, offset=0):
        x = (rect2[2] - rect1[2])/2 + offset
        return x


class BlinkingTextSprite(NewTextSprite):
    def __init__(self, font_render, text, size,
                 bg_color, layers, x=0, y=0, blink_time = 1,
                 bg_transparent=True):
        self.timer = Timer(blink_time)
        NewTextSprite.__init__(self, font_render, text, size, bg_color, layers, x, y, bg_transparent)

    def update(self, *args):
        if self.timer.finished:
            self.timer.reset()
            alpha = self.image.get_alpha()
            if alpha == 0:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(0)

