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
