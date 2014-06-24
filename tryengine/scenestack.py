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

""" Module handling a stack of scenes.""" 


class SceneStack(object):
    """ Used to keep track of all the scenes: level, menu, etc. """

    def __init__(self):
        self.stack = []
        self.last_frame = None

    def push(self, scene):
        top = self.top()
        if top:
            top.pause()
            top.paused = True
        scene._add_internal(self)
        self.stack.append(scene)
        
        try:
            scene._after_init()
        except NotImplementedError:
            pass
    
    def top(self):
        return self.stack[-1] if self.stack else None
    
    def pop(self):
        scene = self.top()
        if scene:
            scene._remove_internal(self)
            self.stack.pop()
        new_top = self.top()
        if new_top:
            new_top.unpause()
            new_top.paused = False
        
        self.last_frame = scene.frame
        return scene

    
