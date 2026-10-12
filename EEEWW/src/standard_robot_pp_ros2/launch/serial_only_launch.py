# Copyright 2025 SMBU-PolarBear-Robotics-Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("standard_robot_pp_ros2")

    device_name = LaunchConfiguration("device_name")
    cmd_vel_topic = LaunchConfiguration("cmd_vel_topic")

    declare_device_name = DeclareLaunchArgument(
        "device_name", default_value="/dev/ttyACM0", description="上位机串口设备"
    )
    declare_cmd_vel_topic = DeclareLaunchArgument(
        "cmd_vel_topic",
        default_value="/cmd_vel",
        description="cmd_vel 订阅主题（跨 namespace 需用绝对名）",
    )

    # 先清空串口积压缓冲区：下位机持续发送无人读取时会残留半截帧，
    # 节点 open 后第一次读到从帧中间切开的字节会触发一次 CRC8 error。
    clear_serial = ExecuteProcess(
        cmd=[
            "bash",
            "-c",
            ["timeout 1 cat ", device_name, " > /dev/null 2>&1 || true"],
        ],
        output="screen",
    )

    serial_node = Node(
        package="standard_robot_pp_ros2",
        executable="standard_robot_pp_ros2_node",
        name="standard_robot_pp_ros2",
        output="screen",
        parameters=[
            os.path.join(pkg_dir, "config", "standard_robot_pp_ros2.yaml"),
            {"device_name": device_name},
        ],
        remappings=[("cmd_vel", cmd_vel_topic)],
    )

    # 清空缓冲区完成后再启动串口节点
    serial_node_after_clear = RegisterEventHandler(
        OnProcessExit(target_action=clear_serial, on_exit=[serial_node])
    )

    ld = LaunchDescription()
    ld.add_action(declare_device_name)
    ld.add_action(declare_cmd_vel_topic)
    ld.add_action(clear_serial)
    ld.add_action(serial_node_after_clear)
    return ld
