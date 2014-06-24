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

""" Module to help reading of the tiled maps. """

# TODO: Overhaul this... it's outdated/ugly

from os.path import join, dirname
from math import ceil

import pygame
import pytmx

import actionsprite
from aparser import ArgumentParser
from sprites import ImageSprite, TryGroup
from utils import extend_dict
from quadtree import QuadTree
import constants as c
import settings as s
from constants import *
import sprites

import scripts

# cameras
from camera import cameras_dict

# localize some constants
WHITE_PIXEL = c.WHITE_PIXEL

class UnknownPlatformType(Exception):
    def __init__(self, error):
        print "The given platform can't be imported."



class Map(object):
    """ Loads a Tiled map and gives some tools to work with it """
    def __init__(self, filename):
        # load it using pytmx
        from pytmx import tmxloader
        self.path = filename
        self.tiledmap = tmxloader.load_pygame(filename, force_colorkey = PINK_TRANSPARENT)
        self.spritesheet = self.tiledmap.tilesets[0].source
        
        # some useful variables
        self.map_size = (self.tiledmap.width * self.tiledmap.tilewidth, self.tiledmap.height * self.tiledmap.tileheight)

        s.tile_width = self.tiledmap.tilewidth
        s.tile_height = self.tiledmap.tileheight

        #used to keep in touch with the objects, placeholder
        self.item_sprites = pygame.sprite.Group()
        
        # collision tiles coordinates and sprites
        self.col_tiles_coords = []
        self.one_way_col = []
        self.collision_group = pygame.sprite.Group()
        
        # single list for all the layers
        self.layers = []
        
        #used to store tiles representing actions: doors, text signs, climbing tiles...
        self.actionsprites = pygame.sprite.Group()
        
        #------------------------
        # Mobs and players.
        # Sotres all the mobs and the player in the same group, used to
        # just run mobs.update
        self.mobs = pygame.sprite.Group()
        self.hostiles = pygame.sprite.Group()

        
        # stores the spawn position of the player, is set by a "Player"
        # type of object in a object layer called "Player" in the Tiled
        # map
        self.player_spawns = {}
        # which one of the moblayers is the one with the player
        self.player_layer = None

        # cameras found in sprites to add to the renderer
        self.cameras = []

        self.debugging = False

        # get all the layers!
        all_tiled_layers = self.tiledmap.all_layers
        for layer in range(len(all_tiled_layers)):
            tiledlayer = all_tiled_layers[layer]
            
            if tiledlayer in self.tiledmap.tilelayers:
                tile_layer_index = self.tiledmap.tilelayers.index(tiledlayer)
                if hasattr(tiledlayer, 'Collision'):
                    new_layer = NewCollisionLayer(self.tiledmap, tile_layer_index)
                else:
                    new_layer = TileLayer(self.tiledmap, tile_layer_index)
                
            elif tiledlayer in self.tiledmap.imagelayers:
                index = self.tiledmap.imagelayers.index(tiledlayer)
                new_layer = ImageLayer(self.tiledmap, index)
                
            elif tiledlayer in self.tiledmap.objectgroups:
                index = self.tiledmap.objectgroups.index(tiledlayer)
                new_layer = ObjectLayer(self.tiledmap, index)
            
            self.layers.append(new_layer)

        # final loop to collect all the layer info
        for layer in self.layers:
            if isinstance(layer, ObjectLayer):
                self.get_info_object_layer(layer)
            elif isinstance(layer, NewCollisionLayer):
                #~ self.collision_group.add(layer.collision)
                self.collision_group.add(layer.static)

        if len(self.collision_group) > 300:
            depth = 8
        else:
            depth = 6

        if self.collision_group.sprites():
            self.collision_tree = QuadTree(self.collision_group, depth)

    def get_info_object_layer(self, layer):
        self.actionsprites.add(layer.actionsprites)
        self.mobs.add(layer)
        self.hostiles.add([i for i in layer.sprites() if i.hostile])
        extend_dict(self.player_spawns, layer.player_spawns)
        self.cameras.extend(layer.cameras)

    def dprint(self,text):
        if self.debugging:
            print text



class GenericLayer(object):
    def __init__(self, tiledmap, **args):
        
        self.parser = ArgumentParser()
        self.args_description = { "name" : { "type" : str, "destination" : "name" },
                                  "opacity" : {"type" : float, "destination" : "opacity", "default": 1.00},
                                  "visible" : {"type" : int, "destination" : "visible", "default": 1} }
                                # TODO TODO TODO the parser is gettint the visible argument as true sometimes... wtf

        self.parser.parse(self.args_description, args, self.__dict__)
        self.tilewidth = tiledmap.tilewidth
        self.tileheight = tiledmap.tileheight
        
        
        self.debugging = False


    def apply_opacity(self, surface, opacity):
        surface = surface.copy().convert_alpha()
        get_at = surface.get_at
        set_at = surface.set_at
        
        w, h = surface.get_size()
        
        for x in range(w):
            for y in range(h):
                r,g,b,a = get_at((x, y))
                a = ceil(a * opacity)
                set_at((x, y), (r,g,b,a))
        
        return surface


    def dprint(self,text):
        if self.debugging:
            print text


class TileLayer(GenericLayer):
    def __init__(self, tiledmap, pytmx_index):
        
        tiled_obj = tiledmap.tilelayers[pytmx_index]
        GenericLayer.__init__(self, tiledmap, **tiled_obj.__dict__)

        # get some custom arguments
        self.args_description = { "width" : { "type" : int, "destination" : "width"},
                                  "height" : { "type" : int, "destination" : "height" } }
        self.parser.parse(self.args_description, tiled_obj.__dict__, self.__dict__)

        # groups to store tiles and animated tiles
        self.static = pygame.sprite.Group()
        self.dynamic = pygame.sprite.Group()

        # read the tiles
        self.read_layer(tiledmap, pytmx_index)

        # generate the static image of the layer
        self.map_size_in_pixels = (self.tilewidth*self.width,self.tileheight*self.height)
        self.static_img = pygame.Surface(self.map_size_in_pixels,pygame.HWSURFACE | pygame.SRCALPHA)
        self.static_img.fill((0,0,0,0))
        self.static.draw(self.static_img)

    def read_layer(self, tiledmap, index):

        # tile imgs with per pixel alpha modified
        opacity_mod_tiles = {}
        tiled_obj = tiledmap.tilelayers[index]
        
        apply_op = self.apply_opacity
        add = self.static.add

        # remember, to use these funcions we have to 
        # use the index from tiledmap.tilelayers
        get_tile_img = tiledmap.getTileImage
        get_tile_prop = tiledmap.getTileProperties
        th = tiledmap.tilewidth
        tw = tiledmap.tileheight
        opacity = self.opacity
        
        # TODO: this is ugly
        if hasattr(self, 'platform_type'):
            platform = self.platform_type
        else:
            platform = sprites.Tile
        
        for i in range(0, tiledmap.width):
            for j in range(0, tiledmap.height):
                tile_img = get_tile_img(i, j, index)
                tile_prop = get_tile_prop((i, j, index))
                if tile_img:
                    tile_img = tile_img.convert()
                    tile_img.set_colorkey(PINK_TRANSPARENT)
                    # Apply layer opacity
                    if opacity != 1.0:
                        tile_img.set_alpha(ceil(opacity*255))
                    add(platform(tile_img, i*tw, j*th, **tiled_obj.__dict__))
                    # TODO TODO TODO TODO... dynamic tiles!


class CollisionLayer(TileLayer):
    def __init__(self, tiledmap, pytmx_index):
        
        tiled_obj = tiledmap.tilelayers[pytmx_index]
        TileLayer.__init__(self, tiledmap, pytmx_index)

        # list to store the coords and group for the tiles
        self.coords_list = []
        self.collision = pygame.sprite.Group()

        # TODO self.dynamic?
        # Is this a oneway collision
        self.onewaycollision = True if (tiled_obj.name == "OneWayCollision") else False
        
        # get the list of coords
        self.get_coords(self.static , self.coords_list)

        # optimize number of collision rects
        self.optimize_collision_sprites(WHITE_PIXEL, 0, self.coords_list, self.collision)


    def get_coords(self, group, coords_list):
        """ Get the list of all the sprite coords
            inthe group and store them in a list. 
            
            This list is later used to optimize the 
            amount of collision rects. """
        sprs = self.static.sprites()
        tw = self.tilewidth
        th = self.tileheight
        coords_append = coords_list.append
        
        for spr in sprs:
            x = spr.rect[0]
            y = spr.rect[1]
            x = x / tw
            y = y / th
            coords_append((x,y))


    def optimize_collision_sprites(self, tile_img, mode, coords_list, group):
        # mode not implemented, but the idea is
        # mode = 0 vertical
        # mode = 1 horizontal
        
        tw = self.tilewidth
        th = self.tileheight
        dprint = self.dprint
        
        # optimizing collision sprites
        consecutive_sprites = []
        temp = []
        
        # collisions optimizing
        # this new algoritm works pretty good! 
        coords_list.sort()
        l = coords_list
        to_del = []
        big_platforms = []

        dprint("Amount of coords = {0}".format(len(l)))
        dprint("### Optimizing")
        for k in coords_list:
            dprint("\n\n\tNew k: {0}".format(k))
            if k in to_del:
                dprint("\t\tskiping {0}".format(k))
                continue
            # grow rectangles to the right
            g_right = True
            right_c = 0
            while g_right:
                temp = (k[0] + right_c + 1, k[1])
                dprint("\t\tIn while with: g_right = {0}, temp = {1}, right_c= {2}".format(g_right, temp, right_c))
                if temp in l:
                    dprint("\t\t\tAdding one sprite to the rect!")
                    right_c += 1
                    to_del.append(temp)
                else:
                    dprint("\t\t\tNO rects to add!")
                    g_right = False
            dprint("\tFinal right counter: {0}".format(right_c))
            dprint("\tAmount of coords to del: {0}".format(len(to_del)))
            # grow down the now possibly big rect
            dprint("\n\tGrowing down!")
            down_c = 0
            g_down = True
            temp_to_del = []
            while g_down:
                dprint("\t\tIn while with: g_down = {0}, down_c= {1}".format(g_right, right_c))
                possible = True
                for i in range(right_c + 1):
                    dprint("\t\t\tIn for with: i = {0}".format(i))
                    temp = (k[0] + i, k[1] + down_c + 1)
                    temp_to_del.append(temp)
                    if temp in to_del:
                        # is already in a rect!
                        # TODO this make it works as expected! but it also 
                        # add more sprites!!! What to do?
                        possible = False
                        break
                        continue
                    elif temp in l:
                        dprint("\t\t\t\tThe tile exist! continue the for")
                        continue
                    else:
                        dprint("\t\t\t\tNO tile here. Break.")
                        possible = False
                        break
                if possible:
                    down_c += 1
                    to_del.extend(temp_to_del)
                else:
                    g_down = False
            big_platforms.append((k,right_c,down_c))
        
        platform_type = OneWayPlatform if self.onewaycollision else Platform
        
        for p in big_platforms:
            (i,j), size_i, size_j = p
            group.add(platform_type(tile_img, i * tw, j * th))

class NewCollisionLayer(TileLayer):
    def __init__(self, tiledmap, pytmx_index):
        """ The same as TileLayer but with colliding sprites. """ 

        tiled_obj = tiledmap.tilelayers[pytmx_index]
        self.platform_type = scripts.__dict__[tiled_obj.Collision]

        TileLayer.__init__(self, tiledmap, pytmx_index)

        # Group with all the platforms
        #~ self.collision = pygame.sprite.Group()


class ObjectLayer(GenericLayer, TryGroup):
    def __init__(self, tiledmap, pytmx_index):
        
        tiled_obj = tiledmap.objectgroups[pytmx_index]
        GenericLayer.__init__(self, tiledmap, **tiled_obj.__dict__)
        self.tiledmap = tiledmap
        # all the sprites are redrawn always, no need for two groups
        # make the self a group
        TryGroup.__init__(self)
        
        # get arguments
        self.args_description = { "width" : { "type" : int, "destination" : "width"},
                                  "height" : { "type" : int, "destination" : "height" } }
        self.parser.parse(self.args_description, tiled_obj.__dict__, self.__dict__)
        
        # some needed stuff
        self.player_spawns = {}
        self.cameras = []
        self.actionsprites = TryGroup()
        
        self.read_objects(tiled_obj)

    def read_objects(self, tiled_obj):
        for obj in tiled_obj:
            t = obj.type
            if t in scripts.__dict__:
                #~ print self.tiledmap.tilesets
                #~ print self.tiledmap.tilesets[0].source
                m = scripts.__dict__[obj.type](**obj.__dict__)
                if obj.type == "Player": self.player_spawns[obj.FromLocation] = m
                self.add(m)
                # add cameras
                if 'Camera' in obj.__dict__:
                    c_list = obj.Camera.split(',')
                    for c in c_list:
                        try:
                            cm = cameras_dict[c](m)
                            self.cameras.append(cm)
                        except:
                            print "Camera error: The value {0} is not a valid camera.".format(c)
            
            elif t in actionsprite.__dict__:
                a = actionsprite.__dict__[obj.type](**obj.__dict__)
                self.actionsprites.add(a)
            else:
                print "Warning! Invalid object type: {0}".format(obj.type)
                pass

class ImageLayer(GenericLayer, TryGroup):

    def __init__(self, tiledmap, pytmx_index):
        #get the tile obj
        tiled_obj = tiledmap.imagelayers[pytmx_index]
        GenericLayer.__init__(self, tiledmap, **tiled_obj.__dict__)
        TryGroup.__init__(self)
        
        # custom info
        self.args_description = { "source" : { "type" : str, "destination" : "source"}}
        self.parser.parse(self.args_description, tiled_obj.__dict__, self.__dict__)
        
        # get the image
        img_name = self.source
        img_dir = dirname(tiledmap.filename)
        img_path = join(img_dir, img_name)
        img = pygame.image.load(img_path).convert()
        
        # apply the layer opacity
        if self.opacity != 1.0:
            # TODO
            # this takes a long time for big images, I'm afraid
            img = self.apply_opacity(img, self.opacity)
        sp = ImageSprite(img, 0, 0)
        self.add(sp)


