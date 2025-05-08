"""
Spectral range utilities for the GWTM application.
These functions handle conversions between different spectral representations
like wavelength, frequency, and energy.
"""

from typing import Tuple, Optional
import numpy as np
from server.core.enums.bandpass import bandpass

# Constants
SPEED_OF_LIGHT = 299792458  # m/s
PLANCK_CONSTANT = 6.62607015e-34  # J*s
ELECTRON_VOLT = 1.602176634e-19  # J

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

def wavetoWaveRange(bandpass: bandpass) -> Tuple[float, float]:
    """
    Get the wavelength range for a specific bandpass.
    
    Args:
        bandpass: Bandpass enum value
    
    Returns:
        Tuple of (min_wavelength, max_wavelength) in Angstroms
    """
    # Define wavelength ranges for common bandpass filters
    bandpass_ranges = {
        'U': (3000, 4000),      # U band: ~300-400 nm
        'B': (3800, 5000),      # B band: ~380-500 nm
        'V': (5000, 6000),      # V band: ~500-600 nm
        'R': (5700, 7000),      # R band: ~570-700 nm
        'I': (7000, 9000),      # I band: ~700-900 nm
        'J': (11000, 14000),    # J band: ~1.1-1.4 μm
        'H': (15000, 18000),    # H band: ~1.5-1.8 μm
        'K': (20000, 24000),    # K band: ~2.0-2.4 μm
        'g': (4000, 5500),      # g band: ~400-550 nm
        'r': (5500, 7000),      # r band: ~550-700 nm
        'i': (7000, 8500),      # i band: ~700-850 nm
        'z': (8500, 9500),      # z band: ~850-950 nm
        'y': (9500, 10700),     # y band: ~950-1070 nm
        'X-ray': (0.1, 100),    # X-ray: ~0.01-10 nm
        'UV': (1000, 4000),     # UV: ~100-400 nm
        'Optical': (4000, 7000), # Optical: ~400-700 nm
        'IR': (7000, 300000),   # IR: ~0.7-30 μm
        'Radio': (1e9, 1e12)    # Radio: ~0.1-100 m (in Angstroms)
    }
    
    band_name = bandpass.name
    if band_name in bandpass_ranges:
        return bandpass_ranges[band_name]
    
    # Return a default range if band not found
    return (4000, 7000)  # Default to optical range

def wavetoEnergy(bandpass: bandpass) -> Tuple[float, float]:
    """
    Get the energy range for a specific bandpass.
    
    Args:
        bandpass: Bandpass enum value
    
    Returns:
        Tuple of (min_energy, max_energy) in eV
    """
    # Get wavelength range in Angstroms
    wave_min, wave_max = wavetoWaveRange(bandpass)
    
    # Convert to energy (shorter wavelength = higher energy)
    energy_max = waveToEnergy(wave_min)
    energy_min = waveToEnergy(wave_max)
    
    return (energy_min, energy_max)

def wavetoFrequency(bandpass: bandpass) -> Tuple[float, float]:
    """
    Get the frequency range for a specific bandpass.
    
    Args:
        bandpass: Bandpass enum value
    
    Returns:
        Tuple of (min_frequency, max_frequency) in Hz
    """
    # Get wavelength range in Angstroms
    wave_min, wave_max = wavetoWaveRange(bandpass)
    
    # Convert to frequency (shorter wavelength = higher frequency)
    freq_max = waveToFreq(wave_min)
    freq_min = waveToFreq(wave_max)
    
    return (freq_min, freq_max)