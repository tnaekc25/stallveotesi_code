from pymavlink import mavutil
import numpy as np, socket, select

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

        self.is_armed = None
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



    def is_armed(self, heartbeat):
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
        if (heartbeat == False):
            return

        self.is_armed = (not self.is_armed(heartbeat))

        self.pixhawk.mav.command_long_send(
            self.pixhawk.target_system,
            self.pixhawk.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            self.is_armed,
            0, 0, 0, 0, 0, 0)




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

    def add_waypoint(self, lat, lon, alt, speed, head):
        mission_items = []
        
        self.pixhawk.mav.mission_request_list_send(self.pixhawk.target_system, self.pixhawk.target_component)
        count_msg = self.pixhawk.recv_match(type='MISSION_COUNT', blocking=True, timeout=2)
        mission_count = count_msg.count if count_msg else 0
        
        for _ in range(mission_count):
            msg = self.pixhawk.recv_match(type='MISSION_ITEM', blocking=True, timeout=2)
            if msg:
                mission_items.append(msg)
        
        seq_base = len(mission_items)
        
        speed_cmd = mavutil.mavlink.MAVLink_mission_item_message(
            target_system=self.pixhawk.target_system,
            target_component=self.pixhawk.target_component,
            seq=seq_base,
            frame=mavutil.mavlink.MAV_FRAME_MISSION,
            command=mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
            current=0,
            autocontinue=1,
            param1=0,
            param2=speed,
            param3=-1,
            param4=0,
            x=0, y=0, z=0
        )
        
        waypoint_cmd = mavutil.mavlink.MAVLink_mission_item_message(
            target_system=self.pixhawk.target_system,
            target_component=self.pixhawk.target_component,
            seq=seq_base + 1,
            frame=mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            command=mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            current=0,
            autocontinue=1,
            param1=0, param2=0, param3=0, param4=head,
            x=lat, y=lon, z=alt
        )
        
        mission_items.append(speed_cmd)
        mission_items.append(waypoint_cmd)
        
        for i, wp in enumerate(mission_items):
            wp.seq = i
        
        self.pixhawk.mav.mission_count_send(
            self.pixhawk.target_system, 
            self.pixhawk.target_component, 
            len(mission_items)
        )
        
        for wp in mission_items:
            self.pixhawk.mav.send(wp)
            time.sleep(0.05)
        
        ack = self.pixhawk.recv_match(type='MISSION_ACK', blocking=True, timeout=5)
        if not ack:
            raise RuntimeError("Mission upload failed: no ACK received")    