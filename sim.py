import random
import pprint
from enum import Enum
from collections import defaultdict
from abc import ABC, abstractmethod

# from typing import override # python 3.12

# fixme: change to only have following dice: 4,6,8,12,20
# fixme: just sim turns where there is no choice (ie: legacy dice):
# * when you have legacy dice, the best action is to fix the highest rank die first
#   (as it has lower probability of returning to legacy pool before all legacy are fixed)

class Action(Enum):
    NEW_DIE = (1,)
    PROMOTE4 = (4,)
    PROMOTE6 = (6,)
    PROMOTE8 = (8,)
    PROMOTE12 = (12,)

ROUNDS = 100

DIDX = {4: 0, 6: 1, 8: 2, 12: 3, 20: 4}
DVAL = [4, 6, 8, 12, 20]
DNEXT = [6, 8, 12, 20]
# coarse upper bound for states
# fixme: refine to sum of the promote/create actions used is <= ROUNDS
DMAX = [
    ROUNDS,
    ROUNDS / 2,
    ROUNDS / 3,
    ROUNDS / 4,
    ROUNDS / 5,
]

DPROMO = [Action.PROMOTE4, Action.PROMOTE6, Action.PROMOTE8, Action.PROMOTE12]


# fixme: use this instead
class DiceState:
    def __init__(self):
        self.dice = [0 for i in range(len(DVAL))]

    def __str__(self):
        return f"{{ d4: {self.dice[0]}, d6: {self.dice[1]}, d8: {self.dice[2]}, d12: {self.dice[3]}, d20: {self.dice[4]} }}"

    def __bool__(self):
        return sum(self.dice) > 0

    def check(self):
        for k, v in DIDX.items():
            assert self.dice[v] >= 0
            assert self.dice[v] <= DMAX[v]


class GameState:
    def __init__(self):
        self.score = 0
        self.round = 0
        self.revenue = DiceState()
        self.legacy = DiceState()

    def check_invariants(self):
        self.revenue.check()
        self.legacy.check()
        assert self.revenue or self.score == 0


def print_state(state):
    print(f"# round: {state.round} / {ROUNDS}\nscore: {state.score}")
    print("revenue: ", end="")
    pprint.pprint(state.revenue)
    print("legacy:  ", end="")
    pprint.pprint(state.legacy)


def get_actions(state):
    assert not state.legacy
    res = [Action.NEW_DIE]
    for i, p in enumerate(DPROMO):
        if state.revenue.dice[i] > 0:
            res.append(p)
    return res


class Game:
    def __init__(self):
        self.state = GameState()

    def update(self, action):
        self.state.check_invariants()
        assert not self.state.legacy
        assert action in get_actions(self.state)

        if action == Action.NEW_DIE:
            self.new_die()
        else:
            val = (
                4
                if action == Action.PROMOTE4
                else 6
                if action == Action.PROMOTE6
                else 8
                if action == Action.PROMOTE8
                else 12
                if action == Action.PROMOTE12
                else -1
            )
            self.promote(val)

        self.roll()
        self.state.round += 1
        while self.state.round < ROUNDS and self.state.legacy:
            self.fix_legacy()
            self.roll()
            self.state.round += 1

    def new_die(self):
        assert not self.state.legacy

        self.state.revenue.dice[0] += 1

    def promote(self, val):
        assert not self.state.legacy
        idx = DIDX[val]
        assert self.state.revenue.dice[idx] > 0

        self.state.revenue.dice[idx] -= 1
        self.state.revenue.dice[idx + 1] += 1

    def fix_legacy(self):
        assert self.state.legacy
        k = 0
        for i, v in enumerate(self.state.legacy.dice):
            if v > 0:
                k = i

        self.state.legacy.dice[k] -= 1
        self.state.revenue.dice[k] += 1

    def roll(self):
        for i, cnt in enumerate(self.state.revenue.dice):
            if cnt == 0:
                continue
            ones = sum(random.random() < 1 / DVAL[i] for _ in range(cnt))
            self.state.score += cnt - ones
            self.state.revenue.dice[i] -= ones
            self.state.legacy.dice[i] += ones

        if not self.state.revenue:
            self.state.score = 0


class Policy(ABC):
    @abstractmethod
    def get_action(self, state):
        pass


def play_policy(policy):
    game = Game()
    while game.state.round < ROUNDS:
        action = policy.get_action(game.state)
        game.update(action)
    return game.state.score


class ManualPolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        print_state(state)
        actions = get_actions(state)
        pprint.pprint(actions)

        action = input()
        if action == "N" or action == "NEW_DIE":
            return Action.NEW_DIE
        if action == "P" or action == "PROMOTE":
            print("which die to promote?")
            die = int(input())
            return DPROMO[DIDX[die]]


class NewOnlyPolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        return Action.NEW_DIE


class PromoPolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        return actions[-1]  # new die is always first action


class PromoOncePolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        if Action.PROMOTE4 in actions:
            return Action.PROMOTE4
        return Action.NEW_DIE


# Try to promote when the expected number of failures reaches some threshold
class ExpLegacyPolicy(Policy):
    def __init__(self, beta):
        self.beta = beta

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        e_failures = 0
        for i, cnt in enumerate(state.revenue.dice):
            e_failures += cnt * 1 / DVAL[i]
        if e_failures < self.beta or len(actions) == 1:
            return Action.NEW_DIE
        return actions[1]


class EL2Policy(ExpLegacyPolicy):
    def __init__(self):
        super().__init__(0.9)


class EL5Policy(ExpLegacyPolicy):
    def __init__(self):
        super().__init__(0.5)


class EL9Policy(ExpLegacyPolicy):
    def __init__(self):
        super().__init__(0.9)


class EL20Policy(ExpLegacyPolicy):
    def __init__(self):
        super().__init__(2.0)


class RandPolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        return random.choice(actions)


class RandLoPolicy(Policy):  # coin flip between new die and promoting the low die
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        if len(actions) == 1:
            return Action.NEW_DIE
        return random.choices([actions[0], actions[1]], weights=[1, len(actions) - 1])[
            0
        ]


class RandHiPolicy(Policy):  # coin flip between new die and promoting the high die
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        return random.choices([actions[0], actions[-1]], weights=[1, len(actions) - 1])[
            0
        ]


# score = play_policy(ManualPolicy())
# print(f"final score: {score}")

for cls in [
    NewOnlyPolicy,
    PromoPolicy,
    PromoOncePolicy,
    EL2Policy,
    EL5Policy,
    EL9Policy,
    EL20Policy,
    RandPolicy,
    RandLoPolicy,
    RandHiPolicy,
]:
    inst = cls()
    avg = sum(play_policy(inst) for i in range(10000)) / 10000
    print(f"{cls.__name__:18}: {avg:9}")
