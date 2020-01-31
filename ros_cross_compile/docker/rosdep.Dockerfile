ARG OS_BASE
FROM ${OS_BASE}

RUN apt-get update && apt-get install -y \
      python-rosdep \
      python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init && rosdep update
COPY gather_rosdeps.sh /root/
RUN mkdir -p /root/ws
WORKDIR /root/ws
ENTRYPOINT ["/root/gather_rosdeps.sh"]
