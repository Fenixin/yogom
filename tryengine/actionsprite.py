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

from os.path import join
from math import hypot

import pygame

from constants import *
from utils import Timer
from animation import OnceUpdateAnimationPlayer, Animation, UpdateAnimationPlayer
from aparser import ArgumentParser
from sound import BetterSound
import settings as s

# make constants locals
# TODO move constants to acces them by reference?


# lets render some text
font = pygame.font.Font(pygame.font.get_default_font(), 12)
small_font = pygame.font.Font(pygame.font.get_default_font(), 8)


class ErrorParsingActionSprite(Exception):
    """ Raised when can't properly read an ActionSprite. """

    def __init__(self, msg):
        """ Class initialiser """
        self.msg = msg
        Exception.__init__(self, msg)

###############
# Base classes
###############


class ActionSprite(pygame.sprite.DirtySprite):
    """ Sprites that holds actions in the engine. At the moment they
        can be Triggers, Teleporters, Loadmap, Texts, Animations. """

        ########################################
        #
        # BIG NOTE TODO TODO TODO
        #
        # For the moment you have to call all the parents
        # before calling ActionSprite.__init__, if not the
        # text image gets overwritteng and bad things happen

        # TODO TODO TODO
        # at the moment parsing will ignore any non requested arguments.
        # That is bad, if you use an argument and write the name
        # wrong it will pass unnoticed complicating all the argument
        # thing a lot.

    def __init__(self, **others):
        # let's try to create a sprite without image
        pygame.sprite.DirtySprite.__init__(self)
        self.visible = 0

        # parse all the information in the tiled object
        self.custom_properties = { "name" : { "type" : str, "destination" : "name" },
                                   "type" : { "type" : str, "destination" : "type" },
                                   "x" : {"type" : int, "destination" : "x"},
                                   "y" : {"type" : int, "destination" : "y"},
                                   "width" : {"type" : int, "destination" : "width"},
                                   "height" : {"type" : int, "destination" : "height"},
                                   "gid" : {"type" : int, "destination" : "gid"} }
        
        self.parser = ArgumentParser(self.custom_properties, others, self.__dict__)
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)
        
        # rect and collision rect
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.col_rect = self.rect.copy()
        
        # we don't want to see the trigger
        self.image = WHITE_PIXEL
        self.image.set_alpha(0)
        self.blendmode = 0
        
        # an image with the friendly name given in tiled
        self.debug_image = small_font.render(self.name, False, GREY, PINK_TRANSPARENT)
        self.debug_image.set_colorkey(PINK_TRANSPARENT)
        
        # Dirty stuff
        self.dirty_rect = self.rect.copy()
        
        # print debug statements?
        self.debugging = False

    def parse_catching_errors(self, definitions, arguments, destination):
        try:
            self.parser.parse(definitions, arguments, destination)
        except ErrorParsingActionSprite as e:
            msg = "ActionSprite \"{0}\" in coords x = {1}, y = {2} gave the next error while parsing:\n {3}".format(self, arguments["x"], arguments["y"], e.msg)
            raise ErrorParsingActionSprite(msg)

    def change_sprite_pos(self, x, y):
        if self.dirty == 1:
            old = self.dirty_rect
        else:
            old = self.rect
        delta_col_x = self.col_rect[0] - self.rect[0]
        delta_col_y = self.col_rect[1] - self.rect[1]
        self.rect = pygame.Rect(x, y, self.rect[2], self.rect[3])

        # update the dirty state
        #~ if delta_x != 0 or delta_y != 0:
            #~ self.dirty = 1

        # move rects
        self.col_rect = pygame.Rect(x + delta_col_x, y + delta_col_y, self.col_rect[2], self.col_rect[3])
        #~ self.feet_rect.move_ip(delta_x, delta_y)
        self.dirty_rect  = old.union(self.rect)
        self.dirty = 1

    def move_sprite(self, delta_x, delta_y):
        """ Moves the two rects representing the sprite, the collision
        one and the drawing one. x and y are the offset of the movement. 
        """
        if self.dirty == 1:
            old = self.dirty_rect
        else:
            old = self.rect
        self.rect = self.rect.move(delta_x, delta_y)

        # update the dirty state
        #~ if delta_x != 0 or delta_y != 0:
            #~ self.dirty = 1

        # move rects
        self.col_rect = self.col_rect.move(delta_x, delta_y)
        #~ self.feet_rect.move_ip(delta_x, delta_y)
        self.dirty_rect  = old.union(self.rect)
        self.dirty = 1

    def get_trigger(self, code = None, event_type = TRIGGER):
        """ Gets all the TRIGGER events in the queue and return only
        the one with code. Puts all the non returned events back in the
        queue. """
        # TODO we suppose there are only one event of the trigger
        # at a given time
        # get the default code
        if code == None: code = self.triggered_code

        # get all the trigger events
        self.dprint("\n### In ActionSprite.get_trigger()")
        l = pygame.event.get(event_type)
        self.dprint("\t Trigger events from queue: {0}".format(str(l)))
        to_return = None
        if len(l) > 1:
            print "#############################################"
            print "# WARNING! There are more than two trigger events"
            print "# at the same time! And this is supossed not to happen"
        # find the one with code
        for e in l:
            self.dprint("\t\t event.code: {0}; searching for code: {1}".format(e.code, code))
            if e.code == code:
                self.dprint("\t\t\t We've got a trigger event! {0}".format(str(e)))
                to_return = e
        #~ # remove the event from the list
        #~ if l and to_return:
            #~ l.remove(to_return)
        
        # repost the events
        for e in l:
            pygame.event.post(e)

        return to_return

    def dprint(self, text):
        if self.debugging: print text


class Triggered(ActionSprite):
    def __init__(self, **others):
        """ Parent class to derivate all the actionsprites that are 
            triggered. """
        ActionSprite.__init__(self, **others)
        
        self.custom_properties = { "TriggeredCode" : { "type" : str, "destination" : "triggered_code" }}
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)

#############
# Triggers
#############

class Trigger(ActionSprite):
    def __init__(self, **others):
        """ Invisible sprite that triggers other action sprites when 
        player collides with its rect. """
        

        ActionSprite.__init__(self, **others)
        
        self.custom_properties = { "TriggerCode" : { "type" : str, "destination" : "trigger_code" }}
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)
        
    def do(self):
        """ Executed when player collides with the trigger rect. Posts
        an event in the queue with the code of the trigger. """
        self.dprint("\n### In Trigger.do()")
        e = pygame.event.Event(TRIGGER, code = self.trigger_code)
        self.dprint("Event: {0}".format(e))
        pygame.event.post(e)


class UseTrigger(Trigger):
    def __init__(self, **others):
        """ Invisible sprite that triggers other action sprites when 
        player collides with its rect and hits the 'use' key. """
        Trigger.__init__(self, **others)
        self.debugging = False
        
    def do(self):
        """ Executed when player collides with the trigger rect. Posts
        an event in the queue with the code of the trigger. """
        self.dprint("\n### In UseTrigger.do()")
        e = self.get_trigger(USE, PLAYER) 
        self.dprint("\tEvent recieved: {0}".format(str(e)))
        if e:
            e = pygame.event.Event(TRIGGER, code = self.trigger_code)
            self.dprint("Event sent: {0}".format(e))
            pygame.event.post(e)


#~ class FuseTrigger(Trigger):
    #~ def __init__(self, **others):
        #~ """ Once on, always on. """
        #~ Trigger.__init__(self, **others)
        #~ self.debugging = False
        #~ self.alwayson = False
        #~ 
    #~ def do(self):
        #~ """ Executed when player collides with the trigger rect. Posts
        #~ an event in the queue with the code of the trigger. """
        #~ self.dprint("\n### In Trigger.do()")
        #~ e = pygame.event.Event(TRIGGER, code = self.trigger_code)
        #~ self.dprint("Event: {0}".format(e))
        #~ pygame.event.post(e)
        #~ self.alwayson = True
    #~ 
    #~ def update(self, *others):
        #~ print "updatingfusetrigger!", self.alwayson
        #~ if self.alwayson:
            #~ print "         doing!"
            #~ self.do()

##########
# Texts
##########

class TextActionSprite(ActionSprite):
    """ Base class to derivate from when creating Text showing in
        screen. """
        
        
        ########################################
        #
        # BIG NOTE TODO TODO TODO 
        #
        # For the moment you have to call all the parents
        # before calling ActionSprite.__init__, if not the
        # text image gets overwritteng and bad things happen
    def __init__(self, **others):
        ActionSprite.__init__(self, **others)
        
        self.custom_properties = { "Text" : { "type" : str, "destination" : "text" },
                                   "AlphaSpeed" : {"type" : int, "destination" : "alphaspeed"}, 
                                   "Follow" : {"type" : int, "destination" : "follow"} }
        
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)
        
        self.visible = 1
        antialias = False
        # create the text
        self.image = font.render(self.text, antialias, WHITE, BLACK)
        # Override the dirty rect
        image_rect = self.image.get_rect()
        self.dirty_rect = pygame.Rect(self.rect[0], self.rect[1], image_rect[2], image_rect[3])
        self.alpha = 0
        self.image.set_alpha(self.alpha)
        self.showing = False
        
        # redefine the rect using the image size
        
        rect = self.image.get_rect()
        rect.x = self.rect.x
        rect.y = self.rect.y
        self.rect = rect
        self.col_rect = rect.copy()

    def do(self):
        """ Print the text. """
        if not self.triggered_code:
            
            self.showing = True
    
    def update_position(self, player):
        self.dprint("\n### TextActionSprite.update_position()")
        if self.follow:
            x = player.col_rect[0] - self.rect[0]
            y = player.col_rect[1] - self.rect[1]
            #~ self.rect.move_ip(x + player.col_rect.width, y - self.image.get_size()[1])
            self.move_sprite(x + player.col_rect.width, y - self.image.get_size()[1])
            self.dprint("\nSeting position to: {0}".format(self.rect))
        
    def update_alpha(self):
        """ Updates the alpha of the surface. """
        self.dprint("\n### TextActionSprite.update_alpha()")
        if self.showing:
            self.alpha += self.alphaspeed
            if self.alpha > 255: self.alpha = 255
            #~ self.showing = False
        else:
            self.alpha -= self.alphaspeed
            if self.alpha < 0: self.alpha = 0
        self.dprint("\nSeting alpha to: {0}".format(self.alpha))
        self.image.set_alpha(self.alpha)


class TriggeredText(TextActionSprite, Triggered):
    """ Text that is triggered from a trigger event. """
    def __init__(self, **others):
        Triggered.__init__(self, **others)
        TextActionSprite.__init__(self, **others)


    def update(self, player, collisions_group, **others):
        self.dprint("\n### TriggeredText.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if e:
            self.dprint("\t\tShowing the text!")
            self.update_position(player)
            self.showing = True
        else:
            self.showing = False
        
        self.update_alpha()


class ToggleText(TextActionSprite, Triggered):
    """ Text that toggles on/off when a trigger event is received. 
        Special parameters are:
        - Delay: amount of time to wait before you can toggle the text
                again.
    """
    def __init__(self, **others):
        Triggered.__init__(self, **others)
        TextActionSprite.__init__(self, **others)
        
        
        # custom parameters
        self.custom_properties = { "Delay" : {"type" : float, "destination" : "delay"} }
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)

        # create the timer
        self.timer = Timer(self.delay)

        # prints lots of debugging text
        self.debugging = False
    
    def update(self, player, collisions_group, **others):
        self.dprint("\n### TriggeredText.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if e and self.timer.finished:
            self.timer.reset()
            self.dprint("\t\tToggling text")

            if self.showing:
                self.update_position(player)
                self.dprint("\t\t\tDeactivating text")
                self.showing = False
            else:
                self.update_position(player)
                self.dprint("\t\t\tActivating text")
                self.showing = True
        
        self.update_alpha()
    
    def do(self):
        pass


###############
# Teleporters
###############

class TriggeredLocationTeleporter(Triggered):
    """ Invisible sprite that teleports the player to its location when
    the trigger event is received. """
    def __init__(self, **others):
        Triggered.__init__(self, **others)
    
    def update(self, player, collisions_group, **others):
        self.dprint("\n### TriggeredLocationTeleporter.update()")
        e = self.get_trigger()
        self.dprint("\tEvent:" + str(e))
        if e:
            # using the player rect instead of the col_rect to calculate the coords
            # we get the player to move almost in the center of one tile.
            
            # TODO TODO TODO move the "move player code" to handle_events in engine.py
            player.move_sprite( self.col_rect[0] - player.rect.x, self.col_rect[1] - player.rect.y )
    
    def do(self):
        pass

class CollisionTriggeredCoordsTeleporter(ActionSprite):
    def __init__(self, **others):
        """ Invisible sprite that theleports sprites that collide with. 
        Special properties are:
        - ToTileX: X coord to move the sprite in tile coords.
        - ToTileY: Y coord to move the sprite in tile coords.
        """
        ActionSprite.__init__(self, **others)
        
        self.custom_properties = { "ToTileX" : { "type" : int, "destination" : "coordx" },
                                   "ToTileY" : { "type" : int, "destination" : "coordy" }}
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)
        
        self.tile_coords = (self.coordx, self.coordy)
        self.pixel_coords = ( self.tile_coords[0] * s.tile_width, self.tile_coords[1] * s.tile_height )
        
        self.visible = 0
        
    def update(self, player, collisions_group, **others):
        self.player = player

    def do(self):
        self.player.move_sprite( self.pixel_coords[0] - self.player.rect.x, self.pixel_coords[1] - self.player.rect.y )



###############
# Sounds
###############

class SoundActionSprite(ActionSprite):
    """ Base class to derivate all sound classes."""
    def __init__(self, **kwargs):
        ActionSprite.__init__(self, **kwargs)
        
        self.custom_properties = { "SoundPath" : { "type" : str, "destination" : "sound_path" },
                                   "DistancePower" : { "type" : float, "destination" : "distance_pow", "default" : 10},
                                   "PanPower" : { "type" : float, "destination" : "pan_pow" , "default" : 10},
                                   "DefaultVolume" : { "type" : float, "destination" : "default_vol", "default" : 1.0},
                                   "Loops" : { "type" : int, "destination" : "loops", "default" : 0 },
                                   "MaxTime" : { "type" : int, "destination" : "maxtime", "default" : 0 },
                                   "FadeInTime" : { "type" : int, "destination" : "fadein_ms", "default" : 500 },
                                   "FadeOutTime" : { "type" : int, "destination" : "fadeout_ms", "default" : 500 },
                                   "MaxDistance" : { "type" : int, "destination" : "max_d_in_tiles", "default": 0 } }

        self.parse_catching_errors(self.custom_properties, kwargs, self.__dict__)
        
        path = join("playaypiratas/world/testing/",self.sound_path)
        
        self.sound = BetterSound(path, self.distance_pow, self.pan_pow, self.default_vol)

        self.visible = 0
    def do(self, **others):
        pass


class PuntualSoundActionSprite(SoundActionSprite):
    def __init__(self, **kwargs):
        
        SoundActionSprite.__init__(self, **kwargs)

        #~ self.custom_properties = {  }
        #~ self.parse_catching_errors(self.custom_properties, kwargs, self.__dict__)
        
        self.max_d = s.tile_width * self.max_d_in_tiles
        
        self.visible = 0

    def update(self, player, col, **others):
        px, py = player.col_rect.center
        x, y = self.rect.center
        sound = self.sound
        
        distance = hypot(px - x, py - y)
        x_distance = px - x

        #~ print "distance: ", distance
        #~ print "maxdistance: ", self.max_d
        #~ print "num of active channels: ", sound.sound.get_num_channels()
        #~ print "channel busy: ", self.sound.channel.get_busy()
        if distance > self.max_d:
            #~ print "stopping sound!"
            sound.fadeout(self.fadeout_ms)
        else:
            sound.update(x_distance, distance)
            
            if not sound.playing:
                sound.play(fade_ms = self.fadein_ms)



###############
# Animations
###############

class AnimationActionSprite(ActionSprite):
    """ Base class to derivate all the AnimationActionSprite classes."""

    def __init__(self, **others):
        ActionSprite.__init__(self, **others)
        
        self.visible = 1
        
        self.custom_properties = {
            "FrameSizeX": {"type": int, "destination": "sizex" },
            "FrameSizeY": {"type": int, "destination": "sizey" },
            "Spritesheet": {"type": str, "destination": "spritesheet_path" },
            "UpdatesPerFrame": {"type": int, "destination": "updates_per_frame" },
            "AlwaysOn": {"type": bool, "destination": "always_on", "default": False},
            "OnceOnAlwaysOn": {"type": bool, "destination": "once_on_always_on", "default": False}, }
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)

        spritesheet = pygame.image.load(join("playaypiratas/world/testing/",self.spritesheet_path)).convert_alpha()
        
        animation = Animation(spritesheet, (self.sizex, self.sizey))
        self.animation_player = UpdateAnimationPlayer(animation, self.updates_per_frame)
        
        # init the sprite with an actual image (action sprite has no image)
        self.image = self.animation_player.get_next_frame()
        image_rect = self.image.get_rect()
        self.dirty_rect = pygame.Rect(self.rect[0], self.rect[1], image_rect[2], image_rect[3])
    
    def next_frame(self):
        """ Updates the image in the sprite. Needs to be called once per
        sprite update to work properly. """
        old = self.image
        self.image = self.animation_player.get_next_frame()
        if old is not self.image:
            self.dirty = 1

    def do(self):
        pass

class OnceAnimationActionSprite(AnimationActionSprite, Triggered):
    """ Plays an animation when triggered by a trigger. The animation is
    player once. 
    Special properties are:
     - TriggeredCode : a string to trigger this actionsprite
     - FrameSizeX" : horizontal size of the animation frame in pixels
     - FrameSizeY" : vertical size of the animation frame in pixels
     - UpdatesPerFrame : speed of the animation in updates
     - Spritesheet : path to the spritesheet to use
    """

    def __init__(self, **others):
        Triggered.__init__(self, **others)
        AnimationActionSprite.__init__(self, **others)

        self.custom_properties = {
            "FrameSizeX": { "type": int, "destination": "sizex" },
            "FrameSizeY": { "type": int, "destination": "sizey" },
            "UpdatesPerFrame": { "type": int, "destination": "updates_per_frame" }, 
            "Spritesheet": { "type": str, "destination": "spritesheet_path" } }
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)

        # TODO hardcoded path! bad thing!
        spritesheet = pygame.image.load(join("playaypiratas/world/testing/",self.spritesheet_path)).convert_alpha()
        
        self.size = (self.sizex, self.sizey)
        self.animation = Animation(spritesheet, (self.size))
        self.animation_player = OnceUpdateAnimationPlayer(self.animation, self.updates_per_frame)
        
        # init the sprite with an actual image (action sprite has no image)
        self.image = self.animation_player.get_next_frame()

    def update(self, player, collisions_group, **others):
        self.dprint("\n### TriggeredAnimation.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if e or self.always_on:
            self.next_frame()
            if self.once_on_always_on:
                self.always_on = True

class TriggeredAnimation(AnimationActionSprite, Triggered):
    """ Plays the given animation when triggered. """
    def __init__(self, **others):
        Triggered.__init__(self, **others)
        AnimationActionSprite.__init__(self, **others)
        
        self.debugging = False
        
    def update(self, player, collisions_group, **others):
        self.dprint("\n### TriggeredAnimation.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if e or self.always_on:
            self.next_frame()

class ToggleAnimation(AnimationActionSprite, Triggered):
    "Animation that can be toggled on/off. """
    def __init__(self, **others):
        Triggered.__init__(self, **others)
        AnimationActionSprite.__init__(self, **others)
        
        self.debugging = False
        self.playing = False
        self.timer = Timer(0.2)
        
        self.animation_player.backwards = True

    def update(self, player, collisions_group, **others):
        self.dprint("\n### ToggleAnimation.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if self.timer.finished and e:
            self.timer.reset()
            self.dprint("\t\tToggling Animation")
            if self.playing:
                self.dprint("\t\t\tDeactivating animation")
                self.playing = False
            else:
                self.dprint("\t\t\tActivating animation")
                self.playing = True
        
        if self.playing:
            self.next_frame()
    

class PingPongTriggeredAnimation(OnceAnimationActionSprite, Triggered):
    """ Animation that tries to be always in start or the end of the
        animation. Kind of an animation of a lever, the lever can be
        switched on/off but alawys end up in the start or end position.
        """
        
    def __init__(self, **others):
        Triggered.__init__(self, **others)
        OnceAnimationActionSprite.__init__(self, **others)
        
        self.debugging = False
        self.playing = False
        self.timer = Timer(0.2)
        
        self.debugging = False

    def do(self):
        pass

    def update(self, player, collisions_group, **others):
        self.dprint("\n### PingPongAnimation.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if e and self.timer.finished:
            #~ import pdb; pdb.set_trace()
            self.dprint("\t\tToggling Animation")
            self.timer.reset()
            if self.animation_player.finished:
                #~ import pdb; pdb.set_trace()
                self.animation_player.finished = False
                self.animation_player.backwards = not self.animation_player.backwards
            else:
                if self.animation_player.backwards:
                    self.animation_player.backwards = False
                else:
                    self.animation_player.backwards = True
            
        
        self.next_frame()


            # TODO!!! InitiallyOn in here is ignored! see the commented code below
                #~ elif o.type == "TriggerCollision":
                    #~ temp = TriggeredCollisionActionSprite(**o.__dict__)
                    #~ self.action_sprites.add(temp)
                    #~ if o.InitiallyOn == "1":
                        #~ self.collision_sprites.add(temp)


###############
# Collisions
###############

class CollisionActionSprite(ActionSprite):
    """ Generic ActionSprite to add sprites that iteract through 
    collisions. """
    def __init__(self, **others):
        ActionSprite.__init__(self, **others)
        self.visible = 0
        
    def update_status(self, collisions_group):
        if self in collisions_group:
            self.remove(collisions_group)
        else:
            self.add(collisions_group)
    
    def do (self):
        pass

class ToggleCollision(CollisionActionSprite, Triggered):
    """ Invisible sprite with a rectangle in the collision group that
    adds or removes itself from the collision group by trigger. """
    def __init__(self, **others):
        CollisionActionSprite.__init__(self, **others)
        Triggered.__init__(self, **others)
        self.visible = 0
        
    def update(self, player, collisions_group, **others):
        self.dprint("\n### TriggeredCollisionActionSprite.update()")
        e = self.get_trigger(self.triggered_code)
        self.dprint("\tEvent:" + str(e))
        if e:
            self.update_status(collisions_group)


###############
# Load Map 
###############

class CollisionTriggeredLoadMap(ActionSprite):
    def __init__(self, **others):
        """ Invisible sprite that triggers the loading of a new map
        when player collides with its rect. """
        ActionSprite.__init__(self, **others)
        
        self.custom_properties = { "Map" : { "type" : str, "destination" : "map" }, 
                                   "To" : { "type" : str, "destination" : "spawn"} }
        self.parse_catching_errors(self.custom_properties, others, self.__dict__)

        self.visible = 0

    def do(self):
        """ Executed when player collides with the trigger rect. Posts
        an event in the queue with the code of the trigger. """
        self.dprint("\n### In Trigger.do()")
        e = pygame.event.Event(ENGINE, code = NEW_MAP, map_path = self.map, spawn = self.spawn)
        self.dprint("Event: {0}".format(e))
        pygame.event.post(e)
