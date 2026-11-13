# Bounded manual drive commands

`fiv_teleop` provides a small safety gate for manual Ackermann messages. It
subscribes to `/manual/drive`, clamps speed to 0.25 m/s and steering to
±0.30 rad by default, disables reverse, and publishes to `/drive`. If manual
commands stop for 0.5 seconds, it sends a zero-speed command. These software
limits are not a physical emergency stop and do not replace the VESC's
verified current/voltage limits.

## Run

Build the package, then start the drive guard:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run fiv_teleop drive_guard
```

In another terminal, send a held-forward command:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic pub --rate 10 /manual/drive \
  ackermann_msgs/msg/AckermannDriveStamped \
  "{drive: {speed: 0.10, steering_angle: 0.0}}"
```

Stop the publisher with Ctrl+C; the guard should publish zero speed after the
timeout. Change only the `speed` and `steering_angle` fields for low-speed
steering checks. Inspect `/drive` before attaching motor output.

Exactly one node should publish actuator commands on `/drive`. Stop the
autonomous controller before starting manual control. Begin with wheels raised,
the motor power disabled or limited, a physical emergency stop available, and
a spotter. Do not use this package on the physical chassis until the exact
VESC/servo gateway and power limits are verified.
