
Explorations for Ben Rady's SWE dice game:
https://www.benrady.com/2023/01/the-software-engineering-game.html

* sim: environment for playing the game including some sample policies
* dp.py: solver for exact optimal strategy

# Setup and Running
We need a couple python packages as dependencies, get them in the preferred way (eg: `venv`):
```
python -m venv venv/
. venv/bin/activate
pip install numpy scipy
```
Scripts take no arguments, edit variables (eg: `ROUNDS`) to run with different parameters:
```
python sim.py
...
python dp.py
...
```

# Symmetries

The game has certain symmetries that simplify modeling:

## Fixing Legacy

We need to fix legacy features.

As all our turns are dedicated to this task until there are no legacy features,
and the game has positive EV, we should try to fix the more robust features so
we can get back to making improvements sooner (in expectation).

So, the optimal strategy whenever there are legacy features is completely
determined, and we can fix these steps as part of the environment.

Note that it is still useful to include the legacy features as states in the DP
as a space-time tradeoff.

## Dice Promotions

The rewards for a working feature are constant (1) but as we improve a dice the
risk of failure decreases.

The relative changes are:
```
$ python promo.py
  i | vs[i] | 1/vs[i] | 1/vs[i] - 1/vs[i+1]
  0 |     4 |   0.250 |              0.0833
  1 |     6 |   0.167 |              0.0417
  2 |     8 |   0.125 |              0.0417
  3 |    12 |   0.083 |              0.0333
  4 |    20 |   0.050 |              0.0000
```

That is, the expected number of failures decreases most with the first
promotion, and (weakly) less with each subsequent promotion.

So, the greedy strategy of always promoting the lowest ranked die is best to
maximize future reward.

(Note, the example playthrough on the original blog post elided the `d10` die,
so I have also skipped it here. Including it does break the greedy sub-strategy)

## Never Skip

The game doesn't have such an action, but it would never be helpful to skip
creating or promoting a dice:
* Having more dice means there are more opportunities to score in the future,
  and decreases the odds of catastrophic failure.
* promoting a dice raises the expected value of the dice itself and decreases
  the odds of catastrophic failure

It is straightforward but tedious to formalize these observations in the
language of MDP's (hint: use the law of total expectation to decompose the
cases).

## TODO: Score Symmetry

TODO: how does having a high working score affect strategy?
* Penalty of zeroing out is higher.
* is there a "retirement cliff" effect prioritizing avoiding catastrophe?
  + it seems that having more reliable systems is highly valuable in longer
    games even absent this effect, so it is probably not affecting policy in
    many states, might be okay to truncate/compress this part of state

2) score: If a round starts in state `S` with score `s` or `s'`, and we are
taking action `A`. Then the relative effect of getting a catastrophic failure
is worse if have a higher score. Suppose we have probability `p` of failing.
Then with score `s` our EV is something like:
```
p*0 + (1-p)*v(
```

# Varying Rounds

The sample policies greatly vary in their relative performance if the number of rounds changes:

```
$ python sim.py   # 10 rounds
NewOnlyPolicy     :   20.4573
PromoPolicy       :   11.4133
PromoOncePolicy   :   17.5017
EL2Policy         :   19.7738
EL5Policy         :   17.3917
EL9Policy         :   19.6538
EL20Policy        :   20.5476
RandPolicy        :   16.6526

$ python sim.py   # 30 rounds
NewOnlyPolicy     :   70.6989
PromoPolicy       :   79.5236
PromoOncePolicy   :   91.8965
EL2Policy         :   78.4788
EL5Policy         :   82.4763
EL9Policy         :   78.4589
EL20Policy        :   71.5793
RandPolicy        :   82.9656

$ python sim.py   # 100 rounds
NewOnlyPolicy     :  183.9438
PromoPolicy       :  652.8854
PromoOncePolicy   :  411.9217
EL2Policy         :  392.2955
EL5Policy         :  540.7135
EL9Policy         :  392.7529
EL20Policy        :  188.2348
RandPolicy        :  432.1997
```

# dp
The value of the game with 10 rounds agrees with the `NewOnlyPolicy` in the `sim.py`:
```
$ python dp.py
20.483601957243238
```

The program currently crashes with memory limits if the instance size exceeds 11. Optimization opportunities:
* implict score representation: the score is only needed for catastrophic
  failure penalty calculations. The probability of a catastrophic failure
  within one step is known (some independent binomial distribution tails
  multiplied). There might be an analytic way to telescope for multiple steps
* dice representations:
  * currently allocate a slot in each dimension as if all dice were of the singular type and no failures are ever observed, it is impossibly for these to simultaneously be true
  * we could do indexing on the basis of the volume of lower-dimensional simplices (Erhardt polynomials) to get a dense representation
  * we also size the legacy dice as if they are independent of the revenue dice, but this wastes space (eg: can't have 10 revenue and legacy dice at the same time)
* representing legacy dice:
  * we allocate slots for the legacy dice in the value function as a space-time tradeoff so we do not need to do multiple rolls to figure out the value of the state
  * otherwise if we have revenue dice d4,d6,...,d20, we would end up "rolling" until we ended the game or had no legacy, effectively computing all paths (maybe down to some epsilon/tail probability or magnitude) to the end of the game
  * there may be a 10-d simplex we could use for the erhardt polynomial constriants. Maybe wolfram alpha can help with computing the polynomials
