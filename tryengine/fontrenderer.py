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
'''
Created on 20/03/2014

@author: Alejandro Aguilera Martínez
@email: fenixin@gmail.com

Module to render fonts with different effects.

See FontRenderer for help.
'''

from itertools import product
from math import ceil

import pygame as pg
from pygame.font import Font
from pygame import Surface
from pygame.transform import laplacian

#TODO: Transparent things aren't handled properly! 
# Choosing the same color as the transparent color 
# used internally will do very ugly stuff


class FontRenderer(object):
    '''
    Object to render text of any size.

    Rendering text is made through layers. Layer are passed to
    render with a list. You can render as many layer as you want.
    Here it is an example with all the layer types:

    layers = [
            ('external_border',{'width':2, 'color':VIOLET}),
            ('shadows',{'positions_and_colors':[((2,-2),GREEN),((1,-1),RED)]}),
            ('normal',{'color':WHITE}),#
            ('internal_border', {'color':(GREEN)}),
            ('textured',{'image':image_texture})
             ]

    '''

    TRANSPARENT = (255, 0, 255)

    def __init__(self, font_file, antialias=False):
        '''
        Constructor
        '''
        
        if font_file:
            self.font_file = font_file
        else:
            self.font_file = pg.font.get_default_font()
        self._font_sizes = {}

        self.antialias = antialias

        # Parameters to create images
        self.DISPLAY_BITDEPTH = pg.display.get_surface().get_bitsize()  
        self.IMG_FLAGS = pg.HWSURFACE
        
    def _add_fontsize(self, filename, size):
        """ Add a font size renderer to _font_sizes. """
        
        self._font_sizes[size] = Font(filename, size)

    def __getitem__(self, size):
        """ Return the proper font size. """
        try:
            return self._font_sizes[size]
        except KeyError:
            self._add_fontsize(self.font_file, size)
            return self._font_sizes[size] 

    def _get_new_surface(self, text, pixel_size):
        """ Return a surface with the needed size for the text."""
        img = Surface(pixel_size, self.IMG_FLAGS)
        img.fill(self.TRANSPARENT)
        img.set_colorkey(self.TRANSPARENT)
        return img
    
    def size(self, text, size, layers = []):
        """ Return the image size in pixels. 
        
        This take into account all the layer given
        and calculate the correct image size.
        """

        x, y = self[size].size(text)
        for layer in layers:
            if layer[0] == 'shadows':
                mx = my = 0
                for t in layer[1]['positions_and_colors']:
                    mx = max(abs(t[0][0]), mx)
                    my = max(abs(t[0][1]), my)
                x += mx*2
                y += my*2

            elif layer[0] == 'external_border':
                width = layer[1]['width']
                x += width*2
                y += width*2
            
        return (x,y)
    
    def _render_internal(self, text, size, color, bg_color):
        """
        Wrapper
        """

        # For fastest blitting set hwsurface and the same
        # bit depth as the display surface.

        # Also for your
        # own sanity, remember that rendering fonts will give 
        # you a 8bit image and, sometimes, this will give 
        # unexpected results
        # when blittings in a 32bits surface

        img = self[size].render(text, self.antialias, color, bg_color)
        return img.convert(self.DISPLAY_BITDEPTH, self.IMG_FLAGS)

    def render(self, text, size, bg_color, bg_transparent, layers):
        """ Render text through the defined layers. """
        
        pixel_size = self.size(text, size, layers)
        wo_effects_ps = self[size].size(text)
        offset = ((pixel_size[0] - wo_effects_ps[0]) / 2, 
                  (pixel_size[1] - wo_effects_ps[1]) / 2)

        result = self._get_new_surface(text, pixel_size)
        result.fill(bg_color)
        if bg_transparent:
            result.set_colorkey(bg_color)

        # Create all the images and blit them together
        images = [getattr(self, '_' + fun)(text, size, pixel_size, offset, **args) for fun, args in layers]
        [result.blit(image, (0,0)) for image in images]
        
        return result

    def _fill_image(self, dest, filler, blendmode = 0):
        """ Fills dest surface with filler repeating if necesary. """
        ds = dest.get_size()
        fs = filler.get_size()
        for x in xrange(int(ceil(ds[0]/float(fs[0])))):
            for y in xrange(int(ceil(ds[1]/float(fs[1])))):
                dest.blit(filler, (x*fs[0],y*fs[1]), None, blendmode)
                print x,y


    """
    Layers
    """


    def _textured(self, text, size, pixel_size, offset, image = None):
        """ Render a textured font.
        
        Transparent colors in the texture will be ignored.
         """

        BG = (0,0,0)
        FG = (255,255,255)
        blendmode = pg.BLEND_MULT
        temp = self._get_new_surface(text, pixel_size)
        temp.fill(BG)
        temp.blit(self._render_internal(text, size, FG, BG), offset)
        self._fill_image(temp, image, blendmode)

        return temp

    def _normal(self, text, size, pixel_size, offset, color = None):
        """ Return a normal render of the text. """
        
        s = self._get_new_surface(text, pixel_size)

        img = self._render_internal(text, size, color, self.TRANSPARENT)
        img.set_colorkey(self.TRANSPARENT)
        s.blit(img, offset)
        return s

    def _shadows(self, text, size, pixel_size, offset, positions_and_colors):
        """ Add 'shadows' with different colors. """
        
        wo_effects_ps = self[size].size(text)
        offset = ((pixel_size[0] - wo_effects_ps[0]) / 2, 
                  (pixel_size[1] - wo_effects_ps[1]) / 2)
        f = self._render_internal
        s = self._get_new_surface(text, pixel_size)
        transparent = self.TRANSPARENT

        for pos,color in positions_and_colors:
            shadow = f(text, size, color, transparent)
            shadow.set_colorkey(transparent)
            n_pos = (pos[0]+offset[0], pos[1]+offset[1])
            s.blit(shadow, n_pos)
        return s

    def _external_border(self, text, size, pixel_size, offset, width = None, color = None):
        """ Add an external border (outside of the font). """
        
        wo_effects_ps = self[size].size(text)
        offset = ((pixel_size[0] - wo_effects_ps[0]) / 2, 
                  (pixel_size[1] - wo_effects_ps[1]) / 2)
        l = []
        for x, y in product(xrange(-width, width+1, 1),xrange(-width, width+1, 1)):
            l.append( ((x,y),color) )
        
        return self._shadows(text, size, pixel_size, offset, l)
    
    def _internal_border(self, text, size, pixel_size, offset, color = None):
        """ Add an internal border (inside of the font). """

        # Use very different colors to get a very sharp edge
        BG = (0,0,0)
        FG = (255,255,255)
        temp = self._get_new_surface(text, pixel_size)
        temp.fill(BG)
        temp.blit(self._render_internal(text, size, FG, BG), offset)
        
        temp = laplacian(temp)
        temp.set_colorkey(FG)

        result = self._get_new_surface(text, pixel_size)
        result.fill(color)
        result.blit(temp, (0,0))
        result.set_colorkey(BG)
        return result
