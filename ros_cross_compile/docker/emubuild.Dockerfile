ARG BASE
FROM ${BASE}

# Build tool
RUN apt-get update && apt-get install -y \
      python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

COPY cc_artifacts/rosdep_apt.sh .
RUN apt-get update && \
    ./rosdep_apt.sh \
    && rm -rf /var/lib/apt/lists/*

COPY cc_artifacts/rosdep_other.sh .
RUN ./rosdep_other.sh
