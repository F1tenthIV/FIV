# FIV ROS 2 workspace

This is the colcon workspace for FIV-owned ROS 2 packages. Add each package
under `src/`; the simulator is included separately as a Git submodule and is
documented in [Simulation/README.md](../Simulation/README.md).
The stereo camera launch and video recorder are documented in
[the camera guide](../docs/camera.md).
The physical hardware bringup and Jetson deployment plan is in
[the hardware guide](../docs/hardware/README.md).
The UST-10LX driver configuration is in
[`fiv_lidar_bringup`](src/fiv_lidar_bringup/README.md).
The bounded manual `/manual/drive` command interface is in
[`fiv_teleop`](src/fiv_teleop/README.md).

## Build

For the agreed Docker setup, enter the running simulator container and build
from its combined workspace. The host `ros_ws/src` directory is mounted at
`/sim_ws/src/fiv`.

```bash
cd /sim_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble \
  --skip-keys "ament_python python-transforms3d-pip"
colcon build --symlink-install
source install/local_setup.bash
```

The simulator image installs `transforms3d` with pip and skips the upstream
`python-transforms3d-pip` rosdep key (and the `ament_python` build-tool key);
these keys are not resolvable in the current Humble rosdep database.

Run the unit tests for the scan algorithm with:

```bash
colcon test --packages-select fiv_gap_follow
colcon test-result --verbose
```

Then run FIV nodes in another shell in the same container, sourcing
`/opt/ros/humble/setup.bash` and `/sim_ws/install/local_setup.bash` first.
Building `ros_ws` directly on a Linux/WSL host is also supported after
installing ROS 2 Humble and the required ROS dependencies.

## Conventions

- Use one ROS 2 package per independently testable capability.
- Keep launch/configuration in `fiv_bringup`, algorithm logic in its own
  package, and use standard ROS messages when possible.
- Add unit tests for algorithm logic and ROS integration tests for topic and
  message wiring.
- Do not commit generated `build/`, `install/`, or `log/` directories.
