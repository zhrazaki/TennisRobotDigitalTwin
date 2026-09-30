"""
Purpose:
    Pure unit-conversion helpers. Official tennis court dimensions are
    published in feet/inches (ITF Rules of Tennis). Unreal Engine works
    in centimeters (1 Unreal Unit = 1 cm, UE5 default). This module is
    the ONLY place unit-conversion math is allowed to happen; every
    other file must call into these functions instead of hand-rolling
    conversions.

Dependencies:
    None (standard library only, no `unreal` import). This keeps the
    module usable outside the Editor (unit tests, other tools, other AIs).

Inputs:
    Plain numbers (int/float) in feet, inches, or meters.

Outputs:
    Plain numbers (float) in centimeters == Unreal Units.
"""

# --- Base conversion constants -------------------------------------------
CM_PER_INCH = 2.54
CM_PER_FOOT = 30.48
CM_PER_METER = 100.0

# 1 Unreal Unit = 1 centimeter (project-wide convention, UE5 default).
# Kept explicit and named so no file ever hardcodes the "1.0" magic number.
UE_UNITS_PER_CM = 1.0


def feet_to_cm(feet: float) -> float:
    """Convert feet to centimeters (== Unreal Units)."""
    return feet * CM_PER_FOOT


def inches_to_cm(inches: float) -> float:
    """Convert inches to centimeters (== Unreal Units)."""
    return inches * CM_PER_INCH


def meters_to_cm(meters: float) -> float:
    """Convert meters to centimeters (== Unreal Units)."""
    return meters * CM_PER_METER


def cm_to_uu(cm: float) -> float:
    """
    Convert centimeters to Unreal Units.
    Exists for readability at call sites (e.g. mesh generation code)
    even though the factor is currently 1.0 — if that project-wide
    convention ever changes, only this function needs to change.
    """
    return cm * UE_UNITS_PER_CM


def cm_to_feet(cm: float) -> float:
    """Convert centimeters back to feet (useful for validation/printing)."""
    return cm / CM_PER_FOOT


def cm_to_inches(cm: float) -> float:
    """Convert centimeters back to inches (useful for validation/printing)."""
    return cm / CM_PER_INCH
