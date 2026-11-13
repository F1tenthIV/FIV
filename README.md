# FIV | F1TENTH Team Four @ UCSB

FIV is our team's ROS 2 software for developing and testing F1TENTH driving
algorithms. The upstream F1TENTH Gym ROS bridge is pinned as a Git submodule;
our algorithms and launch/configuration packages live in this repository.

## Repository layout

```text
FIV/
├── Simulation/       # Pinned simulator + Humble Docker setup
│   ├── f1tenth_gym_ros/  # Upstream Git submodule
│   └── f1tenth_gym/      # Upstream Gym dependency submodule
├── docs/             # Architecture and team workflow
│   └── hardware/     # Jetson, LiDAR, camera, motor and demo roadmap
├── ros_ws/           # Our ROS 2 colcon workspace
│   └── src/          # FIV ROS 2 packages
└── GitFlow.png
```

Implemented packages:

- `fiv_gap_follow`: implemented on `Feature-Simulation`; consumes a laser scan
  and publishes a drive command.
- `fiv_lidar_bringup`: UST-10LX Ethernet driver setup on
  `Lidar-Camera-System`, configured to publish real `/scan` messages.
- `fiv_camera`: stereo processing and camera recording scaffold on
  `Feature-Camera`. It requires a camera driver and calibration; detector/model
  integration is a follow-up.

Planned if the project needs them:

- `fiv_bringup`: launch files and shared parameters.
- `fiv_interfaces`: custom messages/services only when standard ROS messages
  are insufficient.
- `fiv_teleop`: planned on `Algorithms` for bounded manual commands with a
  command timeout.

See [the architecture guide](docs/architecture.md) for package boundaries,
topic contracts, and multi-device ROS notes. See
[the simulator setup guide](Simulation/README.md) before installing the
upstream simulator. Camera topic expectations and recording instructions are
in [the camera guide](docs/camera.md).
The hardware migration sequence and Orin Nano runbook are in
[docs/hardware/](docs/hardware/README.md); see the
[deliverables plan](docs/hardware/deliverables.md) for the full checklists and
[the generated PDF](docs/hardware/FIV_Hardware_Integration_Plan.pdf) for a
shareable version.

## Getting started

1. Our initial baseline is ROS 2 Humble in Docker on WSL 2. Other devices need
   compatible ROS 2 installs and network access; see
   [the architecture guide](docs/architecture.md).
2. Initialize the simulator submodule and start the environment:

   ```bash
   git submodule update --init --recursive
   docker compose -f Simulation/compose.humble.yaml up --build -d
   ```

3. Open `http://localhost:8080/vnc.html` and connect. For simulator and
   workspace commands, follow [Simulation/README.md](Simulation/README.md).
4. Add FIV packages under `ros_ws/src/`, then build them in the running
   container as described in [ros_ws/README.md](ros_ws/README.md).
5. To try the driving controller, run the Follow the Gap node after the
   simulator bridge is publishing `/scan`; it sends commands on `/drive`.

## Team workflow

Use the existing [GitHub Flow](GitFlow.png): work on feature branches and keep
`main` and `release` protected for team-approved changes.
