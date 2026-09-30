"""
Purpose:
    Central, authoritative court configuration. Loads the raw official
    dimensions from Data/court_dimensions.json, converts everything to
    centimeters (== Unreal Units) via Core/units.py, computes the small
    set of derived values every other phase needs (half-lengths, insets,
    box sizes, etc.), and self-validates for internal consistency.

    Every later phase (surface, lines, net, fence, lighting...) must
    read dimensions from THIS module. No file outside Core/ should ever
    contain a hardcoded court number.

Dependencies:
    - Python/Core/units.py            (unit conversion)
    - Data/court_dimensions.json      (raw source numbers)
    - Standard library only (json, os) — no `unreal` import, so this
      file can be loaded and unit-tested outside the Editor.

Inputs:
    Optional explicit path to a dimensions JSON file (defaults to
    Data/court_dimensions.json, resolved relative to this file's
    location assuming the suggested project layout: <root>/Python/Core/
    and <root>/Data/).

Outputs:
    - CourtConfig class: typed access to every court dimension in cm.
    - get_court_config(): cached singleton accessor used by every
      other module (e.g. coordinate_system.py).
"""

import json
import os

from Core import units


class CourtConfigError(Exception):
    """Raised when the dimensions data file is missing or inconsistent."""
    pass


def _default_data_path() -> str:
    """
    Resolve Data/court_dimensions.json relative to this file, assuming
    the suggested layout:
        <project_root>/Python/Core/court_config.py   (this file)
        <project_root>/Data/court_dimensions.json
    """
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(here, "..", ".."))
    return os.path.join(project_root, "Data", "court_dimensions.json")


class CourtConfig:
    """
    Typed, validated, cm-based view of the official tennis court
    dimensions. Construct via get_court_config() rather than directly,
    so the whole project shares one instance.
    """

    # Tolerance used for internal cross-checks (floating point safety).
    EPSILON_CM = 0.01

    def __init__(self, data_path: str = None):
        self.data_path = data_path or _default_data_path()
        raw = self._load_raw(self.data_path)

        # --- Raw dimensions, converted to centimeters -------------------
        self.court_length_cm = units.feet_to_cm(raw["court_length_ft"])
        self.doubles_width_cm = units.feet_to_cm(raw["doubles_width_ft"])
        self.singles_width_cm = units.feet_to_cm(raw["singles_width_ft"])

        self.service_line_distance_from_net_cm = units.feet_to_cm(
            raw["service_line_distance_from_net_ft"]
        )

        self.net_height_center_cm = units.feet_to_cm(raw["net_height_at_center_ft"])
        self.net_height_post_cm = units.feet_to_cm(raw["net_height_at_posts_ft"])
        self.net_post_offset_cm = units.feet_to_cm(
            raw["net_post_offset_from_doubles_sideline_ft"]
        )

        self.line_width_cm = units.inches_to_cm(raw["line_width_in"])
        self.baseline_width_cm = units.inches_to_cm(raw["baseline_width_in"])
        self.center_mark_length_cm = units.inches_to_cm(raw["center_mark_length_in"])
        # Center mark width follows the standard line width.
        self.center_mark_width_cm = self.line_width_cm

        self.recommended_backcourt_clearance_cm = units.feet_to_cm(
            raw["recommended_backcourt_clearance_ft"]
        )
        self.recommended_sidecourt_clearance_cm = units.feet_to_cm(
            raw["recommended_sidecourt_clearance_ft"]
        )

        # --- Derived values ----------------------------------------------
        self.half_length_cm = self.court_length_cm / 2.0
        self.half_doubles_width_cm = self.doubles_width_cm / 2.0
        self.half_singles_width_cm = self.singles_width_cm / 2.0

        # Gap between a doubles sideline and the singles sideline inside it.
        self.singles_sideline_inset_cm = (
            self.doubles_width_cm - self.singles_width_cm
        ) / 2.0

        # Distance from the baseline to the service line.
        self.baseline_to_service_line_cm = (
            self.half_length_cm - self.service_line_distance_from_net_cm
        )

        # Width of one service box (between center line and singles sideline).
        self.service_box_width_cm = self.half_singles_width_cm

        # Distance from court center (Y=0) to each net post.
        self.net_post_span_cm = self.half_doubles_width_cm + self.net_post_offset_cm

        self.validate()

    # ----------------------------------------------------------------- #
    @staticmethod
    def _load_raw(path: str) -> dict:
        if not os.path.isfile(path):
            raise CourtConfigError(
                "Court dimensions file not found at '{0}'. Expected the "
                "suggested layout <project_root>/Data/court_dimensions.json "
                "next to <project_root>/Python/.".format(path)
            )
        with open(path, "r") as f:
            return json.load(f)

    # ----------------------------------------------------------------- #
    def validate(self) -> None:
        """
        Cross-check derived values against independent computations.
        Raises CourtConfigError on any mismatch beyond EPSILON_CM.
        Every later phase can call this again after import to fail fast
        if the config was ever hand-edited into an inconsistent state.
        """
        checks = [
            (
                "singles width + 2*inset == doubles width",
                self.singles_width_cm + 2 * self.singles_sideline_inset_cm,
                self.doubles_width_cm,
            ),
            (
                "baseline-to-service-line + service-line-to-net == half length",
                self.baseline_to_service_line_cm + self.service_line_distance_from_net_cm,
                self.half_length_cm,
            ),
            (
                "2 * service box width == singles width",
                2 * self.service_box_width_cm,
                self.singles_width_cm,
            ),
        ]
        for description, computed, expected in checks:
            if abs(computed - expected) > self.EPSILON_CM:
                raise CourtConfigError(
                    "Consistency check failed: {0} (computed={1:.4f}cm, "
                    "expected={2:.4f}cm)".format(description, computed, expected)
                )

    # ----------------------------------------------------------------- #
    def summary(self) -> str:
        """Human-readable dump of every dimension, in cm and feet, for logs."""
        rows = [
            ("Court length", self.court_length_cm),
            ("Doubles width", self.doubles_width_cm),
            ("Singles width", self.singles_width_cm),
            ("Service line distance from net", self.service_line_distance_from_net_cm),
            ("Baseline to service line", self.baseline_to_service_line_cm),
            ("Singles sideline inset", self.singles_sideline_inset_cm),
            ("Net height (center)", self.net_height_center_cm),
            ("Net height (posts)", self.net_height_post_cm),
            ("Net post span from center (Y)", self.net_post_span_cm),
            ("Standard line width", self.line_width_cm),
            ("Baseline width", self.baseline_width_cm),
            ("Center mark length", self.center_mark_length_cm),
        ]
        lines = ["CourtConfig summary (cm / ft):"]
        for label, value_cm in rows:
            lines.append(
                "  {0:<34} {1:9.2f} cm  ({2:6.2f} ft)".format(
                    label, value_cm, units.cm_to_feet(value_cm)
                )
            )
        return "\n".join(lines)


# --------------------------------------------------------------------- #
# Module-level singleton accessor. Every other module should call
# get_court_config() rather than instantiating CourtConfig() directly,
# so the whole project shares one validated instance.
# --------------------------------------------------------------------- #
_court_config_instance = None


def get_court_config(force_reload: bool = False) -> CourtConfig:
    global _court_config_instance
    if _court_config_instance is None or force_reload:
        _court_config_instance = CourtConfig()
    return _court_config_instance
