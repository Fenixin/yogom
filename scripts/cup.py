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

import pygame

from tryengine.mob import Mob
from tryengine.utils import extend_dict
from tryengine.constants import *
from tryengine.animation import SpeedUpdateAnimationPlayer, Animation
from tryengine.utils import load_sound, image_loader

# data for a cup

# animations info
frame_size = (24,24)

ss_dir = "data/spritesheets/"

class Cup(Mob):
    def __init__(self, **obj):
        """ Returns a Cup object with all the needed parameters """
        # animations
        # we need to create all the animations every time we create a cup, if not bad things will happen
        # Extract max_speed for animation purposes. For Mob movement it will be extracted in Mob class
        try:
            max_speed = obj['max_speed']
        except KeyError:
            max_speed = 0.2
        updates_per_frame = 9

        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)
        spritesheet = image_loader(filename)

        walk_right = spritesheet.subsurface(pygame.Rect(0,3*24, 4*24, 24))
        walk_left = spritesheet.subsurface(pygame.Rect(0,4*24, 4*24, 24))

        # Sounds
        self.hurt = load_sound("data/sounds/relaxing cup.ogg")
        ap_walk_right = SpeedUpdateAnimationPlayer(Animation(walk_right, frame_size, False), updates_per_frame, max_speed)
        ap_walk_left = SpeedUpdateAnimationPlayer(Animation(walk_left, frame_size, False), updates_per_frame, max_speed)

        # List animation PLAYERS in same order as states
        animations = {ANIMATION_IDLE: [ap_walk_left, ap_walk_right],
                      ANIMATION_WALKING: [ap_walk_left, ap_walk_right],
                      ANIMATION_BRAKING: [ap_walk_left, ap_walk_right],
                      ANIMATION_FALLING: [ap_walk_left, ap_walk_right],
                      ANIMATION_STOP: [ap_walk_left, ap_walk_right],
                      ANIMATION_JUMP: [ap_walk_left, ap_walk_right],
                      ANIMATION_SHOOT: [ap_walk_left, ap_walk_right]}

        # Arguments to use with Cup object
        cup = {"animations": animations,
                "col_rect": pygame.Rect(7,12,10,12),
                "friction_factor": 0.5,
                "acceleration": 0.2,
                } 
        extend_dict(cup, obj)
        
        # call the parent
        Mob.__init__(self, **cup)
        
        # debugging?
        self.debugging = False
        
        # Amount of updates that the player will feel damaged
        # (and will go through platforms)
        self.plat_damage = 15 # updates
        self.inmune_damage = 80 # updates
        # Speed to add to the player when hit by a mob:
        # (right direction, left will be mult by -1)
        self.damage_speed = (2,-2)

    def run_ai(self, platforms, player):
        """ Basic automata that walks left and right """
        
        # if the player is controlling this mob skip this
        if self.player_controlled:
            return
        
        # restart the counter if it's too big
        self.counter += 1
        c = self.counter
        if self.counter > 100000:
            self.counter = 0

        if c % self.gonna_frames_skip == 0:
            if self.gonna_bump(platforms):
                #~ print "gonnabumpl!!!"
                self.change_direction()
            if self.has_gravity and self.gonna_fall(platforms):
                self.change_direction()
                #~ print "gonnafall!!!"
        
        # Always walking
        if self.direction == LOOKING_LEFT:
            self.accel_left()
        else:
            self.accel_right()

    def custom_update_actions(self, platforms, new_sprites_group, player):
        if self.col_rect.colliderect(player.col_rect):
            
            if player.inmunity_damage == 0 and not player.winning and not player.loosing:
                xs, ys = self.damage_speed
                if self.col_rect.colliderect(player.col_rect_left):
                    xs = xs
                elif self.col_rect.colliderect(player.col_rect_right):
                    xs *= -1
                else:
                    print "I'm in Cup.custom_update_actions! This should not happen!"
                    x_speed = 0
                player.hurt(self.plat_damage, self.inmune_damage)
                
                player.movement_mods.append((SPEED_ADD, (xs,ys)))
                self.hurt.play()
                
