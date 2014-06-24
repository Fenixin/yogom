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


""" This module parses arguments and stores them in a dictionary.

You can define arguments with type and default. Arguments without default
will be mandatory. Very useful to provide sprites with arguments from tiled.
"""


class ErrorParsingArgument(Exception):
    """ Raised when can't properly parse an Argument. """

    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)


class ArgumentParser(object):
    def __init__(self, arguments_description=None, arguments=None,
                 destination=None):
        """ Parse arguments with descriptions and store them in destination.
            
            argument_description, arguments and destination are dicts.
            """
        if arguments_description != None:
            if isinstance(arguments_description, dict):
                self.description = arguments_description
            else:
                msg = "Error initializing the parser, arguments_description must be dict, given \'{0}\'".format(str(type(arguments_description)))
                raise ErrorParsingArgument(msg)
        if arguments != None:
            if isinstance(arguments, dict):
                self.arguments = arguments
            else:
                msg = "Error initializing the parser, arguments must be dict, given \'{0}\'".format(str(type(arguments)))
                raise ErrorParsingArgument(msg)
        if destination != None:
            if isinstance(destination, dict):
                self.destination = destination
            else:
                msg = "Error initializing the parser, destination must be dict, given \'{0}\'".format(str(type(destination)))
                raise ErrorParsingArgument(msg)

    def check_and_store_dict(self, arg):
        """ Returns the argument if it is a dict raises the proper
            exception if not. """
        

    def parse(self, arguments_description = None, arguments = None, destination = None):
        """ Parse! """

        if arguments_description == None: arguments_description = self.arguments_description
        if arguments == None: arguments = self.arguments
        if destination == None: destination = self.destination
        
        # first check if all the custom properties are present in the
        # arguments given
        for var in arguments_description.keys():
            # if an argument is missing it has to have default
            if var not in arguments and "default" not in arguments_description[var] :
                msg = "The argumetns are missing the property \'{0}\'".format(var)
                raise ErrorParsingArgument(msg)
        
        # now check that all the properties in the arguments are
        # in the description dict
        # SKIP THIS: is more useful to pass all kind of arguments and
        # get whatever is useful for you
        #~ for prop in arguments:
            #~ if prop not in arguments_description.keys():
                #~ msg = "The arguments have the unknown property \'{0}\'".format(prop)
                #~ raise ErrorParsingArgument(msg)
        
        # parse the options and store them

        for var in arguments_description.keys():
            if var in arguments:
                tmp = arguments[var]
                
                ty = arguments_description[var]["type"]
                if "possible_values" in arguments_description[var]:
                    possible_values = arguments_description[var]["possible_values"]
                else:
                    possible_values = None

                # check the type
                if isinstance(tmp, ty):
                    value = tmp
                else:
                    try:
                        value = ty(tmp)
                    except ValueError as e:
                        msg = "The arguments have custom property {0} with invalid type. Expected type: {1}. Found: {2}".format(var, ty, type(tmp))
                        raise ErrorParsingArgument(msg)
                    except TypeError as e:
                        msg = "The arguments have custom property {0} with invalid type. Expected type: {1}. Found: {2}".format(var, ty, type(tmp))
                        raise ErrorParsingArgument(msg)
                
                # check if the given argumen is a possible value
                if possible_values:
                    if value not in possible_values:
                        msg = "The arguments have an unexpected value in property {0}. Possible values: {1}".format(var, possible_values)
                        raise ErrorParsingArgument(msg)
            
            elif "default" in arguments_description[var]:
                # get the default value
                value = arguments_description[var]["default"]
            
            # everything is ok, store the value
            try:
                destination[arguments_description[var]["destination"]] = value
            except KeyError as e:
                msg = "The arguments have no destintion variable in property \'{0}\'".format(var)
                raise ErrorParsingArgument(msg)
