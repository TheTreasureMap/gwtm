# -*- coding: utf-8 -*-
from enum import IntEnum

class depth_unit(IntEnum):
    ab_mag = 1
    vega_mag = 2
    flux_erg = 3
    flux_jy = 4

    def __str__(self):
        split_name = str(self.name).split('_')
        return str.upper(split_name[0]) + ' ' + split_name[1]


class pointing_status(IntEnum):
    planned = 1
    completed = 2
    cancelled = 3


class instrument_type(IntEnum):
    photometric = 1
    spectroscopic = 2


class bandpass(IntEnum):
    U = 1
    B = 2
    V = 3
    R = 4
    I = 5  # noqa: E741
    J = 6
    H = 7
    K = 8
    u = 9
    g = 10
    r = 11
    i = 12
    z = 13
    UVW1 = 14
    UVW2 = 15
    UVM2 = 16
    XRT = 17
    clear = 18
    open = 19
    UHF = 20
    VHF = 21
    L = 22
    S = 23
    C = 24
    X = 25
    other = 26
    TESS = 27
    BAT = 28
    HESS = 29
    WISEL = 30
    q = 31


class wavelength_units(IntEnum):
    nanometer = 1
    angstrom = 2
    micron = 3

    @staticmethod
    def get_scale(unit):
        if unit == wavelength_units.nanometer:
            return 10.0
        if unit == wavelength_units.angstrom:
            return 1.0
        if unit == wavelength_units.micron:
            return 10000.0


class energy_units(IntEnum):
    eV = 1
    keV = 2
    MeV = 3
    GeV = 4
    TeV = 5

    @staticmethod
    def get_scale(unit):
        if unit == energy_units.eV:
            return 1.0
        if unit == energy_units.keV:
            return 1000.0
        if unit == energy_units.MeV:
            return 1000000.0
        if unit == energy_units.GeV:
            return 1000000000.0
        if unit == energy_units.TeV:
            return 1000000000000.0


class frequency_units(IntEnum):
    Hz = 1
    kHz = 2
    GHz = 3
    MHz = 4
    THz = 5

    @staticmethod
    def get_scale(unit):
        if unit == frequency_units.Hz:
            return 1.0
        if unit == frequency_units.kHz:
            return 1000.0
        if unit == frequency_units.MHz:
            return 1000000.0
        if unit == frequency_units.GHz:
            return 1000000000.0
        if unit == frequency_units.THz:
            return 1000000000000.0


class gw_galaxy_score_type(IntEnum):
    default = 1
