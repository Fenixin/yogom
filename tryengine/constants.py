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

""" Module with constants used by the tryengine and a few useful more."""


import pygame

# TODO: Automate all this... is hell now that it's growing


#====================
# EVENT CONSTANTS
#===================

# NOTE TO SELF:
# There are only 32 event types (can be checked by print
# pygame.NUMEVENTS) and userevents start at 24, please,
# don't forget that.
#
events = ['TRIGGER',
    'PLAYER',
    'ENGINE',
    'USE',
    'RENDERER']

#==================================================
# Event codes using type RENDERER. 
RENDERER = pygame.USEREVENT + 0
# Start of renderer codes
RENDERER_SC = 0
# Event codes

FADE = RENDERER_SC + 0
NEXT_CAMERA = RENDERER_SC + 1
CAMERA_LEFT = RENDERER_SC + 2
CAMERA_RIGHT = RENDERER_SC + 3
CAMERA_UP = RENDERER_SC + 4
CAMERA_DOWN = RENDERER_SC + 5
CAMERA_SHAKE = RENDERER_SC + 6

RENDERER_CODES = [
    'FADE',
    'NEXT_CAMERA',
    'CAMERA_LEFT',
    'CAMERA_RIGHT',
    'CAMERA_UP',
    'CAMERA_DOWN',
    'CAMERA_SHAKE',
    ]

#===================================================
# Event triggers, trigger actionsprites and
# other stuff
#
TRIGGER = pygame.USEREVENT + 1
# Start of trigger codes
TRIGGER_SC = 1

#==================================================
# Even raised by the player, event type PLAYER
#
PLAYER = pygame.USEREVENT + 2
# Start of player codes
PLAYER_SC = 200
# Event codes
LEFT = PLAYER_SC + 0
RIGHT = PLAYER_SC + 1
USE = PLAYER_SC + 2
JUMP = PLAYER_SC + 3
SHOOT = PLAYER_SC + 4
RESPAWN = PLAYER_SC + 5

PLAYER_CODES = ['LEFT',
    'RIGHT',
    'USE',
    'JUMP',
    'SHOOT',
    'RESPAWN']


#====================================================
# Engine events that control loading a new map, quit,
# etc. Event type ENGINE
#
ENGINE = pygame.USEREVENT + 3
# Start of engine codes
ENGINE_SC = 300
# Engine codes
NEW_MAP = ENGINE_SC + 0
PAUSE = ENGINE_SC + 1
CHEATS = ENGINE_SC + 2
RELOAD_MAP = ENGINE_SC + 3
CYCLE_DEBUG_MODES = ENGINE_SC + 4
ONE_LAYER_UP = ENGINE_SC + 5
ONE_LAYER_DOWN = ENGINE_SC + 6
CYCLE_DISPLAY_MODES = ENGINE_SC + 7
SUPER_LOW_FPS = ENGINE_SC + 8
E_QUIT = ENGINE_SC + 9
PAUSE = ENGINE_SC + 10
CONTROL_NEXT_MOB = ENGINE_SC + 11
TEST_MOUSE_MOTION = ENGINE_SC + 12
TOGGLE_FULLSCREEN = ENGINE_SC + 13
SCREENSHOT = ENGINE_SC + 14

ENGINE_CODES = ['TOGGLE_FULLSCREEN',
    'NEW_MAP',
    'PAUSE',
    'CHEATS',
    'RELOAD_MAP',
    'CYCLE_DEBUG_MODES',
    'ONE_LAYER_UP',
    'ONE_LAYER_DOWN',
    'CONTROL_NEXT_MOB',
    'CYCLE_DISPLAY_MODES',
    'E_QUIT',
    'PAUSE',
    'SUPER_LOW_FPS',
    'TEST_MOUSE_MOTION',
    'SCREENSHOT',
    ]

#===========================
# OHTER CONSTANTS
#===========================

# Generic directions
DIR_LEFT = 0
DIR_RIGHT = 1
DIR_UP = 2
DIR_DOWN = 3

# directions looking
LOOKING_LEFT  = 0
LOOKING_RIGHT = 1

# generic animations
# each animation should be a tuple with left/right animations
ANIMATION_STOP = 10
ANIMATION_WALKING = 11
ANIMATION_JUMP = 12
ANIMATION_SHOOT = 13
ANIMATION_FALLING = 14
ANIMATION_BRAKING = 15
ANIMATION_IDLE = 16
ANIMATION_CROUCH = 17
ANIMATION_OTHERS = 18 # others, mob specific

animations = ['LOOKING_LEFT',
              'LOOKING_RIGHT',
              'ANIMATION_STOP',
              'ANIMATION_IDLE',
              'ANIMATION_WALKING',
              'ANIMATION_JUMP',
              'ANIMATION_SHOOT',
              'ANIMATION_FALLING',
              'ANIMATION_BRAKING',
              'ANIMATION_CROUCH',
              'ANIMATION_OTHERS',
              ]

directions = [
    'DIR_LEFT',
    'DIR_RIGHT',
    'DIR_UP',
    'DIR_DOWN']


SPEED_SET = 0
SPEED_ADD = 1
POSITION_SET = 2
POSITION_ADD = 3

movement_modifiers = [
    'SPEED_SET',
    'SPEED_ADD',
    'POSITION_SET',
    'POSITION_ADD',]

#=====================
# COLORS AND IMAGES
#=====================

BLACK =  (  0,  0,  0)
GREY =   (128,128,128)
WHITE =  (255,255,255)
SKY =    (  0,192,240)
BLUE =   (  0,  0,255)
GREEN =  (  0,255,  0)
RED =    (255,  0,  0)
PURPLE = (217,  0,217)
VIOLET = (128,  0,255)
YELLOW = (251,255,  0)
ORANGE = (255,165,  0)

PINK_TRANSPARENT = (62, 0, 62)

colors = ['BLACK',
          'GREY',
          'WHITE',
          'SKY',
          'BLUE',
          'GREEN',
          'RED',
          'PURPLE',
          'VIOLET',
          'PINK_TRANSPARENT',
          'YELLOW',
          'ORANGE',
          ]

# images
p_size = 1
t = pygame.Surface((p_size, p_size), pygame.HWSURFACE, 8)
t.fill(WHITE)
WHITE_PIXEL = t

images = ['WHITE_PIXEL']


# Collect all the constants

codes = PLAYER_CODES + RENDERER_CODES + ENGINE_CODES

__all__ = events + animations + directions + movement_modifiers + colors +\
          images + codes
