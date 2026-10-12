"""启动 cmd_vel_serial_node 节点的 launch 文件。

所有参数均可通过命令行覆盖，例如:

    ros2 launch robot_stm32_bridge cmd_vel_serial.launch.py \
        port:=/dev/ttyUSB0 topic:=/red_standard_robot1/cmd_vel baud_rate:=115200
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    topic_arg = DeclareLaunchArgument(
        'topic', default_value='/red_standard_robot1/cmd_vel',
        description='订阅的 cmd_vel 话题名'
    )
    port_arg = DeclareLaunchArgument(
        'port', default_value='/dev/ttyUSB0',
        description='串口设备路径'
    )
    baud_arg = DeclareLaunchArgument(
        'baud_rate', default_value='115200',
        description='串口波特率'
    )
    rate_arg = DeclareLaunchArgument(
        'send_rate', default_value='50.0',
        description='发送频率 (Hz)'
    )
    timeout_arg = DeclareLaunchArgument(
        'timeout_ms', default_value='500',
        description='cmd_vel 超时时间 (ms)，超时自动发零速'
    )

    node = Node(
        package='robot_stm32_bridge',
        executable='cmd_vel_serial_node',
        name='cmd_vel_serial_node',
        parameters=[{
            'topic': LaunchConfiguration('topic'),
            'port': LaunchConfiguration('port'),
            'baud_rate': LaunchConfiguration('baud_rate'),
            'send_rate': LaunchConfiguration('send_rate'),
            'timeout_ms': LaunchConfiguration('timeout_ms'),
        }],
        output='screen',
    )

    return LaunchDescription([
        topic_arg, port_arg, baud_arg, rate_arg, timeout_arg, node,
    ])
