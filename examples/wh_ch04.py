import numpy as np
import matplotlib.pyplot as plt

import statlib.dlm as dlm
reload(dlm)
from statlib.dlm import DLM, st
import statlib.datasets as datasets

lam = 1.
phis = np.arange(0.95, 1.05, .001)
disc = 0.8
y, x = datasets.table_33()

X = np.vstack((np.ones(len(x)),x )).T

m0, C0 = ([0, 0.45], [[0.005, 0],
                          [0, 0.0025]])
n0, s0 = (1, 1)

G = np.diag([lam, phis[0]])

like = []
for phi in phis:
    G = np.diag([lam, phi])

    model = DLM(y, X, G=G, m0=m0, C0=C0, n0=n0, s0=s0,
                state_discount=disc)

    like.append(model.pred_like)

like = np.array(like).prod(axis=1)
lr = like / like.max()
llr = np.log(lr)
fig = plt.figure(figsize=(12, 12))

ax1 = fig.add_subplot(211)
ax1.plot(phis, lr, label='LR')
ax2 = fig.add_subplot(212)
ax2.plot(phis, llr, label='LogLR')
plt.show()

model = dlm.DLM(y, X, G=G, m0=m0, C0=C0, n0=n0, s0=s0,
                state_discount=disc)
