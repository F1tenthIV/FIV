# FIV software architecture

## Runtime shape

Keep the simulator and FIV's algorithms as separate ROS 2 workspaces/processes.
The simulator publishes sensor/state topics and subscribes to drive commands;
FIV nodes consume those topics and publish commands. This lets us run the
algorithm on another computer later without coupling it to the simulator's
Python or container setup.

```text
F1TENTH Gym ROS bridge                 FIV ROS 2 packages
  /scan  ----------------------------> fiv_gap_follow
  /ego_racecar/odom ------------------> future state estimator / controller
  /map   ----------------------------> future map-based planner
  /drive <---------------------------- fiv_gap_follow
```

The bridge's published topics include `/scan`, `/ego_racecar/odom`, and `/map`.
For one-car simulation it subscribes to `/drive` using
`ackermann_msgs/msg/AckermannDriveStamped`. In two-car mode, the opponent
interfaces include `/opp_scan` and `/opp_drive`. Confirm names and message
types against the simulator's active configuration before wiring a node.

## Package responsibilities

- **`fiv_bringup`** owns launch files and shared ROS parameters; it composes
  nodes but should not contain algorithm logic.
- **`fiv_gap_follow`** owns the Follow the Gap algorithm and its ROS node.
  Keep the scan-processing logic testable independently from ROS callbacks.
- **`fiv_camera`** owns camera-specific launch and recording tools. A camera
  driver publishes calibrated stereo topics; stereo processing produces
  disparity/point-cloud data and synchronized images are recorded to video.
  A detector will consume images and publish detections after we choose a
  model. See [the camera guide](camera.md) for the topic contract and launch
  steps.
- **`fiv_interfaces`** is for custom messages/services only when standard
  messages (such as `LaserScan` and `AckermannDriveStamped`) are insufficient.
- **`fiv_teleop`** can provide manual control and test utilities; it must not
  silently compete with an autonomous node for the drive topic.

Put each package under `ros_ws/src/<package_name>`. Keep algorithm-specific
parameters with that algorithm; put shared launch configuration in
`fiv_bringup`.

## Multi-device ROS 2

ROS 2 nodes communicate through DDS, not through a special FIV relay. For
devices on one reachable network:

1. Install compatible ROS 2 distributions and the same required message
   packages on each device.
2. Set the same `ROS_DOMAIN_ID` on every participating process. Keep it
   different from unrelated ROS systems on the network.
3. Ensure ROS 2 is not restricted to loopback (`ROS_LOCALHOST_ONLY=0`, or
   unset) and that host firewalls/network equipment permit DDS discovery and
   traffic. Some Wi-Fi networks block multicast/client-to-client traffic;
   changing `ROS_DOMAIN_ID` will not fix that.
4. Check discovery and topic visibility with `ros2 node list` and
   `ros2 topic list` on both devices before running a car.

If multicast discovery is blocked, decide on a DDS discovery-server or other
network configuration as a separate deployment task. Do not expose ROS 2
traffic to untrusted networks. The included Docker Compose setup uses a
private container network for the simulator and noVNC; it does not by itself
make DDS discovery work from another physical device. WSL 2 and Docker Desktop
networking need a separate end-to-end check before attempting multi-device
control.

## Build and test order

1. Bring up the simulator and confirm its scan and drive topics locally.
2. Implement and unit-test the Follow the Gap scan-to-command logic.
3. Run the node against the simulator; verify it publishes a valid drive
   message and handles invalid/empty scans safely.
4. Bring up calibrated stereo topics and record a short ROS bag/video sample.
5. Test discovery and topic flow across two devices before attempting
   hardware runs.

## Current baseline and follow-up

- ROS 2 Humble on Ubuntu 22.04 in Docker via WSL 2 is the initial development
  baseline. The upstream bridge's Dockerfile is hard-coded to Foxy; FIV uses a
  separate Humble Dockerfile and pins the upstream source as a Git submodule.
  Verify the image build and simulation before relying on it for a demo.
- Target vehicle and sensor configuration, including scan field of view,
  drive limits, and emergency-stop behavior.
- Stereo camera model, driver, synchronization/calibration, and object
  detection model/weights. Until these are selected and tested, camera output
  is for logging/experimentation and must not control `/drive`.
