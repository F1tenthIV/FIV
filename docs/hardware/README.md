# Hardware and deployment plan

This folder is the hardware handoff for moving FIV from simulation to the
physical chassis. The simulator remains a development/test tool. On the car,
the same ROS 2 algorithms consume the real LiDAR topic; do not run the Gym
simulator as the vehicle's sensor source while controlling the physical car.

## Confirmed hardware and decisions

| Item | Current information | What still needs confirmation |
|---|---|---|
| Computer | NVIDIA Jetson Orin Nano Developer Kit | Exact module/RAM and firmware revision |
| OS storage | microSD card | Card size and current JetPack/QSPI version |
| LiDAR | Hokuyo UST-10LX, Ethernet | Verify sensor IP and cable/power accessories |
| Battery | OVONIC 6500 mAh, 130C, 3S LiPo, 11.1 V nominal | Verify label, connector, VESC model, motor and steering servo |
| Camera | Not selected | Prefer OAK-D Lite for the first ROS 2 stereo prototype |
| ROS | Humble | Keep Jetson on JetPack 6.x / Ubuntu 22.04 for the first integrated build |

The 3S battery's nominal voltage is not its maximum voltage: a conventional
3S LiPo is 12.6 V when fully charged. Verify the cell count and charger
settings against the battery label. Do not treat the pack's advertised 130C
rating as a safe design current.

## Target architecture

```text
UST-10LX Ethernet
       |
       v
urg_node -> /scan (sensor_msgs/LaserScan) ---+
                                             |
Stereo camera -> images/depth/detections ----+--> perception/algorithm
                                                  (autonomy first uses LiDAR)
                                                          |
                                                  /drive (AckermannDriveStamped)
                                                          |
                                               VESC + steering actuator
                                                          |
                                                      chassis

F1TENTH Gym simulator supplies simulated /scan and accepts /drive for
desktop testing only. Swap simulated /scan for the real sensor on the car.
```

Keep the sensor, algorithm, and motor driver as separate ROS nodes. Use one
intentional owner of the actuator command at a time: manual teleoperation or
autonomy, never two publishers racing to `/drive`. Add a command mux and a
hardware emergency-stop path before autonomous runs.

## Power and wiring review

The Hokuyo UST-10LX is specified for 12/24 V DC, an operating range of
10–30 V, and 100BASE-TX Ethernet. It draws up to 150 mA in operation and needs
450 mA during startup. The sensor requires a suitable DC supply; Ethernet does
not power it.

- Keep the motor/VESC supply separate from regulated compute and sensor
  supplies. Do not connect a raw battery lead to the Jetson, sensor, or
  camera unless the exact device documentation explicitly approves that
  connection.
- Choose regulated rails, converters, wiring, fuse protection, connectors,
  and current margin from the exact VESC, Jetson input, sensor, and camera
  documentation. The LiDAR rail must remain within 10–30 V and support its
  startup current. If the battery can fall below the regulator's input range,
  choose an appropriate converter rather than assuming nominal voltage.
- Have the team verify polarity, fuse ratings, grounding, connector pinouts,
  and battery low-voltage cutoff before energizing the chassis. Keep a
  physical emergency stop accessible.
- For initial motor tests, raise the driven wheels, restrain the chassis,
  reduce current/speed limits, and keep a person at the physical stop.

This guide is not a substitute for the VESC, battery, carrier-board, or power
converter manuals. Do not infer the VESC/servo wiring or ratings from the
battery label.

## Jetson Linux storage

Use the NVIDIA JetPack 6.2.1 / Jetson Linux 36.4.4 path as the initial baseline:
it supports the Orin Nano Developer Kit and aligns with Ubuntu 22.04 + ROS 2
Humble. NVIDIA's JetPack 6.2.1 instructions explicitly provide a JetPack 6.2
microSD-card installation path for Orin Nano Dev Kits. Use a 64 GB or larger
UHS-I card. Check the board's QSPI/firmware requirements before flashing,
especially for a fresh or JetPack 5.x board.

1. Back up anything on the microSD card; flashing erases it.
2. Download the JetPack 6.2/6.2.1 image and follow NVIDIA's Orin Nano
   Developer Kit SD-card guide with Balena Etcher.
3. Insert the card, boot the kit, finish Ubuntu's first-boot setup, and verify
   the installed JetPack/L4T release before installing ROS.
4. Install ROS 2 Humble and the required packages on Ubuntu 22.04. Build and
   test the workspace directly on the ARM64 Jetson; don't copy x86_64 build
   outputs from WSL.
5. Keep source in `~/FIV` on the Jetson's Linux filesystem. Git stores source,
   not the Linux OS image. Don't build from `/mnt/c/...` on the Jetson; it is
   a Windows path and not the Jetson's native filesystem.
6. Track provisioning commands and versions in this repository, but never
   commit OS images, credentials, bag files, or model weights without an
   agreed storage policy.

JetPack 7.2 and later have a different Jetson ISO installation flow; NVIDIA
notes that SD-card images are no longer supported there. Don't follow the
JetPack 7 flow if the team is keeping the JP6/Humble microSD baseline.

## First camera recommendation

For the first camera purchase, evaluate **Luxonis OAK-D Lite**: it has a
stereo pair and RGB camera, supports ROS 2 Humble through `depthai-ros`, and
can publish stereo depth/AI results. It avoids starting with two independent
cameras that need separate synchronization and calibration. This is a
recommendation, not a confirmed purchase; check mounting, USB 3 bandwidth,
outdoor lighting, desired frame rate, depth range, price, and Jetson driver
compatibility before ordering. Luxonis quotes an ideal stereo range around
0.8–12 m, with shorter-range modes depending on resolution/settings.

Use the camera first for image/depth recording and object detections, not for
steering. The current generic stereo launch expects rectified camera topics;
OAK's own ROS driver may expose different topic names and a depth topic, so
adapt `fiv_camera` to the chosen driver rather than assuming the generic launch
will connect unchanged.

A per-frame point cloud is not complete 3D reconstruction. A persistent
reconstruction needs a pose source (for example calibrated visual-inertial or
LiDAR-inertial odometry/SLAM), timestamp alignment, and registration of depth
frames. Make that a later milestone after collecting calibrated sensor data.

## Workstreams

- [Deliverable checklist and sequence](deliverables.md): Jetson setup, LiDAR,
  simulator, manual control, autonomy, and acceptance gates.
- [Generated step-by-step PDF](FIV_Hardware_Integration_Plan.pdf): a shareable
  runbook built from the hardware, deliverables, and motor-control guides.

Regenerate the PDF after editing either source guide:

```powershell
py -m pip install reportlab
py docs\hardware\generate_plan_pdf.py
```
- `Feature-Simulation`: Gym bridge + Follow the Gap on simulated `/scan`.
- `Algorithms`: testable algorithms and safe command-line/keyboard teleop.
- `Motor-Control`: identify/validate the exact ROS 2 VESC + steering driver,
  calibrate limits, and add actuator safety.
- `Lidar-Camera-System`: UST-10LX bringup, camera driver, timestamps, TF,
  calibration, data recording, and later sensor fusion.

The ROS 1 `f1tenth/vesc` repository contains `catkin` packages. Don't assume
those packages can be built in this ROS 2 Humble workspace; select a maintained
ROS 2 driver or port and validate it with the exact VESC hardware/firmware
before connecting motor outputs.

See the [motor-control checklist](motor-control.md) and the
[`fiv_motor_control` landing area](../../ros_ws/src/fiv_motor_control/README.md).

## Reference sources

- [Hokuyo UST-10LX specifications](https://www.hokuyo-aut.jp/search/single.php?serial=167)
- [ROS 2 urg_node documentation](https://docs.ros.org/en/humble/p/urg_node/)
- [urg_node ROS 2 branch](https://github.com/ros-drivers/urg_node/tree/jazzy)
- [NVIDIA JetPack 6.2.1 installation guide](https://docs.nvidia.com/jetson/jetpack/6.2.1/install-setup/index.html)
- [NVIDIA JetPack 6.2.1 release notes](https://docs.nvidia.com/jetson/jetpack/6.2.1/release-notes/index.html)
- [Luxonis DepthAI ROS documentation](https://docs.luxonis.com/software/ros/depthai-ros/)
- [Luxonis OAK-D Lite specifications](https://docs.luxonis.com/hardware/products/OAK-D%20Lite)
- [F1TENTH VESC repository](https://github.com/f1tenth/vesc)
- [VESC Tool documentation](https://vesc-project.com/vesc_tool)
