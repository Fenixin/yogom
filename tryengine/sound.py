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

""" Better clases for sounds.

BetterSound handles pan in sounds.

"""

from math import exp, atan, pi

import pygame


class BetterSound(object):
    """ Class that adds some more utils to the basic pygame.Sound.
    
        This handles stereo sound with pan and distance changes
        atenuating the sound. """
    def __init__(self, filename, dist_var = 20, pan_blur = 100., default_vol = 1.0):
        
        self.dist_var = 1./dist_var
        self.pan_blur = pan_blur
        self.default_volume = default_vol
        
        self.sound = pygame.mixer.Sound(filename)
        
        self.channel = pygame.mixer.find_channel()


    def play(self, loops=0, maxtime=0, fade_ms=0):
        if self.channel.get_busy():
            self.channel = pygame.mixer.find_channel()
            self.channel.play(self.sound, loops, maxtime, fade_ms)
            
        else:
            self.channel.play(self.sound, loops, maxtime, fade_ms)


    def fadeout(self, fade_ms=0):
        """ Calls the pygame.Sound.fadeout method. """
        self.channel.fadeout(fade_ms)


    def update_pan(self, x_distance):
        """ Distance is the distance in pixels to 
        the hearing point. """
        
        self.left_pan_value = (atan(x_distance / self.pan_blur) + pi)/ (2 * pi)
        self.channel.set_volume(self.left_pan_value, 1 - self.left_pan_value)


    def update_vol(self, distance):
        """ Updates the volume value. """

        vol = exp( -1. * self.dist_var * distance)
        self.sound.set_volume(vol)


    @property
    def playing(self):
        """ Returns True if the sound is being played in 
        at least a channel. """
        return self.channel.get_busy() != 0


    def update(self, distance, x_distance):
        """ Updates pan and volume. """
        self.update_vol(distance)
        self.update_pan(x_distance)
        
