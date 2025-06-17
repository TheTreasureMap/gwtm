"""
Spectral range utilities for the GWTM application.
These functions handle conversions between different spectral representations
like wavelength, frequency, and energy.
"""

from typing import Tuple, Optional
import numpy as np
from server.core.enums.bandpass import Bandpass
from enum import IntEnum

# Constants
SPEED_OF_LIGHT = 299792458  # m/s
PLANCK_CONSTANT = 6.62607015e-34  # J*s
ELECTRON_VOLT = 1.602176634e-19  # J


class SpectralRangeHandler:
    """
    Values for the central wave and bandwidth were taken from:
        http://svo2.cab.inta-csic.es/theory/fps/index.php?mode=browse
        notated by the 'source' field in the following dictionary
        for central_wavelength I used the lam_cen
        for bandwidth I used the FWHM

    Our base for the central wavelengths and bandwidths will be stored in
        Angstroms

    There are following static methods to convert the Angstrom values into ranges for
        frequency in Hz
        energy in eV
    """

    class spectralrangetype(IntEnum):
        wavelength = 1
        energy = 2
        frequency = 3

    # Bandpass wavelength dictionary with central wavelengths and bandwidths in Angstroms
    bandpass_wavelength_dictionary = {
        Bandpass.U: {
            'source': 'CTIO/SOI.bessel_U',
            'central_wave': 3614.82,
            'bandwidth': 617.24
        },
        Bandpass.B: {
            'source': 'CTIO/SOI.bessel_B',
            'central_wave': 4317.0,
            'bandwidth': 991.48
        },
        Bandpass.V: {
            'source': 'CTIO/SOI.bessel_V',
            'central_wave': 5338.65,
            'bandwidth': 810.65
        },
        Bandpass.R: {
            'source': 'CTIO/SOI.bessel_R',
            'central_wave': 6311.86,
            'bandwidth': 1220.89
        },
        Bandpass.I: {
            'source': 'CTIO/SOI.bessel_I',
            'central_wave': 8748.91,
            'bandwidth': 2940.57
        },
        Bandpass.J: {
            'source': 'CTIO/ANDICAM/J',
            'central_wave': 12457.00,
            'bandwidth': 1608.86
        },
        Bandpass.H: {
            'source': 'CTIO/ANDICAM/H',
            'central_wave': 16333.11,
            'bandwidth': 2969.21
        },
        Bandpass.K: {
            'source': 'CTIO/ANDICAM/K',
            'central_wave': 21401.72,
            'bandwidth': 2894.54
        },
        Bandpass.u: {
            'source': 'CTIO/DECam.u_filter',
            'central_wave': 3552.98,
            'bandwidth': 885.05
        },
        Bandpass.g: {
            'source': 'CTIO/DECam.g_filter',
            'central_wave': 4730.50,
            'bandwidth': 1503.06
        },
        Bandpass.r: {
            'source': 'CTIO/DECam.r_filter',
            'central_wave': 6415.40,
            'bandwidth': 1487.58
        },
        Bandpass.i: {
            'source': 'CTIO/DECam.i_filter',
            'central_wave': 7836.21,
            'bandwidth': 1468.29
        },
        Bandpass.z: {
            'source': 'CTIO/DECam.z_filter',
            'central_wave': 9258.37,
            'bandwidth': 1521.09
        },
        Bandpass.UVW1: {
            'source': 'Swift/UVOT.UVW1',
            'central_wave': 2629.35,
            'bandwidth': 656.60
        },
        Bandpass.UVW2: {
            'source': 'Swift/UVOT.UVW2',
            'central_wave': 2089.16,
            'bandwidth': 498.25
        },
        Bandpass.UVM2: {
            'source': 'Swift/UVOT.UVM2',
            'central_wave': 2245.78,
            'bandwidth': 498.25
        },
        Bandpass.clear: {
            'source': 'Generic/clear',
            'central_wave': 2634.44,
            'bandwidth': 3230.16
        },
        Bandpass.open: {
            'source': 'Generic/open',
            'central_wave': 5500.0,
            'bandwidth': 8000.0
        },
        Bandpass.other: {
            'source': 'Generic/other',
            'central_wave': 5500.0,
            'bandwidth': 8000.0
        }
    }

    @staticmethod
    def wavetoWaveRange(central_wave=None, bandwidth=None, bandpass_enum=None):
        """Method that returns the wavelength range from the central_wave and bandwidth, or bandpass"""
        if central_wave is None and bandwidth is None and bandpass_enum is not None:
            bp = SpectralRangeHandler.bandpass_wavelength_dictionary[bandpass_enum]
            central_wave = bp['central_wave']
            bandwidth = bp['bandwidth']

        wave_min = central_wave - (bandwidth / 2.0)
        wave_max = central_wave + (bandwidth / 2.0)

        return wave_min, wave_max

    @staticmethod
    def wavetoEnergy(central_wave=None, bandwidth=None, bandpass_enum=None):
        """Method that returns the corresponding wave range to energy in eV"""
        wave_min, wave_max = SpectralRangeHandler.wavetoWaveRange(central_wave, bandwidth, bandpass_enum)

        ev_max = 12398 / wave_min
        ev_min = 12398 / wave_max

        return ev_min, ev_max

    @staticmethod
    def wavetoFrequency(central_wave=None, bandwidth=None, bandpass_enum=None):
        """Method that returns the corresponding wave range to frequency in Hz"""
        wave_min, wave_max = SpectralRangeHandler.wavetoWaveRange(central_wave, bandwidth, bandpass_enum)

        freq_max = 2997924580000000000.0 / wave_min
        freq_min = 2997924580000000000.0 / wave_max

        return freq_min, freq_max

def waveToFreq(wave: float) -> float:
    """
    Convert wavelength (in Angstroms) to frequency (in Hz).
    
    Args:
        wave: Wavelength in Angstroms
    
    Returns:
        Frequency in Hz
    """
    wavelength_m = wave * 1e-10  # Convert from Angstroms to meters
    return SPEED_OF_LIGHT / wavelength_m

def freqToWave(freq: float) -> float:
    """
    Convert frequency (in Hz) to wavelength (in Angstroms).
    
    Args:
        freq: Frequency in Hz
    
    Returns:
        Wavelength in Angstroms
    """
    wavelength_m = SPEED_OF_LIGHT / freq  # Wavelength in meters
    return wavelength_m * 1e10  # Convert to Angstroms

def waveToEnergy(wave: float) -> float:
    """
    Convert wavelength (in Angstroms) to energy (in eV).
    
    Args:
        wave: Wavelength in Angstroms
    
    Returns:
        Energy in eV
    """
    wavelength_m = wave * 1e-10  # Convert from Angstroms to meters
    freq = SPEED_OF_LIGHT / wavelength_m  # Calculate frequency
    energy_J = PLANCK_CONSTANT * freq  # Calculate energy in Joules
    return energy_J / ELECTRON_VOLT  # Convert to eV

def energyToWave(energy: float) -> float:
    """
    Convert energy (in eV) to wavelength (in Angstroms).
    
    Args:
        energy: Energy in eV
    
    Returns:
        Wavelength in Angstroms
    """
    energy_J = energy * ELECTRON_VOLT  # Convert to Joules
    freq = energy_J / PLANCK_CONSTANT  # Calculate frequency
    wavelength_m = SPEED_OF_LIGHT / freq  # Calculate wavelength in meters
    return wavelength_m * 1e10  # Convert to Angstroms

def freqToEnergy(freq: float) -> float:
    """
    Convert frequency (in Hz) to energy (in eV).
    
    Args:
        freq: Frequency in Hz
    
    Returns:
        Energy in eV
    """
    energy_J = PLANCK_CONSTANT * freq  # Calculate energy in Joules
    return energy_J / ELECTRON_VOLT  # Convert to eV

def energyToFreq(energy: float) -> float:
    """
    Convert energy (in eV) to frequency (in Hz).
    
    Args:
        energy: Energy in eV
    
    Returns:
        Frequency in Hz
    """
    energy_J = energy * ELECTRON_VOLT  # Convert to Joules
    return energy_J / PLANCK_CONSTANT  # Calculate frequency

def wavetoWaveRange(bandpass_enum: Bandpass = None, central_wave: float = None, bandwidth: float = None) -> Tuple[float, float]:
    """
    Get the wavelength range for a specific bandpass using SpectralRangeHandler.
    
    Args:
        bandpass_enum: Bandpass enum value
        central_wave: Central wavelength in Angstroms (alternative to bandpass)
        bandwidth: Bandwidth in Angstroms (alternative to bandpass)
    
    Returns:
        Tuple of (min_wavelength, max_wavelength) in Angstroms
    """
    return SpectralRangeHandler.wavetoWaveRange(central_wave, bandwidth, bandpass_enum)

def wavetoEnergy(bandpass_enum: Bandpass = None, central_wave: float = None, bandwidth: float = None) -> Tuple[float, float]:
    """
    Get the energy range for a specific bandpass using SpectralRangeHandler.
    
    Args:
        bandpass_enum: Bandpass enum value
        central_wave: Central wavelength in Angstroms (alternative to bandpass)
        bandwidth: Bandwidth in Angstroms (alternative to bandpass)
    
    Returns:
        Tuple of (min_energy, max_energy) in eV
    """
    return SpectralRangeHandler.wavetoEnergy(central_wave, bandwidth, bandpass_enum)

def wavetoFrequency(bandpass_enum: Bandpass = None, central_wave: float = None, bandwidth: float = None) -> Tuple[float, float]:
    """
    Get the frequency range for a specific bandpass using SpectralRangeHandler.
    
    Args:
        bandpass_enum: Bandpass enum value
        central_wave: Central wavelength in Angstroms (alternative to bandpass)
        bandwidth: Bandwidth in Angstroms (alternative to bandpass)
    
    Returns:
        Tuple of (min_frequency, max_frequency) in Hz
    """
    return SpectralRangeHandler.wavetoFrequency(central_wave, bandwidth, bandpass_enum)