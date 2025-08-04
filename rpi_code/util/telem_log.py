
import time, datetime, numpy as np

class TelemLog:

	def __init__(self, name):
		self.log_file = open(name, "w")
		self.start_time = 0

	def get_time(self):
		return datetime.datetime.now().strftime("%H:%M:%S") + f".{datetime.datetime.now().microsecond // 1000:03d}"

	def set_start(self):
		self.log_file.write( self.get_time() + ", " + 
			", ".join(("roll", "pitch", "yaw", "airspeed", "groundspeed", "climb", "heading",
			 "altitude", "latitue", "longtitude", "pixhawk_volt", "battery_per", "throttle_inp", "ch1_inp", "ch2_inp", "ch3_inp")) + "\n")

	def write(self, telem_dict):

		roll = "Nan"
		pitch = "Nan"
		yaw = "Nan"
		airspeed = "Nan"
		groundspeed = "Nan"
		climb = "Nan"
		heading = "Nan"
		alt = "Nan"
		lat = "Nan"
		lon = "Nan"
		battery_volt = "Nan"
		battery_per = "Nan"
		throttle = "Nan"
		ch1 = "Nan"
		ch2 = "Nan"
		ch3 = "Nan"

		attitude = telem_dict.get("ATTITUDE")
		vfr_hud = telem_dict.get("VFR_HUD")
		gps = telem_dict.get("GLOBAL_POSITION_INT")
		sys_stat = telem_dict.get("SYS_STATUS")
		rc_channel = telem_dict.get("RC_CHANNELS")

		# Attitude
		if (attitude):
			roll = (attitude.roll / 2*np.pi)*360
			pitch = (attitude.pitch / 2*np.pi)*360
			yaw = (attitude.yaw / 2*np.pi)*360

		# Airspeed, Ground speed, Altitude, Heading
		if (vfr_hud):
			airspeed = vfr_hud.airspeed
			groundspeed = vfr_hud.groundspeed
			climb = vfr_hud.climb
			heading = vfr_hud.heading
			alt = vfr_hud.alt

		# GPS Position
		if (gps):
			lat = gps.lat / 1e7
			lon = gps.lon / 1e7
    
		# Battery Status
		if (sys_stat):
		    battery_volt = sys_stat.voltage_battery / 1000.0
		    battery_per = sys_stat.battery_remaining
    
		# Control Inputs (throttle, roll, pitch, yaw)
		if (rc_channel):
		    cont_inputs = [rc_channel.chan3_raw, rc_channel.chan1_raw, rc_channel.chan2_raw, rc_channel.chan4_raw]
		    throttle, ch1, ch2, ch3 = tuple([(max(0, min(1, ((x-988) / 993))) if x is not None else 0) for x in cont_inputs])

		self.log_file.write( self.get_time() + ", " + 
			", ".join(["{:.2f}".format(x) if type(x) != str else x for x in (roll, pitch, yaw, airspeed, groundspeed, climb, heading,
			 alt, lat, lon, battery_volt, battery_per, throttle, ch1, ch2, ch3)]) + "\n")

	def close(self):
		self.log_file.close()