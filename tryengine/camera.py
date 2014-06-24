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

""" Module that provides with cameras for the renderer.

A camera can follow a sprite or be fixed in a matrix (only having a few
possible positions). The camera will provide a Rect with the visible area of
the map.

"""

import random
import math

import pygame


class Camera(object):
    """ Class to derive all the other cameras. Contains common things.

        A camera has the @property screen_rect that gives which
        subsurface of the whole map is going to the screen.

        Note: Most of the information needed to make Camera work
        properly is added in Renderer.add_camera(). All the info is
        render stuff, as the screen size, map size, etc.
        """

    def __init__(self, sprite):
        # this is the sprite to follow
        self.sprite = sprite

        # this will hold the a pygame rect that determine the subsurface
        # of visible map
        self._screen_rect = None

        # shaking info
        self.frames_to_shake = 0
        self.amount_to_shake = 0
        self.shake_offset = (0,0)

        # speed of the camera, only used in some cameras
        self.vx = 0
        self.vy = 0

        # max speed while moving and acceleration of the camera
        self.max_speed = 20
        self.acceleration = 4
        # between 0 and 1
        self.friction_factor = 0.5

    def check_final_coords(self, x, y):
        """ Takes the x and y coordinates of the screen rect and checks
        if they are inside the map surface. Returns the coords of the
        screen rect so it's completelly inside of the map surface. """

        max_x = (self.map_size_in_tiles[0] - self.screen_size_in_tiles[0]) * self.tile_size[0]
        max_y = (self.map_size_in_tiles[1] - self.screen_size_in_tiles[1]) * self.tile_size[1]
        
        final_x = x
        if final_x < 0:
            final_x  = 0
            self.vx = 0
        elif final_x > max_x:
            final_x = max_x
            self.vx = 0
        
        final_y = y
        if final_y < 0:
            final_y = 0
            self.vy = 0
        elif final_y > max_y:
            final_y = max_y
            self.vy = 0
        
        return final_x, final_y

    def apply_shake(self):
        """ Randomize some values for shaking and store them in 
        self.shake_offset. """
        if self.frames_to_shake:
            self.frames_to_shake -= 1
            self.shake_offset = ((random.random() - 0.5) * 2 * self.amount_to_shake, (random.random()  - 0.5) * 2 * self.amount_to_shake)
        else:
            self.shake_offset = (0, 0)

    def shake(self, frames, max_pixels):
        """ Shake the camera for the given amount of frames a random
        amount of pixels with the given maximum. """
        self.frames_to_shake = frames
        self.amount_to_shake = max_pixels

    def secure_add_speed_x(self, speed):
        """ Adds speed to the camera respecting the maximum speed
        defined in self.max_speed. """
        self.vx += speed
        if abs(self.vx) > self.max_speed:
            self.vx = math.copysign(self.max_speed, self.vx)

    def secure_add_speed_y(self, speed):
        """ Adds speed to the camera respecting the maximum speed
        defined in self.max_speed. """
        self.vy += speed
        if abs(self.vy) > self.max_speed:
            self.vy = math.copysign(self.max_speed, self.vy)

    def accel_right(self):
        """ This is the method to use if you want to move smoothly the
        camera. Uses secure_add_speed with self.acceleration and updates
        the self.moving. """
        self.moving = True
        self.secure_add_speed_x(self.acceleration)

    def accel_left(self):
        """ This is the method to use if you want to move smoothly the
        camera. Uses secure_add_speed with self.acceleration and updates
        the self.moving. """
        self.moving = True
        self.secure_add_speed_x(self.acceleration * -1.)

    def accel_up(self):
        """ This is the method to use if you want to move smoothly the
        camera. Uses secure_add_speed with self.acceleration and updates
        the self.moving. """
        self.moving = True
        self.secure_add_speed_y(self.acceleration * -1)

    def accel_down(self):
        """ This is the method to use if you want to move smoothly the
        camera. Uses secure_add_speed with self.acceleration and updates
        the self.moving. """
        self.moving = True
        self.secure_add_speed_y(self.acceleration)

    def dprint(self, text):
        """ Prints text if the flag self.debugging is True. """
        if self.debugging:
            print text


class ScrollCamera(Camera):
    """ Camera for NewRenderer that follows the given sprite in scrol 
    mode. """
    # TODO: broken with the last changes!
    def __init__(self, sprite, margins=(400, 200), x=0, y=0, speed_factor=0.05):
        Camera.__init__(self, sprite)
        self.__name__ = "ScrollCamera"

        # margin from the camera edges, after that the player will be
        # considererd out of range and will be followed
        self.margins = margins

        # a number representing the moving speed of the camera
        self.speed_factor = speed_factor

        # rect where the player is considered again in view
        self.s_rect_size = (100, 100)

        # stores if we are trying to center the player in the camara
        self.movement = False

        # flag for debugging
        self.debugging = False

        # max speed while moving and acceleration of the camera
        self.max_speed = 1
        self.acceleration = 1
        # between 0 and 1
        self.friction_factor = 0.5

        # movement stuff
        self.vx = self.vy = 0
        self.moving = False

    def __str__(self):
        return self.__name__

    @property
    def screen_rect(self):
        """ Pygame Rect with the proper subsurface to see the sprite. """

        # obtain the how many screens is the sprite to the right and
        # the bottom

        st = self.screen_size_in_tiles
        # screen size in pixels
        sp = (st[0] * self.tile_size[0], st[1] * self.tile_size[1])

        self.apply_shake()

        self.dprint("\n\tUpdating camera position")
        self.dprint("\t\tmovement is {0}".format(self.movement))
        if self.movement:
            small_center = self.inview_rect.center
            sprite_center = self.sprite.rect.center

            vx = math.ceil((sprite_center[0] - small_center[0])*self.speed_factor)
            vy = math.ceil((sprite_center[1] - small_center[1])*self.speed_factor)
            self.dprint("\t\t\t Camera speed: {0},{1}".format(vx, vy))
            self.camera_rect.move_ip(vx, vy)
            self.inview_rect.move_ip(vx, vy)
            self.outview_rect.move_ip(vx, vy)
            if self.inview_rect.contains(self.sprite.rect):
                self.dprint("\t\tThe player is now in the center!")
                self.movement = False
        elif not self.outview_rect.contains(self.sprite.rect):
            
            self.dprint("\tEl sprite se ha salido de los márgenes!")
            self.movement = True

        # final pixel coords, make sure they are inside the screen
        # surface
        final_x = self.camera_rect.left + self.shake_offset[0]
        final_y = self.camera_rect.top + self.shake_offset[1]

        final_x, final_y = self.check_final_coords(final_x, final_y)

        self._screen_rect = pygame.Rect(final_x, final_y, sp[0], sp[1])

        return self._screen_rect


class FreeCamera(Camera):
    """ This camera can be moved around using the .accel_*() methods
    from the general Camera object. """
    def __init__(self, sprite):
        Camera.__init__(self, sprite)
        self.__name__ = "FreeCamera"

        # The player should be in a rect that is considered the center
        # of the camera

        self.moving = False
        self.debugging = False

    def __str__(self):
        return self.__name__

    @property
    def screen_rect(self):
        """ Pygame Rect with the proper subsurface. """

        self.apply_shake()

        st = self.screen_size_in_tiles
        # screen size in pixels
        sp = (st[0] * self.tile_size[0], st[1] * self.tile_size[1])

        # move it
        self.camera_rect.move_ip(int(self.vx), int(self.vy))

        # deacelerate only if the admin is not pressign a key to move
        if not self.moving:
            if self.vx <0.001:
                self.vx = 0
            else: self.vx = self.vx * (1 - self.friction_factor)
            if self.vy <0.001:
                self.vy = 0
            else: self.vy = self.vy * (1 - self.friction_factor)

        # movement for this frame is made
        self.moving = False

        # final pixel coords, make sure they are inside the screen
        # surface

        self.dprint("\t Before check rect: {0}".format(self.camera_rect))
        final_x = self.camera_rect.left + self.shake_offset[0]
        final_y = self.camera_rect.top + self.shake_offset[1]

        final_x, final_y = self.check_final_coords(final_x, final_y)

        self.camera_rect = pygame.Rect(final_x, final_y, sp[0], sp[1])
        
        self.dprint("After check rect: {0}".format(self._screen_rect))
        self.dprint("\t vx = {0}; vy = {1}".format(self.vx, self.vy))
        
        return self.camera_rect


class CenterCamera(Camera):
    """ This camera keeps the given sprite at the center of the screen 
    when possible. """
    def __init__(self, sprite):
        Camera.__init__(self, sprite)
        self.__name__ = "CenterCamera"

        # The player should be in a rect that is considered the center
        # of the camera
        self.debugging = False

    def __str__(self):
        return self.__name__

    @property
    def screen_rect(self):
        """ Pygame Rect with the proper subsurface to keep the sprite
        in the center of the screen. """
        # obtain the how many screens is the sprite to the right and
        # the bottom

        st = self.screen_size_in_tiles
        # screen size in pixels
        sp = (st[0] * self.tile_size[0], st[1] * self.tile_size[1])

        x,y = self.sprite.col_rect.center
        self.dprint("\tSprite at: {0}".format((x,y)))
        x,y = (x - sp[0]/2, y - sp[1]/2)

        # final pixel coords, make sure they are inside the screen
        # surface
        final_x = x + self.shake_offset[0]        
        final_y = y + self.shake_offset[1]

        final_x, final_y = self.check_final_coords(final_x, final_y)

        self._screen_rect = pygame.Rect(final_x, final_y, sp[0], sp[1])
        
        return self._screen_rect


class FixedCamera(Camera):
    """ A simple camera to be used with the NewRenderer for fixed, not
    moving maps. """
    def __init__(self, sprite):
        Camera.__init__(self, sprite)
        self.__name__ = "FixedCamera"

    def __str__(self):
        return self.__name__

    @property
    def screen_rect(self):
        """ Pygame Rect with the proper subsurface. """
        # obtain the how many screens is the sprite to the right and
        # the bottom

        self.apply_shake()

        st = self.screen_size_in_tiles

        sp = (st[0] * self.tile_size[0], st[1] * self.tile_size[1])

        screen_x = int(self.sprite.rect.center[0]) / int(sp[0])
        screen_y = int(self.sprite.rect.center[1]) / int(sp[1])

        # final pixel coords, make sure they are inside the screen
        # surface
        final_x = sp[0] * screen_x + int(self.shake_offset[0])
        final_y = sp[1] * screen_y + int(self.shake_offset[1])

        final_x, final_y = self.check_final_coords(final_x, final_y)
        self._screen_rect = pygame.Rect(final_x, final_y, sp[0], sp[1])

        return self._screen_rect


# dictionary relating strings used in tiled with the camera object
cameras_dict = {"Center": CenterCamera,
               "Free": FreeCamera,
               "Fixed": FixedCamera,
               "Scroll": ScrollCamera}
