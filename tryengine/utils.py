#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   This file is part of TryEngine.
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

""" Module with utils/functions. """

from math import hypot
import weakref

from pygame.time import get_ticks
from pygame.mixer import Sound
import pygame as pg
from pygame import Surface, BLEND_MULT

from constants import PINK_TRANSPARENT, BLACK

#======================
# FUNCTIONS
#======================

def fast_tint(color, image):
    """ Tint an image with a color.
    
    Works better with whiteish images.
    """

    size = image.get_size()
    new_surface = Surface(size)
    new_surface.fill(BLACK)
    new_surface.blit(image, (0,0))
    tinter = Surface(size)
    tinter.fill(color)
    r = tinter.get_rect()
    new_surface.blit(tinter, (0,0), r, BLEND_MULT)
    new_surface.set_colorkey(BLACK)

    return new_surface


def memoizer(new_dict=dict):
    """
    Creates a memoizer with the given dictionary policy. 
 
    The memoizer thus obtained can be used as a decorator to remember the
    results of calls to long-running functions, such as loading images
    from disk. It also means that there will only be one copy of the image,
    which can be quite handy when dealing with restricted resources.
 
    Example:
 
    weak_memoize = memoize(new_dict=weakref.WeakValueDictionary)
 
    @weak_memoize
    def load_image(filename):
        # Your long running image-loading code goes here.
        return result
    
    Code from pygame cookbook:
    http://www.pygame.org/wiki/MemoizingDecorator?parent=CookBook
    """
    def memoize(func):
        cache = new_dict()
 
        def memo(*args, **kwargs):
            try:
                # Create a key, resorting to repr if the key isn't hashable.
                try:
                    k = (args, tuple(kwargs.items()))
                    hash(k)
                except TypeError:
                    k = repr(k)
                    
                # Try to return the result from the cache.
                return cache[k]
            except KeyError:
                # The key wasn't found, so invoke the function and save the
                # result in the cache.
                result = func(*args, **kwargs)
                cache[k] = result
                return result

        return memo
    
    return memoize

weak_memorizer = memoizer(new_dict = weakref.WeakValueDictionary)


@weak_memorizer
def image_loader(filename):
    """ Loads an image with fixed settings.
    
    Apply PINK_TRANSPARENT as colorkey and fastest flags. It also
    has a decorator with a lazy resource loader.

    """

    colorkey = PINK_TRANSPARENT

    # For fastest blitting set hwsurface and the same
    # bit depth as the display surface
    bit_size = pg.display.get_surface().get_bitsize()
    flags = pg.HWSURFACE

    img = pg.image.load(filename).convert(bit_size, flags)
    img.set_colorkey(colorkey, pg.RLEACCEL)

    return img


def extend_dict(to_extend, extension):
    for key in extension:
        to_extend[key] = extension[key]


@weak_memorizer
def load_sound(filename):
    """ Properly load a sound file with fixed settings.

    It also has a decorator with a lazy resource loader.

    """

    f = open(filename, 'r+b')

    return Sound(f)


def create_dot_list(start_pos, end_pos, num_dots):
    width = end_pos[0] - start_pos[0]
    height = end_pos[1] - start_pos[1]
    
    length = hypot(width, height)
    # Space between dots
    spacing = length / (num_dots - 1) 
    
    sen_ang = height / length
    cos_ang = width / length
    p = []
    #~ print cos_ang, sen_ang
    p.append(start_pos)
    for i in xrange(1,num_dots-1):
        p.append((int(round(start_pos[0] + spacing * cos_ang * i)),int(round(start_pos[1] +  spacing * sen_ang * i))))
    p.append(end_pos)
    return p


def collision_detection(left_sprite, right_sprite):
    """ A callback function that makes the collisions between
    the col_rect attribute of the sprite, instead of using the
    rect attribute. 

    Very useful to draw the sprite in a place and to collide it
    somewhere else. """
    
    ls = left_sprite
    rs = right_sprite
    return ls.col_rect.colliderect(rs.col_rect)


def directional_collision_detection(left_sprite, right_sprite, direction):
    """ A callback function that makes the collisions between
    the col_rect attribute of the sprite, instead of using the
    rect attribute. 

    Very useful to draw the sprite in a place and to collide it
    somewhere else. """
    
    ls = left_sprite
    rs = right_sprite
    return rs.col_direction[direction] and ls.col_rect.colliderect(rs.col_rect)


def rects_from_sprites(sprites):
    """ Return a list with 'rect' attribute from
        a list of sprites. """
    return [ sprite.rect for sprite in sprites]


def col_rects_from_sprites(sprites):
    """ Return a list with 'rect' attribute from
        a list of sprites. """
    return [ sprite.col_rect for sprite in sprites]


def visible_col_rects_from_sprites(sprites):
    """ Return a list with a copy of the 'rect' 
    attribute from a list of sprites, for visible sprites. """
    
    return [sprite.col_rect for sprite in sprites if sprite.visible]


def visible_rects_from_sprites(sprites):
    """ Return a list with a copy of the 'rect' 
    attribute from a list of sprites, for visible sprites. """
    
    return [sprite.rect for sprite in sprites if sprite.visible]


def copy_rects_from_sprites(sprites):
    """ Return a list with a copy of the 'rect' 
    attribute from a list of sprites. """
    return [ sprite.rect.copy() for sprite in sprites]


def copy_visible_rects_from_sprites(sprites):
    """ Return a list with a copy of the 'rect' 
    attribute from a list of sprites, for visible sprites. """
    
    return [sprite.rect.copy() for sprite in sprites if sprite.visible]


#=======================
# HOMELESS CLASSES
#=======================

class Timer(object):
    """ Very basic timer. Input in seconds"""
    def __init__(self, seconds):
        self.delay = seconds
        # get_ticks return milliseconds
        self.start_time = get_ticks() / 1000.
    
    def reset(self):
        """ Put to zero the timer. """
        self.start_time = get_ticks() / 1000.

    @property
    def finished(self):
        """ When True the timer has finished. """
        time_until_now = (get_ticks() / 1000.) - self.start_time
        return time_until_now >= self.delay


class Borg(object):
    """ Classes ihereted from this one will share state. 
    
    Extracted from:
    http://www.aleax.it/5ep.html
    """

    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state
