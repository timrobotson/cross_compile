# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import logging
from pathlib import Path

from ros_cross_compile.docker_client import DockerClient
from ros_cross_compile.platform import Platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Rosdep Gatherer')


def build_rosdep_image(
    docker_client: DockerClient, platform: Platform, docker_dir: Path
) -> str:
    output_tag = 'rcc/rosdep:{arch}-{os_name}-{os_distro}'.format(
        arch=platform.arch,
        os_name=platform.os_name,
        os_distro=platform.os_distro,
    )

    logger.info('Building rosdep collector image: %s', output_tag)
    docker_client.build_image(
        dockerfile_dir=docker_dir,
        dockerfile_name='rosdep.Dockerfile',
        tag=output_tag,
        buildargs={
            'BASE_IMAGE': platform.native_base_image,
        },
    )
    logger.info('Successfully created rosdep collector image: %s', output_tag)
    return output_tag


def gather_rosdeps(
    docker_client: DockerClient, image_name: str, workspace: Path, ros_distro: str
):
    logger.info('Running rosdep collector image on workspace...')
    docker_client.run_container(
        image_name=image_name,
        environment={
            'ROSDISTRO': ros_distro,
        },
        volumes={
            workspace: '/root/ws'
        },
    )
