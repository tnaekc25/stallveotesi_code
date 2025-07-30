
import time

class Log:

	def __init__(self):
		self.codes = ["\033[0m", "\033[32m", "\033[31m", "\033[94m"]
		self.start = time.time()

	def print(self, msg, type, end = "\n"):
		print(f"SYSTEM INFO [{int(time.time()-self.start)}] >>> " + self.codes[type] + msg + "\033[0m", end = end)

	def raw_print(self, msg, type, end = "\n"):
		print(self.codes[type] + msg + "\033[0m", end = end)