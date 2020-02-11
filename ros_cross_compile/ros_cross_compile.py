#!/usr/bin/env python

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

"""Executable for cross-compiling ROS and ROS 2 packages."""

import argparse
import logging
import os
from pathlib import Path
import sys
from typing import List

from ros_cross_compile.builders import run_emulated_docker_build
from ros_cross_compile.dependencies import build_rosdep_image
from ros_cross_compile.dependencies import gather_rosdeps
from ros_cross_compile.docker_client import DockerClient
from ros_cross_compile.platform import Platform
from ros_cross_compile.platform import SUPPORTED_ARCHITECTURES
from ros_cross_compile.platform import SUPPORTED_ROS2_DISTROS
from ros_cross_compile.platform import SUPPORTED_ROS_DISTROS
from ros_cross_compile.sysroot_creator import SysrootCreator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='ros_cross_compile',  # this can be invoked from __main__.py, so be explicit
        description='Sysroot creator for cross compilation workflows.')
    parser.add_argument(
        '-a', '--arch',
        required=True,
        type=str,
        choices=SUPPORTED_ARCHITECTURES,
        help='Target architecture')
    parser.add_argument(
        '-d', '--rosdistro',
        required=False,
        type=str,
        default='dashing',
        choices=SUPPORTED_ROS_DISTROS + SUPPORTED_ROS2_DISTROS,
        help='Target ROS distribution')
    parser.add_argument(
        '-o', '--os',
        required=True,
        type=str,
        # NOTE: not specifying choices here, as different distros may support different lists
        help='Target OS')
    parser.add_argument(
        '--sysroot-base-image',
        required=False,
        type=str,
        help='Override the default base Docker image to use for building the sysroot. '
             'Ex. "arm64v8/ubuntu:bionic"')
    parser.add_argument(
        '--sysroot-nocache',
        action='store_true',
        required=False,
        help="When set to true, this disables Docker's cache when building "
             'the Docker image for the workspace')
    parser.add_argument(
        '--ros-workspace',
        required=False,
        type=str,
        default='ros_ws',
        help="The subdirectory of 'sysroot' that contains your 'src' to be built."
             'The output of the cross compilation will be placed in this directory. '
             "Defaults to 'ros_ws'.")
    parser.add_argument(
        '--sysroot-path',
        required=False,
        default=os.getcwd(),
        type=str,
        help="The absolute path to the directory containing 'sysroot' where the "
             "'ros2_ws/src' and 'qemu-user-static' directories you created can be found. "
             'Defaults to the current working directory.')
    parser.add_argument(
        '--custom-setup-script',
        required=False,
        default=None,
        type=str,
        help='Provide a path to a shell script that will be executed in the sysroot container '
             'right before running "rosdep install" for your ROS workspace. This allows for '
             'adding extra apt sources that rosdep may not handle, or other arbitrary setup that '
             'is specific to your application build. See the section on "Custom Setup Script" '
             'in the README.md for more details.')
    parser.add_argument(
        '--custom-data-dir',
        required=False,
        default=None,
        type=str,
        help='Provide a path to a custom arbitrary directory to copy into the sysroot container. '
             'You may use this data in your --custom-setup-script, it will be available as '
             '"./custom_data/" in the current working directory when the script is run.')
    parser.add_argument(
        '--skip-rosdep',
        action='store_true',
        help='Skip checking the workspace for rosdeps. '
             'NOTE that this will cause the buiild to fail if this step has not been run before, '
             'or if you have added new dependencies since the last check.')

    return parser.parse_args(args)


def setup_data_dir():
    """
    Set up the working directory where this tool will build Docker images.

    We need to copy files into this directory.
    The user potentially installed this package into a place needing root privileges to write.
    Therefore, we can't use the existing Dockerfiles in place,
    so we create a directory under the user's home.
    """
    user_config_dir = Path.home() / '.ros_cross_compile' / 'bin'
    user_config_dir.mkdir(parents=True, exists_ok=True)

    if sys.platform == 'linux':
        # copy qemu bins
        pass


def main():
    """Start the cross-compilation workflow."""
    # Configuration
    args = parse_args(sys.argv[1:])
    platform = Platform(args.arch, args.os, args.rosdistro, args.sysroot_base_image)
    docker_client = DockerClient(args.sysroot_nocache)
    sysroot = Path(args.sysroot_path).resolve()
    ros_workspace = sysroot / args.ros_workspace
    docker_dir = Path(__file__).parent / 'docker'

    # cross-compile pipeline
    if not args.skip_rosdep:
        rosdep_image = build_rosdep_image(docker_client, platform, docker_dir)
        gather_rosdeps(docker_client, rosdep_image, ros_workspace, platform.ros_distro)

    sysroot_creator = SysrootCreator(cc_root_dir=args.sysroot_path,
                                     ros_workspace_dir=args.ros_workspace,
                                     platform=platform,
                                     custom_setup_script_path=args.custom_setup_script,
                                     custom_data_dir=args.custom_data_dir)
    sysroot_creator.create_workspace_sysroot_image(docker_client)
    run_emulated_docker_build(docker_client, platform.sysroot_image_tag, ros_workspace)


if __name__ == '__main__':
    if sys.version_info < (3, 5):
        logger.warning('You are using an unsupported version of Python.'
                       'Cross-compile only supports Python >= 3.5 per the ROS2 REP 2000.')
    try:
        main()
    except Exception as e:
        logger.exception(e)
        exit(1)
