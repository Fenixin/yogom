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
""" This module provides with a simple generic automata."""

# TODO: Move debugging to logging, move ticks to updates

from random import random

import pygame


class Automata(object):
    """ Simple class to create a simple automata to automatize mobs.

    You have to provide the number of states, the probability matrixes of every
    state and the state in which we start.
    """

    def __init__(self, num_states, states_prob_matrixes, start_state=0):
        self.num_states = num_states
        # List of prob matrixes
        self.states_prob_matrixes = states_prob_matrixes

        # functions to run in the given state
        # TODO move this to mobs.py?
        #~ self.states_function = states_funcion

        # calculate the acumulated matrix
        self.acum_matrixes = []
        for matrix in self.states_prob_matrixes:
            self.acum_matrixes.append(self._get_acum_matrix(matrix))

        #the matrix contains tuples with prob to the next state, current
        # matrix in use
        self.current_matrix = self.acum_matrixes[0]

        # current state things
        self.current_state = start_state
        self.last_time = pygame.time.get_ticks()
        # stores the state before the last change
        self.last_state = start_state

        # debugging
        self.debugging = False

    def change_matrix(self, index):
        self.dprint("\n### Automata.change_matrix to inedx: {0}".format(index))
        self.current_matrix = self.acum_matrixes[index]

    def dprint(self, text):
        if self.debugging:
            print text

    def next_state(self):
        self.dprint("\n### Automata.next_state")
        cs = self.current_state
        r = random()
        state_transitions = self.current_matrix[cs]
        self.dprint("\t r = {0}, state_transitions = {1}".format(r, state_transitions))
        for prob, state in zip(state_transitions, range(self.num_states)):
            self.dprint("\t\t changing")
            if r <= prob:
                self.dprint("\t\t\t new_state = {0}".format(state))
                self.last_state = self.current_state
                self.current_state = state
                break

    def set_state(self, state):
        """ Sets the current state and skip the timer. """
        self.last_state = self.current_state
        self.current_state = state
        self.reset_timer()

    def get_state(self):
        return self.current_state
            
    def get_last_state(self):
        """ Returns an integer representing the state before this one. """
        return self.last_state

    def _get_acum_matrix(self, matrix):
        """ Calculates an acumulate probability matrix, where each
        row value is the sum of all its predecesors. """
        ns = self.num_states
        new_matrix = [ [] for i in range(self.num_states)]
        for i in range(ns):
            acum = 0.
            for j in range(ns):
                acum += matrix[i][j]
                new_matrix[i].append( acum)
        return new_matrix


class TimedAutomata(Automata):
    """ Class that provides an automata with a minimum time in every state.

    Needs an additional parameter, min_time_state that is the minimum time to
    in the state.
    """
    def __init__(self, num_states, min_time_state, states_prob_matrixes, start_state = 0):
        Automata.__init__(self, num_states, states_prob_matrixes, start_state)
        # contains a list of times with the minimun time to spend in a state
        self.min_states_time = min_time_state

        # current state things
        self.last_time = pygame.time.get_ticks()

        # have we to skip the next timer?
        self.skip_timer = False

    def skip_next_timer(self):
        self.skip_timer = True

    def next_timed_state(self):
        self.dprint("\n### TimedAutomata.next_state")
        now = pygame.time.get_ticks()
        cs = self.current_state
        min_time = self.min_states_time[cs]
        self.dprint("\t now = {0}; current_state = {1}; min_time = {2};".format(now, cs, min_time))
        self.dprint("\t last_time = {0}".format(self.last_time))
        self.dprint("\t {0} > {1}".format(now - self.last_time, min_time*1000))
        if self.skip_timer or now - self.last_time > min_time*1000: # time goes in milliseconds
            if self.skip_timer: self.dprint("\tSkiping timer and changing!")
            else: self.dprint("\tTime to change!")
            self.last_time = now
            self.next_state()
            self.skip_timer = False

    def reset_timer(self):
        """ Sets the timer to zero. """
        now = pygame.time.get_ticks()
        self.last_time = now
