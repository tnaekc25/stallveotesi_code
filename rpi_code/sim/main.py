
import numpy as np
import matplotlib.pyplot as plt

from simulation import RocketSimulation
from rocket import RocketModel
from envr import EnvironmentModel


#m/s^2, kg/m^3 -> by meter
envr = EnvironmentModel(grav = 9.81, ro_path = "", wind_path = "") 
#kg, kg.m^2, m, m^2, coef of drag -> by velocity
rocket = RocketModel(mass = 241, carea = 0.06, cd_path = "") 
sim = RocketSimulation(dt = 0.1, rocket = rocket, envr = envr)

#Initial State
x0 = (0, 0, 10000) #m -> x, y, z -> z is altitude
v0 = (250, 0, 0) #m/s -> x, y, z

# 0 3 6
z0 = np.array((*x0, *v0))
c = sim.simulate(z0)

x1 = [x[0] for x in c][::1]
y1 = [x[1] for x in c][::1]
z1 = [x[2] for x in c][::1]


fig = plt.figure()
ax = plt.axes(projection='3d')

ax.scatter3D(x1[::30], y1[::30], z1[::30], 'green')

plt.show()