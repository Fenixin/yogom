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

""" Module to handle mouse and keyboard input. """

import array
from collections import deque

import pygame
from pygame.locals import *
from pygame.key import get_mods
from pygame.time import get_ticks

from utils import Timer

""" Possible events:
QUIT             none
ACTIVEEVENT      gain, state
KEYDOWN          unicode, key, mod
KEYUP            key, mod
MOUSEMOTION      pos, rel, buttons
MOUSEBUTTONUP    pos, button
MOUSEBUTTONDOWN  pos, button
JOYAXISMOTION    joy, axis, value
JOYBALLMOTION    joy, ball, rel
JOYHATMOTION     joy, hat, value
JOYBUTTONUP      joy, button
JOYBUTTONDOWN    joy, button
VIDEORESIZE      size, w, h
VIDEOEXPOSE      none
USEREVENT        code
"""

# input events used right now
mouse_events = [MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN]

keyboard_events = [KEYDOWN, KEYUP, QUIT]

joystick_events = [JOYAXISMOTION, JOYBALLMOTION, JOYHATMOTION,
                  JOYBUTTONUP, JOYBUTTONDOWN]

input_events = keyboard_events + joystick_events + mouse_events

class Input(object):
    def __init__(self, tracked_key_mods = KMOD_NONE):
        self.kb_size_last_pressed = 10
        self.kb_last_pressed = deque([]) # fast append and popleft
        self.kb_pressed = array.array('b', [0]*1000)
        self.ms_size_last_pressed = 10
        self.ms_last_pressed = deque([]) # fast append and popleft
        self.ms_pressed = array.array('b', [0]*100)
        self.quitting = False
        
        # Act as bitmask toget key modifiers
        self.tracked_key_mods = tracked_key_mods
        
        # used to store Timers for is_pressed()
        self.kb_timers = {}
        self.ms_timers = {}
        
        # keys binded to events or functions
        self.key_bindings = {}
        
        # keyboard modes
        self.lctrl = False
        self.lalt = False
        
        # mouse
        self.mouse_pos = (0,0)
        self.mouse_rel = (0,0)
        self.mouse_drag = False
        self.ms_start_times = {}
        self.ms_clicked = {}
        self.click_time = 200
    
    def update(self):
        self.key_mods = key_mods = get_mods() & self.tracked_key_mods
        
        # TODO del this
        left_control = key_mods & KMOD_LCTRL
        if left_control:
            self.lctrl = True
        else:
            self.lctrl = False
        left_alt = key_mods & pygame.KMOD_LALT
        if left_alt:
            self.lalt = True
        else:
            self.lalt = False
        
        # Clear mouse clicks:
        self.ms_clicked = {}
        
        for event in pygame.event.get(input_events):
            ticks = get_ticks()
            # the player just ALT+F4 the game or hit the x in the window
            if event.type == pygame.QUIT:
                self.quitting = True # The player wants to quit the game
            elif event.type == pygame.KEYDOWN:
                self.kb_pressed[event.key] = 1
                self.kb_last_pressed.append(event.key)
                
            elif event.type == pygame.KEYUP:
                self.kb_pressed[event.key] = 0

            # joystick
            if event.type in joystick_events:
                if event.type is not pygame.JOYAXISMOTION:
                    print event
                    
                # just take them from the event queue
                pass

            # Mouse

            if event.type == MOUSEMOTION:
                self.mouse_pos = event.pos
                self.mouse_rel = event.rel
            elif event.type == MOUSEBUTTONDOWN:
                self.ms_pressed[event.button] = 1
                self.ms_start_times[event.button] = ticks
                self.ms_last_pressed.append(event.button)
            elif event.type == MOUSEBUTTONUP:
                if self.ms_pressed[event.button] == 1 and (
                 ticks - self.ms_start_times[event.button] < self.click_time):
                    self.ms_clicked[event.button] = 1
                else:
                    self.ms_clicked[event.button] = 0

                self.ms_pressed[event.button] = 0
                
                try:
                    del self.ms_start_times[event.button]
                except KeyError:
                    pass

        while (len(self.kb_last_pressed) > 10):
            self.kb_last_pressed.popleft()

    def bind_key_dict(self, kdict):
        """ Iterates a dict adding all the bindings in it. """

        for k in kdict:
            try:
                self.bind_key( k[0], k[1], *kdict[k])
            except TypeError:
                # no mods reported, use zero
                self.bind_key(k, 0, *kdict[k])

    def bind_key(self, key, mods, det_fun, fun, det_args = None):
        """ Binds a pygame key constant to a function/event. 

        The function can't use any arguments. det_fun is the
        function used to detect if the key is pressed or not.
        By default delayed_is_pressed is used, the alternative
        is is_pressed.

        """

        # Check if integers are passed
        if isinstance(key, tuple):
            for k in key:
                if not isinstance(k, int):
                    raise TypeError
        else:
            if not isinstance(key, int):
                raise TypeError

        if det_fun == None:
            det_fun = self.delayed_is_pressed

        self.key_bindings[(key, mods)] = (det_fun, fun, det_args)

    def unbind_keys(self, key):
        """ Unbind key from all actions. """

        # Check if iterable
        try:
            for k in key:
                del self.def_keys[k]
        except TypeError:
            del self.def_keys[key]

    def run_bindings(self):
        """ Iterate all the bindings and run functions/post events. """

        key_bindings = self.key_bindings
        post = pygame.event.post
        key_mods = self.key_mods

        for keys, mods in key_bindings:
            det_fun, fun, det_args = key_bindings[(keys, mods)]
            if mods == key_mods:
                if det_args:
                    pressed = det_fun(self, keys, *det_args)
                else:
                    pressed = det_fun(self, keys)
                
                if pressed:
                    try:
                        post(fun)
                    except TypeError:
                        fun()
                    except pygame.error:
                        print pygame.event.get()
                        raise

    def kb_is_pressed(self, key):
        """ Returns True if the given key, represented by a pygame.K
        value, is pressed. """

        pressed = False
        try:
            for k in key:
                if self.kb_pressed[k] == 0:
                    break
            else:
                pressed = True
        except TypeError:
            if self.kb_pressed[key] != 0:
                pressed = True
        return pressed

    def kb_delayed_is_pressed(self, key, delay = 0.2):
        """ Same as is_pressed but waits delay (s) before returning 
        again a True value. """

        # Check if key/keys is/are pressed
        pressed = self.kb_is_pressed(key)

        # Update timer and return propper value
        if pressed:
            if key in self.kb_timers.keys():
                if self.kb_timers[key].finished:
                    self.kb_timers[key].reset()
                    return True
                else: return False
            else:
                self.kb_timers[key] = Timer(delay)
                return True
        return False

    def ms_delayed_is_pressed(self, button, delay = 0.2):
        """ Same as is_pressed but waits delay (s) before returning 
        again a True value. """

        # Check if button/buttons is/are pressed
        pressed = self.ms_is_pressed(button)

        # Update timer and return propper value
        if pressed:
            if button in self.ms_timers.buttons():
                if self.ms_timers[button].finished:
                    self.ms_timers[button].reset()
                    return True
                else: return False
            else:
                self.ms_timers[button] = Timer(delay)
                return True
        return False

    def ms_is_pressed(self, button):
        """ Returns True if the given button, represented by a pygame.K
        value, is pressed. """

        pressed = False
        try:
            for k in button:
                if self.ms_pressed[k] == 0:
                    break
            else:
                pressed = True
        except TypeError:
            if self.ms_pressed[button] != 0:
                pressed = True
        return pressed

    def ms_has_clicked(self, button):
        """ Return True if mouse has clicked button. """

        try:
            if self.ms_clicked[button] == 1:
                return True
            return False
        except KeyError:
            return False

    def ms_is_dragging(self, button):
        """ Return True if the mouse is drag&dropping with button """

        ticks = get_ticks()
        
        if self.ms_is_pressed(button) and (
         ticks - self.ms_start_times[button] > self.click_time):
            return True
        else:
            return False

    def get_last_pressed(self,):
        return self.kb_last_pressed[-1]



# Constants
INSTANT = Input.kb_is_pressed
DELAYED = Input.kb_delayed_is_pressed
MSINSTANT = Input.ms_is_pressed
MSDELAYED = Input.ms_delayed_is_pressed
