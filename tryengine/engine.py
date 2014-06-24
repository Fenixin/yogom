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

""" This is the main loop, the scene loop.

This probably should be renamed to sceneloop or something like that.
"""

# TODO: There are game stuff around that should not be here.
# gameclock settings are set here, and that is bad.

import sys
from collections import deque
import os.path

import pygame

import settings as s
from constants import *
from gameclock import GameClock
from utils import Borg

#TODO: THIS SHOULD NOT BE HERE
from scripts.scenes import PauseScene

glo = Borg()


class Engine(object):
    """ Class with the scene loop. """

    def __init__(self, scene_stack, display_flags=0):

        self.scene_stack = scene_stack

        # Choose correct method for timing
        if sys.platform in('win32', 'cygwin'):
            time_source = None
        else:
            time_source = lambda: pygame.time.get_ticks() / 1000.
        self.gclock = GameClock(s.TICKS_PER_SECOND, s.MAX_FPS,\
                                time_source=time_source, use_wait=True)

        # show fps in window caption
        if s.CHEATS:
            fps_caption = lambda whatever: self.change_caption(
                s.GAME_NAME + "; fps = " + str(self.gclock.fps))
            self.gclock.schedule_interval(fps_caption, 1.0)
        else:
            fps_caption = lambda whatever: self.change_caption(
                s.GAME_NAME)

        # Create rotating palettes
        glo.rot_pal1 = deque(WHITE_PIXEL.get_palette())
        glo.rot_pal2 = deque(WHITE_PIXEL.get_palette())
        glo.rot_pal3 = deque(WHITE_PIXEL.get_palette())

        # Create a temporal surface for fullscreen scaling
        d_srf = pygame.display.get_surface()
        d_size = d_srf.get_size()
        self.fullscreen_tmp_surface = pygame.Surface(d_size, d_srf.get_flags())
        # TODO: we can use a pattern or an image
        self.fullscreen_tmp_surface.fill(BLACK)
        self.scale = self.scale_windowed

    def change_caption(self, text):
        """ Changes the window caption to text. """
        pygame.display.set_caption(text)

    def print_scene(self, *stuff):
        print self.current_scene

    def handle_events(self, *args):
        # engine events
        l = pygame.event.get(ENGINE)
        for event in l:
            if event.code == TOGGLE_FULLSCREEN:
                self.toggle_fullscreen()
            elif event.code == RELOAD_MAP:
                self.reload_map()
            elif event.code == CHEATS:
                self.toggle_cheats()
            elif event.code == NEW_MAP:
                self.done = True
                self.location_to_spawn = event.spawn
                self.map_to_load = event.map_path
            elif event.code == CYCLE_DEBUG_MODES:
                s.debug_mode = (s.debug_mode + 1) % s.debug_modes
                self.renderer.redraw_background()
            elif event.code == ONE_LAYER_UP:
                self.player.one_layer_up()
            elif event.code == ONE_LAYER_DOWN:
                self.player.one_layer_down()
            elif event.code == CYCLE_DISPLAY_MODES:
                if not (pygame.display.get_surface().get_flags() & pygame.FULLSCREEN):
                    print "Changing mode." 
                    # try to switch to the next size, we can resize
                    # the screen with the mouse, so this could
                    # give a big error
                    current_size = s.screen_size
                    try:
                        i = s.screen_sizes.index(current_size)
                        try:
                            i = i+1
                            new_size = s.screen_sizes[i]
                        except IndexError:
                            i = 0
                            new_size = s.screen_sizes[0]
                    except ValueError:
                        i = 0
                        new_size = s.screen_sizes[0]
                    pygame.display.set_mode(new_size)
                    s.screen_size = new_size
                    s.scale = i+1
            elif event.code == SUPER_LOW_FPS:
                self.fps = 1 if self.fps == 60 else 60
            elif event.code == PAUSE:
                print "Pause!"
                self.scene_stack.push(PauseScene())
            elif event.code == CONTROL_NEXT_MOB:
                # Cutre implementation
                self.player.player_controlled = False
                self.player = self.mobs.sprites()[self.index]
                self.player.player_controlled = True
                if (self.index + 1 == len(self.mobs.sprites())):
                    self.index = 0
                else:
                    self.index += 1
            elif event.code == SCREENSHOT:
                fn = self.get_screenshot_filename()
                pygame.image.save(pygame.display.get_surface(), fn)
            else:
                print "Unhandled event in type ENGINE!"
                print event

        # events from the window
        l = pygame.event.get((pygame.ACTIVEEVENT, pygame.VIDEORESIZE))
        for event in l:
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode(event.size, self.display_flags)

        # other of events
        l = pygame.event.get((pygame.ACTIVEEVENT, pygame.VIDEOEXPOSE))
        for event in l:
            #~ print event
            pass

    def get_screenshot_filename(self):
        name = "screenshot-{:03}.png"
        for i in range(1000):
            t = name.format(i)
            if os.path.isfile(t):
                continue
            else:
                return t
        return "Too_many_screenshots.png"

    def get_best_fit(self, source_surface, destination_surface):
        s_size = source_surface.get_size()
        s_ratio = float(s_size[0]) / float(s_size[1])
        d_size = destination_surface.get_size()
        d_ratio = float(d_size[0]) / float(d_size[1])
        # Height in destination limits
        if d_ratio >= s_ratio:
            new_size = (int(d_size[1] * s_ratio), d_size[1])
            dest = ((d_size[0] - new_size[0]) / 2, 0)

        # Width in destination limits
        elif d_ratio < s_ratio:
            new_size = (d_size[0], int(d_size[0] / s_ratio))
            dest = (0, (d_size[1] - new_size[1]) / 2)

        return pygame.Rect(dest[0], dest[1], new_size[0], new_size[1])

    def toggle_fullscreen(self):
        screen = pygame.display.get_surface()
        if screen.get_flags() & pygame.FULLSCREEN:
            # Go windowed
            print "Going Windowed"
            s.fullscreen = False
            display_flags = 0
            pygame.display.set_mode(s.screen_size, display_flags)
            self.scale = self.scale_windowed
        else:
            # Not in fullscreen, go fullscreen
            print "Going Fullscreen"
            s.fullscreen = True
            modes = pygame.display.list_modes()
            size = modes[0]
            display_flags = pygame.FULLSCREEN
            pygame.display.set_mode(size, display_flags)
            self.scale = self.scale_fullscreen

            r = self.destination = self.get_best_fit(self.current_scene.frame, pygame.display.get_surface())

            self.fullscreen_tmp_surface = pygame.Surface((r[2],r[3]), display_flags)
            self.fullscreen_tmp_surface.fill(BLACK)

    def scene_loop(self):
        """ Main game loop. """
        scene_stack = self.scene_stack
        gclock = self.gclock
        flip = pygame.display.flip
        while scene_stack.top():
            self.current_scene = scene = scene_stack.top()
            
            if scene.finished or glo.quitting:
                # Drop the finished scene or drop all if quitting.
                scene.stop()
                scene_stack.pop()
                continue
            
            self.handle_events()

            # It's probably a good idea to handle input as it's done
            # now, outside of scene.update() NO IT'S NOT!!!!!!!
            gclock.tick()

            if gclock.update_ready:
                scene.handle_input()
                scene.handle_events()
                scene.update()
                self.custom_update_actions()
            if gclock.frame_ready:
                self.scale(scene.new_frame)
                flip()

    def scale_windowed(self, surface):
        display = pygame.display.get_surface()
        display_size = display.get_size()
        pygame.transform.scale(surface, display_size, display)

    def scale_fullscreen(self, frame, keep_ratio=True):
        new_size = self.fullscreen_tmp_surface.get_size()
        r = self.destination
        display = pygame.display.get_surface()
        
        if keep_ratio:
            pygame.transform.scale(frame, new_size, self.fullscreen_tmp_surface)
            display.blit(self.fullscreen_tmp_surface, r)
        else:
            pygame.transform.scale(frame, display.get_size(), display)

    def custom_update_actions(self):
        # Rotate palettes
        glo.rot_pal1.rotate()
        glo.rot_pal2.rotate(2)
        glo.rot_pal3.rotate(3)
