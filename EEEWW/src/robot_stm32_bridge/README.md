# robot_stm32_bridge

ROS 2 Python 节点：订阅 `cmd_vel`，通过串口将速度指令发送给 STM32。

默认串口为 `/dev/ttyUSB0`，默认波特率为 `115200`，并在 `cmd_vel` 超时后发送零速度。
