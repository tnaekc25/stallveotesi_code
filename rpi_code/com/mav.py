from pymavlink import mavutil
import numpy as np, socket, select, time

PWM_THROTTLE_CUT = 0
PWM_ELEVATOR_UP = 2000
PWM_RUDDER_RIGHT = 2000
PWM_AILERON_RIGHT = 2000 

class MavConnect:

    def __init__(self, pixhawk):

        self.pixhawk = pixhawk

        self.sock_connected = False
        self.mav_connected = False

        self.gcs_out = None
        self.gcs_in = None
        self.sock = None

        self.testing = False

        self.is_armed = False
        self.control_mode = None


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
        if (self.gcs_out):
            self.gcs_out.close()

        if (self.gcs_in):
            self.gcs_in.close()

        self.mav_connected = False

    def close_sock(self):
        if (self.sock):
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
        self.pixhawk.mav.rc_channels_override_send(
                self.pixhawk.target_system,
                self.pixhawk.target_component,
                PWM_AILERON_RIGHT,
                PWM_ELEVATOR_UP,
                PWM_THROTTLE_CUT,
                PWM_RUDDER_RIGHT,
                0,
                0,
                0, 0 )


    def send_heartbeat(self):
        self.gcs_out.mav.heartbeat_send(
            type=mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
            autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            base_mode=0,
            custom_mode=0,
            system_status=mavutil.mavlink.MAV_STATE_ACTIVE
        )



    def check_armed(self, heartbeat):
        if heartbeat:
            return (heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        return False

    def is_auto(self, heartbeat):
        if heartbeat and hasattr(self.pixhawk, 'mode_mapping'):
            mode_map = self.pixhawk.mode_mapping()
            reversed_map = {v: k for k, v in mode_map.items()}
            current_mode_name = reversed_map.get(heartbeat.custom_mode) 
            return current_mode_name == 'AUTO'
        return False


    def toggle_arm(self, heartbeat):
        if (not heartbeat):
            return False

        is_armed = (self.check_armed(heartbeat))
            
        self.pixhawk.mav.command_long_send(
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            0 if is_armed else 1,
            21196,
            0, 0, 0, 0, 0
        )
        
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return False

        time.sleep(0.1)
        
        self.pixhawk.mav.set_mode_send(
            self.pixhawk.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            0
        )

        return True




    def toggle_control(self, heartbeat):

        if ((not heartbeat) or (not hasattr(self.pixhawk, 'mode_mapping'))):
            return

        mode_map = self.pixhawk.mode_mapping()
        self.control_mode = 'MANUAL' if self.is_auto(heartbeat) else 'AUTO'
        mode_id = mode_map.get(self.control_mode)

        if (not mode_id):
            return

        self.pixhawk.mav.set_mode_send(
            self.pixhawk.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
    


    def go_waypoint(self, lat, lon, alt, speed, head, lat0, lon0, loggr):
        self.pixhawk.set_mode_apm("GUIDED")
    
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return False
        else:
            return False
    
        self.pixhawk.mav.command_long_send(
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            1, 0, 0, 0, 0, 0, 0
        )
    
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return False
        else:
            return False
    
        loggr.print("MODE IS GUIDED", 1)
    
        time.sleep(2)
    
        R = 6371000
        dlat = np.radians(lat - lat0)
        dlon = np.radians(lon - lon0)
        x = dlon * np.cos(np.radians((lat0 + lat) / 2)) * R
        y = dlat * R
        dist = np.sqrt(x**2 + y**2)
        if dist == 0: dist = 0.001
        vx = speed * x / dist
        vy = speed * y / dist
        vz = 0
    
        self.pixhawk.mav.set_position_target_global_int_send(
            0,
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b0000111111000111,
            int(lat*1e7),
            int(lon*1e7),
            alt,
            vx, vy, vz,
            0, 0, 0,
            head, 0
        )
        loggr.print("TARGET SENT", 1)

        return True


    def return_auto(self):        
        self.pixhawk.set_mode_apm("AUTO")
    
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return False
        else:
            return False
        
        return True