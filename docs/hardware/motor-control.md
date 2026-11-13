# Motor-control integration

This workstream connects the standard FIV `/drive` command to the specific
VESC and steering hardware. The repository intentionally does not send motor
commands yet: the VESC model, firmware, motor, steering servo, actuator
connection, and electrical limits have not been identified.

## Current interface

The upstream simulator and FIV algorithms use
`ackermann_msgs/msg/AckermannDriveStamped` on `/drive`. On the `Algorithms`
branch, the `fiv_teleop drive_guard` node accepts bounded manual commands on
`/manual/drive`, then publishes `/drive`. The VESC gateway should be the only
hardware node consuming that command and should publish odometry, VESC
telemetry, and diagnostics.

```text
/manual/drive -> fiv_teleop drive_guard -> /drive -> VESC/servo gateway
fiv_gap_follow --------------------------^
```

Only one of teleop or autonomy should publish actuator commands at a time.
Do not treat ROS command timeouts as a substitute for an independent physical
emergency stop.

## Blockers to writing hardware-specific code

Record and review these before selecting or configuring a driver:

- VESC manufacturer, exact hardware model/revision, firmware version, and
  VESC Tool compatibility.
- Motor model, pole pairs, gearing, wheel radius, and chassis speed/current
  limits.
- Steering actuator model, connection method, servo range, mechanical stops,
  direction, and Ackermann steering calibration.
- VESC-to-computer connection (USB, UART, CAN, or other) and device path.
- Battery label and cell count. The stated OVONIC battery is 3S, 11.1 V
  nominal; a fully charged conventional 3S LiPo reaches 12.6 V. Verify
  voltage/current limits and low-voltage cutoff from the exact VESC and pack
  manuals.
- Power distribution, fuses, grounds, connectors, and the physical E-stop
  behavior.

Do not infer any of these from the battery's advertised C rating.

## ROS 2 driver decision

The F1TENTH [`vesc`](https://github.com/f1tenth/vesc) repository is a useful
reference, but its `vesc_driver` and `vesc_ackermann` manifests use ROS 1
`catkin`; they cannot be built directly into the Humble workspace. Select a
maintained ROS 2-compatible driver for your exact VESC hardware, or scope and
test a ROS 2 port separately. Verify protocol, firmware, and output scaling
with the VESC disconnected from the motor or wheels raised before enabling
actuation.

## Implementation acceptance criteria

1. Keep the ROS gateway in its own package, planned as `fiv_motor_control`.
2. Accept standard `AckermannDriveStamped`; validate finite values and clamp
   speed, steering, and acceleration limits from reviewed vehicle
   configuration.
3. Command zero on stale input, serial/network error, watchdog fault, or node
   shutdown. Report reason and hardware state in ROS diagnostics.
4. Configure a physical E-stop that does not depend on ROS, DDS, Linux, or
   camera inference.
5. Add tests for scaling, signs, clamp limits, watchdog, disconnection, and
   startup/shutdown. Test with a mock driver or motor disconnected first.
6. Confirm VESC output direction and steering response with driven wheels
   raised, low current limits, and a spotter. Validate the physical E-stop.
7. Conduct short, low-speed tests on a closed course before enabling
   Follow-the-Gap. Review logs and stopping distance after every change.

`ros_ws/src/fiv_motor_control/README.md` is the package landing area for this
workstream. It should not become an executable motor driver until the facts
above are verified.
