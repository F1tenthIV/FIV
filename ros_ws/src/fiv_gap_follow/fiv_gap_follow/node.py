import math
import time

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from fiv_gap_follow.algorithm import GapFollowConfig, STOP, compute_command


class GapFollowNode(Node):
    def __init__(self):
        super().__init__('fiv_gap_follow')
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('drive_topic', '/drive')
        self.declare_parameter('max_speed', 2.0)
        self.declare_parameter('min_speed', 0.5)
        self.declare_parameter('max_steering_angle', 0.42)
        self.declare_parameter('front_fov_degrees', 180.0)
        self.declare_parameter('safety_bubble_radius_m', 0.35)
        self.declare_parameter('min_gap_range_m', 0.8)
        self.declare_parameter('max_range_m', 5.0)
        self.declare_parameter('scan_timeout_sec', 0.5)

        self._config = GapFollowConfig(
            max_speed=float(self.get_parameter('max_speed').value),
            min_speed=float(self.get_parameter('min_speed').value),
            max_steering_angle=float(
                self.get_parameter('max_steering_angle').value
            ),
            front_fov_degrees=float(
                self.get_parameter('front_fov_degrees').value
            ),
            safety_bubble_radius_m=float(
                self.get_parameter('safety_bubble_radius_m').value
            ),
            min_gap_range_m=float(
                self.get_parameter('min_gap_range_m').value
            ),
            max_range_m=float(self.get_parameter('max_range_m').value),
        )
        self._scan_timeout_sec = float(
            self.get_parameter('scan_timeout_sec').value
        )
        if not math.isfinite(self._scan_timeout_sec) or self._scan_timeout_sec <= 0:
            raise ValueError('scan_timeout_sec must be a positive finite number')

        self._drive_publisher = self.create_publisher(
            AckermannDriveStamped,
            str(self.get_parameter('drive_topic').value),
            10,
        )
        self._last_scan_time = time.monotonic()
        self._stale_stop_sent = False
        self.create_subscription(
            LaserScan,
            str(self.get_parameter('scan_topic').value),
            self._on_scan,
            10,
        )
        self.create_timer(0.1, self._stop_if_scan_is_stale)
        self.get_logger().info(
            'Follow the Gap ready: listening for scans and publishing Ackermann drive commands'
        )

    def _publish_command(self, command):
        message = AckermannDriveStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.drive.speed = float(command.speed)
        message.drive.steering_angle = float(command.steering_angle)
        self._drive_publisher.publish(message)

    def _on_scan(self, scan):
        self._last_scan_time = time.monotonic()
        self._stale_stop_sent = False
        command = compute_command(
            scan.ranges,
            scan.angle_min,
            scan.angle_increment,
            scan.range_min,
            scan.range_max,
            self._config,
        )
        self._publish_command(command)

    def _stop_if_scan_is_stale(self):
        if (
            not self._stale_stop_sent
            and time.monotonic() - self._last_scan_time > self._scan_timeout_sec
        ):
            self._publish_command(STOP)
            self._stale_stop_sent = True
            self.get_logger().warning(
                'Laser scan timed out; publishing a zero-speed command'
            )


def main(args=None):
    rclpy.init(args=args)
    node = GapFollowNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
