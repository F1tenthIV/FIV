from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'fiv_lidar_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='FIV Team',
    maintainer_email='fiv-team@example.com',
    description='ROS 2 bringup configuration for the Hokuyo UST-10LX.',
    license='MIT',
    tests_require=['pytest'],
)
