from setuptools import setup
from glob import glob
import os

package_name = 'robot_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='alexandre',
    maintainer_email='alexandre.evain76@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [ 'rbt_control = robot_control.rbt_control:main',
			     'fake_gps = robot_control.fake_gps:main',
        ],
    },
)
#(['launcher.launch.py', 'launcher_robot_eloquent.launch.py', 'launcher_robot_foxy.launch.py']),

