import numpy as np
from fastdtw import fastdtw

x = np.array([1, 2, 3])
y = np.array([2, 3, 4])
dist, path = fastdtw(x, y, dist=lambda a,b: abs(a-b))
print("DTW distance:", dist)
