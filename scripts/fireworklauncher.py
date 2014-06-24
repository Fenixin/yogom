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
from math import pi, hypot

import pygame

from tryengine.constants import *
from tryengine.utils import extend_dict, Timer, Borg, image_loader
from tryengine.animation import SpeedUpdateAnimationPlayer, Animation
from tryengine.mob import Mob
from firework import Firework
from scripts.particles import RandColorParticle

# animations info
frame_size = (16,16)

ss_dir = "data/spritesheets/"

# some needed info for the animations
max_speed = 1.
updates_per_frame = 4


# collision rect
col_rect = pygame.Rect(2,0,16,16)


# Sounds
ignite_sound = pygame.mixer.Sound("data/sounds/mecha.ogg")
ignite_sound.set_volume(0.5)

# Globals and scores
glo = Borg()
SCORE_LIT = 250

class FireworkLauncher(Mob):
    """ The sprite representing a firework. """
    def __init__(self, **obj):
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        spritesheet = image_loader(filename)
        # sprites 16x16 size in (0,144)
        #~ top = spritesheet.subsurface(pygame.Rect(0 + 4*16, 154 + 1*16, 16, 16)
        #~ bottom = spritesheet.subsurface(pygame.Rect(0 + 4*16, 154 + 2*16, 16, 16)
        complete = spritesheet.subsurface(pygame.Rect(0 + 4*16, 144 + 2*16, 16, 16))

        animationplayer = SpeedUpdateAnimationPlayer(Animation(complete, frame_size), updates_per_frame, max_speed)
        other_animation = Animation(complete, frame_size)
        other_animation.mirror()
        other_animationplayer = SpeedUpdateAnimationPlayer(other_animation, updates_per_frame, max_speed)

        animations = {ANIMATION_STOP: [other_animationplayer, animationplayer], 
            ANIMATION_IDLE: [other_animationplayer, animationplayer],
            ANIMATION_WALKING: [other_animationplayer, animationplayer],
            ANIMATION_JUMP: [other_animationplayer, animationplayer],
            ANIMATION_FALLING: [other_animationplayer, animationplayer],
            ANIMATION_SHOOT: [other_animationplayer, animationplayer]}
        
        self.__name__ = "Firework (Spawn coords: ({0},{1}); friendly name: {2}".format(obj["x"], obj["y"], obj["name"])
        
        player_dict = {"animations": animations,
                "col_rect": col_rect,
                "friction_factor": 0.1,
                "max_speed": max_speed, # see above
                "acceleration": 0.01,
                "jump_speed": 0.5} 
        extend_dict(player_dict, obj)

        # Call the parent's constructor
        Mob.__init__(self, **player_dict)

        # is this mob controlled by a player?
        self.player_controlled = False

        # Timer for running
        self.time_before_running = 10.0
        self.multiplier = 1.
        self.max_multiplier = 2.0
        
        self.running_timer = Timer(self.time_before_running)

        self.base_max_speed = self.max_speed
        
        self.debugging = False
        
        
        # Fuse stuff
        self.lit = False
        self.fuse_color = (255,50,150)
        self.fuse_position = (1,13)
        self.rand_particle = {
            "color": self.fuse_color,
            "life_time": 15,
            "max_speed": .5,
            "min_speed": .0,
            "direction": pi/2. + pi,
            "delta_ang": 2* pi,
            "gravity": 0.0,
            "size": (1,1),
            "fade_out_time":15,
            }

        

        self.speed_limit = 3.0
        self.has_gravity = True
        self.gravity = 0.1
        
        # Add the actual firework
        self.first_time = True
        self.d = obj
        
        # Score stuff
        self.SCORE_LIT = SCORE_LIT
        
        # Sound stuff
        self.ignite_sound = ignite_sound

    def jump_internal(self):
        #~ # old version, security copy
        self.jump_speed_x = 1.1
        if self.multiplier >= self.max_multiplier:
            self.vy += -6.
            if self.direction == LOOKING_LEFT:
                #~ print "adding speed!"
                self.vx += - 1 * self.jump_speed_x
            else:
                #~ print "adding speed!"
                self.vx += self.jump_speed_x
        else:
            self.vy += self.jump_speed

    def custom_update_actions(self, platforms, new_sprites_group, player):
        """ Some Player special actions. """


        # Add the firework
        if self.first_time:
            self.first_time = False
            # Add the firework a little on top of the launcher
            self.d["x"] = self.rect.x
            self.d["y"] = self.rect.y - 8
            f = Firework(**self.d)

            self.properly_add_ontop(f)

        # IF NOT THE TEXT LOOKS WRONG
        self.direction = DIR_RIGHT

        # NOTE: This is lit in player.py

        if self.lit and not player.winning:

            self.rand_particle["x"] = self.fuse_position[0] + self.rect[0] - 2
            self.rand_particle["y"] = self.fuse_position[1] + self.rect[1]
            p = RandColorParticle(**self.rand_particle)
            self.properly_add_below(p)
        
        if hypot(self.vx, self.vy) > self.speed_limit:
            self.lit = False

    def respawn(self):
        """ Moves the player sprite to the spawn position. """
        self.lit = False
        self.movement_mods.append((POSITION_SET, self.start_position))

    def run_ai(self, *args):
        pass
