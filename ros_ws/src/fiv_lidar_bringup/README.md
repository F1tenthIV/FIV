# Hokuyo UST-10LX bringup

This package launches the ROS 2 `urg_node` driver for the Ethernet UST-10LX.
It publishes `sensor_msgs/msg/LaserScan` on `/scan` in the `laser` frame so
the existing `fiv_gap_follow` node can consume the real sensor instead of the
simulator.

## Install and configure

On ROS 2 Humble:

```bash
sudo apt update
sudo apt install ros-humble-urg-node
```

Verify the LiDAR's configured IP from its manual or configuration. The
included example uses `192.168.0.10` and TCP port `10940`; change
[`config/ust_10lx.yaml`](config/ust_10lx.yaml) if yours differs.

The UST-10LX has a 270-degree field of view. The YAML sets the expected angular
limits to approximately ±135 degrees; verify the reported scan on the actual
sensor. `laser_frame_id` is deliberately `laser`; publish the measured static
transform from `base_link` to `laser` in the chassis bringup, not in this
sensor-driver package.

## Launch and verify

Build the workspace, then run:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch fiv_lidar_bringup urg.launch.py
```

In another terminal:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic info /scan
ros2 topic hz /scan
ros2 topic echo --once /scan
```

The sensor should be powered separately from its specified DC input. Ethernet
does not supply sensor power. Put the Jetson's LiDAR-facing network interface
on the same subnet as the sensor and verify `ping <sensor-ip>` before starting
the ROS driver.

## On the car

Only switch Follow the Gap to this real `/scan` after confirming the scan
orientation, chassis transform, stale-scan stop, and low-speed command limit.
The sensor driver does not implement a motor emergency stop.
