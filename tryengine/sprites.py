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

""" Module with the basic Sprite from which derivate.

All sprites should derivate from TrySprite and TryMovingSprite.
"""

import sys
from collections import deque
from random import randint
from math import modf

from pygame.sprite import spritecollideany, DirtySprite, OrderedUpdates, Group, RenderUpdates
from pygame import Rect, mask

from utils import collision_detection, Borg
from animation import SpeedAnimationPlayer, SpeedUpdateAnimationPlayer
from constants import *
import settings as s

glo = Borg()


class TryGroup(OrderedUpdates):
    """ Group used in try-engie. """
    def __init__(self, *sprites):
        OrderedUpdates.__init__(self, *sprites)

    def update(self, *args):
        """update(*args)
           call update for all member sprites

           calls the update method for all sprites in the group.
           Passes all arguments on to the Sprite update function.
           Also leaves guests sprites to be updated at the end."""
        
        guests = []
        for s in self.sprites():
            if not s.guest: s.update(*args)
            else: guests.append(s)
        for s in guests:
            s.update(*args)

    def dirtify(self):
        """ Turns all the sprites in the group into 
        dirty sprites. """
        sprites = self.sprites()

        for spr in sprites:
            spr.dirty = 1

    def simple_draw(self, surface):
        """ Draw all the sprites in the given surface.

        It updates lostsprites and take into account blendmodes.
        Please note the dirty attribute in TrySprite doesn't mean
        the same as in DirtySprite.

        """

        spritedict = self.spritedict
        surface_blit = surface.blit
        for s in self.sprites():
            if s.visible:
                s.dirty = 0
                # TODO force allthe sprites to have blendmode
                if hasattr(s, "blendmode"):
                    spritedict[s] = surface_blit(s.image, s.rect, special_flags = s.blendmode)
                else:
                    spritedict[s] = surface_blit(s.image, s.rect)
                    
        self.lostsprites = []

    def interpolate_draw(self, surface, interpolate):
        """ Draw all the sprites in the given surface.

        It updates lostsprites and take into account blendmodes.
        Please note the dirty attribute in TrySprite doesn't mean
        the same as in DirtySprite.

        """

        spritedict = self.spritedict
        surface_blit = surface.blit
        for s in self.sprites():
            if s.visible:
                s.dirty = 0
                try:
                    spritedict[s] = surface_blit(s.image, s.i_rect, special_flags = s.blendmode)
                except AttributeError:
                    spritedict[s] = surface_blit(s.image, s.rect, special_flags = s.blendmode)
                
        self.lostsprites = []
    
    def one_layer_up(self, sprite):
        """ Moves the sprite one layer up in the render group. 
        
        This will make the sprite be seen over other sprites
        in the same group.

        """
        sprites = self._spritelist
        try:
            i = sprites.index(sprite)
        except ValueError:
            raise
        
        if i != 0:
            sprites[i - 1], sprites[i] = sprites[i], sprites[i - 1]
        
    def one_layer_down(self, sprite):
        """ Moves the sprite one layer down in the render group. 
        
        This will make the sprite be seen over other sprites
        in the same group.

        """
        sprites = self._spritelist
        try:
            i = sprites.index(sprite)
        except ValueError:
            raise
        
        if i != len(sprites) - 1:
            sprites[i + 1], sprites[i] = sprites[i], sprites[i + 1]

    def add_below(self, ref_sprite, sprite):
        """ Add the sprite to the group below ref_sprite.
        
        The sprite will be added below ref sprite so ref_sprite is
        on top of it.
        """
        RenderUpdates.add_internal(self, sprite)
        i = self._spritelist.index(ref_sprite)
        self._spritelist.insert(i+1, sprite)
        
        sprite.add_internal(self)

    def add_ontop(self, ref_sprite, sprite):
        """ Add the sprite to the group on top ref_sprite.
        
        The sprite will be added on top of ref sprite so ref_sprite is
        below of it.
        """
        RenderUpdates.add_internal(self, sprite)
        i = self._spritelist.index(ref_sprite)
        self._spritelist.insert(i, sprite)
        
        sprite.add_internal(self)
        
    def ref_render_order_change(self, ref_sprite, sprite, n):
        """ Move sprite n positions from ref_sprite.
        
        Negative n moves sprite on top of refsprite, positive n
        moves sprite below in render order. Note using n = 0 
        moves sprite on top of ref_sprite.
        
        """
        
        sprites = self._spritelist
        
        i = sprites.index(sprite)
        s = sprites.pop(i)
        ref = sprites.index(ref_sprite)

        sprites.insert(ref + n, s)
        

class ImageSprite(DirtySprite):
    """ Simple sprite that hold an image. """
    def __init__(self, img, x, y):
        DirtySprite.__init__(self)
        self.image = img
        self.rect = Rect(x, y, *img.get_rect()[2:])
        self.col_rect = self.rect


class TrySprite(DirtySprite):
    """ A sprite class with all the needed things for try-engine.

    TrySprite subclasses pygame.sprite.DirtySprite. It adds
    some mandatory attributes as col_rect and adds a few methods
    to control the render order.

    It also has a host-guest sprite thingy that makes sure the host sprite
    is updated before the guests sprites. You can attach sprites to sprites
    and it will look nice.

    TrySprites adds the rects: col_rect, i_rect, feet_rect
    dirty_rect, col_rect_left, col_rect_right

    TODO: This is probably outdated!
    The dirty attribute does NOT mean the same as in pygame. The
    meaning is:
     0 = The srpite has been drawn in this frame
     1 = hasn't been drawn in this frame yet
     2 = nothing at the moment

    """
    def __init__(self, img, x, y, col_rect):
        DirtySprite.__init__(self)
        self.image = img
        self.rect = Rect((x,y),self.image.get_rect()[2:])

        self.visible = 1
        self.dirty = 1

        # Directions in which this sprite collide
        self.col_direction = (True, True, True, True)
        
        # Has this sprite sprites attached to him? or the opposite
        # If this is used the guest sprite will be always updated
        # after the host sprite.
        self.guest = False
        self.guests = Group()
        self.host = None

        # Create all the needed rects:
        self.init_rects(self.rect, col_rect)
        
        # Init mask
        self.init_masks()
        
        # if True will print lots of debugging stuff
        self.debugging = False

    def init_rects(self, rect, col_rect):
        """ Create all the rects needed for the sprite
        
        Creates: collision rect, feet rect, interpolation rect, 
        dirty rect and collision mask.

        """
        # List holding all the rects, allow for fast iteration 
        # over all the rects
        self.rect_list = rl = []
        rl.append(self.rect)
        
        # Rect used for collisions
        self.col_rect = col_rect.copy().move(rect[:2])
        rl.append(self.col_rect)
        
        # Used to know where was the last interpolated position
        # TODO: do we use this????
        self.i_rect = rect.copy()
        rl.append(self.i_rect)
        
        # Rect to clear this sprite when drawing
        self.dirty_rect = rect.copy()
        rl.append(self.i_rect)

        # Create a rect representing the feet
        self.feet_rect = self.create_feet()
        rl.append(self.feet_rect)
        
        # Create left and right collision rects
        self.col_rect_left, self.col_rect_right = self.create_left_right()
        rl.append(self.col_rect_left)
        rl.append(self.col_rect_right)

    def create_feet(self):
        """ Creates a pygame Rect that will represent the feet. """
        
        cr = self.col_rect
        # One pixel height rect at the feet, overlapping the col_rect
        # PLEASE NOTE: Any additional rect used for collisions needs to
        # be contained by col_rect, if not bad things happens (colision
        # is detected by one rect but no the other and both are used in
        # orther to collide with all the platforms). That is way the
        # -1 is needed in cr.bottom.
        return Rect(cr.left, cr.bottom - 1, cr.width, 1)
        
        # TODO: This has a problem with col_rects the same size as the
        # normal rect

    def create_left_right(self):
        """ Creates two rects each one being a half of col_rect.
        
        These rects are used to detect which side of the sprites
        touches something.
        """
        
        cr = self.col_rect
        col_rect_left = Rect(cr.left, cr.top, cr.width /2 , cr.height)
        col_rect_right = Rect(cr.left + cr.width/2, cr.top,  cr.width /2, cr.height)
        
        return col_rect_left, col_rect_right

    def init_masks(self):
        """ Init the mask for the sprite. 

        NOTE: any additional rect created must be, in general, inside
        of col_rect. That way collisions will work properly
        
        """
        
        # Create a mask with the image
        # TODO, NOTE TO SELF: The mask will use the first frame
        # in the animation! ALWAYS
        self.mask = mask.from_surface(self.image)
        #~ self.view_mask()

        # Feet mask
        self.feet_mask = mask.Mask((self.rect.width, 1))
        h = self.rect.height
        s_at = self.feet_mask.set_at
        g_at = self.mask.get_at
        for x in xrange(self.rect.width):
            if g_at((x, h - 1)):
                s_at((x, 0), 1)

    #~ @property
    #~ def dirty(self):
        #~ return self._dirty
    #~ 
    #~ @dirty.setter
    #~ def dirty(self, value):
        #~ if self.dirty == 1:
            #~ old = self.dirty_rect
        #~ else:
            #~ old = self.rect
        #~ self.dirty_rect  = old.union(self.rect)
        #~ self._dirty = value

    def add_guest(self, sprite):
        """ Add a guest sprite to this sprite.
        
        The guest sprite will be updated after the host.
         """
         
        self.guests.add(sprite)
        sprite.guest = True
        sprite.host = self
    
    def remove_guest(self, sprite):
        """ Remove a guest sprite to this sprite. """
         
        self.guests.remove(sprite)
        sprite.guest = False
        sprite.host = None

    def add_host(self, sprite):
        """ Add a host for this sprite.
        
        This sprite will be updated after the host sprite.
        """
        self.host = sprite
        self.guest = True
        sprite.guests.add(self)
        
    def remove_host(self):
        """ Remove a host from this sprite. """
        self.host.guests.remove(self)
        self.host = None
        self.guest = False

    def one_layer_down(self):
        """ Moves the sprite one layer down in the render group. 
        
        This will make the sprite be seen below other sprites
        in the same group.

        """
        for g in self.groups():
            if isinstance(g, TryGroup):
                g.one_layer_down(self)

    def one_layer_up(self):
        """ Moves the sprites one layer up in the render group.
        
        This will make the sprite be seen over other sprites
        in the same group.
        
        """

        for g in self.groups():
            if isinstance(g, TryGroup):
                g.one_layer_up(self)

    def move_ontop(self, ref_sprite):
        """ Move this sprite just on top of ref_sprite in render order. """

        for g in self.groups():
            if isinstance(g, TryGroup):
                g.ref_render_order_change(ref_sprite, self, 0)

    def move_below(self, ref_sprite):
        """ Move this sprite just below of ref_sprite in render order. """

        for g in self.groups():
            if isinstance(g, TryGroup):
                g.ref_render_order_change(ref_sprite, self, 1)

    def properly_add_ontop(self, sprite):
        """ Add a new sprite on top of this one.
        
        sprite will be added to all the groups in which self is
        and when in render groups, it will be added on top of 
        self.

        """
        for g in self.groups():
            if isinstance(g, TryGroup):
                g.add_ontop(self, sprite)
            else:
                g.add(sprite)

    def properly_add_below(self, sprite):
        """ Add a new sprite below of this one.
        
        sprite will be added to all the groups in which self is
        and when in render groups, it will be added below of 
        self.

        """
        for g in self.groups():
            if isinstance(g,TryGroup):
                g.add_below(self, sprite)
            else:
                g.add(sprite)

    def change_sprite_pos(self, x, y):
        """ Changes the sprite position to x, y.

        Move all the needed rects to the new x, y position.

        """

        rect = self.rect
        dx, dy = x - rect.left, y - rect.top
        self.move_sprite(dx, dy)

    def move_sprite(self, delta_x, delta_y):
        """ Changes the sprite position by delta_x, delta_y.

        Move all the needed rects by delta_x, delta_y

        """

        rect = self.rect.copy()
        dirty_rect = self.dirty_rect

        # TODO: with movements mods this is probably outdated.
        # All movement is made at the same moment.
        # Note to self: This if-else is needed to clean old sprite
        # positions when two movements are done in the same frame, 
        # for example, teleporting/respawning
#         if self.dirty == 1:
#             old = dirty_rect
#         else:
#             old = rect
        old = rect

        # Move rects
        [r.move_ip(delta_x, delta_y) for r in self.rect_list]

        # Update dirty stuff
        self.dirty_rect = old.union(rect)
        self.dirty = 1

    def move_sprite_float(self, delta_x, delta_y):
        """ Move the sprite a float amount

        Uses the integer part to move the sprite and stores
        the float part in a variable.
        """

        self.fx += delta_x
        self.fy += delta_y

        self.fx, dx = modf(self.fx)
        self.fy, dy = modf(self.fy)

        # move rects
        self.move_sprite(dx, dy)

    def dprint(self,text):
        """ If debugging is True it will print debug text. """
        if self.debugging:
            print text

    def _view_mask(self):
        """ Prints the sprite mask to the terminal and exits

        For debugging purposes.
        """

        print self
        print "Printing mask and exiting."
        for y in xrange(self.mask.get_size()[1]):
            for x in xrange(self.mask.get_size()[0]):
                print self.mask.get_at((x,y)),
            print ""
        sys.exit(0)


class TryMovingSprite(TrySprite):
    """ A TrySprite with all the needed methods to move and collide. """
    def __init__(self, img, x, y, col_rect):
        # Init the parent
        TrySprite.__init__(self, img, x, y, col_rect)

        # Speed and float part of the movement
        self.vx = 0.
        self.vy = 0.
        self.fx = 0.
        self.fy = 0.

        # Is it moving right now?
        self.moving = False

        # TODO: this needs an overhaul
        # Other moving things
        self.jump_available = True
        self.falling = False
        self.jump = False
        self.jump_speed = -12
        self.touch_ground = False

        # Does this sprite decelerates in ground? bye default, yes
        self.decelerate_in_ground = True

        # deque storing all the position/speed modifiers
        # in order of addition. Use append to add one.
        self.movement_mods = deque()

        # What has the sprite moved in the last update:
        # Only takes into account the movement made in move_colliding()
        # This first variable is very sensitive. Increasing it or
        # decreasing it in improper way will make animations to stutter
        self._mean_size = 13
        self.moved_x = 0
        self.moved_y = 0
        self._last_frames_moved_x = deque((0,)*self._mean_size, self._mean_size)
        self._last_frames_moved_y = deque((0,)*self._mean_size, self._mean_size)

        # List of positions in the last frames
        self._amount_last_positions = 10
        self._last_positions = deque([(x,y),(x,y)], self._amount_last_positions)

        # Collision in the last frames.
        # Pygame works with rect, rects use ints, we use floats and we simulate
        # all the float stuff. Collision usually stutter. To make it feel nice
        # we store collision info in the last frames and return true when there
        # is at least one collision in the last choosen-number of frames.
        self._col_queue = 5
        self._last_col_left = deque((False,)*self._col_queue, self._col_queue)
        self._last_col_right = deque((False,)*self._col_queue, self._col_queue)
        self._last_col_up = deque((False,)*self._col_queue, self._col_queue)
        self._last_col_down = deque((False,)*self._col_queue, self._col_queue)

        # Used to store the las value returned by col_down, col_up, etc
        self._last_returned_col_left = False
        self._last_returned_col_right = False
        self._last_returned_col_up = False
        self._last_returned_col_down = False

        # True when the sprite has just collided in that direction, set in
        # move_colliding
        self.just_col_down = False
        self.just_col_up = False
        self.just_col_left = False
        self.just_col_right = False

        # if True will print lots of debugging stuff
        self.debugging = False

    @property
    def col_left(self):
        col = False
        for c in self._last_col_left:
            col = col or c
            if col:
                break

        return col

    @property
    def col_right(self):
        col = False
        for c in self._last_col_right:
            col = col or c
            if col:
                break
        return col

    @property
    def col_up(self):
        col = False
        for c in self._last_col_up:
            col = col or c
            if col:
                break
        return col

    @property
    def col_down(self):
        col = False
        for c in self._last_col_down:
            col = col or c
            if col:
                break
        return col

    @property
    def mean_moved_x(self):
        """ Return the mean of the movement in x axis in the last frames.

        See init to configure the number of frames the mean has.
         """
        return sum(self._last_frames_moved_x) / float(self._mean_size)

    @property
    def mean_moved_y(self):
        """ Return the mean of the movement in x axis in the last frames.

        See init to configure the number of frames the mean has.
         """
        return sum(self._last_frames_moved_y) / float(self._mean_size)

    def jump_internal(self):
        """ Basic jump function.

        Override this function if you want to add something nicer.
        """
        self.add_speed_y(self.jump_speed)

    def apply_movement_mods(self):
        """ Add or set the speed/position of the sprite.

        The idea is that any modification to speed/position is made
        during the self.update() and avoid any ghosts or bad cleanings
        in render.

        All the modifications are applied in proper order. This is the
        right method to use if you want to teleport, respawn, whatever
        your sprite.

        """

        # This seems to be overlay compicated, but it has one
        # purpose, to make all the changes in position and speed
        # at the same time
        queue = self.movement_mods

        try:
            while True:
                ty, mod = queue.popleft()
                if ty == SPEED_SET:
                    self.vx = mod[0]
                    self.vy = mod[1]
                elif ty == SPEED_ADD:
                    self.vx += mod[0]
                    self.vy += mod[1]
                elif ty == POSITION_SET:
                    self.change_sprite_pos(*mod)
                elif ty == POSITION_ADD:
                    self.move_sprite_float(*mod)
        except IndexError:
            pass

    def extend_rect(self, rect, dx, dy):
        """ Extend a rect by dx, dy. DESTRUCTIVE.

        If dx, dy are negative the rect will be extended in left
        and top directions.

        This method will modify the passed rect. Make suer to copy()
        if you want the original.

        """

        if dx > 0:
            rect.width = rect.width + dx
        else:
            dx = abs(dx)
            rect.width = rect.width + dx
            rect.x = rect.x - dx

        if dy > 0:
            rect.height = rect.height + dy
        else:
            dy = abs(dy)
            rect.height = rect.height + dy
            rect.y = rect.y - dy

        return rect

    def move_colliding(self, platforms):
        """ Move the sprite pixel by pixel and collides it.

        Pixel by pixel movement is used, so it's impossible to skip
        any rect or mask with at least one pixel size (or what it's the
        same, it will never go throuh walls no mather the size or the
        speed).

        The movement is made first in the horizontal axis and then in
        the vertical axis. This help sprites to hang in platforms.
        (Useful for platformers)

        The parameter PIXELS_TO_CLIMB tell how many pixels in vertical
        direction can go up in order to keep running (so it will go
        uphill)

        It uses the Platform.collision_detection() method to see if
        we are colliding.

        """

        PIXELS_TO_CLIMB = 2

        up_col = down_col = left_col = right_col = False
        amount_x = amount_y = 0

        # Add this positions to last_positions
        self._last_positions.append(tuple(self.rect[:2]))

        # TODO: if self.vx is always int why do we do xum both up and then make an int
        # is in any moment self.fx >1.0? Don't rememember all this!
        # Get platforms by inflating the col_rect
        total_vx, total_vy = modf(self.vx + self.fx), modf(self.vy + self.fy)
        inflated_rect =  self.extend_rect(self.col_rect.copy(), total_vx[1], total_vy[1])
        #~ print "Col_rect before and after:\n", self.col_rect, "\n", inflated_rect, "\n\n"
        platforms = platforms.hit(inflated_rect)

        # Move sprite horizontally
        if self.vx >= 0:
            move_now = lambda: self.move_sprite(1,0)
            undo_move = lambda: self.move_sprite(-1,0)
            direction = DIR_RIGHT 
        else:
            move_now = lambda: self.move_sprite(-1,0)
            undo_move = lambda: self.move_sprite(1,0)
            direction = DIR_LEFT

        x_iter = abs(int(total_vx[1]))
        if x_iter == 0:
            # We must call collision functions even if there is no
            # movement
            map_coll = [spr for spr in platforms if spr.collision_detection(self, direction)]

        for i in xrange(x_iter):
            #~ print "mov in x:", i, "self.vx", self.vx, "self.rect.left", self.rect.left
            move_now()
            for delta_y in xrange(1, PIXELS_TO_CLIMB):
                # Move the sprite up and check if there are not collisions.
                # TODO: does interfere this map_coll with the other (few lines
                # above) map_coll?
                map_coll = [spr for spr in platforms if spr.collision_detection(self, direction)]
                if not map_coll:
                    # The sprite has overcome an step
                    break
                else:
                    # Go up one pixel more and check again
                    self.move_sprite(0,-1)
            else:
                # There are collisions, there are no steps near. Undo movement
                self.move_sprite(0,  delta_y)
            if map_coll:
                #~ print inflated_rect
                #~ print "colisión en x"
                if direction == DIR_LEFT:
                    left_col = True
                elif direction == DIR_RIGHT:
                    right_col = True
                undo_move()
                self.vx = self.fx = 0
                break
            else:
                # Update amount of movement in x axis:
                amount_x += 1 if direction == DIR_RIGHT else -1
        else:
            # If no collision, sum up the float part of the speed
            self.fx = total_vx[0]

        # Move sprite vertically
        if self.vy >= 0:
            move_now = lambda: self.move_sprite(0, 1)
            undo_move = lambda: self.move_sprite(0, -1)
            direction = DIR_DOWN
        else:
            move_now = lambda: self.move_sprite(0, -1)
            undo_move = lambda: self.move_sprite(0, 1)
            direction = DIR_UP

        y_iter = abs(int(total_vy[1]))
        if y_iter == 0:
            # We must call collision functions even if there is no
            # movement
            map_coll = [spr for spr in platforms if spr.collision_detection(self, direction)]

        for i in xrange(y_iter):
            #~ print "mov in y:", i, "self.vy", self.vy, "self.rect.top", self.rect.top
            move_now()
            map_coll = [spr for spr in platforms if spr.collision_detection(self, direction)]
            if map_coll:
                undo_move()
                if direction == DIR_UP:
                    up_col = True
                elif direction == DIR_DOWN:
                    down_col = True
                self.vy = self.fy = 0
                break
            else:
                # Update amount of movement in x axis:
                amount_y += 1 if direction == DIR_DOWN else -1
        else:
            # If no collision, sum up the float part of the speed
            self.fy = total_vy[0]

        # Update movement variables
        self.moved_x, self.moved_y = amount_x, amount_y
        self._last_frames_moved_x.append(amount_x)
        self._last_frames_moved_y.append(amount_y)

        # Fill up collision values for last frame
        self._last_returned_col_down = self.col_down
        self._last_returned_col_up = self.col_up
        self._last_returned_col_left = self.col_left
        self._last_returned_col_right = self.col_right

        # Update current valuess
        self._last_col_down.append(down_col)
        self._last_col_up.append(up_col)
        self._last_col_left.append(left_col)
        self._last_col_right.append(right_col)

        # Update just collisioned values
        self.just_col_down = not self._last_returned_col_down and self.col_down
        self.just_col_up = not self._last_returned_col_up and self.col_up
        self.just_col_left = not self._last_returned_col_left and self.col_left
        self.just_col_right = not self._last_returned_col_right and self.col_right

        return up_col, down_col, left_col, right_col

    def friction(self):
        """ Apply friction to the sprite. """ 
        self.vx = self.vx * (1. - self.friction_factor)

    def apply_gravity(self, gravity = None):
        """ Increases the vertical speed of the sprite simulating the
            gravity. Also simulates the terminal velocity of a falling
            object """

        if self.has_gravity:
            if not gravity:
                gravity = self.gravity
            correction = self.vy*2*0.02 if self.vy > 0 else 0
            self.vy += gravity - correction

    def quadtree_check_future_collision(self, speed, platforms, col_rect = None):
        """ Checks wether the speed vector is going to give a collision
        in the next tick. Return a list of platform collided.
        
        Takes the speed vector and a group of sprites to check collisions
        with """

        if not col_rect:
            col_rect = self.col_rect

        # Remember, self.rect variables shouldn't be changed
        # of reference.
        # Hold a copy to the reference of the original col_rect
        old_reference_col_rect = self.col_rect
        
        self.col_rect = self.col_rect.move(speed[0], speed[1])

        # NOTE TO FUTURE SELF: .hit() and collision between rects don't
        # use the same algorithm, this make odd stuff some times. For 
        # example, in here .hit() returns some platforms but 
        # .spritecollideany() don't.
        
        # TODO: Maybe would be good idea to make quadtree work with 
        # pygame.Rect() ?
        map_coll = platforms.hit(self.col_rect)
        map_coll = spritecollideany(self, map_coll, collision_detection)

        # Restore the old reference
        self.col_rect = old_reference_col_rect

        return map_coll

    def gonna_bump(self, platforms, distance=None):
        """ Return True if the sprite is going to hit a wall with this speed.

        Uses quadtree platforms.

        """
        if not distance:
            distance = self.col_rect[2]

        if self.direction == LOOKING_LEFT:
            dirmult = -1
        elif self.direction == LOOKING_RIGHT:
            dirmult = 1

        if self.quadtree_check_future_collision(((distance*dirmult),0), platforms):
            return True
        else:
            return False

    def gonna_fall(self, platforms, distance=None):
        """ Return True if the sprite is going to fall with this speed.
        
        Uses quadtree platforms

        """
        if not(distance):
            distance = self.col_rect[2]

        if self.direction == LOOKING_LEFT:
            dirmult = -1
        elif self.direction == LOOKING_RIGHT:
            dirmult = 1

        if self.quadtree_check_future_collision(((distance+2)*dirmult,2), platforms):
            return False
        else:
            return True


class AnimatedSprite(TrySprite):
    """ A sprite with a list of animations, extends TrySprite.
    
    animations is a list of animations. """
    def __init__(self, animations, x, y, col_rect):
        self.animations = animations
        if isinstance(self.animations[ANIMATION_STOP][0], SpeedAnimationPlayer) or isinstance(self.animations[ANIMATION_STOP][0], SpeedUpdateAnimationPlayer):
            img = self.animations[ANIMATION_STOP][0].get_next_frame(0)
        else:
            img = self.animations[ANIMATION_STOP][0].get_next_frame()
        TrySprite.__init__(self, img, x, y, col_rect)


class Tile(DirtySprite):
    """ Sprite used bye all the tiles in the game. """
    def __init__(self, img, x, y, **kwargs):
        self.image = img
        DirtySprite.__init__(self)
        self.rect = Rect((x,y),self.image.get_rect()[2:])
        self.col_rect = self.rect

    def collision_detection(self, sprite, direction):
        """ Return True if the sprite collides with the platform.

        Override this function to make the platform collide.

         """

        raise NotImplemented

    def get_random_subsurface(self, sizex = 2, sizey = 2):
        """ Return a random subsection of the tile image. """
        size = self.image.get_size()
        rect = Rect(randint(0,size[0] - sizex),randint(0, size[1] - sizey), sizex ,sizey)
        return self.image.subsurface(rect)

    def update(self):
        raise NotImplemented
