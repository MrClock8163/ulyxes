import math
import re
from enum import Enum, auto
from typing import Self


__all__ = [
    "RO",
    "PI2",
    "AngleUnit",
    "Angle"
]


RO = 180 * 60 * 60 / math.pi
"""RAD-SEC conversion coefficient"""

PI2 = 2 * math.pi
"""Full angle in RAD"""


class AngleUnit(Enum):
    RAD = auto()
    """Radians"""

    DEG = auto()
    """Degrees"""

    PDEG = auto()
    """Pseudo-degrees (DD.MMSS)"""

    GON = auto()
    """Gradians"""

    MIL = auto()
    """NATO milliradians (6400 mils per circle)"""

    SEC = auto()
    """Arcseconds"""

    DMS = auto()
    """DDD-MM-SS"""

    NMEA = auto()
    """NMEA degrees (DDMM.MMMM)"""


class Angle:
    @staticmethod
    def deg2rad(angle: float) -> float:
        """ Convert DEG to RAD
        """
        return math.radians(angle)

    @staticmethod
    def gon2rad(angle: float) -> float:
        """ Convert GON to RAD
        """
        return angle / 200 * math.pi

    @staticmethod
    def dms2rad(dms: str) -> float:
        """ Convert DMS to RAD
        """
        if not re.search("^[0-9]{1,3}(-[0-9]{1,2}){0,2}$", dms):
            raise ValueError("Angle invalid argument", dms)
        
        items = [float(item) for item in dms.split("-")]
        div = 1
        a = 0
        for val in items:
            a += val / div
            div *= 60

        return math.radians(a)

    @staticmethod
    def dm2rad(angle: float) -> float:
        """ Convert DDMM.nnnnnn NMEA angle to radian"
        """
        w = angle / 100
        d = int(w)
        return math.radians(d + (w - d) * 100 / 60)

    @staticmethod
    def pdeg2rad(angle: float) -> float:
        """ Convert dd.mmss to radian
        """
        d = math.floor(angle)
        angle = round((angle - d) * 100, 10)
        m = math.floor(angle)
        s = round((angle - m) * 100, 10)
        return math.radians(d + m / 60 + s / 3600)

    @staticmethod
    def sec2rad(angle: float) -> float:
        """ Convert seconds to radian
        """
        return angle / RO

    @staticmethod
    def mil2rad(angle: float) -> float:
        """ Convert mills to radian
        """
        return angle / 6400 * 2 * math.pi

    @staticmethod
    def rad2gon(angle: float) -> float:
        """ Convert radian to GON
        """
        return angle / math.pi * 200

    @staticmethod
    def rad2sec(angle: float) -> float:
        """ Convert radian to seconds
        """
        return angle * RO

    @staticmethod
    def rad2deg(angle: float) -> float:
        """ Convert radian to decimal degrees
        """
        return math.degrees(angle)

    @staticmethod
    def rad2dms(angle: float) -> str:
        """ Convert radian to DMS
        """
        signum = "-" if angle < 0 else ""
        secs = round(abs(angle) * RO)
        mi, sec = divmod(secs, 60)
        deg, mi = divmod(mi, 60)
        deg = int(deg)
        return f"{signum:s}{deg:d}-{mi:02d}-{sec:02d}"

    @staticmethod
    def rad2dm(angle: float) -> float:
        """ Convert radian to NMEA DDDMM.nnnnn
        """
        w = angle / math.pi * 180.0
        d = int(w)
        return d * 100 + (w - d) * 60

    @staticmethod
    def rad2pdeg(angle: float) -> float:
        """ Convert radian to pseudo DMS ddd.mmss
        """
        secs = round(angle * RO)
        mi, sec = divmod(secs, 60)
        deg, mi = divmod(mi, 60)
        deg = int(deg)
        return deg + mi / 100 + sec / 10000

    @staticmethod
    def rad2mil(angle: float) -> float:
        """ Convert radian to mills
        """
        return angle / math.pi / 2 * 6400
    
    @staticmethod
    def normalize_rad(angle: float, positive: float = False) -> float:
        norm = angle % PI2

        if not positive and angle < 0:
            norm -= PI2
        
        return norm

    def __init__(self, value: float | str, unit: AngleUnit | str = AngleUnit.RAD, /, normalize: bool = False, positive: bool = False):
        """ Constructor for an angle instance.
        """
        
        self._value: float = 0
        if type(unit) is str:
            try:
                unit = AngleUnit[unit]
            except KeyError as e:
                raise ValueError(f"unknown source unit: {unit}") from e

        match unit, value:
            case AngleUnit.RAD, float() | int():
                self._value = value
            case AngleUnit.DEG, float() | int():
                self._value = self.deg2rad(value)
            case AngleUnit.PDEG, float() | int():
                self._value = self.pdeg2rad(value)
            case AngleUnit.GON, float() | int():
                self._value = self.gon2rad(value)
            case AngleUnit.MIL, float() | int():
                self._value = self.mil2rad(value)
            case AngleUnit.SEC, float() | int():
                self._value = self.sec2rad(value)
            case AngleUnit.DMS, str():
                self._value = self.dms2rad(value)
            case AngleUnit.NMEA, float() | int():
                self._value = self.dm2rad(value)
            case _:
                raise ValueError(f"unknown source unit and value type pair: {unit} - {type(value).__name__}")
        
        if normalize:
            self._value = self.normalize_rad(self._value, positive)
    
    def __str__(self) -> str:
        return f"{self.asunit(AngleUnit.GON):.4f}"
    
    def __repr__(self) -> str:
        return f"({type(self).__name__:s}{self._value:f})"
    
    def __pos__(self) -> Self:
        return Angle(self._value)
    
    def __neg__(self) -> Self:
        return Angle(-self._value)
    
    def __add__(self, other: Self) -> Self:
        if type(other) is not Angle:
            raise TypeError(f"unsupported operand type(s) for +: 'Angle' and '{type(other).__name__}'")
        
        return Angle(self._value + other._value)
    
    def __iadd__(self, other: Self) -> Self:
        if type(other) is not Angle:
            raise TypeError(f"unsupported operand type(s) for +=: 'Angle' and '{type(other).__name__}'")
        
        self._value += other._value
        return self
    
    def __sub__(self, other: Self) -> Self:
        if type(other) is not Angle:
            raise TypeError(f"unsupported operand type(s) for -: 'Angle' and '{type(other).__name__}'")
        
        return Angle(self._value - other._value)
    
    def __isub__(self, other: Self) -> Self:
        if type(other) is not Angle:
            raise TypeError(f"unsupported operand type(s) for -=: 'Angle' and '{type(other).__name__}'")
        
        self._value -= other._value
        return self
    
    def __mul__(self, other: int | float) -> Self:
        if type(other) not in (int, float):
            raise TypeError(f"unsupported operand type(s) for *: 'Angle' and '{type(other).__name__}'")
        
        return Angle(self._value * other)
    
    def __imul__(self, other: int | float) -> Self:
        if type(other) not in (int, float):
            raise TypeError(f"unsupported operand type(s) for *=: 'Angle' and '{type(other).__name__}'")
        
        self._value *= other
        return self
    
    def __truediv__(self, other: int | float) -> Self:
        if type(other) not in (int, float):
            raise TypeError(f"unsupported operand type(s) for /: 'Angle' and '{type(other).__name__}'")
        
        return Angle(self._value / other)
    
    def __itruediv__(self, other: int | float) -> Self:
        if type(other) not in (int, float):
            raise TypeError(f"unsupported operand type(s) for /=: 'Angle' and '{type(other).__name__}'")
        
        self._value /= other
        return self
    
    def __abs__(self) -> Self:
        return self.normalized()
    
    def asunit(self, unit: AngleUnit | str = AngleUnit.RAD) -> float | str:
        if type(unit) is str:
            try:
                unit = AngleUnit[unit]
            except KeyError as e:
                raise ValueError(f"unknown target unit: {unit}") from e

        match unit:
            case AngleUnit.RAD:
                return self._value
            case AngleUnit.DEG:
                return self.rad2deg(self._value)
            case AngleUnit.PDEG:
                return self.rad2pdeg(self._value)
            case AngleUnit.GON:
                return self.rad2gon(self._value)
            case AngleUnit.MIL:
                return self.rad2mil(self._value)
            case AngleUnit.SEC:
                return self.rad2sec(self._value)
            case AngleUnit.DMS:
                return self.rad2dms(self._value)
            case AngleUnit.NMEA:
                return self.rad2dm(self._value)
            case _:
                raise ValueError(f"unknown target unit: {unit}")
    
    def normalized(self, positive: bool = True) -> Self:
        return Angle(self._value, AngleUnit.RAD, True, positive)
