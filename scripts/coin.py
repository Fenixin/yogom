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

from os.path import join, split

from math import cos

from pygame import Rect, mixer

from tryengine.constants import *
from tryengine.utils import extend_dict, Borg, image_loader
from tryengine.animation import Animation, UpdateAnimationPlayer
from tryengine.mob import Mob
from scripts.particles import ScoreText


# all the info to create a player object

# animations info
frame_size = (16,16)

ss_dir = "data/spritesheets/"

# some needed info for the animations
max_speed = 1.
updates_per_frame = 4


# collision rect
col_rect = Rect(0,0,16,16)

# Sounds
coin_sound = mixer.Sound("data/sounds/moneda.ogg")
coin_sound.set_volume(0.25)

# Globals and scores
glo = Borg()
SCORE_COIN = 100

class Coin(Mob):
    
    def __init__(self, **obj):
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        spritesheet = image_loader(filename)
        # sprites 16x16 size in (0,144)
        coin = spritesheet.subsurface(Rect(3*16, 144 + 4 *16, 16*6, 16))
        animationplayer = UpdateAnimationPlayer(Animation(coin, frame_size, False), updates_per_frame)

        animations = {ANIMATION_STOP: [animationplayer, animationplayer], 
            ANIMATION_IDLE: [animationplayer, animationplayer],
            ANIMATION_WALKING: [animationplayer, animationplayer],
            ANIMATION_JUMP: [animationplayer, animationplayer],
            ANIMATION_FALLING: [animationplayer, animationplayer],
            ANIMATION_SHOOT: [animationplayer, animationplayer]}
        
        self.__name__ = "Coin (Spawn coords: ({0},{1}); friendly name: {2}".format(obj["x"], obj["y"], obj["name"])
        
        player_dict = {"animations": animations,
                "col_rect": col_rect,
                "friction_factor": 0.1,
                "max_speed": max_speed, # see above
                "acceleration": 0.9,
                "jump_speed": 0.5} 
        extend_dict(player_dict, obj)

        # Score particle
        score_layers = [('shadows',{'positions_and_colors':[((1,1),GREY)]}),
                       ('normal', {'color':WHITE}),
                       ]
        amplitude_speed = 0.3
        self.score_particle = {
           'text_layers': score_layers,
           'font_size': 8,
           'bg_color': BLACK,
           'bg_transparent': True,
           'gravity': 0.0,
           'life_time':200,
           'fade_out_time':10,
           'vx_function': lambda vx, age: amplitude_speed*cos(age/13.),
           'vy_function': lambda vy, age: -0.1
           }

        # Call the parent's constructor
        Mob.__init__(self, **player_dict)

        # is this mob controlled by a player?
        self.player_controlled = False
        self.has_gravity = False

    def custom_update_actions(self, platforms, new_sprites_group, player):
        """ Some Player special actions. """

        # IF NOT THE TEXT LOOKS WRONG
        self.direction = DIR_RIGHT
        
        if self.visible and player.col_rect.colliderect(self.col_rect):
            self.taken()

    def taken(self):
        self.visible = False
        glo.score += SCORE_COIN
        coin_sound.play()
        r = self.rect
        sp = self.score_particle
        sp['x'] = r.left
        sp['y'] = r.top
        sp['text'] = SCORE_COIN
        self.properly_add_ontop(ScoreText(**sp))

    def respawn(self):
        """ Moves the player sprite to the spawn position. """
        self.movement_mods.append((POSITION_SET, self.start_position))
        self.visible = True

    def run_ai(self, *args):
        pass
