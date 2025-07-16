from pymavlink import mavutil
import numpy as np, socket, select

PWM_THROTTLE_CUT = 1000
PWM_ELEVATOR_UP = 2000
PWM_RUDDER_RIGHT = 2000
PWM_AILERON_RIGHT = 2000 
PWM_FLAPS = 1000

class MavConnect:

    def __init__(self, pixhawk):

        self.pixhawk = pixhawk

        self.sock_connected = False
        self.mav_connected = False

        self.gcs_out = None
        self.gcs_in = None
        self.sock = None

        self.testing = False


    def connect_gcs(self, ip, port1, port2):

        self.gcs_out = mavutil.mavlink_connection(f'udpout:{ip}:{port1}')
        self.gcs_in = mavutil.mavlink_connection(f'udpin:0.0.0.0:{port2}')
        self.mav_connected = True

    def connect_sock(self, ip, port3):
        self.planner_addr = ip
        self.planner_port = port3

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port3))
        self.sock_connected = True


    def close_gcs(self):
        self.gcs_out.close()
        self.gcs_in.close()
        self.mav_connected = False

    def close_sock(self):
        self.sock.close()
        self.sock_connected = False



    def read_pixhawk(self):
        return self.pixhawk.recv_msg()

    def read_planner(self):
        if (self.testing == False):
            data, addr = self.sock.recvfrom(1024)
            return data
        return None

    def send_planner(self, data):
        if (self.testing == False):
            self.sock.sendto(data, (self.planner_addr, self.planner_port))

    def write_pixhawk(self, data):
        if (data):
            self.pixhawk.write(data)

    def send_gcs(self, data):
        if (data):
            self.gcs_out.mav.send(data)

    def get_gcs(self):
        return self.gcs_in.recv_match()

    def send_box(self, box):
        self.gcs_out.mav.statustext_send(
            severity=6,
            text=("BOXINF"+str(box)).encode('utf-8')
        )

    def send_fail(self):
        """self.pixhawk.mav.rc_channels_override_send(
                self.pixhawk.target_system,
                self.pixhawk.target_component,
                PWM_AILERON_RIGHT,
                PWM_ELEVATOR_UP,
                PWM_THROTTLE_CUT,
                PWM_RUDDER_RIGHT,
                PWM_FLAPS,
                0,
                0, 0 )"""
        pass