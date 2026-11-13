from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class GapFollowConfig:
    max_speed: float = 2.0
    min_speed: float = 0.5
    max_steering_angle: float = 0.42
    front_fov_degrees: float = 180.0
    safety_bubble_radius_m: float = 0.35
    min_gap_range_m: float = 0.8
    max_range_m: float = 5.0


@dataclass(frozen=True)
class DriveCommand:
    speed: float
    steering_angle: float


STOP = DriveCommand(speed=0.0, steering_angle=0.0)


def compute_command(
    ranges: Sequence[float],
    angle_min: float,
    angle_increment: float,
    range_min: float,
    range_max: float,
    config: GapFollowConfig = GapFollowConfig(),
) -> DriveCommand:
    """Choose a steering target from a LaserScan-like range sequence."""
    numeric_inputs = (
        angle_min,
        angle_increment,
        range_min,
        range_max,
        config.max_speed,
        config.min_speed,
        config.max_steering_angle,
        config.front_fov_degrees,
        config.safety_bubble_radius_m,
        config.min_gap_range_m,
        config.max_range_m,
    )
    if (
        len(ranges) < 3
        or not all(math.isfinite(value) for value in numeric_inputs)
        or angle_increment <= 0.0
        or range_min < 0.0
        or range_max <= range_min
        or config.max_speed <= 0.0
        or config.min_speed < 0.0
        or config.min_speed > config.max_speed
        or config.max_steering_angle <= 0.0
        or config.front_fov_degrees <= 0.0
        or config.safety_bubble_radius_m < 0.0
        or config.min_gap_range_m <= 0.0
        or config.max_range_m <= range_min
    ):
        return STOP

    fov_half_angle = math.radians(min(config.front_fov_degrees, 360.0)) / 2.0
    scan_limit = min(range_max, config.max_range_m)
    selected_ranges = []
    selected_angles = []

    for index, value in enumerate(ranges):
        angle = angle_min + index * angle_increment
        if abs(angle) > fov_half_angle:
            continue
        if math.isinf(value) and value > 0.0:
            distance = scan_limit
        elif not math.isfinite(value) or value < range_min:
            distance = 0.0
        else:
            distance = min(value, scan_limit)
        selected_ranges.append(distance)
        selected_angles.append(angle)

    if len(selected_ranges) < 3:
        return STOP

    closest_index = min(range(len(selected_ranges)), key=selected_ranges.__getitem__)
    closest_distance = selected_ranges[closest_index]
    if (
        closest_distance > 0.0
        and closest_distance < scan_limit
        and config.safety_bubble_radius_m > 0.0
    ):
        bubble_half_width = int(
            math.ceil(
                math.atan2(config.safety_bubble_radius_m, closest_distance)
                / angle_increment
            )
        )
    else:
        bubble_half_width = 0

    first_bubble_index = max(0, closest_index - bubble_half_width)
    last_bubble_index = min(
        len(selected_ranges), closest_index + bubble_half_width + 1
    )
    for index in range(first_bubble_index, last_bubble_index):
        selected_ranges[index] = 0.0

    gaps = []
    gap_start = None
    for index, distance in enumerate(selected_ranges):
        if distance >= config.min_gap_range_m:
            if gap_start is None:
                gap_start = index
        elif gap_start is not None:
            gaps.append((gap_start, index))
            gap_start = None
    if gap_start is not None:
        gaps.append((gap_start, len(selected_ranges)))
    if not gaps:
        return STOP

    start, end = max(
        gaps,
        key=lambda bounds: (
            bounds[1] - bounds[0],
            max(selected_ranges[bounds[0]:bounds[1]]),
            -abs(
                selected_angles[(bounds[0] + bounds[1] - 1) // 2]
            ),
        ),
    )
    target_index = max(
        range(start, end),
        key=lambda index: (
            selected_ranges[index],
            -abs(selected_angles[index]),
        ),
    )
    steering_angle = selected_angles[target_index]
    steering_angle = max(
        -config.max_steering_angle,
        min(config.max_steering_angle, steering_angle),
    )
    steering_fraction = min(
        abs(steering_angle) / config.max_steering_angle, 1.0
    )
    speed = config.max_speed - (
        config.max_speed - config.min_speed
    ) * steering_fraction
    return DriveCommand(speed=speed, steering_angle=steering_angle)
