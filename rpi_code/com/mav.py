from pymavlink import mavutil
import numpy as np, socket, select, time

PWM_THROTTLE_CUT = 950
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
        self.mode_arr = {10:5, 5:0, 0:10}

    def init(self, heartbeat):
        self.is_armed = self.check_armed(heartbeat)
        self.control_mode = self.get_mode(heartbeat)

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

        self.pixhawk.mav.set_mode_send(
            self.pixhawk.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            0
        )

        time.sleep(0.1)

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

    def preflight(self):            
        self.pixhawk.mav.command_long_send(
            self.pixhawk.target_system, 
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,
            0,
            1,
            1,
            1,
            1,
            0,
            0,
            0
        )

        time.sleep(0.1)

        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return False

        return True

    def abort_land(self):            
        self.pixhawk.mav.command_long_send(
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_CMD_DO_GO_AROUND,
            0,
            0, 0, 0, 0, 0, 0, 0
        )

        time.sleep(0.1)
        
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return False


        return True


    def get_mode(self, heartbeat):
        if heartbeat and hasattr(self.pixhawk, 'mode_mapping'):
            return heartbeat.custom_mode
        return False


    def toggle_control(self, heartbeat):

        if ((not heartbeat) or (not hasattr(self.pixhawk, 'mode_mapping'))):
            return

        mode_map = self.pixhawk.mode_mapping()
        self.control_mode = self.mode_arr.get(self.get_mode(heartbeat))
        self.control_mode = self.control_mode if self.control_mode else 0

        self.pixhawk.mav.set_mode_send(
            self.pixhawk.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            self.control_mode
        )
    


    def go_waypoint(self, lat, lon, lat0, lon0, alt, speed, loggr):
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
        if not (ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
            return False
    
        loggr.print("MODE IS GUIDED", 1)
        time.sleep(1)
    
        self.pixhawk.mav.set_position_target_global_int_send(
            0,
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b0000111111111000,
            int(lat * 1e7),
            int(lon * 1e7),
            alt,
            0, 0, 0,
            0, 0, 0,
            0, 0
        )
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if not (ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
            return False
    
        self.pixhawk.mav.command_long_send(
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
            0,
            1,
            speed,
            -1,
            0, 0, 0, 0
        )
        ack = self.pixhawk.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if not (ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED):
            return False
    
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


    def get_waypoints(self):
        self.pixhawk.mav.mission_request_list_send(
            self.pixhawk.target_system, self.pixhawk.target_component)

        msg = self.pixhawk.recv_match(type="MISSION_COUNT", blocking=True, timeout=5)
            
        if (not msg):
            return []

        wp_total = msg.count
        
        waypoints = []
        for i in range(wp_total):
            self.pixhawk.mav.mission_request_int_send(
                self.pixhawk.target_system, self.pixhawk.target_component, i)        
            msg = self.pixhawk.recv_match(type=["MISSION_ITEM", "MISSION_ITEM_INT"], blocking=True, timeout=5)

            if (not msg):
                return []
        
            if msg.get_type() == "MISSION_ITEM_INT":
                lat, lon, seq = msg.x / 1e7, msg.y / 1e7, msg.seq
            else:
                lat, lon, seq = msg.x, msg.y, msg.seq
        
            waypoints.append((lat, lon, seq))

        self.pixhawk.mav.mission_ack_send(
            self.pixhawk.target_system, self.pixhawk.target_component, 0)

        return waypoints

    def send_wp(self, wp):
        self.gcs_out.mav.statustext_send(
            severity=6,
            text=("WAYPOINT"+str(wp)).encode('utf-8')
        )

        print(wp)