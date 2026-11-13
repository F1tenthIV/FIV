import math

from fiv_gap_follow.algorithm import STOP, compute_command


def make_scan(center_obstacle=None):
    ranges = [5.0] * 181
    if center_obstacle is not None:
        ranges[90] = center_obstacle
    return ranges


def test_clear_corridor_drives_straight():
    command = compute_command(
        make_scan(),
        angle_min=math.radians(-90),
        angle_increment=math.radians(1),
        range_min=0.05,
        range_max=10.0,
    )

    assert command.speed > 0.0
    assert command.steering_angle == 0.0


def test_center_obstacle_causes_steering():
    command = compute_command(
        make_scan(center_obstacle=0.5),
        angle_min=math.radians(-90),
        angle_increment=math.radians(1),
        range_min=0.05,
        range_max=10.0,
    )

    assert command.speed > 0.0
    assert command.steering_angle != 0.0


def test_blocked_scan_stops():
    command = compute_command(
        [0.2] * 181,
        angle_min=math.radians(-90),
        angle_increment=math.radians(1),
        range_min=0.05,
        range_max=10.0,
    )

    assert command == STOP


def test_malformed_scan_stops():
    command = compute_command(
        [math.nan, math.nan, math.nan],
        angle_min=0.0,
        angle_increment=math.radians(1),
        range_min=0.05,
        range_max=10.0,
    )

    assert command == STOP


def test_infinite_ranges_are_treated_as_clear():
    command = compute_command(
        [math.inf] * 181,
        angle_min=math.radians(-90),
        angle_increment=math.radians(1),
        range_min=0.05,
        range_max=10.0,
    )

    assert command.speed > 0.0
    assert command.steering_angle == 0.0
