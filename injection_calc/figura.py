import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

class Figura:
    def __init__(self):
        self.figura()
        
    def figura(self):
        x = np.genfromtxt('Cur&tunes.txt', usecols=(0), delimiter=" ", dtype=None)
        y = np.genfromtxt('Cur&tunes.txt', usecols=(1), delimiter=" ", dtype=None)
        N = np.genfromtxt('Cur&tunes.txt', usecols=(2), delimiter=" ", dtype=None)
        # xgrid, ygrid = np.meshgrid(x,y)


        fig = plt.figure()
        ax = Axes3D(fig)
        ax.plot_trisurf(x, y, N)
        plt.show()

a = Figura()