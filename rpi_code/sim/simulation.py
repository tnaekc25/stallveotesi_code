
import numpy as np
from scipy.optimize import root

from rocket import RocketModel
from envr import EnvironmentModel

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


	def revsim(self, detx, dety, alt, speed, delay):

		vx = 0
		vy = speed

		def residual(pos):
			x0, y0 = pos
			z0 = np.array([x0, y0, alt, vx, vy, 0])
			last = self.simulate(z0, delay)
			return [last[0] - detx, last[1] - dety]

		guess = [detx, dety]

		sol = root(residual, guess)

		if not sol.success:
		 raise RuntimeError("revsim failed to converge")

		x0, y0 = sol.x
		return x0, y0



#m/s^2, kg/m^3 -> by meter
envr = EnvironmentModel(grav = 9.81, ro_path = "", wind_path = "") 
#kg, kg.m^2, m, m^2, coef of drag -> by velocity
rocket = RocketModel(mass = 241, carea = 0.06, cd_path = "") 
sim = RocketSimulation(dt = 0.1, rocket = rocket, envr = envr)

x, y = sim.revsim(0, 200, 10000, 20, 3)
print(x, y)
print(list(map(int, sim.simulate(np.array([x, y, 10000, 0, 20, 0]), 3))))
