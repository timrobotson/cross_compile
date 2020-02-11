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
from typing import Dict
from typing import Optional

import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Docker Image Builder')


class DockerClient:
    """Provide a simplified Docker API for this package's usage patterns."""

    def __init__(self, nocache):
        self._client = docker.from_env()
        self._nocache = nocache

    def build_image(
        self,
        dockerfile_dir: Path,
        dockerfile_name: str,
        tag: str,
        buildargs: Optional[dict],
    ) -> None:
        # Use low-level API to expose build logs
        docker_api = docker.APIClient(base_url='unix://var/run/docker.sock')
        # Note the difference:
        # path – Path to the directory containing the Dockerfile
        # dockerfile – Path within the build context to the Dockerfile
        log_generator = docker_api.build(
            path=str(dockerfile_dir),
            dockerfile=dockerfile_name,
            tag=tag,
            buildargs=buildargs,
            quiet=False,
            nocache=self._nocache,
            decode=True,
        )
        self._process_build_log(log_generator)

    def _process_build_log(self, log_generator) -> None:
        for chunk in log_generator:
            # There are two outputs we want to capture, stream and error.
            # We also process line breaks.
            error_line = chunk.get('error', None)
            if error_line:
                logger.exception(
                    'Error building Docker image. The follow error was caught:\n%s'.format(
                        error_line))
                raise docker.errors.BuildError(error_line)
            line = chunk.get('stream', '')
            line = line.rstrip().lstrip()
            if line:
                logger.info(line)

    def run_container(
        self, image_name: str, environment: Dict[str, str], volumes: Dict[Path, str]
    ) -> None:
        container = self._client.containers.run(
            image=image_name,
            environment=environment,
            volumes={
                str(src): {'bind': dest, 'mode': 'rw'}
                for src, dest in volumes.items()
            } if volumes else {},
            remove=True,
            detach=True,
            network_mode='host',
        )
        logs = container.logs(stream=True)
        for line in logs:
            logger.info(line.decode('utf-8').rstrip())
