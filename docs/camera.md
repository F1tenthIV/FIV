# Stereo camera bringup and recording

The `fiv_camera` package provides a reusable stereo processing launch and a
synchronized side-by-side video recorder. A camera driver is a separate
dependency; choose one that publishes the ROS image and camera calibration
topics below.

## Required camera topics

The default launch expects a driver to publish:

| Topic | Type |
|---|---|
| `/left/image_raw` | `sensor_msgs/msg/Image` |
| `/left/camera_info` | `sensor_msgs/msg/CameraInfo` |
| `/right/image_raw` | `sensor_msgs/msg/Image` |
| `/right/camera_info` | `sensor_msgs/msg/CameraInfo` |

Use the stereo pair's real intrinsic/extrinsic calibration and synchronized
timestamps. The processing pipeline rectifies the images, publishes disparity
and a 3D point cloud (`/disparity`, `/points2`), and the recorder saves
synchronized rectified color images side by side to an MP4. Uncalibrated
images may produce invalid depth; do not treat point-cloud output as reliable
until calibration is checked.

The included Compose setup does not pass camera devices into the container.
After choosing a camera/driver, either add the appropriate WSL USB/device
passthrough and driver to the setup, or run the driver on a machine that can
participate in the same ROS 2 network. The Compose network is private, so it
does not currently expose DDS topics to another physical device.

## Run it

Start the camera driver first. In another shell in the running simulator
container, source ROS and the combined workspace, then launch the stereo
pipeline and recorder:

```bash
source /opt/ros/humble/setup.bash
source /sim_ws/install/setup.bash
ros2 launch fiv_camera stereo_camera.launch.py \
  output_path:=/recordings/stereo_capture.mp4
```

For other camera namespaces, pass `left_namespace:=...` and
`right_namespace:=...`. The recorder synchronizes
`<namespace>/image_rect_color` messages using sensor-data QoS and writes one
MP4 frame per synchronized pair. Stop the launch with Ctrl+C so the MP4 writer
can close the file cleanly.

To keep calibration, disparity, point-cloud, and raw image data for offline
processing as well, record a ROS bag in a separate shell:

```bash
ros2 bag record -o /recordings/stereo_run \
  /left/image_raw /left/camera_info \
  /right/image_raw /right/camera_info \
  /disparity /points2
```

The Compose file mounts the repository's ignored `recordings/` directory at
`/recordings`, so the MP4 and bag remain on the host after the container stops.
For native WSL, create a directory such as `~/fiv_recordings` and pass that path
as `output_path` / the bag destination instead.

Confirm the actual topics with `ros2 topic list`; drivers often use their own
namespace conventions. Check that the MP4 exists and can be opened after
stopping the recorder.

## How camera and driving fit together

```text
stereo camera driver -> stereo_image_proc -> /disparity + /points2
                    \-> fiv_camera recorder -> side-by-side MP4
LiDAR /scan ---------> fiv_gap_follow -----> /drive -> simulator
```

The camera branch is currently for stereo depth output and recording. It does
not include an object-detection model yet: model format, target objects,
hardware acceleration, and labeled classes need to be chosen. Keep detections
as a separate ROS node/topic (the intended standard interface is
`vision_msgs/msg/Detection2DArray`, for example `/perception/detections`); do
not feed uncalibrated camera output into `/drive`. Once calibration and
detection are validated, a later fusion node can combine image detections and
the `/points2` cloud into 3D object locations while the LiDAR controller
remains the driving baseline.
