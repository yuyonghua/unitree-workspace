from setuptools import setup, find_packages

setup(
    name="go2_motion_G",
    version="0.1.0",
    description="Go2 advanced motion control module using RL policies",
    author="unitree-workspace",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "torch",
        "pyyaml",
        "mujoco",
        "unitree_sdk2py",
    ],
)
