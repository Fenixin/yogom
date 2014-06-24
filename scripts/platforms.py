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

import sys

from pygame import Rect, mask

from tryengine.sprites import Tile
from firework import Firework


class Platform(Tile):
    """ Sprite used by tiles that collide """
    def __init__(self, img, x, y, **kwargs):
        Tile.__init__(self, img, x, y)

        # Directions in which this platforms collide
        #                    left, right, top, bottom,
        self.col_direction = (True, True, True, True)

        # it will use the normal collision detection
        self.col_rect = self.rect

    def collision_detection(self, sprite, direction):
        """ Return True if the sprite collides with the platform. """
        sprite.on_platform = self
        if isinstance(sprite, Firework) and sprite.boom_timer:
            return False
        return self.col_direction[direction] and sprite.col_rect.colliderect(self.col_rect)


class HalfPlatform(Platform):
    """ Sprite used by tiles that collide """
    def __init__(self, img, x, y, **kwargs):
        Tile.__init__(self, img, x, y)

        # Directions in which this platforms collide
        #                    left, right, top, bottom,
        self.col_direction = (True, True, True, True)

        # it will use the normal collision detection
        self.col_rect = Rect(x, y + self.rect[3] /2, self.rect[2], self.rect[3] / 2)

    def collision_detection(self, sprite, direction):
        """ Return True if the sprite collides with the platform. """
        sprite.on_platform = self
        # Only Player has this attribute!
        
        if hasattr(sprite, 'half_platform_damage'):
            #~ print "Collision detection"
            #~ print "taken_damage:{0}; ".format(sprite.taken_damage)
            col = self.col_direction[direction] and sprite.col_rect.colliderect(self.col_rect)
            d = sprite.half_platform_damage
            if d > 0:
                if col:
#                     sprite.taken_damage = td + 1 if td == 1 else td
                    #~ print "        Increasing taken_damage"
                    sprite.half_platform_damage = d + 1 if d == 1 else d
                return False
#             elif col:
#                 sprite.taken_damage += 1
            else:
                return col
        # Fireworks, once they take off, go through all platforms
        elif isinstance(sprite, Firework) and sprite.boom_timer:
            return False
        else:
            return self.col_direction[direction] and sprite.col_rect.colliderect(self.col_rect)


class MaskPlatform(Platform):
    def __init__(self, img, x, y, **kwargs):
        Platform.__init__(self,img,x,y, **kwargs)
        
        # The sprite collides with this platform when hits:
        #                    left, right, top, bottom,
        self.col_direction = (True, True, True, True)
        
        # Collision mask
        # TODO: The image should not have a per pixel alpha!
        # This is an old problem in levelpy
        self.mask = mask.from_surface(self.image, 10)

        #~ self.view_mask()

    def view_mask(self):
        print self
        print "Printing mask and exiting."
            
        for y in xrange(self.mask.get_size()[1]):
            for x in xrange(self.mask.get_size()[0]):
                print self.mask.get_at((x,y)),
            print ""
        sys.exit(0)

    def collision_detection(self, sprite, direction):
        """  """
        #~ t1 = self.col_direction[direction]
        #~ offset = (sprite.rect.left - self.rect.left, sprite.rect.top - self.rect.top)
        #~ t2 =  sprite.mask.overlap(self.mask, (sprite.rect.left - self.rect.left, sprite.rect.top - sprite.rect.top))
        #~ print offset
        #~ print t1, t2
        return self.col_direction[direction] and sprite.mask.overlap(self.mask, ((self.rect.left- sprite.rect.left), (self.rect.top - sprite.rect.top)))

class OneWayMaskPlatform(Platform):
    def __init__(self, img, x, y, **kwargs):
        Platform.__init__(self,img,x,y, **kwargs)
        
        # The sprite collides with this platform when hits its:
        #                    left, right, top, bottom,
        self.col_direction = (True, True, False, True)
        
        # Collision mask
        # TODO: The image should not have a per pixel alpha!
        # This is an old problem in levelpy
        self.mask = mask.from_surface(self.image, 10)

        #~ self.view_mask()

    def view_mask(self):
        print self
        print "Printing mask and exiting."
            
        for y in xrange(self.mask.get_size()[1]):
            for x in xrange(self.mask.get_size()[0]):
                print self.mask.get_at((x,y)),
            print ""
        sys.exit(0)

    def collision_detection(self, sprite, direction):
        """  """
        #~ t1 = self.col_direction[direction]
        #~ offset = (sprite.rect.left - self.rect.left, sprite.rect.top - self.rect.top)
        #~ t2 =  sprite.mask.overlap(self.mask, (sprite.rect.left - self.rect.left, sprite.rect.top - sprite.rect.top))
        #~ print offset
        #~ print t1, t2
        return self.col_direction[direction] and sprite.feet_mask.overlap(self.mask, ((self.rect.left- sprite.rect.left), (self.rect.top - sprite.rect.bottom)))


class OneWayPlatform(Platform):
    """ Same as Platform but very thin. """
    def __init__(self, img, x, y, **kwargs):
        Platform.__init__(self,img,x,y, **kwargs)
        
        # The sprite collides with this platform when hits:
        #                    left, right, top, bottom,
        self.col_direction = (False, False, False, True)

        if 'offset' not in kwargs:
            raise ValueError("OneWayPlatform needs an y offset")
        offset =  int(kwargs['offset'])
        # very thin rect
        #~ self.rect = Rect(x, y, self.rect[2], 1)
        self.col_rect = Rect(x, y + offset, self.rect[2], 1)


    def collision_detection(self, sprite, direction):
        """  """
        #~ print self.col_rect, sprite.col_rect, sprite.feet_rect
        #~ print self.col_direction[direction], sprite.feet_rect.colliderect(self.col_rect)

        return self.col_direction[direction] and sprite.feet_rect.colliderect(self.col_rect)
