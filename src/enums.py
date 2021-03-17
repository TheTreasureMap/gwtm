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
    I = 5
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


class gw_galaxy_score_type(IntEnum):
    default = 1
