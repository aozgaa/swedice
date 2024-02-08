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
    NEW_DIE = 1,
    PROMOTE4 = 4,
    PROMOTE6 = 6,
    PROMOTE8 = 8,
    PROMOTE12 = 12,

ROUNDS = 100

DIDX = { 4:0, 6:1, 8:2, 12:3, 20:4 }
DVAL = [4,6,8,12,20]
DNEXT = [6,8,12,20]
# coarse upper bound for states
# fixme: refine to sum of the promote/create actions used is <= ROUNDS
DMAX = [(ROUNDS+1),
        (ROUNDS+1)/2,
        (ROUNDS+1)/3,
        (ROUNDS+1)/4,
        (ROUNDS+1)/5,]
DPROMO = [Action.PROMOTE4,
          Action.PROMOTE6,
          Action.PROMOTE8,
          Action.PROMOTE12]

# fixme: use this instead
class DiceState:
    def __init__(self):
        self.dice = [0 for i in range(len(DVAL))]

    def __str__(self):
        return f"{{ d4: {self.d4}, d6: {self.d6}, d8: {self.d8}, d12: {self.d12}, d20: {self.d20} }}"

    def __bool__(self):
        return sum(self.dice) > 0

    def check(self):
        for k,v in DIDX.items():
            assert(self.dice[v] <= DMAX[v])

class GameState:
    def __init__(self):
        self.score = 0
        self.round = 0
        self.dice = defaultdict(int) # fixme: use DiceState
        self.legacy = defaultdict(int) # fixme: use DiceState

    def check_invariants(self):
        for v in self.dice.values():
            assert(v > 0)
        for v in self.legacy.values():
            assert(v > 0)
        if not self.dice:
            assert(self.score == 0)
    
def print_state(state):
    print(f"# round: {state.round} / {ROUNDS}\nscore: {state.score}")
    print("dice: ", end="")
    pprint.pprint(state.dice)
    print("legacy: ", end="")
    pprint.pprint(state.legacy)

def get_actions(state):
    assert(not state.legacy)
    res = [Action.NEW_DIE]
    for k in state.dice.keys():
        idx = DIDX[k]
        if idx < len(DPROMO):
            res.append(DPROMO[idx])
    return res

class Game:
    def __init__(self):
        self.state = GameState()
    
    def update(self, action):
        self.state.check_invariants()
        assert(not self.state.legacy)
        assert(action in get_actions(self.state))

        if action == Action.NEW_DIE:
            self.new_die()
        else:
            val = 4 if action == Action.PROMOTE4 else \
                    6 if action == Action.PROMOTE6 else \
                    8 if action == Action.PROMOTE8 else \
                    12 if action == Action.PROMOTE12 else -1
            self.promote(val)

        self.roll()
        self.state.round += 1
        while self.state.round < ROUNDS and self.state.legacy:
            self.fix_legacy()
            self.roll()
            self.state.round += 1


    def new_die(self):
        self.state.check_invariants()
        assert(not self.state.legacy)

        self.state.dice[4] += 1

    def promote(self, val):
        self.state.check_invariants()
        assert(not self.state.legacy)
        assert(self.state.dice[val] > 0)

        self.state.dice[val] -= 1
        if self.state.dice[val] == 0:
            del self.state.dice[val]

        self.state.dice[DNEXT[DIDX[val]]] += 1
        self.state.check_invariants()

    def fix_legacy(self):
        self.state.check_invariants()
        assert(self.state.legacy)
        val = sorted(self.state.legacy.keys())[-1]
        assert(self.state.legacy[val] > 0)

        self.state.legacy[val] -= 1
        if self.state.legacy[val] == 0:
            del self.state.legacy[val]
        self.state.dice[val] += 1
        self.state.check_invariants()

    def roll(self):
        self.state.check_invariants()
        for k,v in self.state.dice.items():
            # zeroes = random.binomalvariate(v, 1/k) # added python 3.12
            ones = sum(random.random() < 1/k for i in range(v))
            self.state.score += v - ones
            self.state.dice[k] -= ones
            if ones > 0:
                self.state.legacy[k] += ones

        for k in list(self.state.dice.keys()):
            if self.state.dice[k] == 0:
                del self.state.dice[k]

        if not self.state.dice:
            self.state.score = 0
        self.state.check_invariants()

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
        return actions[-1] # new die is always first action

class PromoOncePolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        if Action.PROMOTE4 in actions:
            return Action.PROMOTE4
        return Action.NEW_DIE

class RandPolicy(Policy):
    def __init__(self):
        pass

    # @override # python 3.12
    def get_action(self, state):
        actions = get_actions(state)
        return random.choice(actions)

# class DPPolicy(Policy):
#     def __init__(self):
#         assert(ROUNDS == 10) # assumed throughout
#         self.d2s = {} # number of active dies to state
#         V[round][score][dies]

# score = play_policy(ManualPolicy())
# print(f"final score: {score}")

for cls in [NewOnlyPolicy, PromoPolicy, PromoOncePolicy, RandPolicy]:
    inst = cls()
    avg = sum(play_policy(inst) for i in range(10000)) / 10000
    print(f"{cls.__name__:18}: {avg:9}")

