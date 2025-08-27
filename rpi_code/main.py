from pymavlink import mavutil
import time, select, numpy as np, sys, subprocess
from threading import Thread, Lock, Event
from com.mav import MavConnect
from com.imgm import RecvClass, SendClass, DetectClass, VideoSave

from sim.simulation import RocketSimulation
from sim.rocket import RocketModel
from sim.envr import EnvironmentModel

from util.log import Log
from util.telem_log import TelemLog
from const import *

if (not PC_TEST):
    import RPi.GPIO as GPIO


#############################

stop_event = Event()

#############################

telemetry_data = {}
gcs_data = {}
box_data = []

img_feed = None
is_det = False

loggr = Log()

read_check = [0, 0, 0, 0]
write_check = [0, 0, 0]

signal_lost = False
lost_start = -1

#############################

firing_lock = Lock()
detection_lock = Lock()
comm_lock1 = Lock()
comm_lock2 = Lock()

detection_count = [0, 0]
last_detect = [-1, -1]
shoot_pos = [None, None]
pos_diff = [None, None]
is_shot = [0, 0]


#############################



## APPLY OBJECT DETECTION AND RUN SIMULATION AND FIRE
def detect_and_fire():

    global box_data, telemetry_data, detection_count, last_detect, pos_diff

    headed = [False, False]

    while (not stop_event.is_set()):
        try:
            if (is_det and (img_feed) is not None and
             (detection_count[0] <= REQUIRED_DETECTION_COUNT or detection_count[1] <= REQUIRED_DETECTION_COUNT)):
                raw_box_data = img_det.get_boxes(img_feed)
                box_data = [[int(box.cls[0].item())] + list(map(int, box.xyxy[0])) for box in raw_box_data] 


                # CHECK TO GO WAYPOINT
                for clss in range(2):
                    if ((True not in headed) and shoot_pos[clss]):
                        if (time.time()-shoot_pos[clss][5] > SHOOT_COOLDOWN):
                            gps = telemetry_data.get("GLOBAL_POSITION_INT")
        
                            if (gps):
                                lat = gps.lat / 1e7
                                lon = gps.lon / 1e7
        
                                tolat = shoot_pos[clss][0]
                                tolon = shoot_pos[clss][1]
        
                                pos_diff[clss] = [abs(lat - shoot_pos[clss][2]), abs(lon - shoot_pos[clss][3])]
            
                                if (pos_diff[0] < MAX_SHOOT_DIST and 
                                    pos_diff[1] < MAX_SHOOT_DIST):
                                    with comm_lock1, comm_lock2:
                                        while True:
                                            if (mav_com.go_waypoint(tolat, tolon, HIT_ALTITUDE,
                                             HIT_AIRSPEED, shoot_pos[clss][4])):
                                                break
                                        headed[clss] = True
    

                for box in box_data:
                    clss = 1 if box[0] else 0
                
                    if last_detect[clss] >= 0 and (time.time() - last_detect[clss]) > DETECTION_TIMEOUT:
                        detection_count[clss] = 0
                
                    if detection_count[clss] < REQUIRED_DETECTION_COUNT:
                        detection_count[clss] += 1
                        last_detect[clss] = time.time()
                
                    elif detection_count[clss] == REQUIRED_DETECTION_COUNT:
                        with detection_lock: 
                            hud = telemetry_data.get("VFR_HUD")
                            attd = telemetry_data.get("ATTITUDE")
                            gps = telemetry_data.get("GLOBAL_POSITION_INT")
                            
                            if (hud and attd and gps):

                                detection_count[clss] += 1
                                last_detect[clss] = -1

                                try:
                                    detx, dety = img_det.get_distance((box[1] + box[3]) / 2,
                                    (box[2] + box[4]) / 2, attd.roll, attd.pitch, hud.alt)
                                except ValueError as e:
                                    continue

                                try:
                                    sx, sy = sim.revsim(detx, dety, 
                                        HIT_ALTITUDE, HIT_AIRSPEED, MDELAY)
                                except RuntimeError as e:
                                    continue

                                lat, lon = img_det.pos_to_gps(gps, hud, sx, sy)

                                shoot_pos[clss] = (lat, lon, gps.lat / 1e7, gps.lon / 1e7, hud.heading, time.time())


                    elif detection_count[clss] > REQUIRED_DETECTION_COUNT:
                        with detection_lock:
                            # CHECK TO FIRE
                            if (headed[clss]):
                                hud = telemetry_data.get("VFR_HUD")
                                attd = telemetry_data.get("ATTITUDE")
                            
                                if (hud and attd):
                                    try:
                                        detx, dety = img_det.get_distance((box[1] + box[3]) / 2,
                                            (box[2] + box[4]) / 2, attd.roll, attd.pitch, hud.alt)
                                    except ValueError:
                                        continue
                                        
                                    c = sim.simulate(np.array((0, 0, hud.alt, 0, hud.airspeed, hud.climb)), MDELAY)
                                    hx, hy = c[0:2]
            
                                    if (abs(hx - detx) < MAX_DIST and abs(hy - dety) < MAX_DIST):
                                        with firing_lock:
                                            p.ChangeDutyCycle(MAX_PWM if clss else MIN_PWM)
                                            is_shot[clss] = 1
    
                                        headed[clss] = False
                                        shoot_pos[clss] = None


            time.sleep(DET_WAIT)
        
        except Exception as e:
            loggr.print("ERROR AT THREAD 0 " + str(e), 2)
            time.sleep(ERROR_WAIT)


## READ AND SEND IMG
def read_send_img():

    global img_feed, video, img_recv, img_send

    while (not stop_event.is_set()):
        try:

            if (img_recv.is_open and img_send.is_open):
                img_feed = img_recv.recv()
                
                if (img_feed is not None):
                    if (IMG_TEST):
                        if (video):
                            video.out.write(img_feed)
                    else:
                        img_send.send(img_feed)
                        
                
                read_check[3] += 1

            time.sleep(IMG_WAIT)

        except Exception as e:
            loggr.print("ERROR AT THREAD 1 " + str(e), 2)
            time.sleep(ERROR_WAIT)



## READ TELEMETRY FROM PIXHAWK AND DATA FROM GCS
def read_data():
    global telemetry_data, lost_start

    while (not stop_event.is_set()):
        try:

            with comm_lock2:
                inputs = []
    
                try:
                    if (mav_com.sock):
                        if (mav_com.sock.fileno() >= 0):
                            inputs.append(mav_com.sock)
                except:
                    loggr.print("socket error before select", 2)
    
    
                try:
                    if (mav_com.pixhawk):
                        fd = mav_com.pixhawk.fd
                        if (fd is not None and fd >= 0):
                            inputs.append(fd)
                except:
                    loggr.print("mavlink error before select 1", 2)
    
    
                try:
                    if (mav_com.gcs_in):
                        fd = mav_com.gcs_in.fd
                        if (fd is not None and fd >= 0):
                            inputs.append(fd)
                except:
                    loggr.print("mavlink error before select 2", 2)
    
    
                if (not inputs):
                    time.sleep(RECV_WAIT)
                    continue
    
    
                readable, _, _ = select.select(
                    inputs,
                    [], [], 0.01)
    
                if (mav_com.pixhawk and mav_com.pixhawk.fd in readable and mav_com.mav_connected):
                    msg = mav_com.read_pixhawk()        
                    if (msg):                        
                        telemetry_data[msg.get_type()] = msg
                        mav_com.send_planner(msg.get_msgbuf())
                        write_check[1] += 1
                        read_check[0] += 1
    
                if (mav_com.sock in readable and mav_com.sock_connected):
                    planner_data = mav_com.read_planner()
                    if (planner_data):
                        mav_com.write_pixhawk(planner_data) 
                        write_check[0] += 1
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

            try:
                time.sleep(ERROR_WAIT)
                mav_com.connect_gcs(IP, *(PORTS[0:2]))
                mav_com.connect_sock(MSIP, PORTS[2])        
            except Exception as e2:
                loggr.print("ERROR AT THREAD 2 - 2 " + str(e2), 2)



# SEND DATA TO GCS AND MISSION PLANNER
def send_data():

    global telemetry_data, detection_count, is_det

    while (not stop_event.is_set()):


            with comm_lock1:
                mav_com.send_heartbeat()
                mav_com.is_armed = mav_com.check_armed(telemetry_data.get("HEARTBEAT"))
    
                for _, msg in list(telemetry_data.items()):
                        if (msg) and not msg.get_type().startswith("UNKNOWN_"):
                            mav_com.send_gcs(msg)
                            write_check[2] += 1
    
                # SEND INFO
                mav_com.gcs_out.mav.statustext_send(
                    severity=6,
                    text=("STATINF"
                    + ('1' if mav_com.is_armed else '0')
                    + ('1' if (mav_com.control_mode == 'MANUAL') else '0')
                    + ('1' if detection_count[0] >= 0 else '0')
                    + ('1' if detection_count[1] >= 0 else '0')
                    + ('1' if is_det else '0')
                    ).encode('utf-8')
                )
    
                # SEND BOXES
                for box in box_data:
                    mav_com.send_box(box)
    
                time.sleep(SEND_WAIT)





def log():

    global read_check, write_check, box_data

    while (not stop_event.is_set()):

        if (signal_lost):
            loggr.print("RC SIGNAL LOST!", 2)
        else:
            loggr.print("READ STATUS: ", 3, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" PXHWK:{read_check[0]}/{write_check[0]} ",
                1 if (read_check[0] or write_check[0]) else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" PLNR:{read_check[1]}/{write_check[1]} ",
                1 if (read_check[1] or write_check[1]) else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" GCS:{read_check[2]}/{write_check[2]} " ,
                1 if (read_check[2] or write_check[2]) else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" CAM:{read_check[3]} ",
                1 if (read_check[3]) else 2, "")
            loggr.raw_print("|", 0, "")
            loggr.raw_print(f" DETECT: {len(box_data)} ",
                1 if len(box_data) else 2, "")
            loggr.raw_print("|", 0 , "") 

            if telemetry_data.get("RC_CHANNELS"):
                loggr.raw_print(f" ({telemetry_data.get('RC_CHANNELS').rssi}) ", 3, "")
            else:
                loggr.raw_print(f" ({-1}) ", 3, "")

            loggr.raw_print("|", 0)

            loggr.raw_print(f" POS:", 3, "")

            if (pos_diff[0]):
                loggr.raw_print(str(round(pos_diff[0][0]), 3) + "," + str(round(pos_diff[0][1]), 3), 1, "")
            else:
                loggr.raw_print("NONE", 2, "")
            
            loggr.raw_print("/", 0 , "") 

            if (pos_diff[1]):
                loggr.raw_print(str(round(pos_diff[1][0]), 3) + "," + str(round(pos_diff[1][1]), 3), 1, "")
            else:
                loggr.raw_print("NONE", 2, "")

            loggr.raw_print("|", 0 , "") 


        read_check = [0, 0, 0, 0]
        write_check = [0, 0, 0]

        time.sleep(LOG_WAIT)


# PROCESS DATA
def mainloop():

    global gcs_data, is_det, telemetry_data, signal_lost, lost_start

    last_channel = -1
    last_rc = -1
    new_channel = -1

    failsafed = False

    while (not stop_event.is_set()):
        try:
            # FAILSAFE
            if (FAILSAFE_ACTIVE):
                if (telemetry_data.get("HEARTBEAT") and telemetry_data.get("HEARTBEAT").system_status == 5
                 and not failsafed and not signal_lost):
                    last_rc = time.time()
                    signal_lost = True

                if (last_rc > 0 and time.time()-last_rc > FAILSAFE_DELAY):
                    failsafed = True
                    mav_com.send_fail()
                    loggr.print(" >>> FAIL SAFE <<< ", 2)

                """rc = (telemetry_data.get("RC_CHANNELS"))
                if (rc):
                    new_channel = rc.chan15_raw

                if (new_channel != last_channel or last_channel < 0):
                    last_rc = time.time()
                    last_channel = new_channel
                    signal_lost = False

                if (last_rc > 0 and time.time()-last_rc > FAILSAFE_DELAY):
                    signal_lost = True
                    mav_com.send_fail()
                    loggr.print(" >>> FAIL SAFE <<< ", 2) """          


            # PROCESS GCS DATA
            blst = gcs_data.get("NAMED_VALUE_INT")
            if (blst):
                if (blst[0].value == 0):
                    with firing_lock:
                        loggr.print("ACTIVATE 1", 0)
                        with firing_lock:
                            p.ChangeDutyCycle(MIN_PWM)
                            is_shot[0] = 1

                elif (blst[0].value == 1):
                    with comm_lock1, comm_lock2:
                        for x in range(ERROR_TRY_COUNT):
                            if (mav_com.toggle_arm(telemetry_data.get("HEARTBEAT"))):
                                break
                            else:
                                print("FAIL ARM")
                    loggr.print("ARM TOGGLE TO: " + str(mav_com.is_armed), 0)

                elif (blst[0].value == 2):
                    is_det = False if is_det else True
                    loggr.print("TOGGLE DETECTION TO: " + str(is_det), 0)

                elif (blst[0].value == 3):
                    with firing_lock:
                        loggr.print("ACTIVATE 2", 0)
                        with firing_lock:
                            p.ChangeDutyCycle(MAX_PWM)
                            is_shot[1] = 1

                elif (blst[0].value == 4):
                    loggr.print("TOGGLE CONTROL TO:" + str(mav_com.control_mode), 0)
                    mav_com.toggle_control(telemetry_data.get("HEARTBEAT"))

                elif (blst[0].value == 5):
                    with firing_lock:
                        p.ChangeDutyCycle(NET_PWM)
                        loggr.print("DE-ACTIVATE", 0)

                blst.pop(0)

            time.sleep(MAIN_WAIT)

        except Exception as e:
            loggr.print("ERROR AT THREAD 4 " + str(e), 2)
            time.sleep(ERROR_WAIT)



def write_telem():

    global telemetry_data, telem_logger

    telem_logger.set_start()

    while (not stop_event.is_set()):
        try:
            telem_logger.write(telemetry_data)
            time.sleep(0.1)

        except Exception as e:
            loggr.print("ERROR AT WRITE 1 " + str(e), 2)
            time.sleep(ERROR_WAIT)



try:
    if __name__ == "__main__":
    

        main_thread = None
        telemlog_thread = None
        detect_thread = None
        send_thread = None
        recv_thread = None
        log_thread = None

        pixhawk = None
        mav_com = None
        img_recv = None
        img_send = None
        p = None


        #CHECK ARGUMENTS
    
        if len(sys.argv) == 2:
            MSIP = IP = sys.argv[1]
    
        if len(sys.argv) > 2:
            IP = sys.argv[1]
            MSIP = sys.argv[2]
    
        if len(sys.argv) > 3:
            TELEM_TEST = int(sys.argv[3])
    
        if len(sys.argv) > 4:
            IMG_TEST = int(sys.argv[4])
    
    
        #>>># START PROCESS
    
        loggr.print(f"Process Starting on GCS: {IP} - MSIP : {MSIP}...", 3, "\n\n")
    
    
        ################## START CRITICAL COMPONENTS ##################
    
        ################## START PIXHAWK CONNECTION ##################
        if (not PC_TEST):
            loggr.print("Starting Pixhawk Connection...", 3)
            pixhawk = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
            loggr.print("Success!\n", 1)
        
        
            loggr.print("Waiting for Pixhawk Hearbeat...", 3)
            pixhawk.wait_heartbeat()
            loggr.print("Success!\n", 1)
            
    
        ################## IMAGE CLASSES ##################
        loggr.print("Starting Detection Model...", 3)
        img_det = DetectClass("model.pt", 663, 663, 320, 240, np.pi / 4)
        loggr.print("Success!\n", 1)
    
        loggr.print("Starting Camera Reader Class...", 3)
        img_recv = RecvClass()
        loggr.print("Success!\n", 1)
    
        loggr.print("Starting Image Sender Class...", 3)
        img_send = SendClass(IP, 5000)
        loggr.print("Success!\n", 1)
        
    
        ################## SIMULATION MODEL ##################
        loggr.print("Starting Simulation Model...", 3)
        #m/s^2, kg/m^3 -> by meter
        envr = EnvironmentModel(grav = 9.81, ro_path = "", wind_path = "") 
        #kg, kg.m^2, m, m^2, coef of drag -> by velocity
        rocket = RocketModel(mass = 241, carea = 0.06, cd_path = "") 
        sim = RocketSimulation(dt = 0.1, rocket = rocket, envr = envr)
        loggr.print("Success!\n", 1)
        
    
    
        ################## MAVLINK CLASS ##################
        loggr.print("Starting GCS Connection...", 3)
        mav_com = MavConnect(pixhawk)
        loggr.print("Success!\n", 1)
        
        if (not PC_TEST):
            ################## START GPIO ##################
            loggr.print("Starting GPIO...", 3)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(SERVO_PIN, GPIO.OUT)
            p = GPIO.PWM(SERVO_PIN, 50)
            loggr.print("Success!\n", 1)
    
    
        ####################################################
        
        if (not PC_TEST):
            for x in range(ERROR_TRY_COUNT):
                try:
                    loggr.print("Opening Camera Stream... [{}]".format((ERROR_TRY_COUNT-x)), 3)
        
                    if (img_recv.start()):
                        loggr.print("Success!\n", 1)
                        break
                    else:
                        loggr.print("Fail!\n", 2)
                        img_recv.close()
                except:
                    loggr.print("Fail!\n", 2)
                    img_recv.close()
        
        
            for x in range(ERROR_TRY_COUNT):
                try:
                    loggr.print("Starting Gstreamer... [{}]".format((ERROR_TRY_COUNT-x)), 3)
        
                    if (img_send.start()):
                        loggr.print("Success!\n", 1)
                        break
                    else:
                        loggr.print("Fail!\n", 2)
                        img_send.close()
                except:
                    loggr.print("Fail!\n", 2)
                    img_send.close()
        
    
        for x in range(ERROR_TRY_COUNT):
            try:
                loggr.print("Connecting GCS... [{}]".format((ERROR_TRY_COUNT-x)), 3)
                mav_com.connect_gcs(IP, *(PORTS[0:2]))
                loggr.print("Success!\n", 1)
                break
            except:
                loggr.print("Fail!\n", 2)
                mav_com.close_gcs()
    
    
        for x in range(ERROR_TRY_COUNT):
            try:
                loggr.print("Connecting Mission Planner... [{}]".format((ERROR_TRY_COUNT-x)), 3)
                mav_com.connect_sock(MSIP, PORTS[2])
                loggr.print("Success!\n", 1)
                break
            except:
                loggr.print("Fail!\n", 2)
                mav_com.close_sock()
    
        if (not PC_TEST):
            for x in range(ERROR_TRY_COUNT):
                try:
                    loggr.print("Starting Servo GPIO... [{}]".format((ERROR_TRY_COUNT-x)), 3)
                    p.start(NET_PWM)
                    loggr.print("Success!\n", 1)
                    break
                except:
                    loggr.print("Fail!\n", 2)


        if (TELEM_TEST):
            loggr.print("Starting with Local Telemetry Logging...", 3)
            telem_logger = TelemLog("telem_log.txt")
            telemlog_thread = Thread(target=write_telem, daemon=False)
            telemlog_thread.start()
        else:
            detect_thread = Thread(target=detect_and_fire, daemon=False)
            detect_thread.start()
    
        send_thread = Thread(target=send_data, daemon=False)
        send_thread.start()
        
        recv_thread = Thread(target=read_data, daemon=False)
        recv_thread.start()

        log_thread = Thread(target=log, daemon=False)
        log_thread.start()
        
        main_thread = Thread(target=mainloop, daemon=False)
        main_thread.start()

        video = None
        if (IMG_TEST):
            loggr.print("Starting with Local Image Save...", 3)
            video = VideoSave()           
        read_send_img()

except KeyboardInterrupt:
    pass

finally:
    #|||# HALT PROCESS

    loggr.print("HALTING...", 3)

    stop_event.set()

    if (main_thread):
        main_thread.join()
    if (telemlog_thread):
        telemlog_thread.join()
    if (detect_thread):
        detect_thread.join()
    if (send_thread):
        send_thread.join()
    if (recv_thread):
        recv_thread.join()
    if (log_thread):
        log_thread.join()

    if (mav_com):
        mav_com.close_sock()
        mav_com.close_gcs()

    if (img_recv):
        img_recv.close()

    if (img_send):
        img_send.close()

    if (pixhawk):
        pixhawk.close()

    if (p):
        p.stop()
        p = None
    
    if (not PC_TEST):
        GPIO.cleanup()

    loggr.print("HALTED", 1)
