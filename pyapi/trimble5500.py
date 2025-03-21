#!/usr/bin/env python
"""
.. module:: trimble5500.py
   :platform: Unix, Windows
   :synopsis: Ulyxes - an open source project to drive total stations and
       publish observation results. GPL v2.0 license Copyright (C)
       2010- Zoltan Siki <siki.zoltan@epito.bme.hu>

.. moduleauthor:: Zoltan Siki <siki.zoltan@epito.bme.hu>

"""

from measureunit import MeasureUnit
from angle import Angle

class Trimble5500(MeasureUnit):
    """ This class contains the Trimble 5500 robotic total station specific
        functions

            :param name: name of ts (str), default 'Trimble 5500'
            :param type: type of ts (str), default 'TPS'
    """
    # Constants for message codes
    codes = {
        'STN': 2,
        'IH': 3,
        'PCODE': 4,
        'PNO': 5,
        'SH': 6,
        'HA': 7,
        'VA': 8,
        'SD': 9,
        'PC': 20,
        'HAREF': 21,
        'SVA': 26,
        'SHA': 27,
        'PPM': 30,
        'PRISMC': 32,
        'NORTHING': 37,
        'EASTING': 38,
        'ELE': 39,
        'TEMP': 56,
        'EARAD': 58,
        'REFRAC': 59,
        'WETTEMP': 66,
        'PRESS': 74
    }

    # Constants for EMD modes
    edmModes = {'STANDARD': 0, 'TRACKING': 1, 'D-BAR': 2, 'FAST': 3,
                'HRD_BAR': 4}
    edmProg = {'DEFAULT': None}

    def __init__(self, name='Trimble 5500', typ='TPS'):
        """ Constructor to leica generic ts
        """
        # call super class init
        super().__init__(name, typ)
        self.edmMode = 0    # standard

    @staticmethod
    def GetCapabilities():
        """ Get instrument specialities

            :returns: empty list, do not use generic instrument
        """
        return ['ROBOT', 'ANGLE', 'EDM', 'RL', 'LASER', 'POSITION']

    def Result(self, msgs, anss):
        """ Parse answer from message

            :param msgs: messages sent to instrument
            :param anss: answers got from instrument
            :returns: dictionary
        """
        msgList = msgs.split('|')
        ansList = anss.split('|')
        res = {}
        for msg, ans in zip(msgList, ansList):
            if len(msg.strip()) == 0:
                continue
            # get command id form message
            ansBufflist = ans.split('\n')
            for ans1 in ansBufflist:
                if '=' in ans1:
                    buf = ans1.strip('\r|').split('=')
                    commandID = int(buf[0])
                    if commandID == self.codes['HA']:
                        res['hz'] = Angle(float(buf[1]), 'PDEG')
                    elif commandID == self.codes['VA']:
                        res['v'] = Angle(float(buf[1]), 'PDEG')
                    elif commandID == self.codes['SD']:
                        res['distance'] = float(buf[1])
                    elif commandID == self.codes['EASTING']:
                        res['east'] = float(buf[1])
                    elif commandID == self.codes['NORTHING']:
                        res['north'] = float(buf[1])
                    elif commandID == self.codes['ELE']:
                        res['elev'] = float(buf[1])
                    # TODO add all codes!
        return res

    def SetPcMsg(self, pc):
        """ Set prism constant

            :param pc: prism constant [mm]
            :returns: set prism constant message
        """
        return 'WG,{0:d}={1:.3f}'.format(self.codes['PC'], pc / 1000.0)

    def GetPcMsg(self):
        """ Get prism constant

            :returns: get prism constant message
        """
        return f"RG,{self.codes['PC']}"

    def SetAtmCorrMsg(self, ppm, pres=None, dry=None, wet=None):
        """ Set atmospheric correction settings using ppm or
            presure, dry and wet temperature

            :param ppm: atmospheric correction [mm/km] (int)
            :param pres: air presure (optional)
            :param dry: dry temperature (optional)
            :param wet: wet temperature (optional)
            :returns: set atmospheric correction message
        """
        if ppm is not None:
            return f"WG,{self.codes['PPM']}={ppm}"
        return f"WG,{self.codes['PRESS']}={pres}|WG,{self.codes['TEMP']}={dry}|WG,{self.codes['WETTEMP']}={wet}"

    def GetAtmCorrMsg(self):
        """ Get atmospheric correction settings

            :returns: atmospheric correction message
        """
        return f"RG,{self.codes['PPM']}"

    def SetRefCorrMsg(self, status, earthRadius, refrac):
        """ Set refraction correction settings

        :param status: not used
        :param earthRadius: radius ot the Earth (int)
        :param refrac: refraction (float)
        :returns: set refraction correction message

        """
        return f"WG,{self.codes['EARAD']}={earthRadius}|WG,{self.codes['REFRAC']}={refrac:.2f}"

    def GetRefCorrMsg(self):
        """ Get refraction correction setting

            :return: refraction correction message

        """
        return f"RG,{self.codes['EARAD']}|RG,{self.codes['REFRAC']}"

    def SetStationMsg(self, e, n, z=None, ih=0):
        """ Set station coordinates

            :param e: easting
            :param n: northing
            :param z: elevation
            :param ih: instrument height
            :returns: set station coordinates message

        """
        msg = f"WG,{self.codes['EASTING']}={e:.3f}|WG,{self.codes['NORTHING']}={n:.3f}"
        if z is not None:
            msg += f"|WG,{self.codes['ELE']}={z:.3f}"
        # TODO instrumenrt height
        msg += f"|WG,{self.codes['IH']}={ih:.3f}"
        return msg

    def GetStationMsg(self):
        """ Get station co-ordinates

            :returns: get station coordinates message

        """
        return f"RG,{self.codes['EASTING']}|RG,{self.codes['NORTHING']}|RG,{self.codes['ELE']}|RG,{self.codes['IH']}"

    def SetEDMModeMsg(self, mode):
        """ Set EDM mode

            :param mode: mode name (str) or code (int)
            :returns: set edm mode message
        """
        if type(mode) is str:
            self.edmMode = self.edmModes[mode]
        else:
            self.edmMode = mode
        return f"PG,3{self.edmMode}"

    def GetEDMModeMsg(self):
        """ Get EDM mode

            :returns: None
        """
        return self.edmMode

    def SetOriMsg(self, ori):
        """ Set orientation angle

            :param ori: bearing of direction (Angle)
            :returns: set orientation angle message

        """
        return f"WG,{self.codes['HAREF']}={ori.GetAngle('PDEG'):.4f}"

    def MoveMsg(self, hz, v, dummy=None):
        """ Rotate instrument to direction

            :param hz: horizontal direction (Angle)
            :param v: zenith angle (Angle)
            :param dummy: dummy parameter for compatibility with Leica
            :returns: rotate message
        """
        # change angles to pseudo DMS
        hz_pdms = hz.GetAngle('PDEG')
        v_pdms = v.GetAngle('PDEG')
        return f"WG,26={v_pdms:.4f}|WG,27={hz_pdms:.4f}|WS=PH02V02"

    def MeasureMsg(self, dummy1=None, dummy2=None):
        """ Measure distance

            :param dummy1: dummy parameter for compatibility with Leica
            :param dummy2: dummy parameter for compatibility with Leica
            :returns: measure message
        """
        return 'TG'

    def GetMeasureMsg(self, dummy1=None, dummy2=None):
        """ Get measured distance

            :param dummy1: dummy parameter for compatibility with Leica
            :param dummy2: dummy parameter for compatibility with Leica
            :returns: get measurement message
        """
        return 'RG'

    def MeasureDistAngMsg(self, dummy=None):
        """ Measure angles and distance

            :param prg: dummy parameter for compatibility with Leica
            :returns: measure angle distance message

        """
        return 'TG|RG'

    def CoordsMsg(self, wait=1000, incl=0):
        """ Get coordinates

            :param wait: wait-time in ms, optional (default 1000)
            :param incl: inclination calculation - 0/1/2 = measure always (slow)/calculate (fast)/automatic, optional (default 0)
            :returns: get coordinates message
        """
        return f"RG,{self.codes['NORTHING']}|RG,{self.codes['EASTING']}|RG,{self.codes['ELE']}"

    def GetAnglesMsg(self):
        """ Get angles

                :returns: get angles message
        """
        return f"RG,{self.codes['HA']}|RG,{self.codes['VA']}"

    def ChangeFaceMsg(self):
        """ Change face

            :returns: None
        """
        return None
