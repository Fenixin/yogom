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

""" tryengine module containing utils to handle sprite animations.

This module contains an Animation class that handles spritesheet animations and
some AnimationPlayers, classes to play the spritesheet animation in different
ways.
"""

# TODO: Move debugging to logging!

from collections import deque

import pygame


class Animation(object):
    """ Handler for spritesheets animations. 

    Expects a surface with the spritesheet and a tuple with ints with the
    frame size. If vertical = True the animations goes from top down, else
    goes left to right.
    """

    def __init__(self, spritesheet, frame_size, vertical=True):
        # Frame number is calculated from the spritesheet
        # Full sprite sheet
        self.spritesheet = spritesheet
        self.tw = frame_size[0]
        self.th = frame_size[1]
        self.vertical = vertical

        # Get the number of frames
        width, height = self.spritesheet.get_size()
        if vertical:
            self.num_frames = height / self.th
        else:
            self.num_frames = width / self.tw

        # List with the frames
        self.frames = []

        # Slice the spritesheet
        self._get_frames()

        # Debugging?
        self.debugging = False

    def _get_frames(self):
        """ Slices the spritesheet and fills up the frames list. """
        w = self.tw
        h = self.th

        for frame in range(self.num_frames):
            if self.vertical:
                self.frames.append(self.spritesheet.subsurface(0, frame*h, w, h))
            else:
                self.frames.append(self.spritesheet.subsurface(frame*w, 0, w, h))

    def mirror(self):
        """ Mirrors all the frames to get the opposite direction animation. """
        for i in range(len(self.frames)):
            self.frames[i] = pygame.transform.flip(self.frames[i], True, False)

    def dprint(self, text):
        """ If self.debugging is True it will print debugging text. """
        if self.debugging:
            print text


class AnimationPlayer(object):
    """ Generic class to play animations, all the players extends this one. """
    def __init__(self, animation):
        # the animation to play
        self.animation = animation
        # stores the index of the current frame
        self.current_frame = 0
        # stores when we got a frame for the last time
        self.last_time = pygame.time.get_ticks()

        # Stores next frames to play in special cases
        self._next_frames = deque()

        self.debugging = False

    def dprint(self, text):
        """ If self.debugging is True it will print debugging text. """
        if self.debugging:
            print text

    def reset(self):
        """ Start the animation from the beginning. """
        self.current_frame = 0

    def _calculate_smooth_reset_frames(self):
        """ Smoothly return to the start of the animation.

        Calculate if we are nearer to the start or the end of the animation and
        play the those frames to reach the start of the animation smoothly.
        """

        cf = self.current_frame
        a = self.animation
        frames = len(a.frames)

        # We are nearer the start of the animation
        if cf > (frames - cf):
            self._next_frames.extend(a.frames[:cf])
        else: # Nearer to the end
            self._next_frames.extend(a.frames[cf:])


class TimedAnimationPlayer(AnimationPlayer):
    """ Plays an animation as time passes.

    NOTE: it's not a good idea to use this! Use some of the Update versions.
    Any old computer that loses updates/frames will make this animations look
    weird. Also, in general this animation player look strange.

    Expects an Animation object and an integer with the frames per second of
    the animation.
    """

    def __init__(self, animation, fps=10):
        # init parent
        AnimationPlayer.__init__(self, animation)

        # number of frames per second, make sure you put less than 
        # the fps of your screen
        self.fps = fps
        # amount of time to wait between frames
        self.delay = pygame.time.get_ticks() / fps

    def get_next_frame(self):
        """ Return the next frame in the animation.

        No frames will be skipped.
        """

        if self._check_time():
            self.current_frame = (self.current_frame + 1) % self.animation.num_frames

        return self.animation.frames[self.current_frame]

    def _check_time(self):
        """ Checks if enough time has passed to switch to the next frame.

        Returns True if so, False otherwise.
        """
        now = pygame.time.get_ticks()
        if self.delay < (now - self.last_time):
            self.last_time = now
            return True
        return False


class SpeedUpdateAnimationPlayer(AnimationPlayer):
    """ A mix of the SpeedAnimationPlayer and UpdateAnimationPlayer.

    Basically it uses UpdateAnimationPlayer to limit the framerate and
    the speed to modulate the speed of the animation.
    """

    def __init__(self, animation, updates_per_frame, max_speed):
        AnimationPlayer.__init__(self, animation)

        # Max speed of the sprite
        self.max_speed = float(max_speed)
        # Number of updates per frame
        self.updates_per_frame = updates_per_frame
        self.update_counter = 0.0 #float! add fractions of update

        self.debugging = False

    def get_next_frame(self, speed):
        """ Return the next frame in the animation.

        To work properly this method should be called every sprite update. It
        will return the same frame if no update is needed.
        """

        if self._next_frames:
            print self._next_frames            
            return self._next_frames.popleft()
        else:
            self.dprint("###In get_next_frame()")
            speed = abs(speed)
            add = float(speed) / self.max_speed if (float(speed) / self.max_speed) > 0.001 else 0
            self.update_counter += add
            self.dprint("\t self.update_counter= {0}".format(self.update_counter))
            if self.update_counter >= self.updates_per_frame:
                self.dprint("\t\tNext frame!")
                self.update_counter = self.update_counter % self.updates_per_frame
                self.current_frame = (self.current_frame + 1) % self.animation.num_frames
                self.dprint("\t\tCurrent frame: {0}; self.update_counter: {1}".format(self.current_frame, self.update_counter))
            
            return self.animation.frames[self.current_frame]
        
    def smooth_reset(self):
        
        self._calculate_smooth_reset_frames()


class UpdateAnimationPlayer(AnimationPlayer):
    """ Play an Animation using updates as time reference.

    In order to keep count of the number of updates, you have to call
    get_next_frame in every sprite update.

    updates_per_frames is an integer with the number of updates the
    sprites has to do in order to get the next frame in the animation.
    """

    def __init__(self, animation, updates_per_frame):
        AnimationPlayer.__init__(self, animation)

        # number of updates per frame
        self.updates_per_frame = updates_per_frame
        self.update_counter = 0

        self.debugging = False

        # is the animation going backwards?
        self.backwards = False

    def get_next_frame(self, speed=None):
        """ Return the next frame in the animation.

        To work properly this method should be called every sprite update. It
        will return the same frame if no update is needed.
        """

        self.dprint("\n## UpdateAnimationPlayer ##")
        if self.backwards:
            self.update_counter -= 1
            if self.update_counter <= 0:
                self.update_counter = self.updates_per_frame
                self.current_frame = (self.current_frame - 1) % self.animation.num_frames
        else:
            self.dprint("\tForward animation")
            
            self.update_counter += 1
            self.dprint("\tUpdate counter: {0}".format(self.update_counter))
            if self.update_counter >= self.updates_per_frame:
                self.update_counter = 0
                self.current_frame = (self.current_frame + 1) % self.animation.num_frames

        return self.animation.frames[self.current_frame]


class OnceUpdateAnimationPlayer(UpdateAnimationPlayer):
    """ Plays an animation as update animation Player but just once.

    The animation won't cycle, it must be reset() by hand and it has
    a flag that let's you check if the animation has finished.
    """

    def __init__(self, animation, updates_per_frame):
        UpdateAnimationPlayer.__init__(self, animation, updates_per_frame)

        # has the animation finished?
        self.finished = False

        # are we playing it backwards?
        self.backwards = False

        self.debugging = False

    def get_next_frame(self):
        """ Return the next frame in the animation.

        To work properly this method should be called every sprite update. It
        will return the same frame if no update is needed.
        """

        if (self.current_frame == self.animation.num_frames - 1 and not self.backwards) or \
           (self.current_frame == 0 and self.backwards):
            #~ import pdb; pdb.set_trace()
            self.finished = True
            #~ if self.backwards:
                #~ self.backwards = False
            #~ else:
                #~ self.backwards = True

        if not self.finished:
            if self.backwards:

                self.update_counter -= 1
                if self.update_counter <= 0:
                    self.update_counter = self.updates_per_frame
                    self.current_frame = (self.current_frame - 1) % self.animation.num_frames
            else:
                self.dprint("\tForward animation")

                self.update_counter += 1
                self.dprint("\tUpdate counter: {0}".format(self.update_counter))
                if self.update_counter >= self.updates_per_frame:
                    self.update_counter = 0
                    self.current_frame = (self.current_frame + 1) % self.animation.num_frames

        return self.animation.frames[self.current_frame]

    def reset(self):
        """ Restart the animation. """
        self.current_frame = 0
        self.finished = False


class SpeedAnimationPlayer(AnimationPlayer):
    """ Animates an sprite using the speed of movement as reference.

    NOTE: Don't use this, use one of the Update animation players, this one
    will look very strange.
    """

    def __init__(self, animation, max_speed):
        AnimationPlayer.__init__(self, animation)

        self.max_speed = float(max_speed)
        # Everytime this variable gets to 1 an sprite pass in the animation
        self.float_sprites = 0.

        self.debugging = False

    def get_next_frame(self, speed):
        speed = abs(speed)
        self.dprint("\n### SpeedAnimation.get_next_frame()")
        self.dprint("\tself.max_speed={0}".format(self.max_speed))
            
        #~ sprites_counter = math.trunc(self.float_sprites)
        self.dprint("\t\t self.float_sprites={0}".format(self.float_sprites))
        if abs(self.float_sprites) >= 1.:
            self.dprint("\t\t\t yes it is!")
            self.current_frame = (self.current_frame + 1) % self.animation.num_frames
            self.float_sprites = 0.
            self.dprint("\t\t\t self.float_sprites={0}".format(self.float_sprites))

        self.dprint("\t\tfloat(speed) / float(self.max_speed)={0}".format(float(speed) / float(self.max_speed)))
        self.float_sprites += float(speed) / float(self.max_speed) 
        
        self.dprint("\t After self.float_sprites={0}".format(self.float_sprites))
        return self.animation.frames[self.current_frame]
