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

"""
Renderer for tiled maps.

Can render maps with layers and opacity in the layers. You need to use this in
conjunction with the camera module and level module.
"""


from math import exp, ceil

from pygame import Surface, time, Rect, Color, event

from level import ImageLayer, ObjectLayer, TileLayer
from constants import *
from utils import copy_visible_rects_from_sprites, rects_from_sprites,\
                  col_rects_from_sprites
from camera import Camera, FreeCamera, ScrollCamera
import settings as s


class RendererError(Exception):
    """ Raised when... something goes wrong in this module """

    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)


class Renderer(object):
    """ General object for a renderer.

    Store and manage cameras and has a method to render rects.
    """

    def __init__(self, level, screen_size):

        self.tiledmap = level.tiledmap
        self.screen_size = screen_size

        self.tw = self.tiledmap.tilewidth
        self.th = self.tiledmap.tileheight
        self.map_size = level.map_size
        self.level = level

        # list of cameras
        self.current_camera = None
        self.current_camera_index = 0
        self.camera_list = []

        # fade in out things
        self.fade_opacity = 0
        self.fading = 0
        self.fade_start_time = None
        self.fade_color = BLACK
        self.generate_fade_image(self.display_size)
        self.fading_speed = 0.003
        self.FADE_IN = 1
        self.FADE_OUT = -1

    def add_camera(self, camera):
        """ Adds a camera to this renderer.

        You can change the used camera while in game using next_camera().

        """

        if isinstance(camera, Camera):
            # the size of the screen diplayed to the player in tiles
            camera.screen_size_in_tiles = self.screen_size_in_tiles
            # the tile size in pixels
            tw = self.level.tiledmap.tilewidth
            th = self.level.tiledmap.tileheight
            mw = self.level.tiledmap.width
            mh = self.level.tiledmap.height

            camera.tile_size = (tw, th)
            # size of the whole map in tiles
            camera.map_size_in_tiles = (mw, mh)

            # size of the map in 'screens'
            mt = camera.map_size_in_tiles
            st = self.screen_size_in_tiles
            camera.map_size_in_screens = (mt[0] / st[0], mt[1] / st[1])

            self.camera_list.append(camera)

            if not self.current_camera:
                self.current_camera = camera
                self.current_camera_index = 0

            x = camera.sprite.rect.x
            y = camera.sprite.rect.y
            ts = (tw, th)
            # TODO move all this inside each camera with _after_init or 
            # any similar name
            if isinstance(camera, ScrollCamera):
                st = self.screen_size_in_tiles
                
                # The player should be in a rect that is considered the center
                # of the camera
                x = camera.sprite.rect.x
                y = camera.sprite.rect.y
                
                camera.camera_rect = Rect(x, y, st[0] * ts[0], st[1] * ts[1])
                camera.outview_rect = camera.camera_rect.inflate(camera.margins[0] * -1, camera.margins[1] * -1)
                # used when recentering the player in the camera
                camera.inview_rect = camera.camera_rect.inflate( camera.s_rect_size[0] - st[0] * ts[0], camera.s_rect_size[1] - st[1] * ts[1])
            if isinstance(camera, FreeCamera):
                camera.camera_rect = Rect(x, y, st[0] * ts[0], st[1] * ts[1])
        else:
            raise RendererError("Error! \'{0}\' is not a camera object!".format(camera))

    def next_camera(self):
        """ Switch to the next camera in the list. """
        try:
            self.current_camera = self.camera_list[self.current_camera_index + 1]
            self.current_camera_index += 1

        except LookupError:
            self.current_camera = self.camera_list[0]
            self.current_camera_index = 0

    def draw_rects(self, surface, rects, offset, size=1, color=WHITE):
        """ Draw all the pygame rects in a iterable.

        Used to draw the collision rects for debugging.
        """

        for rect in rects:
            pygame.draw.rect(surface, color, rect.move(offset[0] * -1 , offset[1] * -1), size)

    def generate_fade_image(self, display_size):
        """ Generate the image used for fade in/out. """
        self.display_size = display_size
        self.fade_image = Surface(self.display_size)
        self.fade_image.fill(self.fade_color)
        self.fade_image.set_alpha(0)

    def update_fading(self):
        """ Does the math to update the fade in/out alpha value. """

        # functions to calculate the opacity of the fade image
        def fun1(time):
            time = time / 1000.
            return 1 - exp(time*( - self.fading_speed))
        def fun2(time):
            time = time / 1000.
            return exp(time*(- self.fading_speed))

        # in the first update there is no fade_start_time
        if not self.fade_start_time:
            self.fade_start_time = time.get_ticks()
        t = time.get_ticks() - self.fade_start_time

        if self.fading == self.FADE_IN:
            # make it zero when it's almost zero
            if self.fade_opacity > 0.003:
                self.fade_opacity = fun2(t)
            else:
                self.fading = 0
                self.fade_opacity = 0

        elif self.fading == self.FADE_OUT:
            # make it one when it's almost one
            if self.fade_opacity < 0.997:
                self.fade_opacity = fun1(t)
            else:
                self.fading = 0
                self.fade_opacity = 1
        
        # calculate the alpha value and set it in the fade_image
        a = ceil(255 * self.fade_opacity)
        if a > 255: a = 255
        self.fade_image.set_alpha(a)

    def fade(self, value, fade_speed=3):
        """ Execute fade in/out.

        Use the constants FADE_IN FADE_OUT to specificate the type of 
        fade, the speed with fade_speed (a positive non-zero float value).
        """

        self.fading_speed = fade_speed
        self.fading = value
        self.fade_start_time = time.get_ticks()

    def toggle_fade(self):
        if self.fade_opacity == 1:
            self.fade(self.FADE_IN, 4)
        elif self.fade_opacity == 0:
            self.fade(self.FADE_OUT, 4)

    def dprint(self,text):
        """ If self.debugging is True it will print all the debugging 
        lines. """
        if self.debugging:
            print text


class LayeredRenderer(Renderer):
    """ A renderer that uses all the layers in a tiled map. """
    def __init__(self, level, screen_size_in_tiles, display_size):

        # the next few variables are used to initialize the parent
        # the size of the screen in tiles
        self.screen_size_in_tiles = screen_size_in_tiles
        # small name for the big variable
        intiles = screen_size_in_tiles
        # this is the size of the surface holding what is 
        # visible right now in the screen
        screen_size = (intiles[0]*level.tiledmap.tilewidth,
                       intiles[1]*level.tiledmap.tileheight )
        self.screen_size = screen_size
        self.ratio = float(screen_size[0]) / float(screen_size[1])
        # Size of the pygame window, the screen being rendered
        # will be scaled to this size
        self.display_size = display_size

        # init the parent
        Renderer.__init__(self, level, screen_size)

        # the size of the whole map in pixels
        self.map_size_in_pixels = (self.tiledmap.width*self.tw,
                                   self.tiledmap.height*self.th)
        # Everything will be drawn in here, used to clear when dirty.
        self.map_background = Surface(self.map_size_in_pixels)
        # This will hold the whole map with sprites included.
        # From here we take the subsurface showed in screen.
        self.full_map = None

        # Keep aspect ratio?
        self.keep_aspect_ratio = True
        self.ratio_display_size = (1,1)
        self.temp_surface = Surface((1,1))
        self.ratio_dest = (0,0)
        self.new_size = self.display_size

        self.debug_images = False
        self.debugging = False

    def coords_from_screen_to_map(self, screen_coords):
        ratio_x = float(self.screen_size[0]) / float(self.display_size[0])
        ratio_y = float(self.screen_size[1]) / float(self.display_size[1])
        new_coord_x = screen_coords[0] * ratio_x + self.current_camera.screen_rect[0]
        new_coord_y = screen_coords[1] * ratio_y + self.current_camera.screen_rect[1]
        return new_coord_x,new_coord_y

    def coords_from_map_to_screen(self, coords):
        pass

    def render_map_background(self, surface=None):
        """ Render the whole static part of a map in the given surface.

        I a surface is not given uses self.map_background. Copy it to
        self.full_map if it doesn't exist.

        Only needs to be called once, after init. Can be used to
        clean sprites that haven't been cleaned properly.
        """
        if surface == None:
            surface = self.map_background

        for i in range(len(self.level.layers)):
            layer = self.level.layers[i]
            if layer.visible:
                if isinstance(layer, ImageLayer):
                    layer.draw(surface)
                elif isinstance(layer, TileLayer):
                    # TODO
                    # animated tiles need som special treatment too
                    layer.static.draw(surface)
                elif isinstance(layer, ObjectLayer):
                    pass

        if self.full_map == None:
            self.full_map = self.map_background.copy()

    def get_dirty_rects(self):
        """ Get all the rects that need to be repainted.
        DEPRECATED

        Because of alpha compositing this have to be called before 
        updating the mobs and after updating the mobs. 

        """

        union_add = self.union_add
        last_dirty_rects = self.last_dirty_rects
        layers = self.level.layers

        for i in range(len(layers)):
            layer = layers[i]
            if not layer.visible: continue
            
            # ImageLayer and TileLayer have no moving parts (yet)
            if isinstance(layer, ImageLayer):
                pass
            elif isinstance(layer, TileLayer):
                # animated tiles need som special treatment too TODO TODO
                pass
            elif isinstance(layer, ObjectLayer):
                some_rects = copy_visible_rects_from_sprites(layer)
                some_rects.extend(copy_visible_rects_from_sprites(layer.actionsprites.sprites()))
                #~ if debug_images:
                    #~ for spr in layer.sprites():
                        #~ if hasattr(spr, 'debug_image'):
                            #~ some_rects.append(spr.debug_image, spr.col_rect)

                # Add all the sprite and make sure there are no
                # overlapping rects

                for r in some_rects:
                    union_add(last_dirty_rects, r)

                # TODO ! this is debugging stuff and should be deleted
                # at the end
                #~ if self.check_overlapping(last_dirty_rects):
                    #~ print "*******************************************************************"
                    #~ print "*******There are overlapping dirty rects! this should not happen!**"
                    #~ print "*******************************************************************"

    def check_overlapping(self, rect_list):
        """ Return True if two or more rects overlap in a list of rects.

        This is not used at the moment, is a debugging stuff.

        """

        overlap = False
        for i in range(len(rect_list)):
            r = rect_list[i]
            for j in range(i+1, len(rect_list)):
                if r.colliderect(rect_list[j]):
                    overlap = True
                    break
            if overlap: break
    
        return overlap

    def union_add(self, rect_list, rect):
        """ Add rect to rect_list joining them if they overlap. """

        rect_col = rect.collidelistall
        rect_list_append = rect_list.append
        rect_list_pop = rect_list.pop
        rect_union = rect.union_ip

        indices = rect_col(rect_list)
        while indices:
            for index in reversed(indices):
                rect_union(rect_list_pop(index))
            indices = rect_col(rect_list)
        else:
            rect_list_append(rect)

    def interpolate_draw(self, surface = None, interpolate = 0.):
        """ Clear and draw the moving part of the map.

        First clear the surface using self.last_dirty_rects, then draw
        all these zones and all the sprites.

        """
        self.dprint("## In LayeredRederer.draw")

        if surface == None:
            surface = self.full_map

        # Speed-ups
        surface_blit = surface.blit
        draw_rects = self.draw_rects
        union_add = self.union_add
        debug_rects = s.debug_mode > 1
        surface_fill = surface.fill
        BACK_COLOR = Color(0,0,0,0)

        # Store debug rects by color
        violet_rects = []
        red_rects = []
        green_rects = []
        blue_rects = []

        # Clear all the dirty rects
        # We are using layers with opacity, steps to make this look nice:
        # - Clear all the dirty rects with the new and the old position of the
        #   sprites, these dirty rects are contained in every TrySprite and are
        #   updated when change_sprite_position and move_sprite are called.
        # - Draw all the layers in correct order.

        # First collect dirty rects
        dirty_rects = []
        tmp_dirty_rects = []

        for i in xrange(len(self.level.layers)):
            layer = self.level.layers[i]
            
            if isinstance(layer, ObjectLayer):
                for spr in layer.sprites():
                    try:
                        vx = spr.vx
                        vy = spr.vy
                    except AttributeError:
                        vx = vy = 0.
                    spr.i_rect = spr.rect.move(vx*interpolate, vy*interpolate)
                # TODO: need to get the interpolated rect, no the original one
                tmp_dirty_rects.extend([spr.i_rect.copy() for spr in layer.sprites()])
                # Next two also need to copy rectangles, if not bad things happen with 
                # not moving sprites
                tmp_dirty_rects.extend([i.copy() for i in layer.spritedict.values() if i != 0])
                tmp_dirty_rects.extend([i.copy() for i in layer.actionsprites.spritedict.values() if i != 0])
                #~ tmp_dirty_rects.extend([spr.dirty_rect for spr in layer.actionsprites.sprites() if spr.visible == 1])
                # don't forget killed sprites! (bad things happen if you forget them)
                tmp_dirty_rects.extend(layer.lostsprites)
                tmp_dirty_rects.extend(layer.actionsprites.lostsprites)
        # Because of opacity we can't have any overlapping rect, if that
        # would  happen layers with opacity will look wierd. Join using union
        # all the overlapping rects

        for r in tmp_dirty_rects:
            union_add(dirty_rects, r)

        # Clear them in the map
        for r in dirty_rects:
            surface_fill(BACK_COLOR, r)
            #~ pygame.draw.rect(surface, RED, r, 3)

        # Iterate layers and redraw dirty rects
        for i in xrange(len(self.level.layers)):
            layer = self.level.layers[i]
            if not layer.visible:
                continue
            self.dprint("\t layer.name = {0}; layer.visible = {1}".format(layer.name, layer.visible))

            if isinstance(layer, ImageLayer):
                spr = layer.sprites()[0]
                img = spr.image
                for r in dirty_rects:
                    #~ if img_rect.colliderect(r): # TODO: is this good or bad idea?
                    surface_blit(img, r, r)
                if debug_rects:
                    red_rects.extend(rects_from_sprites([spr]))

            elif isinstance(layer, TileLayer):
                # Animated tiles need som special treatment TODO TODO.
                img = layer.static_img
                for r in dirty_rects:
                    surface_blit(img, r, r)

            elif isinstance(layer, ObjectLayer):
                # All sprites are redrawn always
                #~ layer.actionsprites.simple_draw(surface)
                #~ layer.simple_draw(surface)
                layer.actionsprites.interpolate_draw(surface, interpolate)
                layer.interpolate_draw(surface, interpolate)

                if debug_rects:
                    violet_rects.extend(col_rects_from_sprites(layer.sprites()))
                    violet_rects.extend([spr.feet_rect for spr in layer.sprites()])
                    blue_rects.extend(rects_from_sprites(layer.actionsprites.sprites()))

        # draw on top all the debug rects collected
        if debug_rects:
            # First collect all the collision rects from the 
            # collision_group used by engine.
            red_rects.extend(col_rects_from_sprites(self.level.collision_group))
            offset = (0, 0)
            size = 1
            iterator = zip(
                (green_rects, blue_rects, red_rects, violet_rects),
                (GREEN, BLUE, RED, VIOLET))
            for rect_list, color in iterator:
                draw_rects(surface, rect_list, offset, size, color)
            draw_rects(surface, red_rects, offset, size, RED)

        # get the camera and the screen rect
        cm = self.current_camera
        #~ print cm.screen_rect
        self.current_screen = self.full_map.subsurface(cm.screen_rect)

        # Get events and update stuff
        self.get_events()

    def get_events(self):
        l = event.get(RENDERER)
        for e in l:
            if e.code == FADE:
                self.toggle_fade()
            elif e.code == NEXT_CAMERA:
                self.next_camera()
            elif e.code == CAMERA_LEFT:
                self.current_camera.accel_left()
            elif e.code == CAMERA_RIGHT:
                self.current_camera.accel_right()
            elif e.code == CAMERA_UP:
                self.current_camera.accel_up()
            elif e.code == CAMERA_DOWN:
                self.current_camera.accel_down()
            elif e.code == CAMERA_SHAKE:
                self.current_camera.shake(30, 5)
            else:
                print "WARNING: Unhandled event code in renderer: {0}".format(e)

    def blit_scaled_map(self, surface):
        """ Scale the subsurface representing the screen and return it.

        Note that this is the only method to obtain the render screen,
        you can if you want get the self.current_screen directly BUT it
        won't have any fading effects.
        """

        # Update the display size
        self.display_size = surface.get_size()

        if self.keep_aspect_ratio:
            size = surface.get_size()
            # If the display size has changed make calculations
            if self.ratio_display_size != size:
                self.ratio_display_size = size
                ratio = float(size[0]) / float(size[1])
                if ratio >= self.ratio:
                    self.new_size = (int(size[1] * self.ratio), size[1])
                    self.ratio_dest = ((size[0] - self.new_size[0]) / 2, 0)
                    self.temp_surface = Surface(self.new_size, pygame.HWSURFACE)
                elif ratio < self.ratio:
                    self.new_size = (size[0], int(size[0] / self.ratio))
                    self.ratio_dest = (0, (size[1] - self.new_size[1]) / 2)
                    self.temp_surface = Surface(self.new_size, pygame.HWSURFACE)

            # Scale the image and blit in the correct place
            # leaving balck bands if needed
            #~ print self.temp_surface.get_flags(), pygame.HWSURFACE
            pygame.transform.scale(self.current_screen, self.new_size, self.temp_surface)
            surface.blit(self.temp_surface, self.ratio_dest)
        else:
            # Just scale the camera to the display surface
            pygame.transform.scale(self.current_screen, surface.get_size(), surface)

        # If the display size has changed update the fading
        # image
        if self.display_size != surface.get_size():
            self.generate_fade_image(surface.get_size())

        # Do fading
        self.update_fading()
        if self.fade_image.get_alpha() != 0:
            surface.blit(self.fade_image, [0, 0])

    def toggle_collision_rects(self):
        if self.debug_images:
            self.debug_images = False
            self.full_map = self.map_background.copy()
        else:
            self.debug_images = True

    def redraw_background(self):
        self.full_map = self.map_background.copy()
