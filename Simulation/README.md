# F1TENTH Gym ROS simulator

The simulator is maintained upstream at
[f1tenth/f1tenth_gym_ros](https://github.com/f1tenth/f1tenth_gym_ros) and is
pinned in [`f1tenth_gym_ros/`](f1tenth_gym_ros/). Its Gym dependency is also
pinned in [`f1tenth_gym/`](f1tenth_gym/). The bridge connects the F1TENTH Gym
environment to ROS 2. Keep upstream files and simulator changes out of FIV's
algorithm packages; propose a fork only if we need to maintain patches.

## Agreed development setup

The initial team baseline is ROS 2 Humble on Ubuntu 22.04 in Docker via WSL 2.
The upstream Dockerfile uses `ros:foxy` and Foxy-specific package names, so do
not use its Docker build unchanged for this baseline. The FIV-owned
`Dockerfile.humble` builds the pinned bridge source against Humble.

From the repository root in a WSL 2 terminal:

```bash
git submodule update --init --recursive
docker compose -f Simulation/compose.humble.yaml up --build -d
```

Open `http://localhost:8080/vnc.html` in a browser and connect. Then enter the
simulation container and launch the bridge:

```bash
docker compose -f Simulation/compose.humble.yaml exec sim bash
source /opt/ros/humble/setup.bash
source /sim_ws/install/setup.bash
ros2 launch f1tenth_gym_ros gym_bridge_launch.py
```

If FIV packages or their dependencies have changed, rebuild with
`docker compose -f Simulation/compose.humble.yaml up --build -d` before
launching. Stop the environment with
`docker compose -f Simulation/compose.humble.yaml down`.

## Alternative: run natively in WSL 2

Use this route if Docker Desktop is unavailable. It assumes Ubuntu 22.04 in
WSL 2 with ROS 2 Humble already installed and WSLg enabled for RViz:

```bash
sudo apt update
sudo apt install -y python3-pip python3-rosdep python3-colcon-common-extensions
source /opt/ros/humble/setup.bash
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update
# Run from the repository root in WSL.
rosdep install -i --from-paths Simulation/f1tenth_gym_ros ros_ws/src \
  --rosdistro humble -y \
  --skip-keys "ament_python python-transforms3d-pip"
python3 -m pip install transforms3d -e Simulation/f1tenth_gym
sudo mkdir -p /sim_ws/src
if [ ! -e /sim_ws/src/f1tenth_gym_ros ]; then
  sudo ln -s "$PWD/Simulation/f1tenth_gym_ros" /sim_ws/src/f1tenth_gym_ros
fi
cd ros_ws
colcon build --symlink-install --base-paths ../Simulation/f1tenth_gym_ros src
source install/setup.bash
ros2 launch f1tenth_gym_ros gym_bridge_launch.py
```

The symlink supplies the absolute map path expected by the upstream simulator.
In another WSL terminal, source ROS and `ros_ws/install/setup.bash` before
running FIV nodes. This native sequence was validated with ROS 2 Humble/WSLg.

## Run the basic driving algorithm

Leave the simulator bridge running in its first terminal. Open a second WSL
terminal at the repository root and start a shell in the same container:

```bash
docker compose -f Simulation/compose.humble.yaml exec sim bash
source /opt/ros/humble/setup.bash
source /sim_ws/install/setup.bash
ros2 topic echo --once /scan
ros2 run fiv_gap_follow gap_follow
```

In a third container shell, inspect the output:

```bash
docker compose -f Simulation/compose.humble.yaml exec sim bash
source /opt/ros/humble/setup.bash
source /sim_ws/install/setup.bash
ros2 topic echo /drive
```

The node implements a basic Follow the Gap controller: it filters the forward
laser scan, masks a safety bubble around nearby obstacles, picks the widest
open gap, and slows down as the steering angle grows. It publishes zero speed
when no usable gap is available or scans stop arriving. This is a learning
baseline, not a race- or hardware-qualified safety controller. Unit tests for
the ROS-independent scan logic are in
`ros_ws/src/fiv_gap_follow/test/`.

The Humble image is a FIV-maintained adaptation, not an upstream-supported
configuration. Validate its build and launch before using it for a demo. The
upstream native instructions document Foxy on Ubuntu 20.04, which is
end-of-life.

## Integration contract

For the default single-car setup, the bridge publishes:

| Topic | Message | Use |
|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | Input to reactive driving algorithms |
| `/ego_racecar/odom` | `nav_msgs/msg/Odometry` | Vehicle state |
| `/map` | `nav_msgs/msg/OccupancyGrid` | Map-based planning |

It subscribes to:

| Topic | Message | Use |
|---|---|---|
| `/drive` | `ackermann_msgs/msg/AckermannDriveStamped` | Ego vehicle command |

In two-car mode, the upstream bridge also documents `/opp_scan` and
`/opp_drive`. Check its `sim.yaml` and launch configuration for the actual
topic names, namespaces, and number of agents; avoid hard-coding assumptions
from the table when using a modified configuration.

For a package build and multi-device networking guidance, see
[the architecture guide](../docs/architecture.md) and
[the FIV workspace guide](../ros_ws/README.md).
