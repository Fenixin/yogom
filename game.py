#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   You only get one! (match).
#   An old style arcade platformer game. Written using tryengine and pygame.
#   Copyright (C) 2014  Alejandro Aguilera (Fenixin) (fenixin@gmail.com)
#   https://github.com/Fenixin/tryengine
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
from os.path import join

import pygame
# When making a Windows pkg with bbfreezeimport/py2exe:
#import pygame._view


from tryengine.utils import Borg
from tryengine.fontrenderer import FontRenderer
import settings as s

# BIG NOTE: pygame can't convert images without initializing
#           pygame.display first

# first pre init the mixer
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)

pygame.init()
pygame.font.init()
pygame.mixer.set_num_channels(24)

# Choose a correct window resolution
s_info = pygame.display.Info()
s_size_rect = pygame.Rect(0,0,s_info.current_w, s_info.current_h)

# Actual pixel resolution of a map
for i in xrange(len(s.screen_sizes) -1 , 0, -1):
    w_size = s.screen_sizes[i]
    w_rect = pygame.Rect(0,0,w_size[0],w_size[1])
    if s_size_rect.contains(w_rect):
        screen_size = w_size
        s.scale = i + 1
        break
else:
    screen_size = s.actual_frame_size
    s.scale = 1

# init the variables!
display_flags = 0
display_depth = 0
icon = pygame.image.load('data/images/icon.png')
icon.set_colorkey((0,0,0))
pygame.display.set_icon(icon)
screen = pygame.display.set_mode(screen_size, display_flags, display_depth)
pygame.display.set_caption(s.GAME_NAME)

# if everything about the pygame import went well then import the ingine.
from tryengine import engine

from tryengine.scenestack import SceneStack
from scripts.scenes import TitleScene, ComicScene, TiledScene, TextScene, TransitionScene
from data.level_list import level_list

scene_stack = SceneStack()

e = engine.Engine(scene_stack, display_flags)

pygame.event.set_blocked([pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP,
    pygame.MOUSEBUTTONDOWN])

# Init some globals
# Globals
emulator_file = "fonts/Emulator.ttf"
tandysoft_file = "fonts/Tandysoft.ttf"
glo = Borg()
antialias = False
glo.emulator_font = FontRenderer(emulator_file, antialias)
glo.tandysoft_font = FontRenderer(tandysoft_file, antialias)
# NOTE TO SELF: never use None as deault font! It will segfault when
# doing packages with bbfreeze!
glo.default_font = FontRenderer(pygame.font.get_default_font())
glo.actual_screen_size = s.actual_frame_size
glo.hiscore = 10000
glo.score = 0
glo.bonus = 3000 # NOT SURE IF A GOOD IDEA!
glo.lives = s.NORMAL_DIFFICULTY_LIVES
glo.start_lives = s.NORMAL_DIFFICULTY_LIVES
glo.extra_lives = 2 # Internal counter don't touch!
glo.last_game_won = False
glo.quitting = False
glo.difficulty = s.NORMAL_DIFFICULTY

def get_new_level(number):
    level_name = level_list[number]['name']
    level_map = level_list[number]['tmx_map']
    level_music = level_list[number]['music']
    level_comic = level_list[number]['comic']
    mobs_mods = level_list[number]['mobs_mods']
    return level_name, level_map, level_music, level_comic, mobs_mods

def round_loop(scene_stack, level_list, glo, start_level=1, round_start=1, increase_per_round=0.1):
    
    level_number = start_level
    round_number = round_start
    glo.last_game_won = True
    congrats_scene = None
    
    while glo.last_game_won:
        glo.last_game_won = False
        level_name, level_map, level_music, level_comic, mobs_mods = get_new_level(level_number)
        if round_number > 1:
            for mob in mobs_mods:
                for mod in mobs_mods[mob]:
                    mobs_mods[mob][mod] *= 1 + (round_number -1) * increase_per_round
        scene_stack.push(TiledScene(level_map, level_music, mobs_mods, scorecounter))
        scene_stack.push(TransitionScene())
        scene_stack.push(TextScene(["ROUND {0}".format (round_number), "STAGE {0}".format(level_number), "{0}".format(level_name)], 3))
        scene_stack.push(ComicScene(level_comic))
        if congrats_scene:
            scene_stack.push(congrats_scene)
        e.scene_loop()
        
        if glo.last_game_won:
            level_number += 1
            if level_number == len(level_list.keys()) + 1:
                congrats_scene = TextScene(["CONGRATULATIONS!","YOU MADE IT TO ROUND: {0}".format(round_number + 1), "SCORE: {0}".format(glo.score)], 4)
            else:
                congrats_scene = None
            
            glo.score += glo.bonus
            if level_number > len(level_list.keys()):
                level_number = start_level
                round_number += 1
        else:
            scene_stack.push(TextScene(["GAME OVER", "SCORE: {0}".format(glo.score)], 4))
            glo.lives = glo.start_lives
            glo.score = 0
            glo.bonus = 0
            glo.extra_lives = 2
            e.scene_loop()
            return

# Level representing all the scores and bonus counters
level_dir = "data/levels/"
scorecounter = join(level_dir, "scorecounter.tmx")


start_level = 1
start_round = 1
increase_per_round = 0.2 # in percentage
while not glo.quitting:
    scene_stack.push(TitleScene())
    
    e.scene_loop()
    round_loop(scene_stack, level_list, glo, start_level, start_round, increase_per_round)


pygame.quit()
