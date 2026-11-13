from setuptools import find_packages, setup


package_name = 'fiv_teleop'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='FIV Team',
    maintainer_email='fiv-team@example.com',
    description='Bounded manual Ackermann command gateway for FIV.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'drive_guard = fiv_teleop.drive_guard:main',
        ],
    },
)
