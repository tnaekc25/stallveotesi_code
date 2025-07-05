from pymavlink import mavutil
import time
import numpy as np

# Your main code should listen on this
DEST_IP = "127.0.0.1"
DEST_PORT = 15555  # Change if needed

# Create a MAVLink UDP output to your main script
pixhawk_sim = mavutil.mavlink_connection(f'udpout:{DEST_IP}:{DEST_PORT}')

print(">>> Pixhawk Simulator started. Sending fake telemetry...")

i = 0
while True:
    roll = abs(np.sin(i / 100) * np.pi * 2)
    pitch = np.sin(i / 100) * np.pi * 2
    yaw = np.sin(i / 100) * np.pi * 2

    pixhawk_sim.mav.heartbeat_send(
        type=mavutil.mavlink.MAV_TYPE_QUADROTOR,
        autopilot=mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        base_mode=0,
        custom_mode=0,
        system_status=mavutil.mavlink.MAV_STATE_ACTIVE
    )

    pixhawk_sim.mav.attitude_send(
        time_boot_ms=i * 100,
        roll=roll,
        pitch=pitch,
        yaw=yaw,
        rollspeed=0,
        pitchspeed=0,
        yawspeed=0
    )

    pixhawk_sim.mav.vfr_hud_send(
        airspeed=12.5,
        groundspeed=13.0,
        alt=100.0 + np.sin(i / 20) * 10,
        climb=0.5,
        heading=90,
        throttle=50
    )

    pixhawk_sim.mav.local_position_ned_send(
        time_boot_ms=i * 100,
        x=0,
        y=0,
        z=-100.0 + np.sin(i / 20) * 5,  # Negative Z for altitude in NED
        vx=0.5,
        vy=0.0,
        vz=-0.2
    )

    time.sleep(0.1)
    i += 1
