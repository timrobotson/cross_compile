# Dockerfiles for cross compiling workflow

The dockerfiles in this directory are used for phases of the cross-compilation build.

Some of their use is non-obvious due to optimization of the build steps, so their purpose is described here.

## Prerequisite setup

Create a folder called `bin/` here.

```
cp /usr/bin/qemu-*-static bin/
```

## Global tagging conventions

* All images built by this tool will start with `rcc/` (for `ROS Cross Compile`)
* All Dockerfiles are named PURPOSE.Dockerfile - images built will be named `rcc/PURPOSE`
* Tags for all images are `OS-DISTRO-ROS_VERSION`, e.g. `ubuntu-bionic-ros2` or `ubuntu-xenial-ros`

A complete example:
* Input: `rosdep.Dockerfile`
* Target: ROS2 on Ubuntu Bionic
* Tag for build `rcc/rosdep:ubuntu-bionic-ros2`

## base.Dockerfile

Create an image that has the ROS apt repos available.
Installs only necessary dependencies to set the locale, get apt keys, and update apt lists.

### Building

Required arguments:
* `OS_BASE`: the image to be FROM
* `ROS_VERSION`: `ros` or `ros2`

Example:

```
docker build . -f base.Dockerfile \
  -t rcc/base:ubuntu-bionic-ros2 \
  --build-arg OS_BASE=ubuntu:bionic \
  --build-arg ROS_VERSION=ROS_VERSION
```

### Usage

This image is used as a base for subsequent stages.


## rosdep.Dockerfile

Extends [`base`](#-base.Dockerfile)

Installs `colcon` and `rosdep` in order to determine the necessary dependencies for a build.
Note that `rosdep` resolution is not architecture-dependent, so the tool collects `rosdep` dependencies on the host native architecture for speed.
It is intended to be built ahead of time and invoked against a source workspace to collect its dependencies.

### Building

Required arguments:
* `OS_BASE`: the `base.Dockerfile`-built image to inherit from

Example:

```
docker build . -f rosdep.Dockerfile \
  --build-arg OS_BASE=rcc/base:ubuntu-bionic-ros2 \
  -t rcc/rosdep:ubuntu-bionic-ros2
```

### Usage

Required variables:
* environment variable `PACKAGE`: the root package of your workspace, we will be installing dependencies for `--packages-up-to` this value
* environment variable `ROSDISTRO`: the ROS distribution you are building against
* mounted colcon workspace at `/root/ws` - the script will look here to find your sources

Output:
* A directory `cc_artifacts` in your ROS workspace, contents:
  * `rosdep_apt.sh` contains a single line apt-get command (an optimization for speed over many commands)

Example:

```
docker run \
  -v ~/my_robot_ws:/root/ws \
  -e PACKAGE=robot_runtime \
  -e ROSDISTRO=eloquent \
  rcc/rosdeps:ubuntu-bionic-ros2
```
