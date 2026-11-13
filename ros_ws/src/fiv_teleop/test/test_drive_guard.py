import math

import pytest

from fiv_teleop.drive_guard import STOP, limit_command


def test_command_is_clamped_to_manual_limits():
    command = limit_command(2.0, -0.8, 0.25, 0.3)

    assert command.speed == 0.25
    assert command.steering_angle == -0.3


def test_reverse_is_disabled():
    command = limit_command(-1.0, 0.0, 0.25, 0.3)

    assert command.speed == 0.0


@pytest.mark.parametrize(
    'speed,steering',
    [
        (math.nan, 0.0),
        (0.1, math.inf),
    ],
)
def test_non_finite_commands_stop(speed, steering):
    assert limit_command(speed, steering, 0.25, 0.3) == STOP


def test_invalid_limits_stop():
    assert limit_command(0.1, 0.1, 0.0, 0.3) == STOP
