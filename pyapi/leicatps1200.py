#!/usr/bin/env python
"""
.. module:: leicatps1200.py
   :platform: Unix, Windows
   :synopsis: Ulyxes - an open source project to drive total stations and
       publish observation results. GPL v2.0 license Copyright (C)
       2010- Zoltan Siki <siki.zoltan@epito.bme.hu>

.. moduleauthor:: Zoltan Siki <siki.zoltan@epito.bme.hu>,
    Daniel Moka <mokadaniel@citromail.hu>

"""

from leicameasureunit import LeicaMeasureUnit

class LeicaTPS1200(LeicaMeasureUnit):
    """ This class contains the Leica TPS1200 robotic total station specific
        functions

            :param name: name of ts (str), default=TPS1200
            :param type: type od ts (str), default=TPS
    """

    def __init__(self, name='Leica TPS1200', typ='TPS'):
        """ Constructor to leica generic ts
        """
        # call super class init
        super().__init__(name, typ)

    # Constants for message codes
    codes = {
        'SWITCHON': 111,
        'SWITCHOFF': 112,
        'SETPC': 2024,
        'GETPC': 2023,
        'INSTRNO': 5003,
        'INSTRNAME': 5004,
        'INTTEMP': 5011,
        'SETATR': 18005,
        'GETATR': 18006,
        'SETLOCK': 18007,
        'GETLOCK': 18008,
        'LOCKIN': 9013,
        'SETATMCORR': 2028,
        'GETATMCORR': 2029,
        'SETREFCORR': 2030,
        'GETREFCORR': 2031,
        'GETSTN': 2009,
        'SETSTN': 2010,
        'SETEDMMODE': 2020,
        'GETEDMMODE': 2021,
        'SETORI': 2113,
        'MOVE': 9027,
        'FINEADJ': 9037,
        'MEASURE': 2008,
        'GETMEASURE': 2108,
        'MEASUREANGDIST': 17017,
        'COORDS': 2082,
        'GETANGLES': 2003,
        'CHANGEFACE': 9028,
        'SETSEARCHAREA': 9043,
        'POWERSEARCH': 9051,
        'SETREDLASER': 1004,
        'GETPT': 17009,
        'SETPT': 17008,
        'GETSPIRAL': 9040,
        'SETSPIRAL': 9041,
        'SEARCHTARGET': 17020
    }

    # Constants for EMD modes
    # RT = Reflector Tape, RL = Reflectorless, LR = Long Range
    edmModes = {'RTSTANDARD': 1, 'STANDARD': 2, 'FAST': 3, 'LRSTANDARD': 4, \
                'RLSTANDARD': 5, 'TRACK': 6, 'RLTRACK': 8, 'TRACK2': 9, \
                'AVERAGING': 10, 'RLAVERAGING': 11, 'LRAVERAGING': 12}

    @staticmethod
    def GetCapabilities():
        """ Get instrument specialities

            :returns: List of specialities
        """
        return ['ROBOT', 'ANGLE', 'EDM', 'ATR', 'LOCK', 'RL', 'POWERSEARCH', \
            'LASER', 'POSITION']

    def SetSearchAreaMsg(self, hzCenter, vCenter, hzRange, vRange, on=1):
        """ set search area for power search

            :param hzCenter: center direction (Angle)
            :param vCenter: center direction (Angle)
            :param hzRange: horizontal range to search (Angle)
            :param vRange: vertical range to search (Angle)
            :param on: 0/1 off/on
        """
        return f"%R1Q,{self.codes['SETSEARCHAREA']}:{hzCenter.GetAngle()},{vCenter.GetAngle()},{hzRange.GetAngle()},{vRange.GetAngle()},{on}"

    def PowerSearchMsg(self, direction):
        """ Power search

            :param direction: 1/-1 clockwise/counter clockwise
            :returns: Power search message
        """
        return f"%R1Q,{self.codes['POWERSEARCH']}:{direction},0"

    def SetRedLaserMsg(self, on):
        """ Set red laser on/off

            :param on: 0/1 turn off/on read laser
            :returns: red laser on/off message
        """
        return f"%R1Q,{self.codes['SETREDLASER']}:{on}"
