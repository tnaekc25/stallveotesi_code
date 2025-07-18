from pymavlink import mavutil
import time, select, socket, numpy as np, sys
from threading import Thread
from com.mav import MavConnect
from com.imgm import RecvClass, SendClass, DetectClass

from sim.simulation import RocketSimulation
from sim.rocket import RocketModel
from sim.envr import EnvironmentModel

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

ERROR_WAIT = 0.1
WAIT_TIME = 0.05
DET_WAIT = 0.1

IP = "10.29.6.165"
MSIP = "10.29.6.79"
PORTS = (14550, 14551, 31313)

MIN_PWM = 2.478
NET_PWM = 7.11
MAX_PWM = 12.874

MDELAY = 1

SERVO_PIN = 12
GPIO.setup(SERVO_PIN, GPIO.OUT)

p = GPIO.PWM(SERVO_PIN, 50)
p.start(NET_PWM)

is_det = False


def connect_mav():
    print(">>> Connecting to GCS Mavlink...")
    mav_com.connect_gcs(IP, *(PORTS[0:2]))
    print("SUCCESS")

def connect_sock():
    print(">>> Connecting to Planner")
    mav_com.connect_sock(MSIP, PORTS[2])
    print("SUCCESS")


print(">>> Connecting to PixHawk...")
#pixhawk = mavutil.mavlink_connection('udp:127.0.0.1:15555')
pixhawk = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
print("SUCCESS")

print(">>> Waiting for heartbeat from Pixhawk...")
pixhawk.wait_heartbeat()
print("SUCCESS")

mav_com = MavConnect(pixhawk)

img_det = DetectClass("model.pt", 1071, 1071, 320, 240)
img_recv = RecvClass()
img_send = SendClass(IP, 5000)


connect_sock()
connect_mav()


#m/s^2, kg/m^3 -> by meter
envr = EnvironmentModel(grav = 9.81, ro_path = "", wind_path = "") 
#kg, kg.m^2, m, m^2, coef of drag -> by velocity
rocket = RocketModel(mass = 241, carea = 0.06, cd_path = "") 
sim = RocketSimulation(dt = 0.1, rocket = rocket, envr = envr)


telemetry_data = {}
gcs_data = {}
box_data = []
img_feed = None
firing = False



## APPLY OBJECT DETECTION AND RUN SIMULATION
def detect_and_fire():

    global box_data, telemetry_data, firing

    while True:
        try:
            if (is_det and (img_feed) is not None):
                raw_box_data = img_det.get_boxes(img_feed)
                box_data = [[int(box.cls[0].item())] + list(map(int, box.xyxy[0])) for box in raw_box_data] 

                for box in box_data:

                    # RUN SIMULATION
                    ned = telemetry_data.get("LOCAL_POSITION_NED")
                    hud = telemetry_data.get("VFR_HUD")
        
                    if (ned and hud):

                        # CALCULATE REAL LIFE DISTANCE
                        detx, dety = img_det.get_distance((box[1] + box[3]) / 2,
                        (box[2] + box[4]) / 2, 0, 0, hud.alt)

                        print(detx, dety)

                        c = sim.simulate(np.array((0, 0, hud.alt, ned.vx, ned.vy, ned.vz)), MDELAY)
                        x, y, z = c[0:3]
                        
                        print(x, y, z)

                        cls = box[0]

                        """
                        if (abs(detx-x) < 2 and abs(dety-y) < 2 and firing == False):
                            firing = True
                            print("FIRE CONDITION")
                            p.ChangeDutyCycle(MAX_PWM if cls else MIN_PWM)
                            firing = False
                        """

            time.sleep(DET_WAIT)
        
        except Exception as e:
            print("ERROR AT THREAD 0", e)
            time.sleep(ERROR_WAIT)


## SEND IMG
def send_img():

    global img_feed

    while True:
        try:
            img_feed = img_recv.recv()
            if (img_feed is not None):   
                img_send.send(img_feed)

            else:
                print("feed is none")
        except Exception as e:
            print("ERROR AT THREAD 1", e)
            img_send.close()
            img_recv.close()
            time.sleep(ERROR_WAIT)
            img_send.restart()
            img_recv.restart()      


## READ TELEMETRY FROM PIXHAWK AND DATA FROM GCS
def read_data():
    global telemetry_data, gcs_data

    while True:
        try:
            readable, _, _ = select.select(
                [mav_com.sock, mav_com.pixhawk.fd, mav_com.gcs_in.fd],
                [], [], 0.01)

            if (mav_com.pixhawk.fd in readable and mav_com.mav_connected):
                msg = mav_com.read_pixhawk()        
                if (msg):
                    telemetry_data[msg.get_type()] = msg
                    mav_com.send_planner(msg.get_msgbuf())
                    #print("Mission Planner >> SENT")

            if (mav_com.sock in readable and mav_com.sock_connected):
                planner_data = mav_com.read_planner()
                if (planner_data):
                    mav_com.write_pixhawk(planner_data) 
                    #print("Mission Planner >> READ")

            if (mav_com.gcs_in.fd in readable and mav_com.mav_connected):
                msg = mav_com.get_gcs()
                if (msg):
                    if (gcs_data.get(msg.get_type()) == None):
                        gcs_data[msg.get_type()] = [msg]
                    else:
                        gcs_data[msg.get_type()].append(msg)
        
        except Exception as e:

            print("ERROR AT THREAD 2", e)
            mav_com.close_sock()
            mav_com.close_gcs()
            time.sleep(ERROR_WAIT)
            connect_sock()
            connect_mav()        



# SEND GCS , GET BUTTON PRESS , CHECK POSITION
def send_gcs():

    global telemetry_data, gcs_data, box_data, is_det, firing

    while True:
        # PROCESS PIXHAWK DATA
        for _, msg in list(telemetry_data.items()):
            if (msg) and not msg.get_type().startswith("UNKNOWN_"):
                mav_com.send_gcs(msg)

                if (msg.get_type() == "GLOBAL_POSITION_INT"):
                    print((msg.lat / 1e7, msg.lon / 1e7))

        # SEND BOXES
        for box in box_data:
            mav_com.send_box(box)

        # PROCESS GCS DATA
        blst = gcs_data.get("NAMED_VALUE_INT")
        if (blst):
            if (blst[-1].value == 0 and firing == False):
                firing = True
                print("ACTIVATE 1")
                p.ChangeDutyCycle(MIN_PWM) 
                firing = False

            elif (blst[-1].value == 3 and firing == False):
                firing = True
                print("ACTIVATE 2")
                p.ChangeDutyCycle(MAX_PWM)
                firing = False

            elif (blst[-1].value == 5 and firing == False):
                firing = True
                print("DE-ACTIVATE")
                p.ChangeDutyCycle(NET_PWM)
                firing = False

            elif (blst[-1].value == 2):
                is_det = False if is_det else True
                print("DETECTION TOGGLE: ", is_det)

            blst.pop()

        time.sleep(WAIT_TIME)



if __name__ == "__main__":
    print(">>> Process Starting...")

    if (len(sys.argv) > 1):
        mav_com.testing = True

    Thread(target=send_img, daemon=True).start()
    Thread(target=detect_and_fire, daemon=True).start()
    Thread(target=read_data, daemon=True).start()
    send_gcs()

    p.stop()
    GPIO.cleanup()