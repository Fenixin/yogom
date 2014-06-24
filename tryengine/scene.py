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

""" Module with the basic scene to derive from when creating scenes. """

import pygame


class Scene(object):
    """ Used by engine.py in union with scenestack.py to run scenes.
    
    To create a scene override the update and draw methods. 
    
    """
    
    def __init__(self):
        self.stack = None
        self.paused = False
        
    def _add_internal(self, stack):
        self.stack = stack
    
    def _remove_internal(self, stack):
        self.stack = None

    def pause(self):
        """ Called when a new scene is on top of this. """
        raise NotImplementedError

    def unpause(self):
        """ Called when this scene is on the top. """
        raise NotImplementedError

    def update(self):
        raise NotImplementedError
    @property
    def frame(self):
        raise NotImplementedError
    @property
    def new_frame(self):
        raise NotImplementedError
    
    def _after_init(self):
        """ Called after scenestack.push has finished. """
        raise NotImplementedError

    def handle_input(self):
        """ Handling of player input. """

        raise NotImplementedError



def center_in_length(obj_size, room_size):
    """ Return the location in which the object is centered in room."""
    return (room_size - obj_size)/2


class SceneWithMusic(Scene):
    def __init__(self, music = None):
        Scene.__init__(self)
        self.music = music
        # In seconds
        self.music_pos = 0.0
        self.volume = 0.7
        

    def pause_music(self):
        """ Stop the music storin the position. """
        
        self.music_pos += pygame.mixer.music.get_pos() / 1000.
        pygame.mixer.music.stop()

    def unpause_music(self):
        """ Unpause music, and posibly, other stuff. 
        
        Coming from other scene will substitute the music file.
        This will reload it from the last position.

        """
        if self.music:
            pygame.mixer.music.load(self.music)
            #pygame.mixer.music.play(0, self.music_pos)
            pygame.mixer.music.play(0, 0)
            pygame.mixer.music.set_volume(self.volume)

    def stop_music(self):
        """ Stop needed things before removing this scene.
        
        At the moment only music is handled this way. 
        
        """

        pygame.mixer.music.stop()


def x_center_sprites(center_to_rect, sprites, offset=0):
    r = center_to_rect
    try:
        spr_l = sprites.sprites()
    except AttributeError:
        spr_l = sprites

    for spr in spr_l:
        rect = spr.rect
        x = (r[2] - rect[2])/2 + offset
        spr.change_sprite_pos(x, spr.rect[1])

def y_center_sprites(center_to_rect, sprites, offset=0):
    r = center_to_rect
    try:
        spr_l = sprites.sprites()
    except AttributeError:
        spr_l = sprites

    for spr in spr_l:
        rect = spr.rect
        y = (r[3] - rect[3])/2 + offset
        spr.change_sprite_pos(spr.rect[0], y)

def ver_justify_sprites(justify_to_rect, sprites, spacer = 25, offset = (0,0)):
    r = justify_to_rect
    i = 0
    for spr in sprites:
        
        rect = spr.rect
        #~ x = (r[2] - rect[2])/2 + offset[0]
        y = (r[3] - rect[3])/2 + i*spacer - 50 + offset[1]
        spr.change_sprite_pos(spr.rect[0], y)
        i += 1

def hor_justify_sprites(justify_to_rect, sprites, spacer = 25, offset = (0,0)):
    r = justify_to_rect
    i = 0

    size_x = 0
    for spr in sprites:
        size_x += spr.rect[2]
        size_x += spacer

    x_start = (r[2] - size_x ) / 2

    x_pos = x_start
    for spr in sprites:
        rect = spr.rect
        x, y = ( x_pos + i*spacer + offset[0], offset[1])
        x_pos += rect[2]
        spr.change_sprite_pos(x, y)
        i += 1

