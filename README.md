## Overview

It is the on-board software and ground control system for an autonomous UAV. The system's primary function is to autonomously detect and engage targets, while providing a robust, real-time interface for human operators.

The architecture is built for reliability and real-time performance, utilizing a multi-threaded approach on a Raspberry Pi to handle concurrent tasks such as MAVLink communication, video processing, and hardware control. A dedicated Ground Control Station (GCS) application provides a comprehensive user interface for monitoring and control.

## System Architecture

The project is divided into two main components:

- **On-Board Software (`/rpi_code`)**:  
  The core Python application that runs on a Raspberry Pi connected to the UAV's hardware. It handles all sensor input, communication, and control logic.

- **Ground Control Station (`/control_station`)**:  
  A PyQt6-based desktop application that runs on a separate computer. It provides a visual and interactive interface for the operator.

## On-Board Software Features

- **MAVLink Telemetry**  
  Establishes a MAVLink connection with a Pixhawk flight controller, allowing it to read flight data (e.g., altitude, velocity, position) and send commands.
  
- **Physics Simulation**  
  A custom physics engine simulates projectile trajectories to calculate precise firing solutions based on the UAV's telemetry and the detected target's position.

- **Autonomous Engagement**  
  The system can automatically trigger the firing mechanism if a calculated firing solution meets a predefined accuracy threshold.

- **Hardware Control**  
  Directly controls a servo motor via Raspberry Pi GPIO pins to operate the physical firing mechanism.

- **Robustness**  
  Includes a failsafe mechanism that responds to lost RC signals, and comprehensive error logging to a console and file.

## Ground Control Station (GCS)

The GCS serves as the operator's primary interface for the entire mission. Its design emphasizes real-time feedback and intuitive control, featuring dedicated gauges, displays, and controls.

- **Main Dashboard**  
  The central display provides an at-a-glance view of all critical flight and system parameters.

  - **Live Video Feed**  
    Displays the perspective in real-time, with overlays of detected object bounding boxes for immediate visual feedback.

  - **Analog Gauges**  
    Visual gauges provide quick, intuitive readings of key flight data:
    - Altitude  
    - Velocity  
    - Heading  
    - Vehicle attitude (roll, pitch, yaw)  
    - Vertical Speed  
    - Ground Speed

  - **Digital Telemetry Panel**  
    Displays precise numerical values for all telemetry data received from the Pixhawk.

  - **GPS Panel**  
    Shows latitude, longitude, and altitude.

- **System Status Indicators**  
  Digital telemetry panel shows operational status of on-board systems:
  - Armed/Disarmed status  
  - Manual/Autonomous mode  
  - Detection status  
  - Firing mechanism status (readiness and state of both firing mechanisms)

- **Manual Control Interface**  
  Dedicated buttons and switches allow the operator to send commands via MAVLink `NAMED_VALUE_INT` messages, including:
  - Arm/Disarm toggle  
  - Mode toggle (manual/autonomous)  
  - Detection on/off toggle  
  - Manual fire buttons for each firing mechanism  
  - Deactivate all mechanisms command

## Communication Protocol

The system relies entirely on MAVLink for communication between the on-board software and the GCS, ensuring robust and low-latency data exchange.

## How to Run

1. **Configure**  
   Edit the `const.py` file to set your specific IP addresses, ports, and PWM values.

2. **Run On-Board Software** (on Raspberry Pi):

   ```bash
   python main.py <GCS_IP> <MISSION_PLANNER_IP> [IS_TELEM_TESTING] [IS_IMG_TESTING]
   ```

   ```bash
   <GCS_IP>: IP address of the computer running the GCS application. If MISSION_PLANNER_IP is not provided, it is also used as MISSION_PLANNER_IP

   <MISSION_PLANNER_IP>: IP address of the mission planner.

   [IS_TELEM_TESTING]: (Optional) 1 to enable local telemetry logging.

   [IS_IMG_TESTING]: (Optional) 1 to enable local video recording.
   ```

3. **Run Ground Control Station** (on operator PC):
    ```bash
    python gui.py

Author

Tuna EKİCİ
