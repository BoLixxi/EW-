from setuptools import find_packages, setup

package_name = 'robot_stm32_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/cmd_vel_serial.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='MiniPC 与 STM32 底盘之间的串口通信模块',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'cmd_vel_serial_node = robot_stm32_bridge.cmd_vel_serial_node:main',
        ],
    },
)
