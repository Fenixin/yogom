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
from math import hypot
from random import randint

import pygame
from pygame import Rect

from tryengine.mob import Mob
from tryengine.utils import extend_dict, Timer, image_loader
from tryengine.constants import *
from tryengine.animation import SpeedUpdateAnimationPlayer, Animation, UpdateAnimationPlayer
from tryengine.utils import load_sound
import settings as s

# data for a Pigeon

ss_dir = "data/spritesheets"

#### generic automata
# States for automata:
#  0 STOP
#  1 flying

prob_without_player = prob_with_player = ( (2.0, 1.0),
                                            (2.0, 1.0) )

generic_matrixes = [prob_without_player, prob_with_player]

# dict for turtle automata
pigeon_automata = {"num_states": 2,
                    "states_prob_matrixes": generic_matrixes,
                    "min_time_state": (3.0, 5.0) }


# animations info
frame_size = (16,16)

ANIMATION_FLYING = ANIMATION_OTHERS + 0

# Sounds
hurt = load_sound("data/sounds/relaxing cup.ogg")
fly_over = load_sound("data/sounds/paloma sobrevolando.ogg")
fly_over.set_volume(0.4)


class Pigeon(Mob):
    def __init__(self, **obj):
        """ Returns a Pigeon object with all the needed parameters """
        # animations
        # we need to create all the animations every time we create a cup, if not bad things will happen
        max_speed = 0.5
        updates_per_frame = 8
        
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        # Spritesheets
        spritesheet = image_loader(filename)

        pigeon_ss = spritesheet.subsurface(Rect(0,9*16, 6*16, 16))

        stay_right = pigeon_ss.subsurface(Rect(0,0,16,16))
        stay_left = pigeon_ss.subsurface(Rect(3*16,0,16,16))

        fly_right = pigeon_ss.subsurface(Rect(0*16,0,16*3,16))
        fly_left = pigeon_ss.subsurface(Rect(3*16,0,16*3,16))

        # Animations
        ap_stay_left = SpeedUpdateAnimationPlayer(Animation(stay_left, frame_size, False), updates_per_frame, max_speed)
        ap_stay_right = SpeedUpdateAnimationPlayer(Animation(stay_right, frame_size, False), updates_per_frame, max_speed)

        ap_fly_left = UpdateAnimationPlayer(Animation(fly_left, frame_size, False), updates_per_frame)
        ap_fly_right = UpdateAnimationPlayer(Animation(fly_right, frame_size, False), updates_per_frame)


        # list animation PLAYERS in same order as states
        animations = {ANIMATION_IDLE: [ap_stay_left, ap_stay_right],
                      ANIMATION_WALKING: [ap_stay_left, ap_stay_right],
                      ANIMATION_BRAKING: [ap_stay_left, ap_stay_right],
                      ANIMATION_FALLING: [ap_stay_left, ap_stay_right],
                      ANIMATION_STOP: [ap_stay_left, ap_stay_right],
                      ANIMATION_JUMP: [ap_stay_left, ap_stay_right],
                      ANIMATION_SHOOT: [ap_stay_left, ap_stay_right],
                      ANIMATION_FLYING: [ap_fly_left, ap_fly_right],
                      }

        # arguments to use with bird object
        bird = {"animations": animations,
                "col_rect": pygame.Rect(5,3,12,14),
                "friction_factor": 1.5,
                "acceleration": 0.2,
                "max_speed": max_speed} 
        extend_dict(bird, obj)
        
        # call the parent
        Mob.__init__(self, **bird)
        
        # Custom stuff
        self.has_gravity = False
        
        # debugging?
        self.debugging = False
        
        # Amount of damage to make to player
        self.damage = 0.35 # updates, default 1
        
        # Another rect outside of self.rect, on the floor
        self.outside_floor_rect = self.feet_rect.move(0,1)
        
        # It will go to random places in the screen
        self.new_place_to_go()
        self.staying_timer = Timer(3)
        
        # Sounds stuff
        self.updates_per_fly_over = 40
        self.fly_over_counter = 0
        
        

    def new_place_to_go(self):
        self.place_to_go = (randint( 2, s.screen_size_in_tiles[0] -2 ) * 16, (randint( 2, s.screen_size_in_tiles[0] -2) * 16))

    def update_animation(self):
        """ Detect the correct animation and update the image of the 
            sprite.
            
            It detects the generic animation defined in utils.py/other
            constants, being these:
            ANIMATION_STOP, ANIMATION_IDLE, ANIMATION_WALKING,
            ANIMATION_JUMP, ANIMATION_SHOOT, ANIMATION_FALLING. """
        
        old = self.image
        """
        if self.vx == 0.0:
            self.braking = False
            if not self.moving_last_frame:
                if self.idle_timer.finished:
                    current_animation = self.animations[ANIMATION_IDLE]
                else:
                    current_animation = self.animations[ANIMATION_STOP]
            else:
                self.moving_last_frame = False
                self.idle_timer.reset()
                current_animation = self.animations[ANIMATION_STOP]
        else: # we've got movement!
            self.moving_last_frame = True
            if self.touch_ground:
                if self.moving:
                    current_animation = self.animations[ANIMATION_WALKING]
                    self.braking = False
                else:
                    self.braking = True
                    current_animation = self.animations[ANIMATION_BRAKING]
            else: # we are flying!
                if self.vy < 0.0:
                    current_animation = self.animations[ANIMATION_JUMP]
                else:
                    current_animation = self.animations[ANIMATION_FALLING]
        """
        current_animation = self.animations[ANIMATION_FLYING]
        
        # choose the correct direction
        current_animation = current_animation[self.direction]
        
        # don't do the moonwalker if we are sliding backwards
        vx = self.vx
        if (self.direction == LOOKING_RIGHT and self.vx < 0) or \
           (self.direction == LOOKING_LEFT and self.vx > 0):
            vx = 0
        
        # retrieve the frame using the correct method depending on the
        # animation player
        if isinstance(current_animation, SpeedUpdateAnimationPlayer):
            if abs(self.vx) < 0.01:
                self.image = current_animation.reset()
                self.image = current_animation.get_next_frame(vx)
            else:
                self.image = current_animation.get_next_frame(vx)
        else: # is a time animation, no need for speed
            self.image = current_animation.get_next_frame()
        
        if self.image is not old:
            self.dirty = 1
        
        # Needed, if not the speed get ridiculous small values
        if abs(self.vx) < 0.05:
            self.vx = 0.0
        if abs(self.vy) < 0.05:
            self.vy = 0.0

    def change_direction(self):
        """ Switch from one direction to another. Used in the generic
            AI. """

        if self.direction == LOOKING_LEFT:
            self.direction = LOOKING_RIGHT
        else:
            self.direction = LOOKING_LEFT


    def run_ai(self, platforms, player):
        """ Runs the generic autoamata, skips the whole function if 
        the player is controlling this mob. """
        dx = self.place_to_go[0] - self.rect[0]
        dy =  self.place_to_go[1] - self.rect[1]
        distance = hypot(dx,dy)
        #~ print dx, dy, distance
        if distance < 5 or not self.staying_timer.finished:
            self.vx = self.vy = 0.0
            if self.staying_timer.finished:
                self.staying_timer.reset()
                self.new_place_to_go()

        else:
            if abs(dx) < 3:
                self.vx = 0.0
            elif dx > 0:
                self.accel_right()
            else:
                self.accel_left()
            if abs(dy) < 3:
                self.vy = 0
            elif dy > 0:
                self.accel_down()
            else:
                self.accel_up()
        
    def get_events(self):
        l = pygame.event.get(PLAYER)
        for e in l:
            if e.code == LEFT:
                self.moving = True
                self.accel_left()
            elif e.code == RIGHT:
                self.accel_right()
                self.moving = True
            elif e.code == JUMP:
                self.jump = True
            elif e.code == USE:
                self.using = True
                self.use_next_frame()
            elif e.code == SHOOT:
                self.shoot_next_frame()
            elif e.code == RESPAWN:
                self.respawn()

    def update(self, platforms, new_sprites_group, player):
        """ Generic mob update function. For a very basic mob you can
            modify the method used here and get the mob moving. """
        
        if self.player_controlled:
            self.get_events()
        
        # Apply all the modifications to the speed

        # TODO
        if self.has_gravity: self.apply_gravity()
        if self.jump and not self.falling:

            self.jump = False
            self.jump_internal()
            self.touch_ground = False

        # calculate the speed and move
        self.apply_movement_mods()
        #~ top, bottom, left, right = self.move_colliding(platforms)
        self.move_sprite_float(self.vx, self.vy)

        # get the next frame image
        self.update_animation()
        # movement for this frame is done
        
        # time to move
        self.run_ai(platforms, player)
        # custom things
        self.custom_update_actions(platforms, new_sprites_group, player)
        
        self.moving = False
        self.using = False

    def custom_update_actions(self, platforms, new_sprites_group, player):
        """ Experimental. It will be called at the end of the generic
            update function in Mob. You can override this method and
            will be called in the generic update. """
        
        px, py = player.rect.center
        sx, sy = self.rect.center
        p_dis = hypot(sx - px, sy - py)
        if p_dis < 20 and not player.winning and not player.inmunity_damage and not player.loosing:
            player.lit_taken += self.damage
            
            if self.fly_over_counter % self.updates_per_fly_over == 0:
                fly_over.play()
            self.fly_over_counter += 1
        else:
            self.fly_over_counter = 0
            
