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
from math import pi, hypot, ceil, cos

from pygame import Rect, event

from tryengine.constants import *
from tryengine.utils import extend_dict, Timer, load_sound, Borg, image_loader
from tryengine.animation import SpeedUpdateAnimationPlayer, Animation,\
                            OnceUpdateAnimationPlayer, UpdateAnimationPlayer
from tryengine.mob import Mob
from fireworklauncher import FireworkLauncher
from scripts.particles import RandColorParticle, ScoreText


glo = Borg()

# animations info
frame_size = (24, 24)
max_speed = 1.3 # default 1.3
updates_per_frame = 6    # default 4
updates_per_frame_slow = 14
updates_per_frame_smoke = 18

ss_dir = "data/spritesheets/"

ANIMATION_DAMAGE = ANIMATION_OTHERS + 0
ANIMATION_LOOSING = ANIMATION_OTHERS + 1
ANIMATION_LOSER = ANIMATION_OTHERS + 2
ANIMATION_WINNING = ANIMATION_OTHERS + 3

# collision rect
col_rect = Rect(6,7,10,17)

# Sounds
jump_sound = load_sound("data/sounds/salto.ogg")
jump_sound.set_volume(0.6)
fall_sound = load_sound("data/sounds/caida.ogg")
step1_sound = load_sound("data/sounds/paso 01.ogg")
step1_sound.set_volume(0.7)
step2_sound = load_sound("data/sounds/paso 02.ogg")
step2_sound.set_volume(0.7)
brake_sound1 = load_sound("data/sounds/frenazo 01.ogg")
brake_sound2 = load_sound("data/sounds/frenazo 02.ogg")
brake_sound3 = load_sound("data/sounds/frenazo 03.ogg")
brake_sounds = [brake_sound1, brake_sound2, brake_sound3]
game_over_sound = load_sound("data/sounds/game over.ogg")
ouch_sound = load_sound("data/sounds/ouch.ogg")


class Player(Mob):
    """ The sprite representing the player. """
    def __init__(self, **obj):
        
        # Load spritesheet and get animations
        filename = split(obj['parent'].tilesets[0].source)[-1]
        filename = join(ss_dir, filename)

        spritesheet = image_loader(filename)
        walk_right = spritesheet.subsurface(Rect(0,0, 4*24, 24))
        walk_left = spritesheet.subsurface(Rect(0,1*24, 4*24, 24))
        brake_right = spritesheet.subsurface(Rect(5*24,0*24, 24, 24))
        brake_left = spritesheet.subsurface(Rect(5*24,1*24, 24, 24))
        #~ fall_right = spritesheet.subsurface(Rect(4*24,0, 24, 24))
        #~ fall_left = spritesheet.subsurface(Rect(5*24,24, 24, 24))
        jump_right = spritesheet.subsurface(Rect(4*24,0, 24, 24))
        jump_left = spritesheet.subsurface(Rect(4*24,24, 24, 24))
        crouch_right = spritesheet.subsurface(Rect(11*24, 0, 24, 24))
        crouch_left = spritesheet.subsurface(Rect(11*24, 24, 24, 24))
        fall_right = spritesheet.subsurface(Rect(0*24, 2*24, 24, 24))
        fall_left = spritesheet.subsurface(Rect(5*24, 2*24, 24, 24))
        stay_right = spritesheet.subsurface(Rect(12*24, 0*24, 24, 24))
        stay_left = spritesheet.subsurface(Rect(12*24, 1*24, 24, 24))
        loosing_right = spritesheet.subsurface(Rect(0*24, 2*24, 24*4, 24))
        loosing_left = spritesheet.subsurface(Rect(5*24, 2*24, 24*4, 24))
        loser_right = spritesheet.subsurface(Rect(3*24, 2*24, 24*2, 24))
        loser_left = spritesheet.subsurface(Rect(8*24, 2*24, 24*2, 24))
        winning_left = winning_right = spritesheet.subsurface(Rect(8*24, 5*24, 24*2, 24))

        ap_walk_right = SpeedUpdateAnimationPlayer(Animation(walk_right, frame_size, False), updates_per_frame, max_speed)
        ap_walk_left = SpeedUpdateAnimationPlayer(Animation(walk_left, frame_size, False), updates_per_frame, max_speed)

        # Brake
        ap_brake_right = SpeedUpdateAnimationPlayer(Animation(brake_right, frame_size, False), updates_per_frame, max_speed)
        ap_brake_left = SpeedUpdateAnimationPlayer(Animation(brake_left, frame_size, False), updates_per_frame, max_speed)

        # Jump and falling
        ap_jump_right = SpeedUpdateAnimationPlayer(Animation(jump_right, frame_size, False), updates_per_frame, max_speed)
        ap_jump_left = SpeedUpdateAnimationPlayer(Animation(jump_left, frame_size, False), updates_per_frame, max_speed)

        # Crouch
        ap_crouch_right = SpeedUpdateAnimationPlayer(Animation(crouch_right, frame_size, False), updates_per_frame, max_speed)
        ap_crouch_left = SpeedUpdateAnimationPlayer(Animation(crouch_left, frame_size, False), updates_per_frame, max_speed)

        # Damaged
        ap_damage_right = SpeedUpdateAnimationPlayer(Animation(fall_right, frame_size, False), updates_per_frame, max_speed)
        ap_damage_left = SpeedUpdateAnimationPlayer(Animation(fall_left, frame_size, False), updates_per_frame, max_speed)

        # Stay
        ap_stay_right = SpeedUpdateAnimationPlayer(Animation(stay_right, frame_size, False), updates_per_frame, max_speed)
        ap_stay_left = SpeedUpdateAnimationPlayer(Animation(stay_left, frame_size, False), updates_per_frame, max_speed)

        # Loosing
        ap_loosing_right = OnceUpdateAnimationPlayer(Animation(loosing_right, frame_size, False), updates_per_frame_slow)
        ap_loosing_left = OnceUpdateAnimationPlayer(Animation(loosing_left, frame_size, False), updates_per_frame_slow)

        # Loser
        ap_loser_right = UpdateAnimationPlayer(Animation(loser_right, frame_size, False), updates_per_frame_smoke)
        ap_loser_left = UpdateAnimationPlayer(Animation(loser_left, frame_size, False), updates_per_frame_smoke)

        # Winning
        ap_winning_right = ap_winning_left = UpdateAnimationPlayer(Animation(winning_left, frame_size, False), updates_per_frame_slow)

        player_animations = {
                ANIMATION_STOP: [ap_stay_left, ap_stay_right],
                ANIMATION_IDLE: [ap_stay_left, ap_stay_right],
                ANIMATION_WALKING: [ap_walk_left, ap_walk_right],
                ANIMATION_JUMP: [ap_jump_left, ap_jump_right],
                ANIMATION_FALLING: [ap_jump_left, ap_jump_right],
                ANIMATION_BRAKING: [ap_brake_left, ap_brake_right],
                ANIMATION_SHOOT: [ap_walk_left, ap_walk_right],
                ANIMATION_CROUCH: [ap_crouch_left, ap_crouch_right],
                ANIMATION_DAMAGE: [ap_damage_left, ap_damage_right],
                ANIMATION_LOOSING: [ap_loosing_left, ap_loosing_right],
                ANIMATION_LOSER: [ap_loser_left, ap_loser_right],
                ANIMATION_WINNING: [ap_winning_right, ap_winning_right],
                }

        self.__name__ = "Player (Spawn coords: ({0},{1}); friendly name: {2}".format(obj["x"], obj["y"], obj["name"])

        #~ Changes in playability
        player_dict = {"animations": player_animations,
                "col_rect": col_rect,
                "friction_factor": 0.1,
                "max_speed": max_speed,  # See above max_speed = 1.3
                "acceleration": 0.09,
                "jump_speed": -1.0}
        extend_dict(player_dict, obj)

        # Call the parent's constructor
        Mob.__init__(self, **player_dict)

        # Is this mob controlled by a player?
        self.player_controlled = True

        # Timer for running
        self.time_before_running = 10  # default 10
        self.multiplier = 1.  # default 1
        self.max_multiplier = 2.0  # default 2
        self.running_timer = Timer(self.time_before_running)

        # Jump variables
        self.amount_of_jump = 5
        self.jump_counter = 0
        self.base_max_speed = self.max_speed
        # Set in update_status()
        self.can_i_jump_higher = True

        # Match things
        self.lit = 100.0
        self.updates_per_lit_unit = 40
        self.lit_counter = 0
        self.match_color = (255, 141, 0)
        self.match_positions = {
            ANIMATION_WALKING: [(2, 10), (21, 10)],
            ANIMATION_CROUCH: [(1, 20), (22, 20)],
            }
        self.match_position = None
        self.match_rect_size = 3
        # Match fire particle:
        self.match_particle = {
            "x": None,
            "y": None,
            "life_time": 10,
            "max_speed": 0.3,
            "min_speed": .0,
            "direction": pi / 2. + pi,
            "delta_ang": 2 * pi,
            "gravity": -0.1,
            "color": self.match_color,
            "size": (1, 1),
            "ref_sprite": None,
            "fade_out_time": 10,
            }

        # Score particle
        score_layers = [('shadows', {'positions_and_colors': [((1, 1), GREY)]}),
                       ('normal', {'color': WHITE}),
                       ]
        amplitude_speed = 0.3
        self.score_particle = {
           'text_layers': score_layers,
           'font_size': 8,
           'bg_color': BLACK,
           'bg_transparent': True,
           'gravity': 0.0,
           'life_time': 200,
           'fade_out_time': 10,
           'vx_function': lambda vx, age: amplitude_speed * cos(age / 13.),
           'vy_function': lambda vy, age: -0.1
           }

        # Speed limit for the match to consume itself faster default 3.7
        self.speed_limit = 4.25

        # Gravity
        self.has_gravity = True
        self.gravity = 0.28

        # Damage stuff
        self.damage_factor = 1.5  # Amount of damage by fall
        self.damage_effect = 0
        self.damage_counter = 0
        self.taken_damage = 0
        self.max_damage = 20
        self.damage_period = 10
        self.lit_taken = 0
        self.create_left_right()

        self.half_platform_damage = 0
        self.inmunity_damage = 0

        # Falling stuff
        self.fallen_updates = 0
        self.max_falling_updates = 16

        # Winning/loosing stuff
        self.winning = False
        self.loosing = False
        self.sound_delay = None
        # Recoil when fai,l default values (0.5, 2.0)
        self.loosing_jump_speed = (1.0, 2.0) 

        ####################
        # Braking variables
        self.updates_per_brake = 120
        self.brake_counter = 0
        # Braking status things.
        # Minimun speed needed to start braking
        self.MIN_BRAKING_SPEED = 0.9
        # Once started braking, speed at which it'll stop braking
        self.BRAKING_UNTIL = 0.0
        # Don't tocuh, internal variable
        self._braking_last_update = False
        self.MIN_UPDATES_WALKING = 60

        ###################
        # Walking variables
        self.step_counter = 0
        self.updates_per_step = 10
        # Walking status things.
        # Both animation and sound playing depends on this:
        self.MINIMUN_WALKING_SPEED = 0.1
        self.walking_update_counter = 0

    @property
    def braking(self):
        """ Return True if the player is braking.

        To configure its behavior use the variables:

        self.MIN_BRAKING_SPEED = Minimun speed needed to start braking

        self.BRAKING_UNTIL = Once started braking, speed at which it'll
                             stop braking

        self._braking_last_update = Don't touch, internal variable
                                    holds if it was braking in last
                                    update

        Search for them in __init__()

        """

        vx = abs(self.vx)
#         print "In self.braking: ", self.walking_update_counter, self.walking_update_counter > self.MIN_UPDATES_WALKING
        if self.col_down:
            if not self.moving:
                if self._braking_last_update:
                    if vx > self.BRAKING_UNTIL:
                        self._braking_last_update = True
                        return True
                    else:
                        self._braking_last_update = False
                        return False
                elif vx > self.MIN_BRAKING_SPEED:
                    if self.walking_update_counter > self.MIN_UPDATES_WALKING:
                        self._braking_last_update = True
                        return True
                else:
                    self._braking_last_update = False
                    return False
            else:
                if (self.direction == LOOKING_RIGHT and self.vx < 0) or \
                   (self.direction == LOOKING_LEFT and self.vx > 0):
                    if self.walking_update_counter > (self.MIN_UPDATES_WALKING // 2):
#                         print "    returning True because because walking counter"
                        self._braking_last_update = True
                        return True
                    elif self._braking_last_update:
#                         print "    returning True because braking last update"
                        self._braking_last_update = True
                        return True
                else:
                    self._braking_last_update = False
                    return False
        return False

    def jump_internal(self):
        """ Return True if jump. """
        if self.jump_available:
            self.can_i_jump_higher = True
            jump_sound.play()
            self.jump_counter = 0
            self.jump_available = False
#             self.jump_last_frame = True
            # IMPORTANT NOTE! FIRST SET THE SPEED TO ZERO, THEN JUMP
            # IF NOT IRREGULAR JUMPS WILL HAPPEN EVERYWHERE
            self.movement_mods.append((SPEED_SET,(self.vx,0.)))
            self.movement_mods.append((SPEED_ADD,(0,self.jump_speed)))
            return True
        else:
            if self.last_frame_jump and self.can_i_jump_higher:
                self.jump_counter += 1
                if not (self.jump_counter > self.amount_of_jump):
                    self.movement_mods.append((SPEED_ADD,(0,self.jump_speed)))
#                     self.jumping_last_update = True
                    return True
        return False

    def update_animation(self):
        """ Detect the correct animation and update the image of the
            sprite.

            It detects the generic animation defined in utils.py/other
            constants, being these:
            ANIMATION_STOP, ANIMATION_IDLE, ANIMATION_WALKING,
            ANIMATION_JUMP, ANIMATION_SHOOT, ANIMATION_FALLING. """

        old = self.image
        # not self.falling avoids rapid change beween animations while
        # colliding and jumping

        # TODO: Change in status variables as self.breaking, self.walking
        # etc... should not be here. I think...

        current_direction = self.direction

        if self.winning:
            self.match_position = None
            current_animation = self.animations[ANIMATION_WINNING]

        elif self.lit >= 0.0:
#             print self._last_frames_moved_x
#             print "CHOOSING ANIMATION"
            if self.braking:
#                 print "ANIMATION BRAKING!"
                current_animation = self.animations[ANIMATION_BRAKING]
                self.match_position = self.match_positions[ANIMATION_WALKING]
            elif not self.mean_moved_x and not self.falling:
                if self.use and self.col_down and self.vx == 0:
                    current_animation = self.animations[ANIMATION_CROUCH]
                    self.match_position = self.match_positions[ANIMATION_CROUCH]
                else:
                    self.match_position = self.match_positions[ANIMATION_WALKING]
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
                self.match_position = self.match_positions[ANIMATION_WALKING]
                self.moving_last_frame = True
                if self.col_down:
                    current_animation = self.animations[ANIMATION_WALKING]
                    #~ if self.moving:
                        #~ current_animation = self.animations[ANIMATION_WALKING]
                    #~ else:
                        #~ current_animation = self.animations[ANIMATION_STOP]
                else: # we are flying!
                    if self.vy < 0.0:
                        current_animation = self.animations[ANIMATION_JUMP]
                    else:
                        current_animation = self.animations[ANIMATION_FALLING]
            
            if (self.falling and self.taken_damage > 0.0) or (self.falling and self.fallen_updates > self.max_falling_updates):
                current_animation= self.animations[ANIMATION_DAMAGE]
        elif self.loosing:
            self.match_position = self.match_positions[ANIMATION_CROUCH]
            current_animation = self.animations[ANIMATION_LOOSING]
            if current_animation[0].finished or current_animation[1].finished:
                current_animation = self.animations[ANIMATION_LOSER]

        # don't do the moonwalker if we are sliding backwards
#         vx = self.vx
        vx = self.mean_moved_x
        if (self.direction == LOOKING_RIGHT and self.vx < 0) or \
           (self.direction == LOOKING_LEFT and self.vx > 0):
            if self.moving:
                # braking animation is already choosen above, but we
                # need to change the direction for this special case.
                current_direction = LOOKING_LEFT if self.direction == LOOKING_RIGHT else LOOKING_RIGHT
            else:
                vx = 0

        # choose the correct direction
        if self.match_position:
            self.match_position = self.match_position[current_direction]

        current_animation = current_animation[current_direction]
        
        # retrieve the frame using the correct method depending on the
        # animation player
        if isinstance(current_animation, SpeedUpdateAnimationPlayer):
            if abs(vx) == 0:
                self.image = current_animation.reset()
                self.image = current_animation.get_next_frame(vx)
            else:
                self.image = current_animation.get_next_frame(vx)
        else: # is a time animation, no need for speed
            self.image = current_animation.get_next_frame()
        
        if self.image is not old:
            self.dirty = 1

    def change_direction(self):
        """ Switch from one direction to the other  """

        self.direction = LOOKING_LEFT if \
            self.direction == LOOKING_RIGHT else LOOKING_RIGHT

    def run_ai(self, platforms, player):
        """ Runs the generic autoamata, skips the whole function if
        the player is controlling this mob. """

        # if the player is controlling this mob skip this
        if self.player_controlled:
            return

    def get_events(self):
        """ Handle all PLAYER events and do actions. """

        moving_left = moving_right = False
        l = event.get(PLAYER)
        # HACK: If you hit use no other order is taken!
        t = [i for i in l if i.code == USE]
        if t:
            self.use_next_frame()
        for e in l:
            if self.use:
                # While using just change the looking direction instead
                # of moving.
                if e.code == LEFT:
                    self.direction = LOOKING_LEFT
                elif e.code == RIGHT:
                    self.direction = LOOKING_RIGHT
            else:
                if e.code == LEFT:
                    moving_left = True
                elif e.code == RIGHT:
                    moving_right = True
                elif e.code == JUMP:
                    self.jump = True
                elif e.code == SHOOT:
                    self.shoot_next_frame()
                elif e.code == RESPAWN:
                    self.respawn()

        # Don't do the moonwalker if you hit left+right
        if moving_left and moving_right:
            self.moving = False
        elif moving_left:
            self.moving = True
            self.accel_left()
        elif moving_right:
            self.accel_right()
            self.moving = True

    def update_status(self, top, bottom, left, right):
        # Stuff for sprite status
        # TODO:
        # Move all this and part of the mob stuff to TryMovingSprite
        # ALSO: This is very sensitive to the order of calling:
        # if you call this after or before move_colliding lots of things
        # change

        if self.col_down:
            if not self.last_frame_jump:
                # Don't jump unless the jump key has been unpressed
                self.jump_available = True
            if not self.moving:
                self.friction()
        else:
            self.jump_available = False

        # Needed to avoid micro mid-air jumps
        if not self.last_frame_jump:
            self.can_i_jump_higher = False

    def custom_update_actions(self, platforms, new_sprites_group, player):
        """ Some Player special actions. """

        ######
        # other stuff: shoot, actions, etc...
        ######
        if self.use and self.col_down:
            self.use = False
            if self.match_position:
                #~ match_p = (self.match_position[0] + self.rect[0],self.match_position[1] + self.rect[1] - 1)
                match_rect = Rect(0,0,self.match_rect_size, self.match_rect_size)
                match_rect.center = (self.match_position[0] + self.rect[0],self.match_position[1] + self.rect[1] - 1)
                l = [spr for spr in self.groups()[0].sprites() if isinstance(spr,FireworkLauncher)]
                for f in l:
                    if f.col_rect.colliderect(match_rect) and \
                        not f.lit and self.vx == 0:
                        f.lit = True
                        glo.score += f.SCORE_LIT
                        size = 12
                        self.score_particle['x'] = self.rect.left
                        self.score_particle['y'] = self.rect.top
                        self.score_particle['text'] = f.SCORE_LIT
                        self.properly_add_ontop(ScoreText(**self.score_particle))
                        f.ignite_sound.play()

        if abs(self.vx) >= self.max_speed:
            if self.running_timer.finished:
                self.multiplier += 0.015 if self.multiplier <= self.max_multiplier else 0.0
                self.max_speed = self.base_max_speed * self.multiplier
        else:
            self.multiplier = 1.
            self.max_speed = self.base_max_speed
            self.running_timer.reset()

        # Draw the match fire particles
        if self.match_position:
            mp = self.match_particle
            mp['x'] = self.match_position[0] + self.rect[0]
            mp['y'] = self.match_position[1] + self.rect[1] - 1
            if self.lit:
                for i in xrange(int(ceil(self.lit /200))):
                    p=RandColorParticle(**mp)
                    player.properly_add_below(p)

        too_fast = hypot(self.vx, self.vy) - self.speed_limit
        if too_fast > 0:
            self.lit -= too_fast * self.damage_factor

        # Falling stuff
        if self.falling:
            self.fallen_updates += 1
        else:
            self.fallen_updates = 0

        # Reduce 'lit' every 'updates_per_lit_unit' updates and 
        # apply modifiers (pigeon attacks)
        if not self.winning:
            self.lit_counter += 1
            if self.lit_counter % self.updates_per_lit_unit == 0:
                self.lit_counter = 0
                self.lit -= 1
            # Apply lit modifiers
            self.lit -= self.lit_taken
            self.lit_taken = 0

        # Damage stuff
        # Look inside the mob classes to see how damage is applied
        if (self.half_platform_damage > 0 or self.inmunity_damage > 0) and not self.winning:
            self.damage_counter += 1
            self.half_platform_damage -= 1 if self.half_platform_damage > 0 else self.half_platform_damage
            self.inmunity_damage -= 1 if self.inmunity_damage > 0 else self.inmunity_damage

            # Need to copy the image. Not copying the image permanently
            # modifies player animations.
            self.image = self.image.copy()
            self.image.set_alpha(int(255*(self.damage_counter % self.damage_period) / (self.damage_period -1)))

        #########
        # Sounds
        if self.just_col_down:
            fall_sound.play()

        # Walking sounds
        if self.moving and self.col_down and \
            self.moved_x:
            self.step_counter += 1
            if self.step_counter % self.updates_per_step == 0:
                if self.step_counter == self.updates_per_step:
                    step1_sound.play()
                else:
                    step2_sound.play()
                    self.step_counter = 0

        # Braking sound
#         print "in custom update options:", self.braking
        if self.braking:
            if self.brake_counter % self.updates_per_brake == 0:
                brake_sounds[2].play()
            self.brake_counter += 1
        else:
            self.brake_counter = 0

        #####################################
        # Amount of match and loosing things
        #

        if self.lit < 0.0 and not self.winning:
            self.loosing = True
            if self.player_controlled:
                ouch_sound.play()
                self.sound_delay = Timer(0.3)

                js = self.loosing_jump_speed

                if self.direction == LOOKING_LEFT:
                    self.movement_mods.append((SPEED_ADD, (js[0], -1 * js[1])))
                else:
                    self.movement_mods.append((SPEED_ADD, (-1 * js[0], -1 * js[1])))

            if self.sound_delay and self.sound_delay.finished:
                game_over_sound.play()
                self.sound_delay = None

            self.player_controlled = False

        if self.winning:
            self.player_controlled = False

        # Update the bonus value
        if not self.winning:
            glo.bonus = int(self.lit) * 10 * 3

        ############
        # Counters
        #
        # NOTE TO FUTURE SELF:
        # Counter must be at the start or at the end, but
        # never in the middle.

        if self.moving and self.col_down:
            self.walking_update_counter += 1
        else:
            self.walking_update_counter = 0

    def hurt(self, platforms, inmunity):
        self.inmunity_damage = inmunity
        self.half_platform_damage = platforms

    def respawn(self):
        """ Moves the player sprite to the spawn position. """
        self.player_controlled = True
        self.winning = False
        self.loosing = False
        self.lit = 100.

        self.movement_mods.append((POSITION_SET, self.start_position))
        self.animations[ANIMATION_LOOSING][0].reset()
        self.animations[ANIMATION_LOOSING][1].reset()
