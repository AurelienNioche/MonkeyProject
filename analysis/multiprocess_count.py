# from multiprocessing import Pool, Process, Queue
#
#
# class CountProcess(Process):
#
#     def __init__(self, counter):
#
#         self.counter = counter
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

x = np.arange(10)
y = np.ones(len(x))

colors = list(cm.rainbow(np.linspace(0, 1, len(y))))
print(colors)
colors = [i[:3] for i in colors]
print(colors)

plt.scatter(x, y, color=colors)

plt.show()