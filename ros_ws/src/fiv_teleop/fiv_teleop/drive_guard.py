from dataclasses import dataclass
import math
import time

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from rclpy.node import Node


@dataclass(frozen=True)
class DriveCommand:
    speed: float
    steering_angle: float


STOP = DriveCommand(speed=0.0, steering_angle=0.0)


def limit_command(
    speed,
    steering_angle,
    max_speed,
    max_steering_angle,
):
    values = (speed, steering_angle, max_speed, max_steering_angle)
    if (
        not all(math.isfinite(value) for value in values)
        or max_speed <= 0.0
        or max_steering_angle <= 0.0
    ):
        return STOP

    bounded_speed = max(0.0, min(speed, max_speed))
    bounded_steering = max(
        -max_steering_angle,
        min(steering_angle, max_steering_angle),
    )
    return DriveCommand(bounded_speed, bounded_steering)


class DriveGuard(Node):
    def __init__(self):
        super().__init__('fiv_drive_guard')
        self.declare_parameter('input_topic', '/manual/drive')
        self.declare_parameter('output_topic', '/drive')
        self.declare_parameter('max_speed', 0.25)
        self.declare_parameter('max_steering_angle', 0.30)
        self.declare_parameter('command_timeout_sec', 0.5)

        self._max_speed = float(self.get_parameter('max_speed').value)
        self._max_steering_angle = float(
            self.get_parameter('max_steering_angle').value
        )
        self._timeout = float(self.get_parameter('command_timeout_sec').value)
        if (
            not math.isfinite(self._timeout)
            or self._timeout <= 0.0
            or not math.isfinite(self._max_speed)
            or self._max_speed <= 0.0
            or not math.isfinite(self._max_steering_angle)
            or self._max_steering_angle <= 0.0
        ):
            raise ValueError('Drive limits and command timeout must be positive and finite')

        self._publisher = self.create_publisher(
            AckermannDriveStamped,
            str(self.get_parameter('output_topic').value),
            10,
        )
        self._last_command = STOP
        self._last_command_time = None
        self._stop_sent = False
        self.create_subscription(
            AckermannDriveStamped,
            str(self.get_parameter('input_topic').value),
            self._on_command,
            10,
        )
        self.create_timer(0.05, self._publish_if_fresh)
        self.get_logger().info(
            'Manual drive guard ready: bounded commands on /manual/drive '
            'are forwarded to /drive; stale input stops'
        )

    def _on_command(self, message):
        self._last_command = limit_command(
            float(message.drive.speed),
            float(message.drive.steering_angle),
            self._max_speed,
            self._max_steering_angle,
        )
        self._last_command_time = time.monotonic()
        self._stop_sent = False

    def _publish(self, command):
        message = AckermannDriveStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.drive.speed = command.speed
        message.drive.steering_angle = command.steering_angle
        self._publisher.publish(message)

    def _publish_if_fresh(self):
        if (
            self._last_command_time is not None
            and time.monotonic() - self._last_command_time <= self._timeout
        ):
            self._publish(self._last_command)
            return

        self._publish(STOP)
        if not self._stop_sent and self._last_command_time is not None:
            self.get_logger().warning(
                'Manual command timed out; publishing zero speed'
            )
        self._stop_sent = True


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = DriveGuard()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
