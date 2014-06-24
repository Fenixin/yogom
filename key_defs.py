#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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


from pygame.locals import *
import pygame.event as e

from tryengine.constants import *
from tryengine.playerinput import INSTANT, DELAYED

key_definitios = { 
    K_UP: (INSTANT, e.Event(PLAYER, code = JUMP)),
    K_SPACE: (INSTANT, e.Event(PLAYER, code = JUMP)),
    K_z: (INSTANT, e.Event(PLAYER, code = JUMP)),
    K_DOWN: (INSTANT, e.Event(PLAYER, code = USE)),
    K_LEFT: (INSTANT, e.Event(PLAYER, code = LEFT)),
    K_RIGHT: (INSTANT, e.Event(PLAYER, code = RIGHT)),
    #~ K_SPACE: (INSTANT, e.Event(PLAYER, code = SHOOT)),
    #~ K_r: (DELAYED, e.Event(PLAYER, code = RESPAWN)),
    
    # Renderer command keys
    (K_RETURN, KMOD_LALT): (DELAYED, e.Event(ENGINE, code = TOGGLE_FULLSCREEN), (0.1,)),
    K_F11: (DELAYED, e.Event(ENGINE, code = TOGGLE_FULLSCREEN), (0.1,)),
    #~ K_f: (DELAYED, e.Event(RENDERER, code = FADE)),
    #~ K_n: (DELAYED, e.Event(RENDERER, code = NEXT_CAMERA)),
    #~ K_LEFT: (INSTANT, e.Event(RENDERER, code = CAMERA_LEFT)),
    #~ K_RIGHT: (INSTANT, e.Event(RENDERER, code = CAMERA_RIGHT)),
    #~ K_UP: (INSTANT, e.Event(RENDERER, code = CAMERA_UP)),
    #~ K_DOWN: (INSTANT, e.Event(RENDERER, code = CAMERA_DOWN)),
    #~ K_k: (INSTANT, e.Event(RENDERER, code = CAMERA_SHAKE)),
    
    # Engine command keys
    #~ (K_r, KMOD_LCTRL): (DELAYED, e.Event(ENGINE, code = RELOAD_MAP)),
    #~ (K_d, KMOD_LCTRL): (DELAYED, e.Event(ENGINE, code = CYCLE_DEBUG_MODES)),
    (K_s, KMOD_LCTRL): (DELAYED, e.Event(ENGINE, code = CYCLE_DISPLAY_MODES)),
    K_F10: (DELAYED, e.Event(ENGINE, code = CYCLE_DISPLAY_MODES)),
    K_F12: (DELAYED, e.Event(ENGINE, code = SCREENSHOT)),
    #~ (K_v, KMOD_LCTRL): (DELAYED, e.Event(ENGINE, code = SUPER_LOW_FPS), (0.1,)),
    #~ K_q: (DELAYED, e.Event(ENGINE, code = QUIT), (0.1,)),
#     K_ESCAPE: (DELAYED, e.Event(ENGINE, code = PAUSE)),
#     K_p: (DELAYED, e.Event(ENGINE, code = PAUSE)),
    #~ (K_g, KMOD_LCTRL): (DELAYED, e.Event(ENGINE, code = ONE_LAYER_UP)),
    #~ (K_t, KMOD_LCTRL): (DELAYED, e.Event(ENGINE, code = ONE_LAYER_DOWN)),
    #~ K_j: (DELAYED, e.Event(ENGINE, code = CONTROL_NEXT_MOB)),
    #~ K_l: (DELAYED, e.Event(ENGINE, code = CHEATS)),
    # Engine mouse bindings
    

}
