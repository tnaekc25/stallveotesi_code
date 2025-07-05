
class RocketModel:

	def __init__(self, mass, carea, cd_path):
		self.m = mass
		self.ca = carea
		self.cd_model = cd_path

	def cd(self, spd):
		return 0.26
