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
from math import pi, cos
from random import randint, choice, random

import pygame

from tryengine.constants import *
from tryengine.utils import extend_dict, Timer, Borg, image_loader, fast_tint
from tryengine.animation import SpeedUpdateAnimationPlayer, Animation,\
    UpdateAnimationPlayer
from tryengine.mob import Mob
import tryengine.animation

from scripts.particles import ScoreText, AnimatedRandParticle, RandColorParticle,\
    RandImageParticle

# animations info
frame_size = (16,16)

ss_dir = "data/spritesheets/"

# some needed info for the animations
max_speed = 6.
updates_per_frame = 4

# collision rect
col_rect = pygame.Rect(2,0,14,24)

# Sounds
boom1_sound = pygame.mixer.Sound("data/sounds/fuego artificial 02.ogg")
boom2_sound = pygame.mixer.Sound("data/sounds/fuego artificial.ogg")
boom_sounds = [boom1_sound, boom2_sound]

# Globals and scores
glo = Borg()
SCORE_LIT = 500

class Firework(Mob):
    """ The sprite representing a firework. """
    def __init__(self, **obj):
        
        self.SCORE_LIT = SCORE_LIT
        
        filename =  split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        spritesheet = image_loader(filename)
        complete = spritesheet.subsurface(pygame.Rect(0 + 4*16, 144 + 3*16, 16, 16))
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
        
        # Smoke things
        self.update_counter = 0
        self.updates_per_smoke = 5
        smokes =  spritesheet.subsurface(pygame.Rect(0 + 8*16, 144 + 3*16, 4*16, 16))
        self.smoke_anim = UpdateAnimationPlayer(Animation(smokes, (16,16), False), self.updates_per_smoke)
        self.smoke_particle = {
            'animation': self.smoke_anim,
            "life_time": 60,
            "max_speed": .0,
            "min_speed": .0,
            "direction": pi / 2.,
            "delta_ang": pi / 8.,
            "gravity": 0.0,
            "fade_out_time": 100,
            "collides": False,
            }
        
        # Fire particles thing
        self.fire_color = (255,141,0)
        self.fire_particles_per_update = 4
        self.fire_particle = {
            "color":self.fire_color,
            "life_time": 8,
            "max_speed": 1.,
            "min_speed": 0.5,
            "direction": pi/2.,
            "delta_ang": pi,
            "gravity": 0.1,
            "size": (2,2),
            "ref_sprite": self,
            "fade_out_time":10,
            "collides": False,
            }
        
        
        self.__name__ = "Firework (Spawn coords: ({0},{1}); friendly name: {2}".format(obj["x"], obj["y"], obj["name"])
        
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
        
        
        # rocket science
        player_dict = {"animations": animations,
                "col_rect": col_rect,
                "friction_factor": 0.,
                "max_speed": max_speed, # see above
                "acceleration": 0.13,
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
        min_delay = 1.2
        max_delay = 1.6
        self.ignite_sound = pygame.mixer.Sound("data/sounds/cohete subiendo.ogg")
        self.ignite_sound.set_volume(0.15)
        self.explosion_delay = min_delay + (max_delay-min_delay)*random()
        # Lit = int with ticks until boom
        sparkles1 =  spritesheet.subsurface(pygame.Rect(0 + 12*16, 144 + 3*16, 2*16, 16)) #bolas
        sparkles2 =  spritesheet.subsurface(pygame.Rect(0 + 7*16, 144 + 3*16, 2*16, 16)) #chispas mecha
        sparkles3 =  spritesheet.subsurface(pygame.Rect(0 + 11*16, 144 + 4*16, 2*16, 16)) #centella no solida
        sparkles4 =  spritesheet.subsurface(pygame.Rect(0 + 13*15, 144 + 4*16, 6*16, 16)) #centella guai
        # pos x, pos y, tam x, tam y
        color_list = [WHITE, SKY, BLUE, GREEN, PURPLE, ORANGE, YELLOW, RED]
        
        
        sparkles = fast_tint(choice(color_list), sparkles4)
        sparkles_anim = Animation(sparkles, (16,16), False)
        sparkles_anim_player = UpdateAnimationPlayer(sparkles_anim, 60)
        self.lit = -1
        
        self.num_particles = 80
        self.color = color_list[randint(0,len(color_list) -1)]
        self.fuse_position = (1,13)
        self.rand_particle = {
            "animation":sparkles_anim_player,
            "life_time": 60,
            "max_speed": 4.8,
            "min_speed": 1.0,
            "direction": pi/2. + pi,
            "delta_ang": 2* pi,
            "gravity": 0.05,
            "fade_out_time":25,
            "friction_factor": 0.03,
            }


        self.speed_limit = 3.0
        self.has_gravity = True
        self.gravity = 0.1
        
        # Boom stuff
        self.boom_timer = None
        

        # Score text stuff
        self.font_size = 12

        # IF NOT THE TEXT LOOKS WRONG
        self.direction = DIR_RIGHT

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
        """ Some Firework special actions. """

        if self.lit > 0:
            self.lit -= 1

        elif self.lit == 0:
            if not self.boom_timer:
                self.ignite_sound.play()
                self.boom_timer = Timer(self.explosion_delay)
            #~ self.rand_particle["x"] = self.fuse_position[0] + self.rect[0] - 2
            #~ self.rand_particle["y"] = self.fuse_position[1] + self.rect[1] + 16
            if self.boom_timer and not self.boom_timer.finished:
                self.accel_up()
                self.update_counter += 1
                img = self.smoke_anim.get_next_frame()
                if self.update_counter % self.updates_per_smoke == 0:
                    x, y = self.rect.left, self.rect.center[1]
                    self.smoke_particle['image'] = img
                    self.smoke_particle['x'] = x+1
                    self.smoke_particle['y'] = y
                    p = RandImageParticle(**self.smoke_particle)
                    self.properly_add_ontop(p)

                # Draw the fire particles
                self.fire_particle['x'] = self.rect.center[0]
                self.fire_particle['y'] = self.rect.bottom 
                for i in xrange(self.fire_particles_per_update):
                    p = RandColorParticle(**self.fire_particle)
                    player.properly_add_ontop(p)

        if self.boom_timer and self.boom_timer.finished:
            self.rand_particle["x"] = self.rect.center[0]
            self.rand_particle["y"] = self.rect.center[1] 
            self.ignite_sound.stop()
            
            for i in xrange(self.num_particles):
                b=AnimatedRandParticle(**self.rand_particle)
                self.properly_add_ontop(b)
            boom_sounds[randint(0,len(boom_sounds) -1)].play()
            glo.score += self.SCORE_LIT
            r = self.rect
            sp = self.score_particle
            sp['x'] = r.left
            sp['y'] = r.top
            sp['text'] = SCORE_LIT
            self.properly_add_ontop(ScoreText(**sp))
            self.kill()

    def respawn(self):
        """ Moves the player sprite to the spawn position. """
        self.lit = -1
        self.movement_mods.append((POSITION_SET, self.start_position))

    def run_ai(self, *args):
        pass
