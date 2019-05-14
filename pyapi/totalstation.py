#!/usr/bin/env python
"""
.. module:: totalstation.py
   :platform: Unix, Windows
   :synopsis: Ulyxes - an open source project to drive total stations and
       publish observation results.  GPL v2.0 license Copyright (C)
       2010-2013 Zoltan Siki <siki@agt.bme.hu>

.. moduleauthor:: Zoltan Siki <siki@agt.bme.hu>,
    Daniel Moka <mokadaniel@citromail.hu>
"""
import logging
import time
from instrument import Instrument
from angle import Angle
from leicatps1200 import LeicaTPS1200
from leicatcra1100 import LeicaTCRA1100
from leicatca1800 import LeicaTCA1800
from trimble5500 import Trimble5500
from serialiface import SerialIface
from echowriter import EchoWriter

class TotalStation(Instrument):
    """ Generic total station instrument

            :param name: name of instrument
            :param measureUnit: measure unit part of instrument
            :param measureIface: interface to physical unit
            :param writerUnit: store data, default None
    """
    FACE_LEFT = 0
    FACE_RIGHT = 1
    FACE_AVG = 2

    def __init__(self, name, measureUnit, measureIface, writerUnit=None):
        """ Constructor
        """
        # call super class init
        super(TotalStation, self).__init__(name, measureUnit, measureIface,
                                           writerUnit)
        if isinstance(measureUnit, Trimble5500):
            # change default eol marker for read
            measureIface.eomRead = '>'

#        self.__class__.add_totalStation(self)

    def __str__(self):
        return '<{} object from {} module at {} address | MeasureUnit: {} | MeasureInterface: {} >'\
            .format(type(self).__name__, self.__module__, hex(id(self)),
                    self.measureUnit.GetName(), self.measureIface.name)

    def __repr__(self):
        muString = self.measureUnit.GetName()
        muString = muString.replace(' ', '') + '()'
        return "{}('{}',{},'{}')".format(type(self).__name__, self.name,
                                         muString, self.measureIface.GetName())

    def SetPc(self, pc):
        """ Set prism constant

            :param pc: prism constant [m]
            :returns: processed answer from instrument
        """
        msg = self.measureUnit.SetPcMsg(pc)
        return self._process(msg)

    def GetPc(self):
        """ Get prism constant

            :returns: processed answer from instrument
        """
        msg = self.measureUnit.GetPcMsg()
        return self._process(msg)

    def SetATR(self, atr):
        """ Set ATR on

            :param atr: 0/1 ATR off/on
            :returns: processed answer from instrument
        """
        msg = self.measureUnit.SetATRMsg(atr)
        return self._process(msg)

    def GetATR(self):
        """ Get ATR status of instrument

            :returns: 0/1 ATR off/on
        """
        msg = self.measureUnit.GetATRMsg()
        return self._process(msg)

    def SetPrismType(self, typ):
        """ Set prism type
            :param typ: prizm type
        """
        msg = self.measureUnit.SetPrismTypeMsg(typ)
        return self._process(msg)

    def GetPrismType(self):
        """ Get prism type
        """
        msg = self.measureUnit.GetPrismTypeMsg()
        return self._process(msg)

    def SetLock(self, lock):
        """ Set lock on prism

            :param lock: 0/1 lock off/on
            :returns: processed answer from instrument
        """
        msg = self.measureUnit.SetLockMsg(lock)
        return self._process(msg)

    def GetLock(self):
        """ Get lock status

            :returns: lock status of the instrument 0/1 on/off
        """
        msg = self.measureUnit.GetLockMsg()
        return self._process(msg)

    def LockIn(self):
        """ Turn on lock

            :returns: empty
        """
        msg = self.measureUnit.LockInMsg()
        return self._process(msg)

    def SetAtmCorr(self, valueOfLambda, pres, dryTemp, wetTemp=None):
        """ Set atmospheric correction

            :param valueOfLambda: instrument specific constant
            :param pres: air presure
            :param dryTemp: dry temperature
            :param wetTemp: wet temperature
        """
        if wetTemp is None:
            wetTemp = dryTemp - 5.0
        msg = self.measureUnit.SetAtmCorrMsg(valueOfLambda, pres, dryTemp,
                                             wetTemp)
        return self._process(msg)

    def GetAtmCorr(self):
        """ Get atmospheric correction

            :returns: atmospheric corrections (dictionary)
        """
        msg = self.measureUnit.GetAtmCorrMsg()
        return self._process(msg)

    def SetRefCorr(self, status, earthRadius, refracticeScale):
        """ Set refraction correction

            :param status: ???
            :param earthRadius: radius of earth
            :param refracticeScale: ???
        """
        msg = self.measureUnit.SetRefCorrMsg(status, earthRadius,
                                             refracticeScale)
        return self._process(msg)

    def GetRefCorr(self):
        """ Get refraction correction

            :returns: refraction correction (dictionary)
        """
        msg = self.measureUnit.GetRefCorrMsg()
        return self._process(msg)

    def SetStation(self, easting, northing, elevation, ih=0.0):
        """ Set station coordinates

            :param easting: easting of station
            :param northing: northing of station
            :param elevation: elevation of station
            :param ih: instrument height
            :returns: ???
        """
        msg = self.measureUnit.SetStationMsg(easting, northing, elevation, ih)
        return self._process(msg)

    def GetStation(self):
        """ Get station coordinates

            :returns: station coordinates and instrument height (dictionary)
        """
        msg = self.measureUnit.GetStationMsg()
        return self._process(msg)

    def SetEDMMode(self, mode):
        """ Set EDM mode

            :param mode: mode name/id as listed in measure unit
            :returns: empty dictionary
        """
        msg = self.measureUnit.SetEDMModeMsg(mode)
        return self._process(msg)

    def GetEDMMode(self):
        """ Get EDM mode

            :returns: actual EDM mode
        """
        msg = self.measureUnit.GetEDMModeMsg()
        return self._process(msg)

    def SetOri(self, ori):
        """ Set orientation

            :param ori: bearing to direction (Angle)
            :returns: empty dictionary
        """
        # clear previous distance measured
        ans = self.Measure('CLEAR')
        if 'errCode' in ans:
            return ans
        msg = self.measureUnit.SetOriMsg(ori)
        return self._process(msg)

    def SetRCS(self, rcs):
        """ Remote control
        """
        msg = self.measureUnit.SetRCSMsg(rcs)
        return self._process(msg)

    def Move(self, hz, v, atr=0):
        """ Rotate instrument to a given direction

            :param hz: horizontal direction (Angle)
            :param v: zenith (Angle)
            :param atr: 0/1 ATR on/off
        """
        hz.Positive()    # negative angles are not accepted by totalstations
        v.Positive()
        msg = self.measureUnit.MoveMsg(hz, v, atr)
        return self._process(msg)

    def Measure(self, prg='DEFAULT', incl=0):
        """ Measure distance

            :param prg: EDM program, DEFAULT is the only reasonable value
            :param incl: not used, only for compability
            :returns: empty dictionary
        """
        if type(prg) is str:
            prg = self.measureUnit.edmProg[prg]
        msg = self.measureUnit.MeasureMsg(prg, incl)
        return self._process(msg)

    def GetMeasure(self, wait=15000, incl=0):
        """ Get measured values

            :param wait: waiting time in ms
            :param inc: inclination ...
            :returns: observations in a dictionary
        """
        msg = self.measureUnit.GetMeasureMsg(wait, incl)
        i = 0
        meas = self._process(msg)
        while 'distance' not in meas and i < 20:   # wait for trimble 5500
            i += 1
            time.sleep(2)
            meas = self._process(msg)
        return meas

    def MeasureDistAng(self, prg='DEFAULT'):
        """ Measure distance and return observations

            :returns: observations in a dictionary
        """
        if type(prg) is str:
            prg = self.measureUnit.edmProg[prg]
        msg = self.measureUnit.MeasureDistAngMsg(prg)
        return self._process(msg)

    def Coords(self, wait=15000, incl=0):
        """ Read coordinates from instrument

            :param wait: waiting time ms
            :param incl: inclination
            :returns: coordinates in a dictionary
        """
        msg = self.measureUnit.CoordsMsg(wait, incl)
        return self._process(msg)

    def GetAngles(self):
        """ Get angles from instrument

            :returns: angles in a dictionary
        """
        msg = self.measureUnit.GetAnglesMsg()
        return self._process(msg)

    def ClearDistance(self):
        """ Clear measured distance on instrument
        """
        msg = self.measureUnit.ClearDistanceMsg()
        return self._process(msg)

    def ChangeFace(self):
        """ Change face

            :returns: empty dictionary
        """
        msg = self.measureUnit.ChangeFaceMsg()
        if msg is None:
            angles = self.GetAngles()
            angles['hz'] += Angle(180, 'DEG')
            angles['v'] = Angle(360, 'DEG') - angles['v']
            return self.Move(angles['hz'], angles['v'])
        return self._process(msg)

    def SetRedLaser(self, on):
        """ Set on/off red laser

            :param on: 0/1 off/on
            :returns: empty dictionary or error
        """
        msg = self.measureUnit.SetRedLaserMsg(on)
        return self._process(msg)

    def SetSearchArea(self, hzCenter=None, vCenter=None, \
                      hzRange=None, vRange=None, on=1):
        """ Set range for power search

            :param hzCenter: center direction (Angle)
            :param vCenter: center direction (Angle)
            :param hzRange: horizontal range to search (default full circle) (Angle)
            :param vRange: vertical range to search (default 95 degree) (Angle)
            :param on: 0/1 off/on
        """
        if hzCenter is None or vCenter is None:
            angles = self.GetAngles()
            if hzCenter is None:
                hzCenter = angles['hz']
            if vCenter is None:
                vCenter = angles['v']
            if hzRange is None:
                hzRange = Angle(399.9999, 'GON')
            if vRange is None:
                vRange = Angle(95, 'DEG')
        msg = self.measureUnit.SetSearchAreaMsg(hzCenter, vCenter, hzRange,
                                                vRange, on)
        return self._process(msg)

    def PowerSearch(self, direction=1):
        """ Start power search

            :param direction: 1/-1 clockwise/counter clockwise
            :returns: empty list if succesfull
        """
        msg = self.measureUnit.PowerSearchMsg(direction)
        return self._process(msg)

    def GetSpiral(self):
        """ Get search spiral parameters

            :returns: horizontal and vertical range
        """
        msg = self.measureUnit.GetSpiralMsg()
        return self._process(msg)

    def SetSpiral(self, dRangeHz, dRangeV):
        """ Set search spiral parameters

            :param dRangeHz: horizontal range (Angle)
            :param dRangeV: vertical range (Angle)
        """
        msg = self.measureUnit.SetSpiralMsg(dRangeHz, dRangeV)
        return self._process(msg)

    def SearchTarget(self):
        """ Search target

            :returns: TODO
        """
        msg = self.measureUnit.SearchTargetMsg()
        return self._process(msg)

    def SwitchOn(self, mode=1):
        """ Switch on or wake up instrument and change to remote control

            :param mode: 0/1 local/remote mode
            :returns: empty list if successful, timeout may occure
        """
        msg = self.measureUnit.SwitchOnMsg(mode)
        return self._process(msg)

    def SwitchOff(self):
        """ Switch off instrument

            :param mode: 0/1 power down/sleep state
            :returns: processed answer from instrument
        """
        msg = self.measureUnit.SwitchOffMsg()
        return self._process(msg)

    def GetInstrumentNo(self):
        """ Get instrument factory number

            :returns: processed answer from instrument
        """
        msg = self.measureUnit.GetInstrumentNoMsg()
        return self._process(msg)

    def GetInstrumentName(self):
        """ Get instrument name

            :returns: processed answer from instrument
        """
        msg = self.measureUnit.GetInstrumentNameMsg()
        return self._process(msg)

    def GetInternalTemperature(self):
        """ Get instrument internal temperature

            :returns: processed answer from instrument
        """
        msg = self.measureUnit.GetInternalTemperatureMsg()
        return self._process(msg)

    def GetFace(self):
        """ Get face left or face right

            :returns: 0/1 face left/face right in a dictionary or None in case of error
        """
        a = self.GetAngles()
        if 'v' in a:
            if a['v'].GetAngle('GON') < 200:
                face = self.FACE_LEFT
            else:
                face = self.FACE_RIGHT
            return {'face': face}
        logging.error(" Getangles failed")
        return None

    def MoveRel(self, hz_rel, v_rel, atr=0):
        """ Rotate the instrument relative to actual direction

            :param hz_rel: relative horizontal rotation (Angle)
            :param v_rel: relative zenith rotation (Angle)
            :param atr: 0/1 atr on/off
        """
        #get the actual direction
        msg = self.measureUnit.GetAnglesMsg()
        res = self._process(msg)
        if 'hz' in res and 'v' in res:
            return self.Move(res['hz'] + hz_rel, res['v'] + v_rel, atr)
        return None

if __name__ == "__main__":
    import time
    logging.getLogger().setLevel(logging.DEBUG)
    #mu = LeicaTPS1200()
    #mu = LeicaTCA1800()
    mu = Trimble5500()
    iface = SerialIface("rs-232", "/dev/ttyUSB0")
    wrt = EchoWriter()
    ts = TotalStation("Leica", mu, iface, wrt)
    #ts.SetStation(10.0, 20., 30., 1.0)
    print(ts.GetStation())
    #print(ts.GetInstrumentNo())
    #ts.GetInstrumentName()
    #ts.SetEDMMode(ts.measureUnit.edmModes['RLSTANDARD'])
    #ts.SetPc(0.0068)
    #print(ts.GetPc())
    print(ts.GetAngles())
    ts.Move(Angle(90, 'DEG'), Angle(85, 'DEG'))
    #ts.SetEDMMode(ts.measureUnit.edmModes['STANDARD'])
    ts.Measure()
    meas = ts.GetMeasure()
    #while 'distance' not in meas:
    #time.sleep(5)
    #meas = ts.GetMeasure()
    #print(meas)
    #ts.SwitchOff()
