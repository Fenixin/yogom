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


screen_size_in_tiles = (18,20)
actual_frame_size = fs = (288, 320)
scale = 2
#             18*16      , 20*16
screen_size = (actual_frame_size[0] *scale, actual_frame_size[1] *scale)
screen_sizes = [actual_frame_size, (fs[0]*2, fs[1]*2), (fs[0]*3, fs[1]*3,)]
fullscreen = False

TICKS_PER_SECOND = 100.0
MAX_FPS = 60
debug_mode = 0
debug_modes = 2

GAME_NAME = "You only get one! (match)"

# Others:
CHEATS = False
TOUCH_CONTROL = False
NORMAL_DIFFICULTY_LIVES = 2
PERMAFIRED_DIFFICULTY_LIVES = 0

# Constants
PERMAFIRED_DIFFICULTY = 0
NORMAL_DIFFICULTY = 1