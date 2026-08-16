import numpy as np

N = 10000

x = [0.8, 2.0, 3.0, 4.0]
ux = [0.0054, 0.0087, 0.012, 0.015]
y = [0.115, 0.276, 0.387, 0.500]
uy = [0.00078, 0.0084, 0.0096, 0.0038]

a_sim = []
b_sim = []

for i in range(N):
    xs = np.random.normal(x, ux)
    ys = np.random.normal(y, uy)
    RL = np.polyfit(xs, ys, 1)
    a_sim.append(RL[0])
    b_sim.append(RL[1])

ua = np.std(a_sim)
ub = np.std(b_sim)

print(f"ua: {ua}, ub: {ub}")
