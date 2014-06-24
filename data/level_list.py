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

from os.path import join

import scripts

level_dir = "data/levels/"
music_dir = "data/music/"
comic_dir = "data/comics/"

level_list = {
    1: {'name': "Madrid", 'comic': join(comic_dir, "madrid.png" ), 'tmx_map': join(level_dir, "madrid.tmx"), 'music': join(music_dir, "01 Madrid.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.5}, scripts.Cup : {'max_speed' : 0.18} }},
    2: {'name': "Paris", 'comic': join(comic_dir, "paris.png" ),'tmx_map': join(level_dir, "paris.tmx"), 'music': join(music_dir, "02 Paris.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.5}, scripts.Cup : {'max_speed' : 0.17} }},
    3: {'name': "Cairo", 'comic': join(comic_dir, "cairo.png" ),'tmx_map': join(level_dir, "cairo.tmx"), 'music': join(music_dir, "03 Egipto.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.63}, scripts.Cup : {'max_speed' : 0.18} }},
    8: {'name': "Sydney", 'comic': join(comic_dir, "sydney.png" ),'tmx_map': join(level_dir, "sydney.tmx"), 'music': join(music_dir, "04 Australia.ogg"), 
        'mobs_mods' : {scripts.Boomerang : {'max_speed' :1.3 , 'acceleration' : 0.06}, scripts.Cup : {'max_speed' : 0.19} }},
    5: {'name': "Venus", 'comic': join(comic_dir, "venus.png" ),'tmx_map': join(level_dir, "venus.tmx"), 'music': join(music_dir, "05 Venus.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.5}, scripts.Cup : {'max_speed' : 0.18} }},
    4: {'name': "Mount Fuji", 'comic': join(comic_dir, "japon.png" ),'tmx_map': join(level_dir, "japon.tmx"), 'music': join(music_dir, "06 China.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.7}, scripts.Cup : {'max_speed' : 0.16} }},
    6: {'name': "???", 'comic': join(comic_dir, "nowhere.png" ),'tmx_map': join(level_dir, "nowhere.tmx"), 'music': join(music_dir, "07.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.8}, scripts.Cup : {'max_speed' : 0.16} }},
    7: {'name': "New York", 'comic': join(comic_dir, "NYC.png" ),'tmx_map': join(level_dir, "NYC.tmx"), 'music': join(music_dir, "08 USA.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.48}, scripts.Cup : {'max_speed' : 0.16} }},
    9: {'name': "Rapa Nui", 'comic': join(comic_dir, "rapanui.png" ),'tmx_map': join(level_dir, "rapanui.tmx"), 'music': join(music_dir, "09 Isla De Pascua.ogg"), 
        'mobs_mods' : {scripts.Pigeon : {'max_speed' :0.65}, scripts.Cup : {'max_speed' : 0.17} }},
    #10: {'name': "Space", 'comic': join(comic_dir, "moon.jpg" ),'tmx_map': join(level_dir, "moon.tmx"), 'music': join(music_dir, "01 Madrid.ogg"), },
    }

