import cv2
import numpy as np
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import Image

from fiv_camera.recorder import (
    StereoVideoRecorder,
    combine_stereo_frames,
    validate_recording_settings,
)


def test_stereo_frames_are_combined_side_by_side():
    left = np.zeros((2, 3, 3), dtype=np.uint8)
    right = np.ones((2, 3, 3), dtype=np.uint8)

    combined = combine_stereo_frames(left, right)

    assert combined.shape == (2, 6, 3)
    assert np.array_equal(combined[:, :3], left)
    assert np.array_equal(combined[:, 3:], right)


def test_stereo_frames_must_have_matching_dimensions():
    with pytest.raises(ValueError, match='identical shapes'):
        combine_stereo_frames(
            np.zeros((2, 3, 3), dtype=np.uint8),
            np.zeros((3, 3, 3), dtype=np.uint8),
        )


@pytest.mark.parametrize(
    'output_path,fps,codec,slop',
    [
        ('', 30.0, 'mp4v', 0.05),
        ('capture.mp4', 0.0, 'mp4v', 0.05),
        ('capture.mp4', float('nan'), 'mp4v', 0.05),
        ('capture.mp4', 30.0, 'bad', 0.05),
        ('capture.mp4', 30.0, 'mp4v', -0.05),
        ('capture.mp4', 30.0, 'mp4v', float('inf')),
    ],
)
def test_invalid_recording_settings_are_rejected(
    output_path, fps, codec, slop
):
    with pytest.raises(ValueError):
        validate_recording_settings(output_path, fps, codec, slop)


def test_recording_settings_expand_the_destination():
    output_path = validate_recording_settings(
        '~/fiv_recordings/capture.mp4',
        30.0,
        'mp4v',
        0.05,
    )

    assert output_path.endswith('/fiv_recordings/capture.mp4')


def test_recorder_writes_synchronized_stereo_video(tmp_path):
    left_topic = '/fiv_camera_test/left'
    right_topic = '/fiv_camera_test/right'
    output_path = str(tmp_path / 'stereo.mp4')
    rclpy.init(args=[
        '--ros-args',
        '-p', f'left_image_topic:={left_topic}',
        '-p', f'right_image_topic:={right_topic}',
        '-p', f'output_path:={output_path}',
    ])
    recorder = StereoVideoRecorder()
    publisher_node = rclpy.create_node('fiv_camera_test_publisher')
    left_publisher = publisher_node.create_publisher(Image, left_topic, 10)
    right_publisher = publisher_node.create_publisher(Image, right_topic, 10)
    executor = SingleThreadedExecutor()
    executor.add_node(recorder)
    executor.add_node(publisher_node)

    try:
        for _ in range(10):
            executor.spin_once(timeout_sec=0.1)
        for index in range(10):
            left = make_image(index, (0, 0, 255))
            right = make_image(index, (0, 255, 0))
            left_publisher.publish(left)
            right_publisher.publish(right)
            for _ in range(4):
                executor.spin_once(timeout_sec=0.05)
        assert recorder._frames_written > 0
    finally:
        executor.remove_node(recorder)
        executor.remove_node(publisher_node)
        publisher_node.destroy_node()
        recorder.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    capture = cv2.VideoCapture(output_path)
    try:
        assert capture.isOpened()
        assert capture.get(cv2.CAP_PROP_FRAME_COUNT) > 0
        assert capture.get(cv2.CAP_PROP_FRAME_WIDTH) == 128
    finally:
        capture.release()


def make_image(index, color):
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    image[:, :] = color
    message = Image()
    message.header.stamp.sec = 1
    message.header.stamp.nanosec = index * 10_000_000
    message.height = 64
    message.width = 64
    message.encoding = 'bgr8'
    message.is_bigendian = 0
    message.step = 64 * 3
    message.data = image.tobytes()
    return message
