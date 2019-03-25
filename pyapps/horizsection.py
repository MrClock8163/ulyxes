#!/usr/bin/env python
"""
.. module:: horizsection.py

.. moduleauthor:: Viktoria Zubaly, Zoltan Siki

Sample application of Ulyxes PyAPI to measure a horizontal section
target on the first point of the section and start this app
coordinates and observations are written to csv file

    :param argv[1] (angle step): angle step between points in DEG, default 45
    :param argv[2] (sensor): 1100/1800/1200, default 1200
    :param argv[3] (port): serial port, default /dev/ttyUSB0
    :param argv[4] (max angle): stop at this direction, default 360 degree
    :param argv[5] (tolerance): acceptable tolerance (meter) from the horizontal plane, default 0.01
    :param argv[6] (iteration): max iteration number for a point, default 10
"""
import sys
import time
import re
import math
import logging

sys.path.append('../pyapi/')

from angle import Angle, PI2
from serialiface import SerialIface
from csvwriter import CsvWriter
from leicatps1200 import LeicaTPS1200
from leicatcra1100 import LeicaTCRA1100
from trimble5500 import Trimble5500
from totalstation import TotalStation

class HorizontalSection(object):
    """ Measure a horizontal section at a given elevation
        :param ts: total station instance
        :param elev: elevation for section
        :param hz_start: start horizontal direction (Angle)
        :param step: horizontal step angle (Angle)
        :param hz_max: end horizontal direction (radians)
        :param maxiter: max iteration to find elevation
        :param tol: tolerance for horizontal angle
    """

    def __init__(self, ts, elev=None, hz_start=None,
                 stepinterval=Angle(45, "DEG"), maxa=PI2, maxiter=10, tol=0.02):
        """ initialize """
        self.ts = ts
        self.elev = elev
        self.hz_start = hz_start
        self.stepinterval = stepinterval
        self.maxa = maxa
        self.maxiter = maxiter
        self.tol = tol

    def run(self):
        """ do the observations in horizontal section """
        self.ts.Measure()    # initial measurement for startpoint
        if self.hz_start is not None:
            # rotate to start position, keeping zenith angle
            a = self.ts.GetAngles()
            print (a)
            print (self.hz_start.GetAngle())
            print (a['v'].GetAngle())
            self.ts.Move(self.hz_start, a['v'])
        startp = self.ts.GetMeasure()
        i = 0
        while 'distance' not in startp and i < 20:
            i += 1
            time.sleep(2)
            startp = self.ts.GetMeasure()   # wait for trimble 5500
        if self.ts.measureIface.state != self.ts.measureIface.IF_OK or 'errorCode' in startp:
            print('FATAL Cannot measure startpoint')
            return 1

        # height of startpoint above the horizontal axis
        if self.elev is None:
            height0 = math.cos(startp['v'].GetAngle()) * startp['distance']
        else:
            height0 = self.elev
        w = True
        try:
            self.ts.SetRedLaser(1)       # turn on red laser if possible
        except:
            pass
        act = Angle(0)  # actual angle from startpoint
        while act.GetAngle() < self.maxa: # go around the whole circle
            self.ts.Measure() # measure distance0
            if self.ts.measureIface.state != self.ts.measureIface.IF_OK:
                self.ts.measureIface.state = self.ts.measureIface.IF_OK
                self.ts.MoveRel(self.stepinterval, Angle(0))
                continue
            if isinstance(self.ts.measureUnit, Trimble5500):
                time.sleep(5)
            nextp = self.ts.GetMeasure()  # get observation data
            if self.ts.measureIface.state != self.ts.measureIface.IF_OK:
                # cannot measure, skip
                self.ts.measureIface.state = self.ts.measureIface.IF_OK
                self.ts.MoveRel(self.stepinterval, Angle(0))
                continue

            if 'v' not in nextp or 'distance' not in nextp or 'hz' not in nextp:
                self.ts.MoveRel(self.stepinterval, Angle(0))
                continue

            height = math.cos(nextp['v'].GetAngle()) * nextp['distance']
            index = 0
            while abs(height-height0) > self.tol:  # looking for right elevation
                w = True
                zenith = nextp['v'].GetAngle()
                zenith1 = math.acos(height0 / nextp['distance'])
                self.ts.MoveRel(Angle(0), Angle(zenith1-zenith))
                self.ts.Measure()
                index += 1
                if index > self.maxiter or \
                    self.ts.measureIface.state != self.ts.measureIface.IF_OK:
                    w = False
                    self.ts.measureIface.state = self.ts.measureIface.IF_OK
                    logging.warning('Missing measurement')
                    break
                nextp = self.ts.GetMeasure()
                while 'distance' not in nextp:   # wait for trimble 5500
                    time.sleep(2)
                    nextp = self.ts.GetMeasure()

                if 'v' not in nextp or 'distance' not in nextp:
                    break
                height = math.cos(nextp['v'].GetAngle()) * nextp['distance']
            if 'distance' in nextp and w:
                coord = self.ts.Coords()
                res = dict(nextp.items() + coord.items())
                wrt.WriteData(res)
            self.ts.MoveRel(self.stepinterval, Angle(0))
            act += self.stepinterval
        # rotate back to start
        self.ts.Move(startp['hz'], startp['v'])
        return 0

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.WARNING)
    # process commandline parameters
    if len(sys.argv) > 1:
        stepinterval = Angle(float(sys.argv[1]), 'DEG')
    else:
        stepinterval = Angle(45, 'DEG')
    if len(sys.argv) > 2:
        stationtype = sys.argv[2]
    else:
        stationtype = '1200'
    if len(sys.argv) > 3:
        port = sys.argv[3]
    else:
        port = '/dev/ttyUSB0'
    if len(sys.argv) > 4:
        maxa = float(sys.argv[4]) / 180.0 * math.pi
    else:
        maxa = PI2
    tol = 0.01
    if len(sys.argv) > 5:
        tol = float(sys.argv[5])
    maxiter = 10    # number of iterations to find point on horizontal plan
    if len(sys.argv) > 6:
        maxiter = int(sys.argv[6])
    iface = SerialIface("rs-232", port)
    if iface.state != iface.IF_OK:
        print("serial error")
        exit(1)
    if re.search('120[0-9]$', stationtype):
        mu = LeicaTPS1200()
    elif re.search('110[0-9]$', stationtype):
        mu = LeicaTCRA1100()
    elif re.search('550[0-9]$', stationtype):
        mu = Trimble5500()
        iface.eomRead = b'>'
    else:
        print("unsupported instrument type")
        exit(1)
    wrt = CsvWriter(angle='DMS', dist='.3f',
                    filt=['id', 'east', 'north', 'elev', 'hz', 'v', 'distance'],
                    fname='stdout', mode='a', sep=';')

    ts = TotalStation(stationtype, mu, iface)
    if isinstance(mu, Trimble5500):
        print("Set Trimble 550x to direct reflex (MNU 722) and press Enter")
        raw_input('')
    else:
        ts.SetEDMMode('RLSTANDARD') # reflectorless distance measurement
    h_sec = HorizontalSection(ts)
    h_sec.run()
