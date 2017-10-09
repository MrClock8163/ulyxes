#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. module:: confreader.py
   :platform: Unix, Windows
   :synopsis: Ulyxes - an open source project to drive total stations and
           publish observation results.
           GPL v2.0 license
           Copyright (C) 2010-2013 Zoltan Siki <siki@agt.bme.hu>

.. moduleauthor:: Zoltan Siki <siki@agt.bme.hu>
"""
import logging
import os
from jsonreader import JSONReader

class ConfReader(JSONReader):
    """ Class to read json configuration file

            :param name: name of reader (str), default None
            :param fname: name of input file
            :param filt: obligatory fields for Load
            :param pars: a dictionary for parameter validation e.g. {key : {}}, valid keys for individual config parameters are: required (True/False), type (int/float/str/list)
    """

    def __init__(self, name = None, fname = None, filt = None, pars = None):
        """ Constructor
        """
        super(ConfReader, self).__init__(name, fname, filt)
        self.pars = pars

    def Check(self):
        """ Validate config values and send warning/error to log

            :returns: True/False
        """
        # check for required pars and
        # set default values for missing parameters
        for par in self.pars:
            if self.pars[par]['required'] and not par in self.json:
                logging.error("missing required parameter: " + par)
                return False
            if 'default' in self.pars[par] and not par in self.json:
                self.json[par] = self.pars[par]['default']
        for par in self.json:
            if not par in self.pars:
                logging.warning("unknown parameter: " + par)
                continue
            # type checking
            pardef = self.pars[par]
            if 'type' in pardef:
                if pardef['type'] == 'int' and type(self.json[par]) is not int:
                    logging.error("type mismatch parameter: " + par)
                    return False
                elif pardef['type'] == 'float' and \
                    type(self.json[par]) is not int and \
                    type(self.json[par]) is not float:
                    logging.error("type mismatch parameter: " + par)
                    return False
                elif pardef['type'] == 'list' and \
                    type(self.json[par]) is not list:
                    logging.error("type mismatch parameter: " + par)
                    return False
                elif pardef['type'] == 'file' and \
                    type(self.json[par]) is not str and \
                    not os.path.isfile(self.json[par]):
                    logging.error("type mismatch parameter or file does not exist: " + par)
                    return False
                # check set for valid values
                if 'set' in pardef and \
                    not self.json[par] in pardef['set']:
                    logging.error("invalid value: " + par)
                    return False
                    # TODO reglist
        # TODO complex rules e.g. no fix but gama_path given
        return True

if __name__ == '__main__':
    config_pars = {
        'log_file': {'required' : True, 'type': 'file'},
        'log_level': {'required' : True, 'type': 'int',
        'set': [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR ]},
        'log_format': {'required': False, 'default': "%(asctime)s %(levelname)s:%(message)s"},
        'station_type': {'required' : True, 'type': 'str', 'set': ['1200', '1800', '1100']},
        'station_id': {'required' : True, 'type': 'str'},
        'station_height': {'required': False, 'default': 0, 'type': 'float'},
        'station_coo_limit': {'required': False, 'default': 0.01, 'type': 'float'},
        'orientation_limit': {'required': False, 'default': 0.1, 'type': 'float'},
        'faces': {'required': False, 'default': 1, 'type': 'int'},
        'fix_list': {'required': False, 'type': 'list'},
        'mon_list': {'required': False, 'type': 'list'},
        'max_try': {'required': False, 'type': 'int', 'default': 3},
        'delay_try': {'required': False, 'type': 'float', 'default': 0},
        'dir_limit': {'required': False, 'type': 'float', 'default': 0.015},
        'port': {'required' : True, 'type': 'str'},
        'coo_rd': {'required' : True},
        'coo_wr': {'required' : True},
        'obs_wr': {'required': False},
        'met_wr': {'required': False},
        'avg_wr': {'required': False, 'type': 'int', 'default': 1},
        'decimals': {'required': False, 'type': 'int', 'default': 4},
        'gama_path': {'required': False, 'type': 'file'},
        'stdev_angle': {'required': False, 'type': 'float', 'default': 1},
        'stdev_dist': {'required': False, 'type': 'float', 'default': 1},
        'stdev_dist1': {'required': False, 'type': 'float', 'default': 1.5},
        'dimension': {'required': False, 'type': 'int', 'default': 3},
        'probability': {'required': False, 'type': 'float', 'default': 0.95},
        'blunders': {'required': False, 'type': 'int', 'default': 1},
        'met': {'required': False, 'set': ['WEBMET', 'BMP180', 'SENSEHAT']},
        'met_addr': {'required': False},
        'met_par': {'required': False},
        '__comment__': {'required': False, 'type': 'str'}
    }
    jr = ConfReader('test', '../pyapps/robotplus.json', None, config_pars)
    if jr.state == jr.RD_OK:
        print jr.Load()
        print jr.Check()
    else:
        print "config file?"
