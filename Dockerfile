FROM osrf/ros:humble-desktop

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-vcstool \
    python3-rosdep \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pymycobot
RUN pip3 install pymycobot --upgrade

# Set locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Create workspace
WORKDIR /ros2_ws/src

# Copy the repository into the workspace
COPY . mycobot_ros2

# Import additional repositories
WORKDIR /ros2_ws
RUN vcs import src < src/mycobot_ros2/warehouse_ros_mongo.repos

# Install workspace dependencies
RUN apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -y

# Build the workspace
RUN . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install

# Setup environment for interactive shell
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

# Entrypoint setup
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["bash"]
