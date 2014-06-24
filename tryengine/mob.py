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

""" Basic mob class, that uses TrySprite to work.

If you want a typical mob moving around you should take this class as 
parent.
 """

from math import copysign
from random import randint

from pygame import event, font

import automata
from sprites import AnimatedSprite, TryMovingSprite
from animation import SpeedUpdateAnimationPlayer
from utils import Timer
from aparser import ArgumentParser, ErrorParsingArgument
from constants import *


class ParseMobError(Exception):
    """ Error parsing the arguments of a Mob. """

    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)

######################
# TODO TODO TODO:
# we could add a new module that imports all the mobs
# so we can add mobs in level.py as we do with actionsprites

#font render
small_font = font.Font(font.get_default_font(), 8)

#### generic automata
# States for automata:
#  0 STOP
#  1 WALKING

prob_without_player = prob_with_player = ( (0.0, 1.0),
                                            (0.0, 1.0) )

generic_matrixes = [prob_without_player, prob_with_player]

# dict for turtle automata
generic_automata = {"num_states": 2,
                    "states_prob_matrixes": generic_matrixes,
                    "min_time_state": (0.0, 5.0) }


class Mob(AnimatedSprite, TryMovingSprite):
    """ Stores all the info for a mob, AI included. 
        Needed parameteres:
         animations
         x
         y
         col_rect
         
        Not needed, defaulted parameteres:
         automata
         max_speed
         acceleration
         frection_factor
    """
    def __init__(self, **kwargs):
        
        # check for the basic parameteres to call AnimatedSprite and BetterSprite
        animations = kwargs["animations"]
        x = kwargs["x"]
        y = kwargs["y"]
        col_rect = kwargs["col_rect"]

        self.start_position = (x,y) # used for restarting the player if dead

        # constants that were in player, this should be here or in bettersprite?
        # can he jump right now?
        self.jump_available = True
        # have he to jump next update?
        self.jump = False
        # have we hit jump last frame?
        self.last_frame_jump = False
        # have to shoot next update?
        self.shoot = False
        # is the player trying to move? (pressing a move key?)
        self.moving = False
        # touching ground?
        self.touch_ground = False
        # is the player falling?
        self.falling = False
        # do we want to use anything?
        self.use = False
        # Gravity to apply to this mob
        self.gravity = 0.5
        # Touch ground in this frame?
        self.just_touch_ground = False
        # Is braking? TODO: player uses a new function/property
        # which conflicts with this, transfer that method over here?
        #~ self.braking = False
        # Using?
        self.using = False
        # Speed minimun, after thata is put to zero
        self.min_speed = 0.01

        # call the parent and override a lot of defaulted variables
        AnimatedSprite.__init__(self, animations, x, y, col_rect)
        TryMovingSprite.__init__(self, self.image, x, y, col_rect)
        
        # start filling the class
        self.custom_properties = {
            "jump_speed": { "type": float, "destination" : "jump_speed", "default": -5 },
            "automata": { "type": automata.Automata, "destination" : "automata", "default": None },
            "has_gravity": {"type": bool, "destination" : "has_gravity", "default": True},
            "max_speed": {"type": float, "destination" : "max_speed", "default": 0.2},
            "acceleration": {"type": float, "destination" : "acceleration", "default": 0.2},
            "direction": {"type": int, "destination" : "direction", "default": LOOKING_LEFT},
            "acceleration": {"type": float, "destination" : "acceleration", "default": 0.5},
            "friction_factor": {"type": float, "destination" : "friction_factor", "default": 0.5},
            "name" : {"type": str, "destination": "name"},
            "hostile": {"type": bool, "destination": "hostile", "default": False},
            "accel_on_air":{"type": bool, "destination": "accel_on_air", "default": False},
            "killable":{"type": bool, "destination": "killable", "default": False},
            }

        self.parser = ArgumentParser(self.custom_properties, kwargs, self.__dict__)
        self.parse_catching_errors(self.custom_properties, kwargs, self.__dict__)
        
        # insert the generic automata if it's None
        if self.automata == None:
            self.automata = automata.TimedAutomata(**generic_automata)
            self.automata.set_state(randint(0,1))
        
        # an image with the friendly name given in tiled
        self.debug_image = small_font.render(self.name, False, GREY, PINK_TRANSPARENT)
        self.debug_image.set_colorkey(PINK_TRANSPARENT)
        #~ self.debug_sprite = DebugSprite(self.debug_image, x, y, self)

        # other stuff
        self.changing_direction = False
        # Timer to control if the mob is idle
        self.idle_timer = Timer(5) # TODO! add an option to be able to set this externally
        # used to control animations
        self.moving_last_frame = False

        # is this mob controlled by a player?
        self.player_controlled = False
        
        # the ai doesn't need to run every frame
        # this can be setted by mob
        self.ai_frames_skip = 40
        self.gonna_frames_skip = 10
        self.counter = 0


    def parse_catching_errors(self, definitions, arguments, destination):
        try:
            self.parser.parse(definitions, arguments, destination)
        except ErrorParsingArgument, e:
            msg = "The mob \"{0}\" in coords x = {1}, y = {2} gave the next error while parsing:\n {3}".format(self, arguments["x"], arguments["y"], e.msg)
            raise ParseMobError(msg)


    def update_animation(self):
        """ Detect the correct animation and update the image of the 
            sprite.
            
            It detects the generic animation defined in utils.py/other
            constants, being these:
            ANIMATION_STOP, ANIMATION_IDLE, ANIMATION_WALKING,
            ANIMATION_JUMP, ANIMATION_SHOOT, ANIMATION_FALLING. """
        
        old = self.image
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
        
        # if the player is controlling this mob skip this
        if self.player_controlled:
            return
        
        # restart the counter if it's too big
        self.counter += 1
        c = self.counter
        if self.counter > 100000:
            self.counter = 0
        
        #update automata
        if c % self.ai_frames_skip == 0:
            self.automata.next_timed_state()
        state = self.automata.get_state()
        
        if c % self.gonna_frames_skip == 0:
            if self.gonna_bump(platforms):
                #~ print "gonnabumpl!!!"
                self.change_direction()
            if self.has_gravity and self.gonna_fall(platforms):
                self.change_direction()
                #~ print "gonnafall!!!"
        
        if state == 1: # walking
            if self.direction == LOOKING_LEFT:
                self.accel_left()
            else:
                self.accel_right()

    def get_events(self):
        l = event.get(PLAYER)
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

        # TODO: blah, this is hell, blah
        if self.has_gravity: self.apply_gravity()
        if self.jump:
            self.last_frame_jump = True
            self.jump = False
            if not self.falling:
                if self.jump_internal():
                    pass
        else:
            self.last_frame_jump = False
        # calculate the speed and move
        self.apply_movement_mods()
        top, bottom, left, right = self.move_colliding(platforms)
        self.update_status(top, bottom, left, right)
        
        # Needed, if not the speed get ridiculous small values
        if abs(self.vx) < self.min_speed:
            self.vx = 0.0
        if abs(self.vy) < self.min_speed:
            self.vy = 0.0

        #~ self.move_sprite_float(self.vx, self.vy)
        # get the next frame image
        self.update_animation()
        # movement for this frame is done
        
        # time to move
        self.run_ai(platforms, player)
        # custom things
        self.custom_update_actions(platforms, new_sprites_group, player)
        
        self.moving = False
        self.using = False

    def update_status(self,top, bottom, left, right):
        # Stuff for sprite status
        if bottom:
            if not self.touch_ground:
                self.just_touch_ground = True
            self.touch_ground = True
            self.jump_available = True
            if not self.moving:
                self.friction()
        else:
            # NOTE: hacky stuff
            # WARNING
            if self.vy > 1.5:
                self.falling = True
            else:
                self.falling = False
            if self.falling:
                self.touch_ground = False
            self.just_touch_ground = False

    def custom_update_actions(self, platforms, new_sprites_group, player):
        """ Experimental. It will be called at the end of the generic
            update function in Mob. You can override this method and
            will be called in the generic update. """
        
        pass

    def use_next_frame(self):
        """ Use whatever thing we've got near. """
        self.use = True

    def set_speed_x(self,speed):
        self.vx = speed
    
    def set_speed_y(self,speed):
        self.vy = speed

    def add_speed_x(self, speed):
        self.vx += speed

    def add_speed_y(self, speed):
        self.vy += speed

    def secure_add_speed_x(self, speed):
        if (speed > 0 and self.vx < 0) or (speed < 0 and self.vx > 0):
            self.vx += speed
        elif not abs(self.vx) >= self.max_speed:
            self.vx += speed

    def secure_add_speed_y(self, speed):
        self.add_speed_y(speed)
        if abs(self.vy) > self.max_speed:
            self.vy = copysign(self.max_speed, self.vy)

    def accel_right(self):
        """ Accel the mob to the right by his own will.
        
            This is the correct method to use if you want to move the 
            mob by its own self. Or the player because he pushed a key.
            """
        self.moving = True
        self.direction = LOOKING_RIGHT
        self.secure_add_speed_x(self.acceleration)

    def accel_left(self):
        """ Accel the mob to the left by his own will.
        
            This is the correct method to use if you want to move the 
            mob by its own self. Or the player because he pushed a key.
            """
        self.moving = True
        self.direction = LOOKING_LEFT
        self.secure_add_speed_x(self.acceleration * -1.)

    def accel_up(self):
        self.moving = True
        self.secure_add_speed_y(self.acceleration * -1.)

    def accel_down(self):
        self.moving = True
        self.secure_add_speed_y(self.acceleration)

    def accel_y(self):
        self.secure_add_speed_y(self.acceleration)

    def shoot_next_frame(self):
        """ Run this method to shoot the next frame. """
        self.shoot = True

    def respawn(self):
        """ Moves the player sprite to the spawn position. """
        self.movement_mods.append((POSITION_SET, self.start_position))

