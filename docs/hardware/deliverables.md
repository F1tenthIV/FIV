# Hardware deliverables: step-by-step plan

This is the recommended sequence for the two requested demonstrations. Treat
each numbered acceptance gate as a stop/go decision. Do not skip from a
successful simulator run to an autonomous hardware run.

## Deliverable A — Jetson, simulator algorithm, and physical car

### A1. Prepare the Jetson development environment

1. Record Jetson module/RAM, carrier-board revision, QSPI version, battery,
   VESC model/firmware, motor, steering servo, and all connector/voltage
   specifications in the team's hardware inventory.
2. Back up the microSD card. Flash NVIDIA JetPack 6.2.1 / Jetson Linux 36.4.4
   using NVIDIA's Orin Nano SD-card guide and Balena Etcher. Use at least a
   64 GB UHS-I card. Check/update firmware if NVIDIA's guide requires it.
3. Boot Ubuntu, connect networking, update packages, and verify JetPack/L4T.
   Install ROS 2 Humble using the
   [official Ubuntu ARM64 instructions](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html),
   then install colcon, rosdep, and project dependencies.
4. Keep a native clone at `~/FIV`, not under a Windows-mounted path. Fetch the
   agreed branch and initialize the simulator submodules:

   ```bash
   cd ~/FIV
   git fetch origin
   git switch Motor-Control
   git pull --ff-only
   git submodule update --init --recursive
   ```

5. Build on ARM64:

   ```bash
   source /opt/ros/humble/setup.bash
   rosdep update
   rosdep install -i --from-paths Simulation/f1tenth_gym_ros ros_ws/src \
     --rosdistro humble -y \
     --skip-keys "ament_python python-transforms3d-pip"
   python3 -m pip install transforms3d -e Simulation/f1tenth_gym
   cd ros_ws
   colcon build --symlink-install --base-paths ../Simulation/f1tenth_gym_ros src
   colcon test --packages-select fiv_gap_follow fiv_lidar_bringup fiv_teleop
   colcon test-result --verbose
   ```

   These instructions need their first on-device verification; desktop WSL
   success does not prove every dependency works on ARM64.

### A2. Keep simulator validation separate

1. On a development PC, launch `f1tenth_gym_ros` and confirm simulated `/scan`,
   `/drive`, and `/ego_racecar/odom`.
2. Run `fiv_gap_follow`; inspect its output and tune it in simulation.
3. Keep the Gym simulator for algorithm development, regression tests, and
   demos. On the car, run the FIV algorithm package on the Jetson and feed it
   the real UST-10LX `/scan`. The Gym environment is not required on the car
   for that algorithm to run.
4. Do not copy the PC's `build/`, `install/`, or `log/` directories to the
   Jetson. Build ROS packages natively on each target architecture.

The simulator can be built on the Orin for bench/performance experiments, but
keep it disarmed and isolated from real hardware. The bridge and the physical
LiDAR both use `/scan`; the simulator and motor gateway both use `/drive`.
Running both in the same ROS domain without explicit remapping risks the
algorithm consuming simulated data or a command going to the wrong system.
For the first car demo, run simulation on the development PC and run the
algorithm + real sensor + verified motor gateway on the Jetson.

### A3. Wire and bring up the Hokuyo UST-10LX

1. Confirm the label really reads UST-10LX (not UST-10LX-H01 or another
   revision), its supplied cable, polarity, and IP address using the manual.
   The ROS driver example uses `192.168.0.10:10940`; verify the actual sensor
   configuration instead of assuming its address.
2. Supply the sensor from a separate regulated rail in its documented
   10–30 V range. Budget at least the documented 450 mA startup current. The
   Ethernet cable only carries data; it does not power the LiDAR.
3. Connect the LiDAR Ethernet directly to the Jetson, or through an isolated
   team switch. Put the Jetson's LiDAR-facing Ethernet interface and sensor on
   the same subnet. Example only if the LiDAR is confirmed at `192.168.0.10`:
   Jetson `192.168.0.15/24`. Don't set two devices to the same IP.
4. Verify the link, address, and route. Ping the confirmed sensor address
   before launching ROS. If there is no response, check link LEDs, power,
   cable, subnet, and actual sensor IP before changing ROS code.
5. In `ros_ws`, install/build `fiv_lidar_bringup`; launch it with the checked
   sensor IP:

   ```bash
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ros2 launch fiv_lidar_bringup urg.launch.py
   ```

6. Confirm `/scan` is `sensor_msgs/msg/LaserScan`, that messages arrive at
   roughly the sensor's 25 ms scan period, and that the scan angle is about
   ±135 degrees (270 degrees total). Inspect the data with
   `ros2 topic hz /scan`, `ros2 topic echo --once /scan`, and RViz.
7. Measure the LiDAR pose on the chassis and publish the correct static TF from
   `base_link` to `laser`. Don't copy the simulator's scan offset; measure the
   actual hardware mount.

**Acceptance gate:** stable scans, correct frame and orientation, plausible
ranges, and a visible scan in RViz while the chassis is stationary.

### A4. Power and inspect the chassis without motion

1. Confirm the actual 3S LiPo label and balance charger. Verify the fully
   charged voltage, acceptable low-voltage cutoff, and physical battery
   condition.
2. Make a reviewed power-distribution diagram from the exact manuals. Keep a
   fused motor/VESC rail and separate regulated compute, LiDAR, and camera
   rails. Confirm voltage, peak current, connector polarity, cable gauge,
   fusing, grounding, and thermal margin before connecting loads.
3. Install the Jetson and sensor securely; strain-relieve cables and prevent
   steering, tires, or chassis edges from pulling on Ethernet/USB/power leads.
4. Power only the Jetson and sensors first. Confirm no brownouts, overheating,
   unexpected resets, or LiDAR disconnects while logging `/scan`.

**Acceptance gate:** 10 minutes of stable compute + sensor operation without
motor power applied.

## Deliverable B — Manual commands and a cautious autonomy demo

### B1. Establish a safe command path

1. Identify the VESC make/model, firmware, control connection, motor type, and
   steering actuator/interface. Confirm each with its manual and the chassis
   wiring diagram.
2. In VESC Tool, verify the motor/servo setup, direction, current limits,
   battery limits, and low-voltage protection with the wheels raised. Do not
   load a guessed configuration or enable a generic ROS driver on the floor.
3. Select a ROS 2 Humble-compatible VESC driver. The F1TENTH `vesc` repository
   has ROS 1 `catkin` package manifests; it is not a drop-in ROS 2 package.
   Validate the selected driver against your exact controller before allowing
   it to command the motor.
4. Integrate exactly one actuator gateway that accepts bounded
   `AckermannDriveStamped`, reports state/diagnostics, and stops on stale
   commands or driver failure. Keep a physical E-stop independent of ROS.
5. Ensure only one command path is enabled. Stop the Follow-the-Gap node, run
   `ros2 run fiv_teleop drive_guard`, and inspect `/drive` publishers. The
   drive guard clamps speed to 0.25 m/s and steering to ±0.30 rad by default,
   disables reverse, and sends zero speed if the manual command goes stale.
   These software limits are not an E-stop.

### B2. Demonstrate manual control

1. Use the `Algorithms` branch for the manual command/algorithm work and the
   `Motor-Control` branch for the specific VESC/steering gateway.
2. First test commands with no motor connected or with the chassis lifted.
   Verify zero means stop, reverse is disabled unless deliberately enabled,
   steering signs match the vehicle, speed and steering are clamped, and
   timeout sends zero.
3. Keep `fiv_teleop drive_guard` running and send test commands on
   `/manual/drive` (not directly to `/drive`):

   ```bash
   ros2 topic pub --rate 10 /manual/drive \
     ackermann_msgs/msg/AckermannDriveStamped \
     "{drive: {speed: 0.10, steering_angle: 0.0}}"
   ```

   Stop the command publisher with Ctrl+C; verify that `/drive` goes to zero
   after the timeout. Never publish to `/drive` while another control node is
   active.
4. With the car on the ground, use an open, closed course, a spotter, low
   speed/current limits, an immediate physical stop, and short runs. Verify
   straight-line motion and steering one direction at a time.

**Acceptance gate:** manual forward, stop, and left/right steering work at
low speed; releasing the command source stops the car; the physical E-stop
works every time.

### B3. Add autonomy only after the manual gate passes

1. Connect the verified LiDAR driver to `fiv_gap_follow` using `/scan`.
2. Start with a conservative speed below walking pace and measured steering
   limits. The existing algorithm defaults to 2 m/s; do not use that default
   for first hardware tests. Set appropriate ROS parameters and keep a hardware
   E-stop operator in control.
3. Test on blocks, then at walking speed in a closed course. Log `/scan`,
   `/drive`, odometry, and diagnostics with rosbag.
4. Test failure conditions: unplug/stall scan, stop the algorithm, interrupt
   Jetson power, lose VESC communication, and hit E-stop. Each case must stop
   propulsion predictably.
5. Only consider higher speed or camera-assisted decisions after repeated
   low-speed runs, validated calibration, and a reviewed safety checklist.

**Acceptance gate:** reproducible low-speed obstacle avoidance, safe timeout
behavior, acceptable stopping distance, no competing `/drive` publisher, and
complete logs.

## Deliverable C — Camera, perception, and reconstruction

1. Confirm the camera model and host interface before ordering. OAK-D Lite is
   the suggested first prototype because a ROS 2 Humble driver and stereo
   depth pipeline are available. Confirm fit, USB, environment, frame rate,
   and range for your specific track.
2. Mount rigidly; record the lens baseline and camera-to-vehicle transform.
   Calibrate the rig and verify rectified left/right images and depth with
   known-distance targets.
3. Record synchronized images, calibration, `/scan`, `/drive`, and vehicle
   odometry in ROS bags. Save preview video separately; a video alone loses
   calibration/timestamps needed for depth reconstruction.
4. Add a detector after selecting target classes and a model that can run on
   the Jetson. Publish 2D detections; fuse detections with calibrated depth to
   create 3D object locations.
5. For persistent 3D reconstruction, add validated pose estimation/SLAM and
   register point clouds over time. Do not label per-frame disparity/cloud as
   a reconstructed map.
6. Keep camera perception advisory until detection, depth, timing, and failure
   modes are validated. Don't make the camera a `/drive` publisher by default.

## Git and completion

Work in feature branches and submit pull requests:

- `Algorithms` → `Motor-Control` / `Lidar-Camera-System` integration after
  interface agreement.
- `Lidar-Camera-System` provides real `/scan` and calibrated camera inputs.
- `Motor-Control` provides the verified `/drive` actuator gateway.
- Use `Feature-Simulation` for regression tests and keep `main` for reviewed,
  integrated releases.

Before calling the car demo-ready, attach: hardware inventory, wiring/power
diagram, exact JetPack/ROS/driver versions, build/test output, short
simulation and sensor rosbag, manual-control/E-stop sign-off, and the
low-speed autonomy test log.
