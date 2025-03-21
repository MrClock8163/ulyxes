#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
.. module:: measuretoprism.py

.. moduleauthor:: dr. Zoltan Siki <siki@agt.bme.hu>, Viktoria Zubaly, Daniel Moka <mokadaniel@citromail.hu>

Sample application of Ulyxes PyAPI to measure to a moving prism/object.
    Select different modes for different scenarios<br>
    0 - determine the horizontal movement of a bridge pylon without prism using
    edm mode RLSTANDARD<br>
    1 - determine the movement of a slowly moving prism to determine 3D defomation<br>
    2 - determine vertical movement of a prism, deflection of a bridge, we suppose horizontal distance is not changed (without lock ATR targeting before angles<br>
    3 - determine vertical movement of a moving prism, we suppose horizontal distance is not changedi (lock on prism)<br>
    4 - determine 3D movement of a moving prism on a car/machine (lock on prism)<br>
    5 - measure points if the prism stopped for 3-5 seconds (lock on prism)<br>

    :param argv[1] (sensor): 110n/180n/120n, default 1200
    :param argv[2] (mode): 0/1/2/3/4/5 without ATR/with ATR/with ATR no distance/lock single distance/lock with distance/store if stopped, default 4
    :param argv[3] (edm): edm mode STANDARD/FAST, default FAST
    :param argv[4] (port): serial port, use a filename for local iface, default COM7
    :param argv[5] (file): output file, data are appended to the end of the file
"""
import re
import sys
import logging
import math
import os.path
import signal

# check PYTHONPATH
if len([p for p in sys.path if 'pyapi' in p]) == 0:
    if os.path.isdir('../pyapi/'):
        sys.path.append('../pyapi/')
    else:
        print("pyapi not found")
        print("Add pyapi directory to the Python path or start your application from ulyxes/pyapps folder")
        sys.exit(1)

from angle import Angle
from serialiface import SerialIface
from totalstation import TotalStation
from localiface import LocalIface
from csvwriter import CsvWriter
from echowriter import EchoWriter
from leicatcra1100 import LeicaTCRA1100
from leicatca1800 import LeicaTCA1800
from leicatps1200 import LeicaTPS1200
from trimble5500 import Trimble5500
from axis10 import Axis10

def exit_on_ctrl_c(signal, frame):
    """ catch interrupt (Ctrl/C) and exit gracefully """
    print("\nCtrl/C was pressed, exiting...")
    sys.exit(0)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.ERROR)
    # Process command line parameters
    if len(sys.argv) == 1:
        print('Usage: {} instrument [mode [EDM_mode [serial [output_csv]]]]'.format(sys.argv[0]))
        exit()
    # Instrument type
    if len(sys.argv) > 1:
        if re.search('110[0-9]$', sys.argv[1]):
            mu = LeicaTCRA1100()
        elif re.search('180[0-9]$', sys.argv[1]):
            mu = LeicaTCA1800()
        elif re.search('120[0-9]$', sys.argv[1]):
            mu = LeicaTPS1200()
        elif re.search('550[0-9]$', sys.argv[1]):
            mu = Trimble5500()
        elif sys.argv[1]lower() == "axis10":
            mu = Axis10()
        else:
            mu = LeicaTPS1200()
    else:
        mu = LeicaTPS1200()

    # Measure mode
    mode = 4   # lock with distance measurement
    if len(sys.argv) > 2:
        try:
            mode = int(sys.argv[2])
        except ValueError:
            mode = 4
    # EDM mode
    edm = 'FAST'
    if len(sys.argv) > 3:
        edm = sys.argv[3]
    # Serial port
    com = '/dev/ttyUSB0'
    if len(sys.argv) > 4:
        com = sys.argv[4]
    if re.search('^COM[0-9]+', com) or re.search('^/dev/.*tty', com):
        iface = SerialIface("rs-232", com)
    else:
        iface = LocalIface("testIface", com) # Local iface for testing the module

    if iface.state != iface.IF_OK:
        sys.exit(1)
    # Writer
    if len(sys.argv) > 5:
        wrt = CsvWriter(angle='GON', dist='.3f', dt='%Y-%m-%d %H:%M:%S.%f',
                        filt=['id', 'datetime', 'hz', 'v', 'distance', 'east', 'north', 'elev'],
                        fname=sys.argv[5], mode='a', sep=';')
    else:
        wrt = EchoWriter(angle='GON', dist='.3f', dt='%Y-%m-%d %H:%M:%S.%f',
                         filt=['id', 'datetime', 'hz', 'v', 'distance', 'east', 'north', 'elev'])
    signal.signal(signal.SIGINT, exit_on_ctrl_c)    # catch Ctrl/C
    ts = TotalStation("Leica", mu, iface)
    slopeDist = 0
    if edm not in mu.edmModes:
        edm = 'FAST'
    ts.SetEDMMode(edm)
    # initialize instrument and variables
    if mode > 0:
        ts.SetLock(0)
        ts.SetATR(1)
        ts.MoveRel(Angle(0), Angle(0), 1)
        ts.Measure()
        measurement = ts.GetMeasure()
        if 'distance' in measurement:
            slopeDist = measurement['distance']

        if mode in (3, 4, 5):
            ts.SetLock(1)
            ts.LockIn()
            if mode == 5:
                last_hz = measurement['hz'] # direction of last measured point
                last_v = measurement['v']
                prev_hz = measurement['hz'] # direction of last measured point
                prev_v = measurement['v']
                moving = True
                limit = Angle('0-03-00', 'DMS') # minimal angle change to measure
                n = 0
    else:
        try:
            ts.SetATR(0)
        except:
            pass

    # infinite loop of measuring
    while ts.measureIface.state == ts.measureIface.IF_OK:
        if mode == 0:
            ts.Measure() # distance measurement without ATR
            measurement = ts.GetMeasure()
        elif mode == 1:
            ts.MoveRel(Angle(0), Angle(0), 1)  # aim on target with ATR
            ts.Measure()
            measurement = ts.GetMeasure()
        elif mode == 2:
            # aim on target with ATR without distance measurements
            ts.MoveRel(Angle(0), Angle(0), 1)
            measurement = ts.GetAngles()
        elif mode == 3:
            measurement = ts.GetAngles() # get angles only
        elif mode == 4:
            # get distance measurement with targeting mode
            ts.Measure()
            measurement = ts.GetMeasure()
        elif mode == 5:
            # go and stop, store full measurements within the limitation
            measurement = ts.GetAngles()

            if moving:
                if abs(prev_hz.GetAngle() - measurement['hz'].GetAngle()) < limit.GetAngle() and \
                   abs(prev_v.GetAngle() - measurement['v'].GetAngle()) < limit.GetAngle():
                    n += 1
                    # store if the measured values within the angle limitation three times
                    if n <= 3:
                        continue
                    ts.Measure()
                    measurement = ts.GetMeasure()
                    moving = False # approximately standing
                    last_hz = measurement['hz'] # direction of last stored point
                    last_v = measurement['v']
                    prev_hz = measurement['hz'] # direction of last examined point
                    prev_v = measurement['v']
                    n = 0 # start counting again if the last examind point is stored
                else:
                    prev_hz = measurement['hz']
                    prev_v = measurement['v']
                    continue
            else:
                if abs(last_hz.GetAngle() - measurement['hz'].GetAngle()) >= limit.GetAngle() or \
                   abs(last_v.GetAngle() - measurement['v'].GetAngle()) >= limit.GetAngle():
                    moving = True # still moving
                continue

        #  Get each measurement data
        if 'distance' in measurement:  # Check existance of 'distance' key
            slopeDist = measurement['distance']
        if 'hz' in measurement:  # Check existence of 'hz' key
            hz = measurement['hz']
        if 'v' in measurement:  # Check existence of 'v' key
            v = measurement['v']

        # Compute relative coordinates according to the instrument origin
        if 'hz' in measurement and 'v' in measurement:
            measurement['east'] = slopeDist * math.sin(v.GetAngle()) * \
                math.sin(hz.GetAngle())
            measurement['north'] = slopeDist * math.sin(v.GetAngle()) * \
                math.cos(hz.GetAngle())
            measurement['elev'] = slopeDist * math.cos(v.GetAngle())

            # Store in file the measurements
            wrt.WriteData(measurement)
            #print(measurement)
        else:
            print("Some measurement data(s) are missing...")
