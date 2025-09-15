
############### DELAY CONST ################

DET_WAIT = 0
HEAD_WAIT = 0.1
MAIN_WAIT = 0.1
SEND_WAIT = 0.05
IMG_WAIT = 0.05
RECV_WAIT = 0
LOG_WAIT = 1

PWMRET_WAIT = 2
PWM_WAIT = 2

ERROR_WAIT = 0.1

#############################################

FAILSAFE_DELAY = 0.5
FAILSAFE_ACTIVE = True

############## NETWORK CONST ###############

IP = "192.168.0.103"
MSIP = "192.168.0.103"
PORTS = (14550, 14551, 31313) # send recv mp

############################################


################ SERVO CONST ################

MIN_PWM = 3
NET_PWM = 7
MAX_PWM = 12
MDELAY = 1
SERVO_PIN = 12

################ DETECTION CONST ################

UPPER_DET_LIM = 520
LOWER_DET_LIM = 120

REQUIRED_DETECTION_COUNT = 1
DETECTION_TIMEOUT = 3

MAX_SHOOT_DIST = 5

SHOOT_COOLDOWN = 5

SEARCH_TIMEOUT = 5
DET_CONF = 0.7

SIMPLE_FIRE = True

AUTO_HEAD_DIST = 15
AUTO_SHOOT_DIST = 15


IMG_FPS = 30
IMG_WIDTH = 640
IMG_HEIGHT = 480

############################################

HIT_ALTITUDE = 40
HIT_AIRSPEED = 15

#############################################

ERROR_TRY_COUNT = 3

#############################################

PC_TEST = False

IMG_TEST = 2
TELEM_TEST = True

USE_GCS_MSN = False