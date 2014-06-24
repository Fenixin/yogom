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

from math import pi, atan2, hypot, ceil, cos
import sys
from os.path import split, join
from random import random, choice, randint

import pygame
import pygame.event as e
from pygame.locals import *

from tryengine.constants import *
from tryengine.playerinput import Input
from tryengine.utils import Timer, Borg, collision_detection, image_loader,\
    fast_tint
from tryengine.scene import SceneWithMusic, hor_justify_sprites, x_center_sprites, ver_justify_sprites, center_in_length
from tryengine.sprites import ImageSprite, TrySprite, TryGroup
from tryengine.level import Map
from tryengine.animation import Animation, UpdateAnimationPlayer
from scripts.particles import CoveringSprite, RotatingPaletteScoreText, \
    SimpleAnimatedParticle, RandImageParticle, AnimatedRandParticle
from scripts.textsprites import BlinkingTextSprite, MultiLineTextSprite, NewTextSprite, TextSprite

import settings as s
import scripts 
import tryengine.renderer as renderer
# Globals
glo = Borg()


def render_strings(strings, font_render, antialias, color, background=(0,0,0)):
    g = TryGroup()
    l = []
    
    for s in strings:
        spr = TextSprite(font_render, s, color, background, antialias)
        g.add(spr)
        l.append(spr)
    
    return g, l

def new_render_strings(strings, font_render, size, bg_color, bg_transparent, layers):
    l = []
    bg_transparent = True
    for s in strings:
        spr = NewTextSprite(font_render, s, size, bg_color, layers, bg_transparent)
        l.append(spr)
    g = TryGroup(l)
    return g, l



class SimpleScene(SceneWithMusic):
    """ Simple scene with inpunt handling. """
    def __init__(self, music = None):
        SceneWithMusic.__init__(self, music)
        self.pause_status = False
    
    def pause(self):
        self.pause_music()
        self.pause_status = True
    def unpause(self):
        self.unpause_music()
        self.pause_status = False
    def stop(self):
        self.stop_music()
    def clear_callback(self, surf, rect):
        color = 0, 0, 0
        surf.fill(color, rect)
    def handle_input(self, *args):
        if pygame.event.get(QUIT):
            glo.quitting = True
            self.finished = True
        l = pygame.event.get(KEYDOWN)
        for e in l:
            if e.key == K_ESCAPE or e.key == K_p:
                self.stack.push(PauseScene())
            elif e.key == K_q:
                glo.quitting = True
                self.finished = True
                glo.last_game_won = True
            elif e.key in (K_SPACE, K_RETURN) :
                self.finished = True
                glo.last_game_won = True
            elif e.key == K_F11 or (e.key == K_RETURN and \
                    (pygame.key.get_mods() & KMOD_ALT)):
                pygame.event.post(pygame.event.Event(ENGINE, code = TOGGLE_FULLSCREEN))
            elif e.key == K_F10:
                pygame.event.post(pygame.event.Event(ENGINE, code = CYCLE_DISPLAY_MODES))
            elif e.key == K_F12:
                pygame.event.post(pygame.event.Event(ENGINE, code = SCREENSHOT))


class TitleScene(SimpleScene):
    """ Title and credits. """
    def __init__(self):
        SimpleScene.__init__(self)
        
        # Music
        self.music = "data/music/Main Title.ogg"
        pygame.mixer.music.load(self.music)
        
        # Render to
        frame_size = s.actual_frame_size
        self.frame_surface = pygame.Surface(frame_size)
        self.frame_rect = self.frame_surface.get_rect()
        
        # Credits and title image and MW logo
        self.credits_image = pygame.Surface(frame_size)
        self.credits_image.fill(BLACK)
        self.title_image_filename = "data/images/cover_final.png"
        self.title_image_pos = (0,7)
        self.title_image = pygame.image.load(self.title_image_filename).convert()
        #self.title_image = pygame.transform.scale(self.title_image, frame_size)
        self.title_image_spr = TrySprite(self.title_image, 0, 0, self.title_image.get_rect())
        self.background = self.credits_image

        mw_logo = pygame.image.load("data/images/Logo_MW.png")
        mw_logo_spr = TrySprite(mw_logo, 0, 0, mw_logo.get_rect())
        
        # Credits
        credit_size = 10
        credit_strings = [
            "RUBER EAGLENEST: DESIGN, GRAPHICS",
            "AND ANIMATION",
            "PATRICIA AGUILERA: GRAPHICS, COVER",
            "AND COMICS",
            "FENIXIN: PROGRAMMING AND ENGINE",
            "THE MOONWALKERS: SOUND AND MUSIC",
            "EMULATOR AND TANDYSOFT FONTS",
            "BY NEALE DAVIDSON",
            "TITLE FONT BY YUJI OSHIMOTO",
            ]
        # Settings for strings
        layers = [('normal',{'color':WHITE})]
        bg_color = BLACK
        bg_transparent = True
        self.group, l = new_render_strings(credit_strings, glo.emulator_font, credit_size, bg_color, bg_transparent, layers)
        # Insert the moonwalkers logo
        mw_index = 4
        l.insert(mw_index, mw_logo_spr)
        self.group.add(mw_logo_spr)
        
        # Center them
        x_center_sprites(self.frame_rect, self.group, 0)
        ver_justify_sprites(self.frame_rect, l, 25, (0,-70))

        ###############
        # Title screen
        
        # Group holding all the texts and sprites
        self.splay_group = TryGroup()
        
        # Sprite with the fire animation
        spritesheet = image_loader("data/spritesheets/madrid.png")
        # Make a sprite

        updates_per_frame = 10
        self.fire = spritesheet.subsurface(pygame.Rect(8*16,144 + 16*2, 4*16, 16))
        self.fire_a = UpdateAnimationPlayer(Animation(self.fire, (16,16), False), updates_per_frame)
        fire_particle = {'x': 177,
                         'y': 103,
                         'animation': self.fire_a,
                         'gravity': 0.0}
        self.fire_s = SimpleAnimatedParticle(**fire_particle)
        self.splay_group.add(self.fire_s)
        
        # Hi score 
        hi_text = "HI: {0}".format(glo.hiscore)
        bg_color = BLACK
        bg_transparent = True
        hi_x = 120
        hi_y = 3
        size = 10
        self.hi_score = NewTextSprite(glo.emulator_font, hi_text, size, bg_color, layers, hi_x, hi_y, bg_transparent)
        
        # Options:
        layers = [('normal',{'color':GREY})]

        # Position in Y
        options_y_pos = 305
        size = 8
        self.key_dif_normal = "F8: NORMAL DIFFICULTY"
        self.key_dif_permafired = "F8: PERMAFIRED"
        bg_color = BLACK
        bg_transparent = True
        if glo.start_lives == s.NORMAL_DIFFICULTY_LIVES:
            dif_text = self.key_dif_normal
        else:
            dif_text = self.key_dif_permafired
        self.key_dif_spr = NewTextSprite(glo.tandysoft_font, dif_text, size, bg_color, layers, 0, 0, bg_transparent)
        self.key_zoom = "F10: ZOOM {0}"
        self.key_zoom_spr = NewTextSprite(glo.tandysoft_font, self.key_zoom.format("X" + str(s.scale)), size, bg_color, layers, 0, 0, bg_transparent)
        key_fs = "F11: FULLSCREEN"
        self.key_fs_spr = NewTextSprite(glo.tandysoft_font, key_fs, size, bg_color, layers, 0, 0, bg_transparent)

        options = [self.key_dif_spr, self.key_zoom_spr, self.key_fs_spr]

        # Press space to start
        layers = [('shadows',{'positions_and_colors':[((1,1),GREY)]}),
                ('normal',{'color':YELLOW}),
                ]
        size = 10
        key_space = "PRESS SPACE TO PLAY"
        bg_color = BLACK
        self.key_space_spr = BlinkingTextSprite(glo.emulator_font, key_space, size, bg_color,layers, 0, 0, 0.5)

        x_center_sprites(self.frame_rect, [self.key_space_spr], 0)
        options_spacer = 10
        hor_justify_sprites(self.frame_rect, options, options_spacer, (10, options_y_pos))
        ver_justify_sprites(self.frame_rect, [self.key_space_spr], 24, (0,75))
        
        self.splay_group.add(self.hi_score, options, self.key_space_spr)

        # Instructions:
        instr_y_pos = 220
        size = 10
        # Press space to start
        layers = [('normal',{'color':WHITE})]
        
        self.instr1 = "HELP MACARIO, THE PYROTECHNICIAN\nTO GET HIS JOB DONE. UNFORTUNATELY\nHE KEEPS LOSING HIS MATCHBOXES!"
        self.instr1_spr = MultiLineTextSprite(glo.emulator_font, self.instr1, size, bg_color, layers, x=0, y=instr_y_pos)
        self.instr1_spr.visible = 1
        self.instr2 = "CROUCH TO LIGHT THE FIREWORKS\nBEFORE THE MATCH EXTINGUISES AND\nMACARIO GETS WARNED BY HIS BOSS"
        self.instr2_spr = MultiLineTextSprite(glo.emulator_font, self.instr2, size, bg_color, layers, x=0, y=instr_y_pos)
        self.instr2_spr.visible = 0
        self.instr3 = "USE ARROWS TO RUN, JUMP AND CROUCH.\nMIND THE CRITTERS! IF YOU FALL,\nTHE MATCH WILL BURN OUT FASTER."
        self.instr3_spr = MultiLineTextSprite(glo.emulator_font, self.instr3, size, bg_color, layers, x=0, y=instr_y_pos)
        self.instr3_spr.visible = 0
        self.instructions = [self.instr1_spr,self.instr2_spr,self.instr3_spr]
        x_center_sprites(self.frame_rect, self.instructions, 0)
        self.instr_showing = 3
        self.instr_timer = None # seconds
        self.instr_updates_off = 30
        self.instr_update_counter = 0
        self.splay_group.add(self.instructions)

        # Copyright
        cr = "\xa9 2014 WINGLESS LITTLE PEOPLE"
        cr_y_pos = 270
        size = 10
        layers = [
                ('shadows',{'positions_and_colors':[((1,1),GREY)]}),
                ('normal',{'color':GREEN}),
                ]
        self.cr = NewTextSprite(glo.emulator_font, cr, size, bg_color, layers, 0, cr_y_pos)
        x_center_sprites(self.frame_rect, [self.cr], 0)
        self.splay_group.add(self.cr)

        ########################
        # Sync music and title
        self.start_time = pygame.time.get_ticks()
        self.background_time = 6.117
        self.time_viewing = 1000
        self.finished = False

        # Make credits show only once
        self.first_time = True
        self.background_timer = None

        # Things for fireworks after title music
        # Per explosion
        self.num_particles = 80
        self.spritesheet = image_loader("data/spritesheets/madrid.png")
        self.sparkle = self.spritesheet.subsurface(
                                pygame.Rect(0 + 13*15, 144 + 4*16, 6*16, 16))
        self.boom_timer = Timer(1)
        self.color_list = [WHITE, SKY, BLUE, GREEN, PURPLE, ORANGE, YELLOW, RED]
        self.rand_particle = {
                "animation": None,
                "life_time": 60,
                "max_speed": 4.8,
                "min_speed": 1.0,
                "direction": pi/2. + pi,
                "delta_ang": 2* pi,
                "gravity": 0.05,
                "fade_out_time": 25,
                "friction_factor": 0.03,
                }
        # Sounds
        boom1_sound = pygame.mixer.Sound("data/sounds/fuego artificial 02.ogg")
        boom2_sound = pygame.mixer.Sound("data/sounds/fuego artificial.ogg")
        self.boom_sounds = [boom1_sound, boom2_sound]

    @property
    def new_frame(self):
        self.group.clear(self.frame_surface, self.background)
        self.group.simple_draw(self.frame_surface)
        return self.frame_surface

    @property
    def frame(self):
        return self.frame_surface

    def update(self, *args):
        self.group.update(None, None, None)
        if self.first_time:
            self.background = self.credits_image
            pygame.mixer.music.play()
            self.first_time = False
            self.background_timer = Timer(self.background_time)

        if self.background_timer and self.background_timer.finished:
            self.group.empty()
            self.background.blit(self.title_image, self.title_image_pos)
            self.group.clear(self.frame_surface, self.frame_surface)
            self.background_timer = None
            self.frame_surface.blit(self.title_image, self.title_image_pos)
            self.group.add(self.splay_group)
            self.instr_timer = Timer(8)

        if self.instr_timer and self.instr_timer.finished:
            # Black them all
            for i in xrange(len(self.instructions)):
                    self.instructions[i].visible = 0
            self.instr_update_counter += 1
            if self.instr_update_counter % self.instr_updates_off == 0:
                self.instr_update_counter = 0
                self.instr_timer.reset()
                self.instr_showing = (self.instr_showing + 1) % len(self.instructions)
                for i in xrange(len(self.instructions)):
                    if i == self.instr_showing:
                        self.instructions[i].visible = 1
                    else:
                        self.instructions[i].visible = 0

        # Fireworks when the title music stops
        if not pygame.mixer.music.get_busy() and self.boom_timer.finished:
            # Reset the timer
            self.boom_timer = Timer(1 + random())
            # Create a new animation for the particle and tint it
            sparkles = fast_tint(choice(self.color_list), self.sparkle)
            sparkles_anim = Animation(sparkles, (16, 16), False)
            sparkles_anim_player = UpdateAnimationPlayer(sparkles_anim, 60)
            # Set the particle and create it
            x = randint(25, 150)
            y = randint(25, 109)
            self.rand_particle['animation'] = sparkles_anim_player
            self.rand_particle['x'] = x
            self.rand_particle['y'] = y

            for i in xrange(self.num_particles):
                b = AnimatedRandParticle(**self.rand_particle)
                self.group.add(b)

            # Sound
            choice(self.boom_sounds).play()


    def handle_input(self, *args):
        """ Please note, this must be similar to all the scenes
        input so it doesn't change what controls to use. """
        
        if pygame.event.get(QUIT):
            glo.quitting = True
            self.finished = True
        l = pygame.event.get(KEYDOWN)
        for e in l:
            if e.key == K_ESCAPE or e.key == K_p:
                self.stack.push(PauseScene())
            elif e.key == K_q:
                glo.quitting = True
                self.finished = True
            elif e.key == K_SPACE :
                self.finished = True
            elif e.key == K_F11 or (e.key == K_RETURN and \
                    (pygame.key.get_mods() & KMOD_ALT)): # Fullscreen
                pygame.event.post(pygame.event.Event(ENGINE, code = TOGGLE_FULLSCREEN))
                if not s.fullscreen:
                    self.key_zoom_spr.text = self.key_zoom.format("X3")
                else:
                    self.key_zoom_spr.text = self.key_zoom.format("X" + str(s.scale))
            elif e.key == K_F10: # Display modes
                pygame.event.post(pygame.event.Event(ENGINE, code = CYCLE_DISPLAY_MODES))
                scale = s.scale + 1 if s.scale < 3 else 1
                t = self.key_zoom.format("X" + str(scale))
                self.key_zoom_spr.text = t
            elif e.key == K_F8: # Change difficulty
                if self.key_dif_spr.text == self.key_dif_normal:
                    self.key_dif_spr.text = self.key_dif_permafired
                    glo.start_lives = s.PERMAFIRED_DIFFICULTY_LIVES
                    glo.lives = glo.start_lives
                    glo.difficulty = s.PERMAFIRED_DIFFICULTY
                else:
                    self.key_dif_spr.text = self.key_dif_normal
                    glo.start_lives = s.NORMAL_DIFFICULTY_LIVES
                    glo.lives = glo.start_lives
                    glo.difficulty = s.NORMAL_DIFFICULTY

            elif e.key == K_F12: # Screenshot
                pygame.event.post(pygame.event.Event(ENGINE, code = SCREENSHOT))

    def handle_events(self, *args):
        pass


class ComicScene(SimpleScene):
    """ Scene with comics between levels. """
    def __init__(self, filename, music = "data/music/Oh Dear Not Again!.ogg"):
        SimpleScene.__init__(self, music)

        #~ frame_size = s.actual_frame_size
        # Comics will use a bigger frame size! Just to make it readable
        frame_size = (s.actual_frame_size[0]*3, s.actual_frame_size[1]*3)
        self.frame_surface = pygame.Surface(frame_size)
        comic = image_loader(filename)

        ratio = comic.get_size()[0] / float(frame_size[0])
        comic = pygame.transform.scale(comic, (frame_size[0], int(comic.get_size()[1] / ratio)))
        x = 0
        y = center_in_length(comic.get_size()[1], frame_size[1])
        comic_spr = TrySprite(comic, x,y, comic.get_rect())

        self.group = TryGroup(comic_spr)
        
        tile_x = frame_size[0] /3
        tile_y = comic.get_size()[1]

        black_surface1 = pygame.Surface((tile_x,tile_y))
        black_surface2 = pygame.Surface((tile_x,tile_y))
        black_surface1.set_alpha(255)
        black_surface2.set_alpha(255)

        self.spr1 = spr1 = CoveringSprite(black_surface1, tile_x, y, black_surface1.get_rect())
        self.spr2 = spr2 = CoveringSprite(black_surface2, tile_x * 2, y, black_surface1.get_rect())
        self.group.add([spr1,spr2])
        
        self.start_time = pygame.time.get_ticks()
        self.t1 = 3
        self.t2 = 8
        
        self.finished = False

        self.first_update = True

    @property
    def new_frame(self):
        self.group.clear(self.frame_surface, self.clear_callback)
        self.group.simple_draw(self.frame_surface)
        return self.frame_surface

    @property
    def frame(self):
        return self.frame_surface

    def update(self, *args):
        self.group.update()
        if self.first_update:
            self.timer1 = Timer(self.t1)
            self.timer2 = Timer(self.t2)

            pygame.mixer.music.load("data/music/Oh Dear Not Again!.ogg")
            pygame.mixer.music.play()
            self.first_update = False
        if self.timer1.finished:
            self.spr1.smooth_kill = True
        if self.timer2.finished:
            self.spr2.smooth_kill = True
        if not self.paused and not pygame.mixer.music.get_busy():
            self.finished = True

    def handle_events(self, *args):
        pass

    def calculate_alpha(self, current_time, start_time, length):
        alpha = ((current_time - start_time) /length ) * 255
        alpha = int(alpha)
        return alpha if alpha >= 0 else 0


class TiledScene(SimpleScene):
    """ Scene holding the game itself. All is in a tiled map. """
    
    def __init__(self, map_to_load, music, mobs_modifiers = None, scorecounter = None):
        SimpleScene.__init__(self, music)

        self.frame_surface = pygame.Surface(s.actual_frame_size)
        
        self.finished = False

        # for mouse controller
        self.event_counter1 = 0
        self.event_counter2 = 0
        self.event1 = None
        self.event2 = None

        # Count the joysticks the computer has
        joystick_count=pygame.joystick.get_count()
        if joystick_count == 0:
            # No joysticks!
            #~ print ("Error, I didn't find any joysticks.")
            self.hat_x = self.hat_y = 0
            self.my_joystick = None
        else:
            # Use joystick #0 and initialize it
            #~ print "{0} joysticks found! NOTE joystick are \
                #~ disabled for the moment.".format(joystick_count)
            # Don't init the joystick yet... the error in pygame/pysdl
            # is annoying
            #~ self.my_joystick = pygame.joystick.Joystick(0)
            #~ self.my_joystick.init() 
            self.my_joystick = None
            self.hat_x = self.hat_y = 0

        # uncoment to hide mouse
        #~ pygame.mouse.set_visible(0)

        # init the keyboard input
        self.kb = Input(KMOD_LALT | KMOD_LCTRL)

        # which spawn should we put the player on?
        # filled up after loading a map
        self.location_to_spawn = None

        # this events can overflow the queue in some ocasions, after
        # using them they are cleared from the queue every frame
        # TODO: this should not happen 
        self.events_to_clear = [TRIGGER, PLAYER]

        # is the player running?
        self.cheat_running = False
        self.multiplier = 10
        
        # Load key binds
        from key_defs import key_definitios
        self.kb.bind_key_dict(key_definitios)

        # Init stuff
        self.load_map(map_to_load)
        self.init_renderer()

        # Add the spritesheet used to globals
        ss_dir = "data/spritesheets/"
        sp = glo.spritesheet = self.level.spritesheet
        filename =  split(sp)[-1]
        filename = join(ss_dir, filename)
        spritesheet = image_loader(filename)
        glo.spritesheet = spritesheet

        # add the player sprite in the correct spawn point
        if not self.location_to_spawn:
            p = self.level.player_spawns['inicial']
        else:
            p = self.level.player_spawns[self.location_to_spawn]
        self.player = p
        self.mobs.add(p)
        
        # this is not very convincing but works:
        # iterate through all the player representing spawn points
        # and 'kill' them so don't appear in any group
        for k in self.level.player_spawns.keys():
            if self.player == self.level.player_spawns[k]: continue
            else:
                self.level.player_spawns[k].kill()

        # add cameras
        if len(self.level.cameras) == 0:
            print "Warning!!! no cameras in this level! won't continue!"
            sys.exit(1)
        for c in self.level.cameras:
            # add the camera only if the sprite is alive
            # (is in a pygame.Group)
            #~ if c.sprite in self.mobs or c.sprite == self.player:
            self.renderer.add_camera(c)

        self.first_update = True

        # Collect all the fireworks in the same group
        self.fireworks = pygame.sprite.Group()
        for m in self.mobs:
            if isinstance(m,scripts.FireworkLauncher):
                self.fireworks.add(m)

        # To control the last seconds of the game when loosing or winning
        self.loosing_timer = Timer(3)
        self.loosing = False
        self.winning = False
        # This one is calculated on the fly depending on the number
        # of fireworks
        self.winning_bonus_timer = None
        self.winning_timer = None
        self.transfer_factor = 0.03
        self.transfer_sound = pygame.mixer.Sound("data/sounds/moneda.ogg")
        self.transfer_sound.set_volume(0.27)
        self.transfer_sound_counter = 0
        self.transfer_sound_updates_per_play = 5

        # Apply mobs modifiers by type
        if mobs_modifiers:
            for m in self.mobs.sprites():
                if type(m) in mobs_modifiers:
                    mods = mobs_modifiers[type(m)]
                    for key in mods:
                        m.__dict__[key] = mods[key]

        # Get the scorecounter if there's one and add it to the current
        # level
        if scorecounter:
            counters = Map(scorecounter)
            layer = counters.layers[0]
            self.level.get_info_object_layer(layer)
            # Last layer, last rendered (on top)
            self.level.layers.append(layer)
            self.mobs.add(layer.sprites())

        # Draw a first frame
        self.new_frame

        # Handle Perfect level, meaning, the player
        # got all the coins and get extra score.
        self.SCORE_PERFECT = 2500
        self.made_perfect = False
        self.made_perfect_delay = None
        self.made_perfect_delay_time = 2.1
        self.perfect_sound = pygame.mixer.Sound("data/sounds/perfect.ogg")
        # Extralife particle
        score_layers = [('shadows',{'positions_and_colors':[((1,1),GREY)]}),
                       ('normal', {'color':WHITE}),
                       ]
        amplitude_speed = 0.3
        self.perfect_particle = {
           'text': None,
           'text_layers': score_layers,
           'font_size': 12,
           'bg_color': BLACK,
           'bg_transparent': True,
           'gravity': 0.0,
           'life_time':200,
           'fade_out_time':10,
           'vx_function': lambda vx, age: amplitude_speed*cos(age/13.),
           'vy_function': lambda vy, age: -0.1,
           'x': None,
           'y': None,
           }
        
        # Extra life sound
        self.extralife_sound = pygame.mixer.Sound("data/sounds/extralife.ogg")
        # Extralife particle
        score_layers = [('shadows',{'positions_and_colors':[((1,1),GREY)]}),
                       ('normal', {'color':WHITE}),
                       ]
        self.extralife_particle = {
           'text': 'EXTRA LIFE',
           'text_layers': score_layers,
           'font_size': 12,
           'bg_color': BLACK,
           'bg_transparent': True,
           'gravity': 0.0,
           'life_time':200,
           'fade_out_time':10,
           'vx_function': lambda vx, age: amplitude_speed*cos(age/13.),
           'vy_function': lambda vy, age: -0.1,
           'x': 110,
           'y': 100,
           
           }


    def toggle_cheats(self):
        """ Supersize player jump and speed. """

        if not self.cheat_running:
            self.cheat_running = True
            self.player.base_max_speed  = self.player.base_max_speed * self.multiplier
            self.player.jump_speed = self.player.jump_speed * self.multiplier / 5.
        else:
            self.cheat_running = False
            self.player.base_max_speed = self.player.base_max_speed / self.multiplier
            self.player.jump_speed = self.player.jump_speed / self.multiplier * 5.

    def init_renderer(self):
        """ Init the renderer. """
        # needed info
        self.screen_size_in_tiles = s.screen_size_in_tiles
        self.tile_size = ((s.tile_width, s.tile_height))
        
        # init the renderer
        self.renderer = renderer.LayeredRenderer(self.level, self.screen_size_in_tiles, pygame.display.get_surface().get_size())

        # render the static part of the map
        self.renderer.render_map_background()

    def load_map(self, map_to_load):
        """ Take path to map and fill up variables. """
        # loading the map
        try:
            self.level = level = Map(map_to_load)
        except Exception, e:
            
            print "{:=^60}".format("")
            print "{:*^60}".format(" Something went wrong loading the solicited map! ")
            print "{:=^60}".format("")
            print
            print "Error: ", str(e)
            print e.__dict__
            raise

        # the player will be put in place later
        self.player = None
        
        # get references from the level sprite groups
        self.mobs = TryGroup(self.level.mobs)
        self.hostiles = level.hostiles
        self.killables = TryGroup([spr for spr in self.mobs.sprites() if spr.killable])
        self.actions = level.actionsprites
        self.collisions_group = level.collision_group

    def handle_events(self):
        """ Handle all the events in the queue.
        
        Retrieve them from the queue and do the needed actions in the
        main game loop.
        
        """
        
        pass
        
    def reload_map(self):
        """ This probably should be called restart level.
        
        It reset coin status and places every mob in spawn position.
        """
        # Fake reload map...
        for spr in self.mobs.sprites():
            if hasattr(spr, 'respawn'):
                spr.respawn()
        self.loosing = False
        glo.lives -= 1
        pygame.mixer.music.stop()
        pygame.mixer.music.play()
        

    def handle_input(self):
        """ Update keyboard status, call needed functions. """

        # Speed ups
        kb = self.kb
        kb_is_pressed = kb.kb_is_pressed
        kb_delayed_is_pressed = kb.kb_delayed_is_pressed
        player = self.player
        
        # Event processing.
        # We use our personal keyboard handler, see playerinput.py
        kb.update()
        
        if s.CHEATS:
            # Ignite all the fireworks
            if kb_is_pressed(K_i):
                for spr in self.mobs.sprites():
                    if isinstance(spr, scripts.FireworkLauncher):
                        spr.lit = True
            # Kill de player, for debugging:
            if kb_delayed_is_pressed(K_k):
                player.lit = 1.0
        
            # Cheat, increase/decrease score by 1000
            if kb_delayed_is_pressed(K_MINUS, .05):
                glo.score -= 1000
            elif kb_delayed_is_pressed(K_PLUS, .05):
                glo.score += 1000
            
            # Get all coins!
            if kb_delayed_is_pressed(K_u, 1.0):
                [mob.taken() for mob in self.mobs.sprites() if (isinstance(mob,scripts.Coin) and mob.visible )]
        
        if s.TOUCH_CONTROL:
            # Experiment on mouse and touchpad controller.
            
            # Movement
            
            if kb.ms_is_dragging(1):
                x,y = self.renderer.coords_from_screen_to_map(kb.mouse_pos)
                vector = (x - player.rect.center[0] , player.rect.center[1] - y )
                radius = hypot(*vector)
                try:
                    angle = atan2(vector[1],vector[0])
                except ZeroDivisionError:
                    angle = pi / 2 if vector[1] > 0 else 3 * pi/2
                #~ print "angulo: " , angle
                #~ print "radio: " , radius
                dangle =  angle * (180.0 /pi)
                #~ print dangle
                if dangle <= 70 and dangle > -45 and radius > 10:
                    pygame.event.post(e.Event(PLAYER, code = RIGHT))
                elif ((dangle > 110 and dangle <= 180) or (dangle <= -135 and dangle > -180)) and radius > 10:
                    pygame.event.post(e.Event(PLAYER, code = LEFT))
                elif dangle <= -45 and dangle > -90 and radius > 10:
                    player.direction = DIR_RIGHT
                    pygame.event.post(e.Event(PLAYER, code = USE))
                elif dangle <= -90 and dangle > -134 and radius > 10:
                    player.direction = DIR_LEFT
                    pygame.event.post(e.Event(PLAYER, code = USE))
            
            # Jumping
                    
            if kb.ms_has_clicked(1):
                x,y = self.renderer.coords_from_screen_to_map(kb.mouse_pos)
                vector = (x - player.rect.center[0] , player.rect.center[1] - y )
                try:
                    angle = atan2(vector[1],vector[0])
                except ZeroDivisionError:
                    angle = pi / 2 if vector[1] > 0 else 3 * pi/2
                #~ print angle
                dangle =  angle * (180.0 /pi)
                #~ print dangle
                if (dangle > 85 and dangle <= 90): # tall jump right
                    self.event1 = e.Event(PLAYER, code = JUMP)
                    self.event2 = e.Event(PLAYER, code = RIGHT)
                    self.event_counter1 = 6
                    self.event_counter2 = 1
                elif (dangle > 90 and dangle <= 95): # tall jump left
                    self.event1 = e.Event(PLAYER, code = JUMP)
                    self.event2 = e.Event(PLAYER, code = LEFT)
                    self.event_counter1 = 6
                    self.event_counter2 = 1
                elif (dangle > 25 and dangle <= 85): # wide jump right
                    self.event1 = e.Event(PLAYER, code = JUMP)
                    self.event2 = e.Event(PLAYER, code = RIGHT)
                    self.event_counter1 = 5
                    self.event_counter2 = 20
                    #~ self.player.movement_mods.append((SPEED_ADD,(self.player.max_speed,self.player.jump_speed * 5)))
                elif (dangle > 0 and dangle <= 25) or (dangle <= 0 and dangle > -25): # small jump right
                    self.event1 = e.Event(PLAYER, code = JUMP)
                    self.event2 = e.Event(PLAYER, code = RIGHT)
                    self.event_counter1 = 3
                    self.event_counter2 = 15
                    #~ self.player.movement_mods.append((SPEED_ADD,(self.player.max_speed,self.player.jump_speed * 5)))
                elif (dangle > 95 and dangle <= 155): # wide jump left
                    self.event1 = e.Event(PLAYER, code = JUMP)
                    self.event2 = e.Event(PLAYER, code = LEFT)
                    self.event_counter1 = 5
                    self.event_counter2 = 20
                    #~ self.player.movement_mods.append((SPEED_ADD,(self.player.max_speed*-1,self.player.jump_speed * 5)))
                elif (dangle > 155 and dangle <= 180) or (dangle <= -135 and dangle > -180): # small jump left
                    self.event1 = e.Event(PLAYER, code = JUMP)
                    self.event2 = e.Event(PLAYER, code = LEFT)
                    self.event_counter1 = 3
                    self.event_counter2 = 15
                    #~ self.player.movement_mods.append((SPEED_ADD,(self.player.max_speed*-1,self.player.jump_speed * 5)))
            
            # Correctly handle jumping:
            if self.event_counter1 and self.event1:
                pygame.event.post(self.event1)
                self.event_counter1 -= 1
            else:
                self.event1 = None
            if self.event_counter2 and self.event2:
                pygame.event.post(self.event2)
                self.event_counter2 -= 1
            else:
                self.event2 = None

        kb.run_bindings()

        if kb_is_pressed(K_q) or \
            kb.quitting:
            glo.quitting = True
            self.finished = True
        
        if kb_is_pressed(K_ESCAPE) or kb_is_pressed(K_p):
            self.stack.push(PauseScene())

    def update(self):
        if self.first_update:
            pygame.mixer.music.load(self.music)
            pygame.mixer.music.play(0)
            self.first_update = False

        # Check if all the fireworks are lit
        if self.all_fireworks_lit:
            pygame.mixer.music.fadeout(500)
            min_ticks_per_boom = 45
            max_ticks_per_boom = 60
            ticks = 0
            if not self.player.winning:
                # Ignite all the fireworks
                for spr in self.mobs.sprites():
                    if isinstance(spr, scripts.Firework):
                        rnd = min_ticks_per_boom + int((max_ticks_per_boom - min_ticks_per_boom)*random()) + (spr.rect[1]/16)
                        spr.lit = ticks + rnd
                        
                        ticks += rnd
            self.player.winning = True
            if not self.winning:
                self.winning = True
                # Every tick is 1/60th of a second + 3 seconds to let
                # all the fireworks end
                self.winning_timer = Timer( 1./60. * ticks + 3)
            if self.winning_timer.finished and not self.winning_bonus_timer:
                # Transfer bonus points to score
                if glo.bonus >= 1:
                    transfer = int(ceil(glo.bonus * self.transfer_factor))
                    glo.bonus -= transfer
                    glo.score += transfer
                    
                    self.transfer_sound_counter += 1
                    if self.transfer_sound_counter % self.transfer_sound_updates_per_play == 0:
                        self.transfer_sound.play()
                else:
                    glo.bonus = 0
                    self.winning_bonus_timer = Timer(2)
            if self.winning_bonus_timer and self.winning_bonus_timer.finished:
                glo.last_game_won = True
                self.finished = True

        # Check if the match has burnt out
        if self.player.lit < 0.0:
            pygame.mixer.music.fadeout(500)
            if not self.loosing:
                self.loosing = True
                self.loosing_timer.reset()
            if self.loosing_timer.finished:
                
                if glo.lives > 0:
                    self.reload_map()
                else:
                    self.finished = True

            glo.last_game_won = False

        # make local variables, slightly faster code
        # for very repetitive code
        player = self.player
        mobs = self.mobs
        hostiles = self.hostiles
        actions = self.actions
        col = self.level.collision_tree
        spritecollide = pygame.sprite.spritecollide
        new_sprites_group= None
        
        mobs.update(self.level.collision_tree, None, self.player)

        # ActionSprite stuff
        # NOTE: the collision with action sprites should be before the update()
        # at the end we have to clear all the TRIGGER events from the queue 
        # to make all work as expected!
        #
        # ALSO: We can't have two or more TRIGGERS triggering stuff at the 
        # at the same time! Limitation of this method
        #
        # see if the player touches any action tiles
        
        # TODO: make actionspries be triggered by any mob. Look how
        # sprite.groupcollide works and implement one with col_rect.
        # Example: spritecollide(mobs, actions)
        actions_to_do = pygame.sprite.spritecollide(player, actions, False, collision_detection)
        for action in actions_to_do:
            action.do()
        # action sprites update!
        actions.update(player, col)
        # clear the event queue from TRIGGER events
        pygame.event.clear(self.events_to_clear)

        # Check for extra lives
        def get_extra_life():
            player.properly_add_below(RotatingPaletteScoreText(**self.extralife_particle))
            glo.lives += 1
            glo.extra_lives -= 1
            self.extralife_sound.play()

        if not glo.difficulty == s.PERMAFIRED_DIFFICULTY:
            if glo.score >= 20000 and glo.extra_lives == 2:
                get_extra_life()
            elif glo.score >= 50000 and glo.extra_lives == 1:
                get_extra_life()
            elif glo.score >= 100000 and\
                 -1 * (glo.score // 100000) + 1 == glo.extra_lives:
                get_extra_life()

        # Check for perfect level
        if self.all_coins_taken and not self.made_perfect:
            self.made_perfect = True
            glo.score += self.SCORE_PERFECT
            self.perfect_position = (player.rect[0] - 15, player.rect[1])
            ppd = self.perfect_particle
            ppd['x'] = player.rect[0] -15
            ppd['y'] = player.rect[1]
            ppd['text'] = 'PERFECT'

            player.properly_add_below(RotatingPaletteScoreText(**ppd))
            self.made_perfect_delay = Timer(self.made_perfect_delay_time)
            self.perfect_sound.play()

        if self.made_perfect_delay and self.made_perfect_delay.finished:
            self.made_perfect_delay = None
            ppd = self.perfect_particle
            ppd['x']=self.perfect_position[0]
            ppd['y']=self.perfect_position[1]
            ppd['text']='  +2500'
            player.properly_add_below(RotatingPaletteScoreText(**ppd))

        # TODO: This is a workaround for a bug in pygame with windows!!
        # Loop the music
        # This is workaround. Pygame makes some strange noises (cracking) when
        # using the default looping with pygame.mixer.music.play(-1). Looping it manually
        # fixes the problem
        if not pygame.mixer.music.get_busy() and not self.winning and not self.loosing and not self.pause_status:
            pygame.mixer.music.stop()
            pygame.mixer.music.play()

    @property
    def all_coins_taken(self):
        # List with all the visible coins
        l = [mob for mob in self.mobs.sprites() if (isinstance(mob,scripts.Coin) and mob.visible )]
        # If there are no visible coins all are taken
        return not bool(l)

    @property
    def all_fireworks_lit(self):
        l = [mob for mob in self.mobs.sprites() if (isinstance(mob,scripts.FireworkLauncher) and not mob.lit )]
        return not bool(l)

    def count_mob(self, mob_class):
        c = 0
        for f in self.fireworks.sprites():
            if isinstance(f,mob_class):
                c += 1 
        return c

    @property
    def new_frame(self, interpolate = 0.0):
        self.renderer.interpolate_draw()
        return self.renderer.current_screen

    @property
    def frame(self, interpolate = 0.0):
        return self.renderer.current_screen


class TransitionScene(SimpleScene):
    """ Make a beautiful transition from second-to-top to top scene."""
    
    def __init__(self, transition_type = 0):
        SimpleScene.__init__(self)
        
        frame_size = s.actual_frame_size
        self.frame_surface = pygame.Surface(frame_size)
        
        self.from_frame = None
        self.to_frame = None
        
        self.group = TryGroup()
        
        self.vy = 16
        self.finished = False

    def update(self, *args):
        if not self.from_frame:
            frame_size = s.actual_frame_size
            #~ print frame_size
            self.from_frame = self.stack.last_frame
            self.to_frame = self.stack.stack[-2].new_frame
            
            self.spr_from = spr_from = ImageSprite(self.from_frame, 0, 0)
            self.spr_to =  spr_to = ImageSprite(self.to_frame, 0, - frame_size[1])
            #~ print self.spr_to.rect
            
            self.group = TryGroup(spr_from, spr_to)
        for spr in self.group:
            spr.rect.move_ip(0,self.vy)
        
        #~ print self.spr_to.rect.y
        #~ print self.spr_from.rect.y
        if self.spr_to.rect.y >= 0:
            self.finished = True
            self.stack.pop()
            

    @property
    def new_frame(self):
        self.group.clear(self.frame_surface, self.clear_callback)
        self.group.simple_draw(self.frame_surface)
            
        return self.frame_surface

    @property
    def frame(self):
        return self.frame_surface

    def handle_input(self, *args):
        if pygame.event.get(QUIT):
            glo.quitting = True
            self.finished = True
            pygame.event.post(pygame.event.Event(ENGINE, code = QUIT))

    def handle_events(self, *args):
        if pygame.event.get(KEYDOWN):
            self.finished = True
            glo.last_game_won = True


class TextScene(SimpleScene):
    """ Scenes consisting only in text. """

    def __init__(self, strings, duration, spacer=25):
        SimpleScene.__init__(self)
        
        frame_size = s.actual_frame_size
        self.frame_surface = pygame.Surface(frame_size)
        self.frame_rect = self.frame_surface.get_rect()
        
        self.group = TryGroup()
        size = 10
        layers = [
#                 ('external_border',{'width':2, 'color':VIOLET}),
                ('shadows',{'positions_and_colors':[((1,1),GREY)]}),
                ('normal',{'color':WHITE}),#
#                 ('internal_border', {'color':(GREEN)}),
                  ]
        bg_color = BLACK
        bg_transparent = True
        self.group, l = new_render_strings(strings, glo.emulator_font, size, bg_color, bg_transparent, layers)
        x_center_sprites(self.frame_rect, l, 0)
        ver_justify_sprites(self.frame_rect, l, 25, (0,0))
        
        self.start_time = pygame.time.get_ticks()
        self.time_viewing = duration
        self.finished = False

        self.first_time = True
        
        self.music_pos = 0

    def update(self, *args):
        if self.first_time:
            self.timer = Timer(self.time_viewing)
            self.first_time = False
        if self.timer.finished or self.finished or glo.quitting:
            self.stack.pop()

    @property
    def new_frame(self):
        self.group.clear(self.frame_surface, self.clear_callback)
        self.group.simple_draw(self.frame_surface)
        return self.frame_surface

    @property
    def frame(self):
        return self.frame_surface

    def stop(self):
        """ Stop needed things before removing this scene.

        At the moment only music is stopped. 

        """

        pass

    def handle_events(self, *args):
        pass

    def calculate_alpha(self, current_time, start_time, length):
        alpha = ((current_time - start_time) /length ) * 255
        alpha = int(alpha)
        return alpha if alpha >= 0 else 0


class PauseScene(TextScene):
    def __init__(self, text = "PAUSE"):
        text_lines = ["PAUSE", " ", "PRESS <ESC> TO RESUME", "PRESS <R> TO RESTART", "PRESS <Q> TO QUIT"]
        TextScene.__init__(self, text_lines, -1)
        
    def update(self, *args):
        self.group.update()

    def _after_init(self):
        self.background = self.stack.stack[-2].frame.copy()
        tmp = pygame.Surface(self.background.get_size())
        tmp.fill(BLACK)
        tmp.set_alpha(128)
        self.background.blit(tmp, (0,0))
        self.frame_surface.blit(self.background, (0,0))

    @property
    def new_frame(self):
        self.group.clear(self.frame_surface, self.background)
        self.group.simple_draw(self.frame_surface)
        return self.frame_surface

    def handle_input(self, *args):
        if pygame.event.get(QUIT):
            glo.quitting = True
            self.finished = True
        l = pygame.event.get(KEYDOWN)
        for e in l:
            if e.key == K_ESCAPE or e.key == K_p:
                self.finished = True
            elif e.key == K_q:
                self.finished = True
                glo.quitting = True
            elif e.key == K_r:
                self.finished = True
                glo.last_game_won = False
                glo.lives = 0
                for s in self.stack.stack:
                    s.finished = True
            elif e.key == K_F12:
                pygame.event.post(pygame.event.Event(ENGINE, code = SCREENSHOT))
                
