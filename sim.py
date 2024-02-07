import random
import pprint
from enum import Enum
from collections import defaultdict

# fixme: change to only have following dice: 4,6,8,12,20
# fixme: just sim turns where there is no choice (ie: legacy dice):
# * when you have legacy dice, the best action is to fix the highest rank die first
#   (as it has lower probability of returning to legacy pool before all legacy are fixed)

class GameState:
    def __init__(self):
        self.dice = defaultdict(int)
        self.dice[4] = 1
        self.legacy = defaultdict(int)
        self.score = 0

    def check_invariants(self):
        for v in self.dice.values():
            assert(v > 0)
        for v in self.legacy.values():
            assert(v > 0)
        if not self.dice:
            assert(self.score == 0)
    
    def print(self):
        print(f"score: {self.score}")
        print("dice: ", end="")
        pprint.pprint(self.dice)
        print("legacy: ", end="")
        pprint.pprint(self.legacy)

class Action(Enum):
    NEW_DIE = 1,
    FIX_LEGACY = 2,
    PROMOTE = 3,

class Game:
    def __init__(self):
        self.state = GameState()

    def action(self, act, val=-1):
        if act == Action.NEW_DIE:
            self.new_die()
        elif act == Action.FIX_LEGACY:
            self.fix_legacy()
        elif act == Action.PROMOTE:
            self.promote(val)

    def get_actions(self):
        res = []
        for k in self.state.legacy.keys():
            res += (Action.FIX_LEGACY, k)
        if not self.state.legacy:
            res += (Action.NEW_DIE, 0)
            for k in self.state.dice.keys():
                res += (Action.PROMOTE, k)
        return res


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

        self.state.dice[val+2] = 1 + (self.state.dice.get(val+2) or 0)
        self.state.check_invariants()

    def fix_legacy(self):
        self.state.check_invariants()
        assert(self.state.legacy)
        val = sorted(self.state.legacy.keys())[-1]
        assert(self.state.legacy[val] > 0)

        self.state.legacy[val] -= 1
        if self.state.legacy[val] == 0:
            del self.state.legacy[val]
        self.state.dice[val] = 1 + (self.state.dice.get(val) or 0)
        self.state.check_invariants()

    def roll(self):
        self.state.check_invariants()
        for k,v in self.state.dice.items():
            # zeroes = random.binomalvariate(v, 1/k)
            ones = sum(random.random() < 1/k for i in range(v))
            self.state.score += v - ones
            self.state.dice[k] -= ones
            if ones > 0:
                self.state.legacy[k] = ones + (self.state.legacy.get(k) or 0)

        for k in list(self.state.dice.keys()):
            if self.state.dice[k] == 0:
                del self.state.dice[k]

        if not self.state.dice:
            self.state.score = 0
        self.state.check_invariants()

class PlayGame:
    def __init__(self):
        self.game = Game()
        self.round = 0

    def play(self):
        for i in range(10):
            self.game.state.print()
            actions = self.game.get_actions()
            pprint.pprint(actions)
            act = input()
            if act == "N" or act == "NEW_DIE":
                self.game.action(Action.NEW_DIE)
            if act == "F" or act == "FIX_LEGACY":
                self.game.action(Action.FIX_LEGACY)
            if act == "P" or act == "PROMOTE":
                print("which die to promote?") 
                die = int(input())
                self.game.action(Action.PROMOTE, die)
            
            self.game.roll()

        print(f"final score: {self.game.state.score}")

