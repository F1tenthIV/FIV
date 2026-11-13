import math
import os

import cv2
from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def validate_recording_settings(output_path, fps, codec, sync_slop_sec):
    output_path = str(output_path)
    if not output_path.strip():
        raise ValueError('output_path must not be empty')
    if not math.isfinite(fps) or fps <= 0.0:
        raise ValueError('fps must be a positive finite number')
    if len(codec) != 4:
        raise ValueError('codec must be a four-character OpenCV codec')
    if not math.isfinite(sync_slop_sec) or sync_slop_sec < 0.0:
        raise ValueError('sync_slop_sec must be a non-negative finite number')
    return os.path.abspath(os.path.expanduser(output_path))


def combine_stereo_frames(left, right):
    if left.shape != right.shape:
        raise ValueError('Left and right camera frames must have identical shapes')
    return cv2.hconcat((left, right))


class StereoVideoRecorder(Node):
    def __init__(self):
        super().__init__('fiv_stereo_video_recorder')
        self.declare_parameter('left_image_topic', '/left/image_rect_color')
        self.declare_parameter('right_image_topic', '/right/image_rect_color')
        self.declare_parameter(
            'output_path', '/recordings/stereo_capture.mp4'
        )
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('codec', 'mp4v')
        self.declare_parameter('sync_slop_sec', 0.05)

        codec = str(self.get_parameter('codec').value)
        self._fps = float(self.get_parameter('fps').value)
        sync_slop = float(
            self.get_parameter('sync_slop_sec').value
        )
        self._output_path = validate_recording_settings(
            self.get_parameter('output_path').value,
            self._fps,
            codec,
            sync_slop,
        )

        self._codec = codec
        self._bridge = CvBridge()
        self._writer = None
        self._frame_size = None
        self._frames_written = 0
        self._shape_warning_logged = False

        left_subscriber = Subscriber(
            self,
            Image,
            str(self.get_parameter('left_image_topic').value),
            qos_profile=qos_profile_sensor_data,
        )
        right_subscriber = Subscriber(
            self,
            Image,
            str(self.get_parameter('right_image_topic').value),
            qos_profile=qos_profile_sensor_data,
        )
        self._synchronizer = ApproximateTimeSynchronizer(
            [left_subscriber, right_subscriber],
            queue_size=10,
            slop=sync_slop,
        )
        self._synchronizer.registerCallback(self._record_pair)
        self.get_logger().info(
            f'Recording synchronized stereo images to {self._output_path}'
        )

    def _record_pair(self, left_message, right_message):
        left = self._bridge.imgmsg_to_cv2(
            left_message, desired_encoding='bgr8'
        )
        right = self._bridge.imgmsg_to_cv2(
            right_message, desired_encoding='bgr8'
        )
        if left.shape != right.shape:
            if not self._shape_warning_logged:
                self.get_logger().warning(
                    'Left/right image sizes differ; dropping mismatched pairs'
                )
                self._shape_warning_logged = True
            return

        height, width = left.shape[:2]
        frame_size = (width * 2, height)
        if self._writer is None:
            os.makedirs(os.path.dirname(self._output_path), exist_ok=True)
            self._writer = cv2.VideoWriter(
                self._output_path,
                cv2.VideoWriter_fourcc(*self._codec),
                self._fps,
                frame_size,
            )
            if not self._writer.isOpened():
                self._writer.release()
                self._writer = None
                raise RuntimeError(
                    f'OpenCV could not open video output {self._output_path}; '
                    'check the codec and destination path'
                )
            self._frame_size = frame_size
            self.get_logger().info(
                f'Opened video output at {frame_size[0]}x{frame_size[1]} pixels'
            )
        elif frame_size != self._frame_size:
            raise RuntimeError(
                'Camera image dimensions changed during recording; '
                'start a new recording for the new resolution'
            )

        self._writer.write(combine_stereo_frames(left, right))
        self._frames_written += 1

    def destroy_node(self):
        if self._writer is not None:
            self._writer.release()
            self._writer = None
            self.get_logger().info(
                f'Saved {self._frames_written} stereo frames to {self._output_path}'
            )
        else:
            self.get_logger().warning(
                'No synchronized stereo frames received; no video was saved'
            )
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = StereoVideoRecorder()
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
