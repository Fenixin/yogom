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

'''
Created on 29/05/2014

@author: Alejandro Aguilera Martínez
@email: fenixin@gmail.com
'''

from math import sin, cos, ceil
from random import random

from pygame import Surface, Rect

from sprites import TryMovingSprite
from constants import *
from aparser import ArgumentParser, ErrorParsingArgument
from utils import Borg
from types import FunctionType
from animation import AnimationPlayer

glo = Borg()


class ParseParticleError(Exception):
    """ Error parsing the arguments of a particle. """
    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)


class BaseParticle(object):
    def __init__(self, *args, **kwargs):
        pass
    def parse_catching_errors(self, parser, definitions, arguments, destination):
        """ Parse kwargs raising proper exceptions. """
        try:
            parser.parse(definitions, arguments, destination)
        except ErrorParsingArgument, e:
            msg = "The particle \"{0}\" gave the next error while parsing arguments:\n {1}".format(self.__class__, e.msg)
            raise ParseParticleError(msg)

class TryParticle(TryMovingSprite, BaseParticle):
    '''
    classdocs
    '''

    def __init__(self, **kwargs):
        '''
        Constructor
        '''
        BaseParticle.__init__(self)
        self.update_functions = {}

        self.custom_properties = {
            'collides': { "type": bool, "destination" : "collides", "default": False },
            'gravity': { 'type': float, 'destination': 'gravity', 'default': 2.0},
            'has_gravity': { "type": bool, "destination" : "has_gravity", "default": True },
            'image': {'type': Surface, 'destination': 'image', 'default': WHITE_PIXEL.convert()},
            'x': {'type': int, 'destination': 'start_x'},
            'y': {'type': int, 'destination': 'start_y'},
            'col_rect': {'type': Rect, 'destination': 'col_rect', 'default': Rect(0,0,1,1)},
            'friction_factor': {'type': float, 'destination': 'friction_factor', 'default': 0.0}
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)

        TryMovingSprite.__init__(self, self.image, self.start_x, self.start_y, self.col_rect)
        
        # Other specific stuff
        # Age of the particle in updates
        self.age = 0

    def update(self, platforms, new_sprites_group, player):
        self.age += 1
        for f in self.update_functions.keys():
            f(self)
        if self.collides:
            self.move_colliding(platforms)
            self.apply_gravity()
        else:
            self.apply_gravity()
            self.move_sprite_float(self.vx, self.vy)

        self.friction()

        self.custom_update_actions(platforms, new_sprites_group, player)

    def custom_update_actions(self, platforms, new_sprites_group, player):
        pass

class FadeOutParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self)
        self.custom_properties = {
            'fade_out_time': { "type": int, "destination" : "fade_out_time", "default": 30 },
            'life_time': { "type": int, "destination" : "life_time", "default": 30 },
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)
        
        self.update_functions[_update_fadeout] = None
        self.update_functions[_update_kill] = None

class RandomSpeedParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self)
        self.custom_properties = {
            'max_speed': { "type": float, "destination": "max_speed", "default": 1.0 },
            'min_speed': { "type": float, "destination": "min_speed", "default": 0.1 },
            'direction': { 'type': float, 'destination': 'direction', 'default': 0.0},
            'delta_ang': { 'type': float, 'destination': 'delta_ang', 'default': 360.}
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)
        
        self.vx, self.vy = _get_rand_speeds(self)

class RotatingPaletteParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self)
        # TODO: This needs args and a way to ask the engine for palettes!
        
        self.update_functions[_update_palette] = None

class ColorParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self)
        self.custom_properties = {
            'color': { "type": tuple, "destination" : "color", "default": WHITE },
            'size': { "type": tuple, "destination" : "size", "default": (1,1) },
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)
        
        # Create the image color
        img = Surface(self.size)
        img.fill(self.color)
        self.image = img.convert()


class TextParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self, **kwargs)
        self.custom_properties = {
            'text': { "type": str, "destination" : "text" },
            'font_size': { "type": int, "destination" : "font_size"},
            'text_layers': {'type': list, 'destination': 'layers'},
            'bg_color': {'type': tuple, 'destination': 'bg_color'},
            'bg_transparent': {'type': bool, 'destination': 'bg_transparent'}
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)

        # Generate text image
        # TODO: Get also a font_renderer in the arguments
        img = glo.default_font.render(self.text, self.font_size, self.bg_color, self.bg_transparent, self.layers)
        self.image = img

class FunctionSpeedParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self, **kwargs)
        self.custom_properties = {
            'vx_function': {'type': FunctionType, 'destination': 'vx_function'},
            'vy_function': {'type': FunctionType, 'destination': 'vy_function'},
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)
        
        self.update_functions[_update_speeds_using_functions] = None

class AnimatedParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self, **kwargs)
        self.custom_properties = {
            'animation': {'type': AnimationPlayer, 'destination': 'animation'},
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)
        
        self.image = self.animation.get_next_frame()
        
        self.update_functions[_update_animation]=None
        

class FunctionPositionParticle(BaseParticle):
    def __init__(self, **kwargs):
        BaseParticle.__init__(self, **kwargs)
        self.custom_properties = {
            'x_function': {'type': FunctionType, 'destination': 'x_function'},
            'y_function': {'type': FunctionType, 'destination': 'y_function'},
            }
        
        parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(parser, self.custom_properties, kwargs, self.__dict__)
        
        self.image = self.animation.get_next_frame()
        
        self.update_functions[_update_position_using_functions]=None
        

#####################
# Update and other functions
#####################

def _update_position_using_functions(cls, *args):
    cls

def _update_animation(cls, *args):
    # TODO: some type of animations won't work this way
    cls.image = cls.animation.get_next_frame()


def _update_speeds_using_functions(cls, *args):
    cls.vx = cls.vx_function(cls.vx, cls.age)
    cls.vy = cls.vy_function(cls.vy, cls.age)

def _update_palette(cls, *args):
    cls.image.set_palette(glo.rot_pal3)

def _get_rand_speeds(cls):
    ang = (cls.direction - cls.delta_ang / 2.) + cls.delta_ang * random()
    speed = cls.min_speed + (cls.max_speed - cls.min_speed) * random()
    vx = speed * cos(ang)
    vy = speed * sin(ang)
    return vx, vy

def _update_kill(cls, *args):
    if cls.age >= cls.life_time:
        cls.kill()

def _update_fadeout(cls, *args):
    dying_time = cls.age - (cls.life_time - cls.fade_out_time)
    if dying_time > 0:
        a = ceil((1.0 - (dying_time)/float(cls.fade_out_time)  ) * 255)
        cls.image.set_alpha(a)

