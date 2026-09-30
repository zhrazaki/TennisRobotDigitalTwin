"""
Purpose:
    Defines the project's world-space coordinate convention and turns the
    raw dimensions in CourtConfig into concrete 3D points/lines every
    later phase can consume directly (surface mesh corners, line strips,
    service box rectangles, net endpoints, center marks...).

    COORDINATE CONVENTION (read this before writing any other phase):
        - 1 Unreal Unit = 1 centimeter.
        - World origin (0, 0, 0) sits exactly at the court's geometric
          center, at ground level — i.e. where the net's center strap
          crosses the center line.
        - +X axis runs from the center toward one baseline ("far" end).
          -X axis runs toward the other baseline ("near" end).
        - +Y axis runs from the center toward one doubles sideline
          ("right"). -Y axis runs toward the other doubles sideline
          ("left").
        - +Z axis is up (Unreal standard).
    This file is the single place that convention is encoded. No other
    phase should independently decide where a baseline or sideline is.

Dependencies:
    - Python/Core/court_config.py (dimensions, via get_court_config())
    - Standard library only — no `unreal` import, so results (plain
      tuples) can be consumed by Tools/, Blueprints (via export), or a
      future C++ module without pulling in the Editor API here.

Inputs:
    None required — reads the shared CourtConfig singleton.

Outputs:
    Plain (x, y, z) float tuples in centimeters, and small dicts/lists
    grouping related points (corners, boxes, marks). See function
    docstrings below for exact shapes.
"""

from Core.court_config import get_court_config


def get_court_origin():
    """The court center, by definition. Always (0.0, 0.0, 0.0)."""
    return (0.0, 0.0, 0.0)


def get_baseline_x(ground_z: float = 0.0):
    """Return (positive_x_baseline, negative_x_baseline) X coordinates."""
    cfg = get_court_config()
    return (cfg.half_length_cm, -cfg.half_length_cm)


def get_service_line_x():
    """
    Return (positive_x_service_line, negative_x_service_line) X coords.
    The origin (0,0,0) is at the NET, so the service line's X coordinate
    is simply its distance from the net — cfg.service_line_distance_from_net_cm.
    (Do not confuse this with cfg.baseline_to_service_line_cm, which is the
    separate gap between the service line and the baseline.)
    """
    cfg = get_court_config()
    return (cfg.service_line_distance_from_net_cm, -cfg.service_line_distance_from_net_cm)


def get_doubles_sideline_y():
    """Return (positive_y_sideline, negative_y_sideline) Y coordinates."""
    cfg = get_court_config()
    return (cfg.half_doubles_width_cm, -cfg.half_doubles_width_cm)


def get_singles_sideline_y():
    """Return (positive_y_sideline, negative_y_sideline) Y coordinates."""
    cfg = get_court_config()
    return (cfg.half_singles_width_cm, -cfg.half_singles_width_cm)


def get_doubles_court_corners(ground_z: float = 0.0):
    """
    Four outer corners of the full doubles court, ordered
    counter-clockwise starting at (+X, +Y): far-right, far-left,
    near-left, near-right.
    Returns a list of 4 (x, y, z) tuples.
    """
    x_pos, x_neg = get_baseline_x()
    y_pos, y_neg = get_doubles_sideline_y()
    return [
        (x_pos, y_pos, ground_z),
        (x_pos, y_neg, ground_z),
        (x_neg, y_neg, ground_z),
        (x_neg, y_pos, ground_z),
    ]


def get_singles_court_corners(ground_z: float = 0.0):
    """Same as get_doubles_court_corners() but for the singles lines."""
    x_pos, x_neg = get_baseline_x()
    y_pos, y_neg = get_singles_sideline_y()
    return [
        (x_pos, y_pos, ground_z),
        (x_pos, y_neg, ground_z),
        (x_neg, y_neg, ground_z),
        (x_neg, y_pos, ground_z),
    ]


def get_service_boxes(ground_z: float = 0.0):
    """
    The four service boxes, each as a dict:
        {
            "name": "far_right" | "far_left" | "near_right" | "near_left",
            "corners": [(x,y,z) x4]   # net-side pair first, service-line-side pair second
        }
    "far"/"near" refers to +X/-X, "right"/"left" refers to +Y/-Y.
    """
    x_svc_pos, x_svc_neg = get_service_line_x()
    y_pos, y_neg = get_singles_sideline_y()

    boxes = [
        {
            "name": "far_right",
            "corners": [
                (0.0, y_pos, ground_z),
                (x_svc_pos, y_pos, ground_z),
                (x_svc_pos, 0.0, ground_z),
                (0.0, 0.0, ground_z),
            ],
        },
        {
            "name": "far_left",
            "corners": [
                (0.0, 0.0, ground_z),
                (x_svc_pos, 0.0, ground_z),
                (x_svc_pos, y_neg, ground_z),
                (0.0, y_neg, ground_z),
            ],
        },
        {
            "name": "near_right",
            "corners": [
                (0.0, y_pos, ground_z),
                (x_svc_neg, y_pos, ground_z),
                (x_svc_neg, 0.0, ground_z),
                (0.0, 0.0, ground_z),
            ],
        },
        {
            "name": "near_left",
            "corners": [
                (0.0, 0.0, ground_z),
                (x_svc_neg, 0.0, ground_z),
                (x_svc_neg, y_neg, ground_z),
                (0.0, y_neg, ground_z),
            ],
        },
    ]
    return boxes


def get_center_service_line(ground_z: float = 0.0):
    """
    The center service line as two segments (net to each service line),
    since it's conceptually one line but geometrically split at the net.
    Returns a list of 2 dicts: {"name": ..., "start": (x,y,z), "end": (x,y,z)}
    """
    x_svc_pos, x_svc_neg = get_service_line_x()
    return [
        {"name": "center_service_line_far", "start": (0.0, 0.0, ground_z), "end": (x_svc_pos, 0.0, ground_z)},
        {"name": "center_service_line_near", "start": (0.0, 0.0, ground_z), "end": (x_svc_neg, 0.0, ground_z)},
    ]


def get_net_line(ground_z: float = 0.0):
    """
    Net centerline endpoints at X=0, spanning between the net posts
    (i.e. beyond the doubles sidelines by net_post_offset_cm).
    Returns {"start": (x,y,z), "end": (x,y,z)}.
    """
    cfg = get_court_config()
    return {
        "start": (0.0, cfg.net_post_span_cm, ground_z),
        "end": (0.0, -cfg.net_post_span_cm, ground_z),
    }


def get_net_post_positions(ground_z: float = 0.0):
    """
    Ground-level (X, Y, Z) position for each of the two net posts.
    Returns {"positive_y_post": (x,y,z), "negative_y_post": (x,y,z)}.
    Post height itself is cfg.net_height_post_cm (used when the actual
    post mesh is spawned in a later phase).
    """
    cfg = get_court_config()
    return {
        "positive_y_post": (0.0, cfg.net_post_span_cm, ground_z),
        "negative_y_post": (0.0, -cfg.net_post_span_cm, ground_z),
    }


def get_center_marks(ground_z: float = 0.0):
    """
    The two small center marks at each baseline (short line perpendicular
    to the baseline, marking the midpoint between singles sidelines).
    Returns a list of 2 dicts:
        {
            "name": "center_mark_far" | "center_mark_near",
            "baseline_x": float,
            "start": (x,y,z),   # at the baseline
            "end":   (x,y,z),   # center_mark_length_cm inward from baseline
        }
    """
    cfg = get_court_config()
    x_pos, x_neg = get_baseline_x()
    inward_pos = x_pos - cfg.center_mark_length_cm
    inward_neg = x_neg + cfg.center_mark_length_cm
    return [
        {
            "name": "center_mark_far",
            "baseline_x": x_pos,
            "start": (x_pos, 0.0, ground_z),
            "end": (inward_pos, 0.0, ground_z),
        },
        {
            "name": "center_mark_near",
            "baseline_x": x_neg,
            "start": (x_neg, 0.0, ground_z),
            "end": (inward_neg, 0.0, ground_z),
        },
    ]


def get_surface_dimensions():
    """
    Total playing-surface pad size in centimeters: the doubles court
    plus the recommended run-off clearance on every side (ITF-recommended
    minimums, not just the marked lines). Used by Phase 2 (surface mesh)
    and later by Phase 6 (fence placement, which sits just outside this).
    Returns (length_cm, width_cm).
    """
    cfg = get_court_config()
    length_cm = cfg.court_length_cm + 2 * cfg.recommended_backcourt_clearance_cm
    width_cm = cfg.doubles_width_cm + 2 * cfg.recommended_sidecourt_clearance_cm
    return (length_cm, width_cm)


def get_surface_corners(ground_z: float = 0.0):
    """
    Four outer corners of the full playing-surface pad (court + run-off),
    ordered the same way as get_doubles_court_corners(): far-right,
    far-left, near-left, near-right.
    Returns a list of 4 (x, y, z) tuples.
    """
    length_cm, width_cm = get_surface_dimensions()
    x = length_cm / 2.0
    y = width_cm / 2.0
    return [
        (x, y, ground_z),
        (x, -y, ground_z),
        (-x, -y, ground_z),
        (-x, y, ground_z),
    ]


def get_all_key_points(ground_z: float = 0.0):
    """
    Convenience aggregator used by Tools/validate_phase1_config.py (and
    reusable by later phases / other AIs) to fetch every key point in
    one call instead of importing each function individually.
    """
    return {
        "origin": get_court_origin(),
        "doubles_corners": get_doubles_court_corners(ground_z),
        "singles_corners": get_singles_court_corners(ground_z),
        "service_boxes": get_service_boxes(ground_z),
        "center_service_line": get_center_service_line(ground_z),
        "net_line": get_net_line(ground_z),
        "net_posts": get_net_post_positions(ground_z),
        "center_marks": get_center_marks(ground_z),
        "surface_corners": get_surface_corners(ground_z),
    }


def validate_layout() -> None:
    """
    Cross-check computed geometry against CourtConfig independently of
    CourtConfig.validate(), to catch mistakes made in THIS file.
    Raises AssertionError on failure.
    """
    cfg = get_court_config()
    eps = cfg.EPSILON_CM

    doubles_corners = get_doubles_court_corners()
    width = abs(doubles_corners[0][1] - doubles_corners[1][1])
    length = abs(doubles_corners[0][0] - doubles_corners[2][0])
    assert abs(width - cfg.doubles_width_cm) < eps, "Doubles corner width mismatch"
    assert abs(length - cfg.court_length_cm) < eps, "Doubles corner length mismatch"

    net = get_net_line()
    net_span = abs(net["start"][1] - net["end"][1])
    assert abs(net_span - 2 * cfg.net_post_span_cm) < eps, "Net span mismatch"

    boxes = get_service_boxes()
    assert len(boxes) == 4, "Expected exactly 4 service boxes"
    for box in boxes:
        xs = [c[0] for c in box["corners"]]
        ys = [c[1] for c in box["corners"]]
        box_width = max(ys) - min(ys)
        box_depth = max(xs) - min(xs)
        assert abs(box_width - cfg.service_box_width_cm) < eps, (
            "Service box '%s' width mismatch" % box["name"]
        )
        assert abs(box_depth - cfg.service_line_distance_from_net_cm) < eps, (
            "Service box '%s' depth mismatch" % box["name"]
        )

    surface_corners = get_surface_corners()
    surface_length = abs(surface_corners[0][0] - surface_corners[2][0])
    surface_width = abs(surface_corners[0][1] - surface_corners[1][1])
    expected_length = cfg.court_length_cm + 2 * cfg.recommended_backcourt_clearance_cm
    expected_width = cfg.doubles_width_cm + 2 * cfg.recommended_sidecourt_clearance_cm
    assert abs(surface_length - expected_length) < eps, "Surface length mismatch"
    assert abs(surface_width - expected_width) < eps, "Surface width mismatch"
