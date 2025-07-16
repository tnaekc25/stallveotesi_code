from pymavlink import mavutil
import time, select, socket, numpy as np, sys
from threading import Thread
from com.mav import MavConnect
from com.imgm import RecvClass, SendClass, DetectClass

from sim.simulation import RocketSimulation
from sim.rocket import RocketModel
from sim.envr import EnvironmentModel

from log import Log

import RPi.GPIO as GPIO

# DELAY CONST

DET_WAIT = 0.1
MAIN_WAIT = 0.1
SEND_WAIT = 0.1
IMG_WAIT = 0.1
RECV_WAIT = 0
LOG_WAIT = 1

ERROR_WAIT = 0.1

FAILSAFE_DELAY = 1.5


# NETWORK CONST

IP = "10.58.7.165"
MSIP = "10.58.7.165"
PORTS = (14550, 14551, 31313) # send recv mp


# SERVO CONST #

MIN_PWM = 2.478
NET_PWM = 7.11
MAX_PWM = 12.874
MDELAY = 1
SERVO_PIN = 12


#############################

img_det = DetectClass("model.pt", 1071, 1071, 320, 240)
img_recv = RecvClass()
img_send = SendClass(IP, 5000)

#m/s^2, kg/m^3 -> by meter
envr = EnvironmentModel(grav = 9.81, ro_path = "", wind_path = "") 
#kg, kg.m^2, m, m^2, coef of drag -> by velocity
rocket = RocketModel(mass = 241, carea = 0.06, cd_path = "") 
sim = RocketSimulation(dt = 0.1, rocket = rocket, envr = envr)


#############################

telemetry_data = {}
gcs_data = {}
box_data = []

img_feed = None
firing = False
is_det = False

loggr = Log()

loggr.print(f"Process Starting on GCS: {IP} - MSIP : {MSIP}...", 3, "\n\n")

loggr.print("Starting Pixhawk Connection...", 3)
pixhawk = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
loggr.print("Success!\n", 1)

loggr.print("Starting GCS Connection...", 3)
mav_com = MavConnect(pixhawk)
loggr.print("Success!\n", 1)

loggr.print("Starting GPIO...", 3)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SERVO_PIN, GPIO.OUT)
p = GPIO.PWM(SERVO_PIN, 50)
loggr.print("Success!\n", 1)

read_check = [0, 0, 0, 0]
signal_lost = False

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
        
                    if (0 and ned and hud):

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
            loggr.print("ERROR AT THREAD 0 " + str(e), 2)
            time.sleep(ERROR_WAIT)


## READ AND SEND IMG
def read_send_img():

    global img_feed

    while True:
        try:

            if (img_recv.is_open and img_send.is_open):
                img_feed = img_recv.recv()
                if (img_feed is not None):
                    read_check[3] += 1   
                    img_send.send(img_feed)

            time.sleep(IMG_WAIT)

        except Exception as e:
            loggr.print("ERROR AT THREAD 1 " + str(e), 2)
            img_send.close()
            img_recv.close()
            time.sleep(ERROR_WAIT)
            img_send.start()
            img_recv.start()      


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
                    read_check[0] += 1

            if (mav_com.sock in readable and mav_com.sock_connected):
                planner_data = mav_com.read_planner()
                if (planner_data):
                    mav_com.write_pixhawk(planner_data) 
                    read_check[1] += 1

            if (mav_com.gcs_in.fd in readable and mav_com.mav_connected):
                msg = mav_com.get_gcs()
                if (msg):
                    if (gcs_data.get(msg.get_type()) == None):
                        gcs_data[msg.get_type()] = [msg]
                    else:
                        gcs_data[msg.get_type()].append(msg)

                    read_check[2] += 1

            time.sleep(RECV_WAIT)
        
        except Exception as e:
            loggr.print("ERROR AT THREAD 2 " + str(e), 2)
            mav_com.close_sock()
            mav_com.close_gcs()
            time.sleep(ERROR_WAIT)
            mav_com.connect_gcs(IP, *(PORTS[0:2]))
            mav_com.connect_sock(MSIP, PORTS[2])        



# SEND DATA TO GCS AND MISSION PLANNER
def send_data():

    global telemetry_data

    while True:
        try:
            for _, msg in list(telemetry_data.items()):
                    if (msg) and not msg.get_type().startswith("UNKNOWN_"):
                        mav_com.send_gcs(msg)

                        """if (msg.get_type() == "GLOBAL_POSITION_INT"):
                            print((msg.lat / 1e7, msg.lon / 1e7))"""

            # SEND BOXES
            for box in box_data:
                mav_com.send_box(box)

            time.sleep(SEND_WAIT)

        except Exception as e:
            loggr.print("ERROR AT THREAD 3 " + str(e), 2)
            time.sleep(ERROR_WAIT)  




def log():

    global read_check

    while True:
        if (signal_lost):
            loggr.print("RC SIGNAL LOST!", 2)
        else:
            loggr.print("READ STATUS: ", 3, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" PIXHAWK:{read_check[0]} ", 1 if read_check[0] else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" PLANNER:{read_check[1]} ", 1 if read_check[1] else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" GCS:{read_check[2]} " , 1 if read_check[2] else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" Camera:{read_check[3]} ", 1 if read_check[3] else 2)
            loggr.raw_print("|", 0, "")

        read_check = [0, 0, 0, 0]

        time.sleep(LOG_WAIT)


# PROCESS DATA
def mainloop():

    global gcs_data, is_det, firing, telemetry_data, signal_lost

    lost_start = -1

    while True:

        if telemetry_data.get("RC_CHANNELS").signal_lost:
            if (lost_start >= 0 and time.time() - lost_start > FAILSAFE_DELAY):
                mav_com.send_fail()
                loggr.print(" >>> FAIL SAFE <<< ", 2)            
            else:
                signal_lost = True
                lost_start = time.time()
        
        elif signal_lost:
            signal_lost = False 


        # PROCESS GCS DATA
        blst = gcs_data.get("NAMED_VALUE_INT")
        if (blst):
            if (blst[-1].value == 0 and firing == False):
                firing = True
                loggr.print("ACTIVATE 1", 0)
                p.ChangeDutyCycle(MIN_PWM) 
                firing = False

            elif (blst[-1].value == 3 and firing == False):
                firing = True
                loggr.print("ACTIVATE 2", 0)
                p.ChangeDutyCycle(MAX_PWM)
                firing = False

            elif (blst[-1].value == 5 and firing == False):
                firing = True
                loggr.print("DE-ACTIVATE", 0)
                p.ChangeDutyCycle(NET_PWM)
                firing = False

            elif (blst[-1].value == 2):
                is_det = False if is_det else True
                loggr.print("DETECTION TOGGLE: " + is_det, 0)

            blst.pop()

        time.sleep(MAIN_WAIT)



if __name__ == "__main__":

    if len(sys.argv) == 2:
        MSIP = IP = sys.argv[1]

    elif len(sys.argv) == 3:
        IP = sys.argv[1]
        MSIP = sys.argv[2]


    loggr.print("Opening Camera Stream...", 3)
    if (img_recv.start()):
        loggr.print("Success!\n", 1)
    else:
        loggr.print("Fail!\n", 2)

    loggr.print("Starting Gstreamer...", 3)
    img_send.start()
    if (img_send.start()):
        loggr.print("Success!\n", 1)
    else:
        loggr.print("Fail!\n", 2)

    loggr.print("Waiting for Pixhawk Hearbeat...", 3)
    pixhawk.wait_heartbeat()
    loggr.print("Success!\n", 1)

    loggr.print("Connecting GCS and Mission Planner...", 3)
    mav_com.connect_gcs(IP, *(PORTS[0:2]))
    mav_com.connect_sock(MSIP, PORTS[2])
    loggr.print("Success!\n", 1)

    loggr.print("Starting Servo GPIO...", 3)
    p.start(NET_PWM)
    loggr.print("Success!\n", 1)

    Thread(target=read_send_img, daemon=True).start()
    Thread(target=detect_and_fire, daemon=True).start()
    Thread(target=send_data, daemon=True).start()
    Thread(target=read_data, daemon=True).start()
    Thread(target=log, daemon=True).start()
    mainloop()

    p.stop()
    GPIO.cleanup()