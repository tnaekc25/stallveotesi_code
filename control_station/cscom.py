import os
os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2, time

from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QPalette, QColor, QFont, QImage, QPen


from pymavlink import mavutil
from threading import Thread, Lock
from random import randint



class MavCom:

    def __init__(self):

        self.mav_in = None
        self.mav_out = None

        self.attitude = (0, 0, 0)
        
        self.heading = 0
        self.altitude = 0 

        self.airspeed = 0
        self.ground_speed = 0
        self.vertical_speed = 0

        self.cont_inputs = (0, 0, 0, 0)

        self.gps_pos = (0, 0)

        self.battery_volt = 0
        self.battery_per = 0


        self.is_armed = 0
        self.control_mode = 0
        self.left_stat = 0
        self.right_stat = 0
        self.is_det = 0


        self.last_heartbeat = -1
        self.start_time = time.time()
        self.connected = False

        self.boxes = []
        self.waypoints = []
        self.current_wp = -1

        self.comm_lock = Lock()


        #self.fp = open("out.txt", "r")


    def connect(self, ip, port1, port2):
        self.mav_in = mavutil.mavlink_connection(f'udpin:0.0.0.0:{port1}')
        self.mav_out = mavutil.mavlink_connection(f'udpout:{ip}:{port2}')

        print(">>> Created mavlink connection...")

        self.mav_out.mav.heartbeat_send(
                type=mavutil.mavlink.MAV_TYPE_GCS,
                autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                base_mode=0,
                custom_mode=0,
                system_status=mavutil.mavlink.MAV_STATE_ACTIVE
            )

        print(">>> Heartbeat Sent...")


    def close(self):

        self.connected = False
        self.last_heartbeat = -1

        if (self.mav_in):
            self.mav_in.close()
        if (self.mav_out):
            self.mav_out.close()

        self.mav_in = None
        self.mav_out = None

        print(">>> Mavlink connection closed...")


    def check_connection(self):

        if (self.last_heartbeat < 0):
            return

        elif (time.time() - self.last_heartbeat > 20):
            print(">>> CONNECTION LOST for 20 SEC, CLOSING...")
            self.close()

        elif (time.time() - self.last_heartbeat > 10):
            print(">>> CONNECTION LOST for 10 SEC...")
            

    def recv_message(self):

        with self.comm_lock:

            msg = self.mav_in.recv_match(blocking=True)
            if not msg:
                return 0
        
            msg_type = msg.get_type()
        
            if msg_type == "HEARTBEAT":
                self.last_heartbeat = time.time()
                self.connected = True
                #print(f">>> HEARTBEAT RECV AT {self.last_heartbeat-self.start_time}")
    
                return 1
    
            # Attitude
            elif msg_type == "ATTITUDE":
                self.attitude = (msg.roll, msg.pitch, msg.yaw)
                return 1
        
            # Airspeed, Ground speed, Altitude, Heading
            elif msg_type == "VFR_HUD":
                self.airspeed = msg.airspeed
                self.ground_speed = msg.groundspeed
                self.vertical_speed = msg.climb
                self.heading = msg.heading
                return 1
        
            # GPS Position
            elif msg_type == "GLOBAL_POSITION_INT":
                self.gps_pos = (msg.lat / 1e7, msg.lon / 1e7)
                self.altitude = (msg.relative_alt / 1000) if msg.relative_alt > 0 else 0
                return 1
        
            # Battery Status
            elif msg_type == "SYS_STATUS":
                self.battery_volt = msg.voltage_battery / 1000.0
                self.battery_per = msg.battery_remaining
                return 1
        
            # Control Inputs (throttle, roll, pitch, yaw)
            elif msg_type == "RC_CHANNELS":
                self.cont_inputs = [msg.chan3_raw, msg.chan1_raw, msg.chan2_raw, msg.chan4_raw]
                self.cont_inputs = tuple([(max(0, min(1, ((x-988) / 993))) if x is not None else 0) for x in self.cont_inputs])
                return 1
    
            elif msg_type == "MISSION_CURRENT":
                self.current_wp = msg.seq
    
            elif msg_type == "STATUSTEXT":
                recvd = (msg.text.rstrip('\x00'))
    
                if len(recvd) > 6:
                    if recvd[0:6] == "BOXINF":
                        self.boxes.append(tuple(map(int, recvd[7:-1].split(','))))
    
                    elif len(recvd) > 7:
                        if recvd[0:7] == "STATINF":
                            spltted = list(recvd[7:])
                            if (len(spltted) > 4):
                                self.is_armed = (spltted[0] == '1')
                                self.control_mode = (spltted[1] == '1')
                                self.left_stat = (spltted[2] == '1')
                                self.right_stat = (spltted[3] == '1')
                                self.is_det = (spltted[4] == '1')
    
                        elif len(recvd) > 8:
                            if recvd[0:8] == "WAYPOINT":
                                spltd = recvd[9:-1].split(',')
                                wp = (float(spltd[0]), float(spltd[1]), int(float(spltd[2])))
                                self.waypoints.append(wp)
    
                return 1

        return 0


    def send_button(self, i):
        if (self.connected):
            self.mav_out.mav.named_value_int_send(
                int(i*10),
                b"button_data",
                i
            )

    def draw_rect(self, img):
        if (self.boxes):
            box = self.boxes[-1]
            self.boxes.pop()
            cls, x1, y1, x2, y2 = box
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255 if cls else 0, 0 if cls else 255), 2)
        




        ## TESTING ##
    def read_test(self):


        if (self.mav_in == None):
            return

        def exg(inp):
            return max(0, min(1, 0.5 + (inp-0.5)*1.2))


        line = self.fp.readline()

        time.sleep(0.056)

        arr = [float(x) for x in line.split(" ")]
    
        self.attitude = (arr[3], arr[4], arr[5])
        
        self.heading = arr[6]
        self.altitude = arr[2] 
    
        self.airspeed = arr[1]*0.8
        
        self.ground_speed = arr[13]
        self.vertical_speed = arr[14]
    
        self.cont_inputs = list(map(exg, (arr[7], arr[8], arr[9], arr[10])))
    
        self.gps_pos = (arr[11], arr[12])
    
        self.battery_volt = 0
        self.battery_per = 0
    ###########


    def getWaypoints(self):
        self.waypoints = []

        self.mav_out.mav.named_value_int_send(
            int(8*10),
            b"button_data",
            8
        )


    def sendMission(self, waypoints):

        if (not self.connected):
            return

        self.comm_lock.acquire(blocking=False)

        self.mav_out.mav.mission_count_send(
            self.mav_out.target_system,
            self.mav_out.target_component,
            len(waypoints),
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION
        )

        for wp in waypoints:
            msg = self.mav_in.recv_match(type='MISSION_REQUEST_INT', blocking=True)
            seq = msg.seq
        
            w = waypoints[seq]
        
            self.mav_out.mav.mission_item_int_send(
                self.mav_out.target_system,
                self.mav_out.target_component,
                w["seq"],
                w["frame"],
                w["command"],
                w["current"],
                w["autocontinue"],
                w["param1"],
                w["param2"],
                w["param3"],
                w["param4"],
                int(w["x"] * 1e7),
                int(w["y"] * 1e7),
                int(w["z"])
            )

            print(f"Sent waypoint {seq}")  

        self.comm_lock.release()


class ImageCom:
    def __init__(self, port):

        self.cap = None

        gst_pipeline = (
            f"udpsrc port={port} caps=application/x-rtp,media=video,encoding-name=H264,payload=96 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
        )

        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        #self.test_cap = cv2.VideoCapture("test.mp4")

    def get_img(self):
        if (self.cap):
            ret, last = self.cap.read()
            return last
        return None

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def cv2_to_qpixmap(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_image)
        

    ## TESTING ##
    def get_test(self):
        ret, frame = self.test_cap.read()
        return frame if ret else None
    ##############