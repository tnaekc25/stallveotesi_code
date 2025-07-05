import os
os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")

from pymavlink import mavutil
import time, cv2
from threading import Thread


class MavCom:

    def __init__(self):

        self.mav_in = None
        self.mav_out = None

        self.attitude = (0, 0, 0)
        
        self.heading = 0
        self.altitude = 0 

        self.airspeed = 0
        self.ground_speed = 0

        self.cont_inputs = (0, 0, 0, 0)

        self.gps_pos = (0, 0)

        self.battery_volt = 0
        self.battery_per = 0


    def connect(self, ip, port1, port2):

        if (self.mav_out and self.mav_in):
            self.close()

        self.mav_in = mavutil.mavlink_connection(f'udpin:0.0.0.0:{port1}')
        self.mav_out = mavutil.mavlink_connection(f'udpout:{ip}:{port2}')

        print(">>> Sending Heartbeat...")
        self.mav_out.mav.heartbeat_send(
                type=mavutil.mavlink.MAV_TYPE_GCS,
                autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                base_mode=0,
                custom_mode=0,
                system_status=mavutil.mavlink.MAV_STATE_ACTIVE
            )

        print("Sent!")


    def close(self):
        self.mav_in.close()
        self.mav_out.close()


    def recv_message(self):

        msg = self.mav_in.recv_match(blocking=True)
        if not msg:
            return 0
    
        msg_type = msg.get_type()
    
        # Attitude
        if msg_type == "ATTITUDE":
            self.attitude = (msg.roll, msg.pitch, msg.yaw)
            return 1
    
        # Airspeed, Ground speed, Altitude, Heading
        elif msg_type == "VFR_HUD":
            self.airspeed = msg.airspeed
            self.ground_speed = msg.groundspeed
            self.heading = msg.heading
            self.altitude = msg.alt if msg.alt > 0 else 0
            return 1
    
        # GPS Position
        elif msg_type == "GLOBAL_POSITION_INT":
            self.gps_pos = (msg.lat / 1e7, msg.lon / 1e7)
            return 1
    
        # Battery Status
        elif msg_type == "SYS_STATUS":
            self.battery_volt = msg.voltage_battery / 1000.0
            self.battery_per = msg.battery_remaining
            return 1
    
        # Control Inputs (throttle, roll, pitch, yaw)
        elif msg_type == "RC_CHANNELS_RAW":
            self.cont_inputs = (msg.chan3_raw, msg.chan1_raw, msg.chan2_raw, msg.chan4_raw)
            return 1

    def send_button(self, i):
        self.mav_out.mav.named_value_int_send(
            int(i*10),
            b"button_data",
            i
        )


class ImageCom:
    def __init__(self, port):

        self.cap = None

        gst_pipeline = (
            f"udpsrc port={port} caps=application/x-rtp,media=video,encoding-name=H264,payload=96 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
        )

        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    def get_img(self):
        if (self.cap):
            ret, last = self.cap.read()
            return last
        return None

    def close():
        if (self.cap):
            self.cap.release()