
############### DELAY CONST ################

DET_WAIT = 0.03
MAIN_WAIT = 0.1
SEND_WAIT = 0.1
IMG_WAIT = 0.01
RECV_WAIT = 0
LOG_WAIT = 1

ERROR_WAIT = 0.1

#############################################

FAILSAFE_DELAY = 1
FAILSAFE_ACTIVE = False

############## NETWORK CONST ###############

IP = ""
MSIP = ""
PORTS = (14550, 14551, 31313) # send recv mp

############################################


################ SERVO CONST ################

MIN_PWM = 2
NET_PWM = 8
MAX_PWM = 13
MDELAY = 1
SERVO_PIN = 12

################ DETECTION CONST ################

REQUIRED_DETECTION_COUNT = 1
DETECTION_TIMEOUT = 3

MAX_SHOOT_DIST = 5
MAX_DIST = 5

SHOOT_COOLDOWN = 5

SEARCH_TIMEOUT = 5
DET_CONF = 0.6

IS_MANUAL = True
SIMPLE_FIRE = False

STRETCH_FIX = 0.7

############################################

HIT_ALTITUDE = 40
HIT_AIRSPEED = 15

#############################################

ERROR_TRY_COUNT = 3

#############################################

PC_TEST = False
IMG_TEST = True
TELEM_TEST = False