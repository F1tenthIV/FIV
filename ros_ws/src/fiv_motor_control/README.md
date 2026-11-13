# FIV motor-control package landing area

No motor-control ROS package is implemented yet. First record the exact VESC
hardware/firmware, motor, servo, connection, power diagram, and emergency-stop
behavior as requested by
[the motor-control integration checklist](../../../docs/hardware/motor-control.md).

The planned package will consume bounded
`ackermann_msgs/msg/AckermannDriveStamped` commands on `/drive`, drive the
verified VESC and steering actuator, and report telemetry/odometry. Do not
copy the ROS 1 `catkin` F1TENTH VESC packages directly into this ROS 2 Humble
workspace.

No actuator commands are sent by this placeholder.
