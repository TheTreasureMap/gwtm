from enum import IntEnum

class bandpass(IntEnum):
    """Enumeration for bandpasses."""
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