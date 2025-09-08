
############### DELAY CONST ################

DET_WAIT = 0.05
MAIN_WAIT = 0.1
SEND_WAIT = 0.05
IMG_WAIT = 0.02
RECV_WAIT = 0
LOG_WAIT = 1

PWMRET_WAIT = 3
PWM_WAIT = 2

ERROR_WAIT = 0.1

#############################################

FAILSAFE_DELAY = 0.5
FAILSAFE_ACTIVE = True

############## NETWORK CONST ###############

IP = ""
MSIP = ""
PORTS = (14550, 14551, 31313) # send recv mp

############################################


################ SERVO CONST ################

MIN_PWM = 0.4
NET_PWM = 9
MAX_PWM = 15
MDELAY = 1
SERVO_PIN = 12

################ DETECTION CONST ################

REQUIRED_DETECTION_COUNT = 2
DETECTION_TIMEOUT = 3

MAX_SHOOT_DIST = 5
MAX_DIST = 5

SHOOT_COOLDOWN = 5

SEARCH_TIMEOUT = 5
DET_CONF = 0.7

IS_MANUAL = True
SIMPLE_FIRE = True

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
IMG_TEST = True
TELEM_TEST = False

USE_GCS_MSN = True