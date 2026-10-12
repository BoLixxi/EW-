#!/usr/bin/env python3
"""cmd_vel_serial_node.py — 订阅 cmd_vel 话题，经串口下发到 STM32。

功能:
  - 订阅 geometry_msgs/msg/Twist 话题（默认 /red_standard_robot1/cmd_vel）
  - 将 vx/vy/wz 打包为 22 字节二进制帧（见 protocol.py）
  - 以固定频率经串口发送
  - 串口打开失败时自动周期重试（设备热插拔可自动重连）
  - cmd_vel 断流超时后自动下发零速（安全停车）

所有参数均可通过 ROS 2 参数 / launch 文件覆盖，见 README.md。
"""

import threading
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from robot_stm32_bridge.protocol import pack_velocity_frame


class CmdVelSerialNode(Node):
    """订阅 cmd_vel，通过串口发送速度指令到 STM32。"""

    def __init__(self):
        super().__init__('cmd_vel_serial_node')

        # ---- 声明参数 (默认值见 README 参数表) ----
        self.declare_parameter('topic', '/red_standard_robot1/cmd_vel')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('send_rate', 50.0)
        self.declare_parameter('timeout_ms', 500)

        self._topic = self.get_parameter('topic').value
        self._port = self.get_parameter('port').value
        self._baud_rate = int(self.get_parameter('baud_rate').value)
        self._send_rate = float(self.get_parameter('send_rate').value)
        self._timeout_ms = int(self.get_parameter('timeout_ms').value)

        # ---- 速度缓存 (线程安全) ----
        self._lock = threading.Lock()
        self._vx = 0.0
        self._vy = 0.0
        self._wz = 0.0
        self._last_cmd_time = time.time()

        # ---- 串口句柄 (初始为 None, 由定时器周期重试打开) ----
        self._ser = None

        # ---- 订阅 cmd_vel ----
        self._sub = self.create_subscription(Twist, self._topic, self._cb, 10)
        self.get_logger().info(f'已订阅话题: {self._topic}')

        # ---- 定时发送 (含串口自动重连) ----
        self._timer = self.create_timer(1.0 / self._send_rate, self._tick)

        self.get_logger().info(
            f'节点就绪: 串口 {self._port} @ {self._baud_rate} bps, '
            f'发送频率 {self._send_rate} Hz, 超时 {self._timeout_ms} ms'
        )

    # ----------------------------------------------------------
    # 串口管理
    # ----------------------------------------------------------
    def _open_serial(self):
        """尝试打开串口，成功返回 Serial 对象，失败返回 None。"""
        try:
            import serial
            ser = serial.Serial(
                port=self._port,
                baudrate=self._baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.01,
            )
            self.get_logger().info(f'串口已打开: {self._port}')
            return ser
        except Exception as e:
            self.get_logger().warn(
                f'串口打开失败 ({self._port}): {e}，将自动重试',
                throttle_duration_sec=5.0,
            )
            return None

    def _ensure_serial(self):
        """串口未打开时尝试重连（设备插入后自动连上）。"""
        if self._ser is not None:
            return True
        self._ser = self._open_serial()
        return self._ser is not None

    # ----------------------------------------------------------
    # 回调与发送
    # ----------------------------------------------------------
    def _cb(self, msg: Twist):
        with self._lock:
            self._vx = float(msg.linear.x)
            self._vy = float(msg.linear.y)
            self._wz = float(msg.angular.z)
            self._last_cmd_time = time.time()

    def _tick(self):
        # 未打开串口则尝试打开，失败直接返回（下个周期再试）
        if not self._ensure_serial():
            return

        with self._lock:
            vx = self._vx
            vy = self._vy
            wz = self._wz
            last = self._last_cmd_time

        # 超时保护: cmd_vel 断流后自动停车
        now = time.time()
        if (now - last) > self._timeout_ms / 1000.0:
            vx = vy = wz = 0.0

        try:
            frame = pack_velocity_frame(vx, vy, wz)
            self._ser.write(frame)
            self._ser.flush()
        except Exception as e:
            self.get_logger().error(
                f'串口发送失败: {e}，将尝试重连',
                throttle_duration_sec=5.0,
            )
            # 发送异常通常意味着设备断开，关闭句柄以便重连
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def destroy_node(self):
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelSerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
