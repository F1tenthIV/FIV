from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    left_namespace = LaunchConfiguration('left_namespace')
    right_namespace = LaunchConfiguration('right_namespace')
    return LaunchDescription([
        DeclareLaunchArgument(
            'left_namespace',
            default_value='left',
            description='Namespace used by the left stereo camera driver',
        ),
        DeclareLaunchArgument(
            'right_namespace',
            default_value='right',
            description='Namespace used by the right stereo camera driver',
        ),
        DeclareLaunchArgument(
            'approximate_sync',
            default_value='true',
            description='Allow small timestamp differences between stereo frames',
        ),
        DeclareLaunchArgument(
            'output_path',
            default_value='/recordings/stereo_capture.mp4',
            description='Side-by-side video path; parent directories are created',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('stereo_image_proc'),
                    'launch',
                    'stereo_image_proc.launch.py',
                ])
            ),
            launch_arguments={
                'left_namespace': left_namespace,
                'right_namespace': right_namespace,
                'approximate_sync': LaunchConfiguration('approximate_sync'),
            }.items(),
        ),
        Node(
            package='fiv_camera',
            executable='stereo_video_recorder',
            name='stereo_video_recorder',
            parameters=[{
                'left_image_topic': [
                    left_namespace, '/image_rect_color',
                ],
                'right_image_topic': [
                    right_namespace, '/image_rect_color',
                ],
                'output_path': LaunchConfiguration('output_path'),
            }],
            output='screen',
        ),
    ])
