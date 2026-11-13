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
├── ros_ws/           # Our ROS 2 colcon workspace
│   └── src/          # FIV ROS 2 packages
└── GitFlow.png
```

Planned ROS packages (add these as the team implements them):

- `fiv_bringup`: launch files and shared parameters.
- `fiv_gap_follow`: Follow the Gap node; consumes a laser scan and publishes a
  drive command.
- `fiv_interfaces`: only if we need custom ROS messages or services. Prefer
  standard ROS messages when they fit.
- `fiv_teleop`: optional manual control and safety testing tools.

See [the architecture guide](docs/architecture.md) for package boundaries,
topic contracts, and multi-device ROS notes. See
[the simulator setup guide](Simulation/README.md) before installing the
upstream simulator.

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

## Team workflow

Use the existing [GitHub Flow](GitFlow.png): work on feature branches and keep
`main` and `release` protected for team-approved changes.
