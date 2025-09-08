
import numpy as np

class EnvironmentModel:

	def __init__(self, grav, ro_path, wind_path):
		self.g = grav
		self.wind_model = wind_path
		self.ro_model = ro_path

	def ro(self, alt):
		return 1.293

	def wind(self, alt):
		return np.array((0, 0, 0))
