import random
import pprint
from enum import IntEnum
from collections import defaultdict
from abc import ABC, abstractmethod

# from typing import override # python 3.12

class Action(IntEnum):
    NEW_DIE = (0,)
    PROMOTE = (1,)


ROUNDS = 22

MAX_SCORE = (
    ROUNDS * (ROUNDS + 1)
) / 2  # if we add a new dice every round and never hit a legacy roll

DIDX = {4: 0, 6: 1, 8: 2, 12: 3, 20: 4}
DVAL = [4, 6, 8, 12, 20]
DNEXT = [6, 8, 12, 20]
# coarse upper bound for states (assumes all coins are of the given number)
DMAX = [
    ROUNDS,
    ROUNDS / 2,
    ROUNDS / 3,
    ROUNDS / 4,
    ROUNDS / 5,
]


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
    for i in range(len(DNEXT)):
        if state.revenue.dice[i] > 0:
            res.append(Action.PROMOTE)
            break
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
        elif action == Action.PROMOTE:
            self.promote()
        else:
            assert False

        self.roll()
        self.state.round += 1
        while self.state.round < ROUNDS and self.state.legacy:
            self.fix_legacy()
            self.roll()
            self.state.round += 1

    def new_die(self):
        assert not self.state.legacy

        self.state.revenue.dice[0] += 1

    def promote(self):
        assert not self.state.legacy
        for i in range(len(DNEXT)):
            if self.state.revenue.dice[i] > 0:
                self.state.revenue.dice[i] -= 1
                self.state.revenue.dice[i + 1] += 1
                return
        assert False

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

    def __str__(self):
        return f"{type(self).__name__}()"

    def __format__(self, spec):
        return format(str(self), spec)


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
            return Action.PROMOTE


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
        if state.revenue.dice[0] > 0:
            return Action.PROMOTE
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

    def __str__(self):
        return f"ExpLegacyPolicy({self.beta})"

    def __format__(self, spec):
        return format(str(self), spec)


class RandPolicy(Policy):
    def __init__(self, pnew):
        self.pnew = pnew

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        if len(actions) == 1:
            return Action.NEW_DIE
        return random.choices(actions, cum_weights=[self.pnew, 1])[0]

    def __str__(self):
        return f"RandPolicy({self.pnew})"

    def __format__(self, spec):
        return format(str(self), spec)


# score = play_policy(ManualPolicy())
# print(f"final score: {score}")

def play_strats():
    for inst in [
        NewOnlyPolicy(),
        PromoPolicy(),
        PromoOncePolicy(),
        ExpLegacyPolicy(0.2),
        ExpLegacyPolicy(0.5),
        ExpLegacyPolicy(0.9),
        ExpLegacyPolicy(1.0),
        ExpLegacyPolicy(2.0),
        RandPolicy(0.1),
        RandPolicy(0.2),
        RandPolicy(0.5),
        RandPolicy(0.8),
        RandPolicy(0.9),
        RandPolicy(1),  # same as NewOnlyPolicy
    ]:
        avg = sum(play_policy(inst) for i in range(10000)) / 10000
        print(f"{inst:20}: {avg:9}")

if __name__ == "__main__":
    play_strats()
