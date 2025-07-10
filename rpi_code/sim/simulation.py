
import numpy as np

class RocketSimulation:

	def __init__(self, dt, rocket, envr):
		self.dt = dt
		self.rocket = rocket
		self.envr = envr


	def simulate(self, z0, delay):
		last = z0
		
		for x in range(round(delay / self.dt)):			
			#Heun Method - use more precise alternative
			zp = last + self._delayf(last)*self.dt
			last = last + (self._delayf(last) + self._delayf(zp))*self.dt/2.0

		while last[2] > 0:			
			#Heun Method - use more precise alternative
			zp = last + self._stepf(last)*self.dt
			last = last + (self._stepf(last) + self._stepf(zp))*self.dt/2.0

		return last


	def _norm(self, arr):
		n = np.linalg.norm(arr)
		return arr/n if n else np.array((0, 0, 0))

	def _delayf(self, z):
		vx, vy, vz = z[3:6] # get velocity

		return np.array((vx, vy, vz, 0, 0, 0))


	def _stepf(self, z):

		alt = z[2] # get altitude
		vx, vy, vz = z[3:6] # get velocity

		rvel = np.array((vx, vy, vz))-self.envr.wind(alt) # relative velocity
		rspd = np.linalg.norm(rvel) # relative speed

		if rspd < 1e-6:
			dragU = liftU = np.zeros(3)
		else:
			dragU = - rvel / rspd # Drag Direction Global

		cd = self.rocket.cd(rspd) # get coef of drag
		ro = self.envr.ro(alt) # get air density
	
		dragM = 0.5*self.rocket.ca*cd*ro*(rspd**2) # calculate drag magnitude	
		drag = dragU * dragM # get drag force

		ax, ay, az = ((drag / self.rocket.m) +
		 np.array((0, 0, -self.envr.g))) # calculate accel

		return np.array((vx, vy, vz, ax, ay, az))