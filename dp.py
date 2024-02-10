import numpy as np
import scipy as sp
from enum import IntEnum

ROUNDS = 14 # crashes at 12...

MAX_SCORE = (ROUNDS * (ROUNDS + 1)) // 2  # if we add a new dice every round and never hit a legacy roll

DVAL = [4, 6, 8, 12, 20]
# coarse upper bound for states
DMAX = [
    ROUNDS,
    ROUNDS // 2,
    ROUNDS // 3,
    ROUNDS // 4,
    ROUNDS // 5,
]


class Action(IntEnum):
    NEW_DIE = (0,)
    PROMOTE = (1,)


V = {}
# V = np.zeros(  # dp
#     (
#         ROUNDS,
#         MAX_SCORE + 1,
#         DMAX[0] + 1,  # revenue
#         DMAX[1] + 1,
#         DMAX[2] + 1,
#         DMAX[3] + 1,
#         DMAX[4] + 1,
#         DMAX[0] + 1,  # legacy
#         DMAX[1] + 1,
#         DMAX[2] + 1,
#         DMAX[3] + 1,
#         DMAX[4] + 1,
#     ),
#     dtype=float,
# )

DPPolicy = np.zeros(  # dp
    (
        ROUNDS,
        MAX_SCORE + 1,
        DMAX[0] + 1,  # revenue
        DMAX[1] + 1,
        DMAX[2] + 1,
        DMAX[3] + 1,
        DMAX[4] + 1,
    ),
    dtype=Action,
)


# counts probability of k failures where probability of success is p
def binomp(N, k, p):
    return sp.special.binom(N, k) * (p ** (N - k)) * ((1 - p) ** k)


def rollv(rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20):
    res = 0
    rnd_ = rnd + 1
    for r4_ in range(r4 + 1):
        p4 = binomp(r4, r4_, 1 / DVAL[0])
        for r6_ in range(r6 + 1):
            p6 = binomp(r6, r6_, 1 / DVAL[1])
            for r8_ in range(r8 + 1):
                p8 = binomp(r8, r8_, 1 / DVAL[2])
                for r12_ in range(r12 + 1):
                    p12 = binomp(r12, r12_, 1 / DVAL[3])
                    for r20_ in range(r20 + 1):
                        p20 = binomp(r20, r20_, 1 / DVAL[4])
                        delta = r4_ + r6_ + r8_ + r12_ + r20_
                        score_ = 0 if delta == 0 else score + delta
                        l4_ = l4 + r4 - r4_
                        l6_ = l6 + r6 - r6_
                        l8_ = l8 + r8 - r8_
                        l12_ = l12 + r12 - r12_
                        l20_ = l20 + r20 - r20_
                        p = p4 * p6 * p8 * p12 * p20
                        res += p * dpv(rnd_, score_, r4_, r6_, r8_, r12_, r20_, l4_, l6_, l8_, l12_, l20_)
    return res


def dpv(rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20):
    if rnd >= ROUNDS:
        return score

    v = V.get((rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20), None)
    if v:
        return v

    # check for legacy
    legacyv = 0
    if l20:
        legacyv = rollv(rnd, score, r4, r6, r8, r12, r20 + 1, l4, l6, l8, l12, l20 - 1)
    elif l12:
        legacyv = rollv(rnd, score, r4, r6, r8, r12 + 1, r20, l4, l6, l8, l12 - 1, l20)
    elif l8:
        legacyv = rollv(rnd, score, r4, r6, r8 + 1, r12, r20, l4, l6, l8 - 1, l12, l20)
    elif l6:
        legacyv = rollv(rnd, score, r4, r6 + 1, r8, r12, r20, l4, l6 - 1, l8, l12, l20)
    elif l4:
        legacyv = rollv(rnd, score, r4 + 1, r6, r8, r12, r20, l4 - 1, l6, l8, l12, l20)
    if legacyv:
        V[(rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20)] = legacyv
        return legacyv

    # add a dice
    addv = rollv(rnd, score, r4 + 1, r6, r8, r12, r20, l4, l6, l8, l12, l20)

    # try promo
    promov = 0
    if r4:
        promov = rollv(rnd, score, r4 - 1, r6 + 1, r8, r12, r20, l4, l6, l8, l12, l20)
    elif r6:
        promov = rollv(rnd, score, r4, r6 - 1, r8 + 1, r12, r20, l4, l6, l8, l12, l20)
    elif r8:
        promov = rollv(rnd, score, r4, r6, r8 - 1, r12 + 1, r20, l4, l6, l8, l12, l20)
    elif r12:
        promov = rollv(rnd, score, r4, r6, r8, r12 - 1, r20 + 1, l4, l6, l8, l12, l20)

    if addv >= promov:
        DPPolicy[rnd, score, r4, r6, r8, r12, r20] = 0  # new_die
        V[(rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20)] = addv
        return addv
    else:
        DPPolicy[rnd, score, r4, r6, r8, r12, r20] = 1  # promote
        V[(rnd, score, r4, r6, r8, r12, r20, l4, l6, l8, l12, l20)] = promov
        return promov


# top-down
v = dpv(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
print(v)
