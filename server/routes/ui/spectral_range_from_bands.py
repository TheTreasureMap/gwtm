"""Update spectral range from selected bands endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db

router = APIRouter(tags=["UI"])


@router.get("/ajax_update_spectral_range_from_selected_bands")
async def spectral_range_from_selected_bands(
    band_cov: str, spectral_type: str, spectral_unit: str, db: Session = Depends(get_db)
):
    """Calculate spectral range based on selected bands."""
    from server.core.enums.wavelengthunits import WavelengthUnits
    from server.core.enums.energyunits import EnergyUnits
    from server.core.enums.frequencyunits import FrequencyUnits
    from server.core.enums.bandpass import Bandpass

    if not band_cov or band_cov == "null":
        return {"total_min": "", "total_max": ""}

    # Split bands
    bands = band_cov.split(",")
    mins, maxs = [], []

    for b in bands:
        try:
            # Find the bandpass enum value
            band_enum = [x for x in Bandpass if b == x.name][0]
            band_min, band_max = None, None

            # Handle different spectral types
            if spectral_type == "wavelength":
                # Get wavelength range for this band
                from server.utils.spectral import wavetoWaveRange

                band_min, band_max = wavetoWaveRange(bandpass_enum=band_enum)
                # Get the scale factor for the requested unit
                # Handle unit name aliases (nm -> nanometer)
                unit_name = spectral_unit
                if spectral_unit == "nm":
                    unit_name = "nanometer"
                unit = [x for x in WavelengthUnits if unit_name == x.name][0]
                scale = WavelengthUnits.get_scale(unit)

            elif spectral_type == "energy":
                # Get energy range for this band
                from server.utils.spectral import wavetoEnergy

                band_min, band_max = wavetoEnergy(bandpass_enum=band_enum)
                # Get the scale factor for the requested unit
                unit = [x for x in EnergyUnits if spectral_unit == x.name][0]
                scale = EnergyUnits.get_scale(unit)

            elif spectral_type == "frequency":
                # Get frequency range for this band
                from server.utils.spectral import wavetoFrequency

                band_min, band_max = wavetoFrequency(bandpass_enum=band_enum)
                # Get the scale factor for the requested unit
                unit = [x for x in FrequencyUnits if spectral_unit == x.name][0]
                scale = FrequencyUnits.get_scale(unit)

            # If we got valid values, append them to our lists
            if band_min is not None and band_max is not None:
                mins.append(band_min / scale)
                maxs.append(band_max / scale)

        except (IndexError, ValueError):
            # Skip invalid bands
            continue

    # Return the overall range
    if mins:
        return {"total_min": min(mins), "total_max": max(maxs)}
    else:
        return {"total_min": "", "total_max": ""}
