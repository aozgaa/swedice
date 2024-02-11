
Explorations for Ben Rady's SWE dice game:
https://www.benrady.com/2023/01/the-software-engineering-game.html

* `sim.py`: environment for playing the game including some sample policies
* `dp.py`: solver for exact optimal strategy
* `dp.cpp`: sovler implementation in c++ that handles larger inputs (up to ~22).

# The Game

The game is a single player game involving dice with the following number of
faces: 4,6,8,12,20

The goal of the game is to maximize the final score.

The game is played for `R` rounds (10 in the original version) with the
following state in each round:
* the round number
* the current score
* the number of `d4`,`d6`,...,`d20` "revenue" dice the player has
* the number of `d4`,`d6`,...,`d20` "legacy" dice the player has

In the first round the player has no dice and an initial score of 0.

Repeat the following `R` times:
1) if the player has an "legacy" dice, they pick one of them to convert into a
revenue die.
2) Otherwise, the player picks to either:
  a) add a new d4 to their revenue pool
  b) promote a "revenue" dice to the next number of faces
3) The player then rolls all their "revenue" dice:
  * any dice landing on `1` go into the legacy pile
  * increment the score by one for all dice remaining in the "revenue" pile
4) If there are no "revenue" dice, set the score to 0

The player's score is their score at the completion of the final round.

(In a multiplayer variant where palyers compete for the maximum final score and
process a round in turn order, there could be strategic decisions to make in
terms of increasing variance while lowering expectation in order to increase
probability of winning)

# Results Summary

* 10 round game: always create a new die.
* 30 round game:  promote a dice to a d6 if possible, otherwise create a new die.
* 100 round game: promote if possible, otherwise create a new die.

# Setup and Running
We need a couple python packages as dependencies, get them in the preferred way
(eg: `venv`):
```
python -m venv venv/
. venv/bin/activate
pip install numpy scipy
```
Scripts take no arguments, edit variables (eg: `ROUNDS`) to run with different
parameters:
```
python sim.py
...
python dp.py
...
```

For the c++ `dp` program, `Boost.ContainerHash` is used for hashing tuples.
Follow the
[Getting Started Guide](https://www.boost.org/doc/libs/1_84_0/more/getting_started/index.html)
to setup.

Build with something like
```
make dp CXXFLAGS="-std=c++2b -O3"
```
and run with
```
./dp
```

# Symmetries

The game has certain symmetries that simplify modeling:

## Fixing Legacy

When a legacy dice is obtained, we need to fix legacy features. As all our
turns are dedicated to this task until there are no legacy features, and the
game has positive EV, we should try to fix the more robust features so we can
get back to making improvements sooner (in expectation).

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
so I have also skipped it here. Including it does break this greedy
sub-strategy)

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

# Varying Rounds

The sample policies greatly vary in their relative performance if the number of rounds changes:


```
$ python sim.py          # 10 rounds
policy                      mean    p10    p20    p50    p90    p95    p99    max
-----------------------  -------  -----  -----  -----  -----  -----  -----  -----
NewOnlyPolicy()          20.4285      9     15     21     30     33     38     47
PromoPolicy()            11.3936      7      9     12     15     15     15     15
PromoOncePolicy()        17.5299     11     14     18     24     25     28     30
ExpLegacyPolicy(0.2)     13.8859      8     11     15     18     19     20     20
ExpLegacyPolicy(0.5)     17.5381      9     14     19     24     25     28     29
ExpLegacyPolicy(0.9)     19.6407      9     15     21     28     30     33     38
ExpLegacyPolicy(1.0)     19.8342      9     15     21     28     31     34     39
ExpLegacyPolicy(2.0)     20.4322      9     15     21     30     33     37     46
RandPolicy(0.1)          12.6042      7      9     13     17     19     22     35
RandPolicy(0.2)          13.8666      8     10     14     20     22     25     34
RandPolicy(0.5)          17.451       9     13     18     25     28     32     40
RandPolicy(0.8)          19.697      10     14     20     29     31     36     44
RandPolicy(0.9)          20.1577     10     15     21     29     32     37     48
RandPolicy(1)            20.4376     10     15     21     30     33     38     48
PromoThenNewPolicy(0.1)  11.4551      7      9     12     15     15     15     15
PromoThenNewPolicy(0.2)  11.3855      7      9     12     15     15     15     15
PromoThenNewPolicy(0.5)  11.4877      7      9     12     15     15     15     15
PromoThenNewPolicy(0.8)  11.3894      7      9     12     15     15     15     15
PromoThenNewPolicy(0.9)  11.3881      7      9     12     15     15     15     15
NewThenPromoPolicy(0.1)  20.4706     10     15     21     30     33     38     48
NewThenPromoPolicy(0.2)  20.4961     10     15     21     30     33     38     50
NewThenPromoPolicy(0.5)  20.5538     10     15     21     30     33     37     51
NewThenPromoPolicy(0.8)  20.4216      9     15     21     30     32     37     48
NewThenPromoPolicy(0.9)  20.5329     10     15     21     30     33     37     47

$ python sim.py          # 30 rounds
policy                      mean    p10    p20    p50    p90    p95    p99    max
-----------------------  -------  -----  -----  -----  -----  -----  -----  -----
NewOnlyPolicy()          70.5769     19     49     77    101    109    123    152
PromoPolicy()            79.6702     67     72     80     92     94     99    104
PromoOncePolicy()        92.0301     70     78     93    115    122    133    170
ExpLegacyPolicy(0.2)     79.2237     64     70     80     93     96    102    111
ExpLegacyPolicy(0.5)     82.5735     62     71     84    102    106    115    126
ExpLegacyPolicy(0.9)     78.5807     44     63     82    106    113    125    145
ExpLegacyPolicy(1.0)     77.0499     40     62     81    106    113    125    153
ExpLegacyPolicy(2.0)     71.3014     20     52     78    102    109    122    149
RandPolicy(0.1)          80.9594     66     72     82     95     99    106    128
RandPolicy(0.2)          83.5825     67     73     84    101    105    116    144
RandPolicy(0.5)          85.8505     62     73     88    110    116    128    153
RandPolicy(0.8)          78.0927     38     63     83    107    114    126    163
RandPolicy(0.9)          74.4417     27     58     80    104    112    125    148
RandPolicy(1)            70.9955     18     50     78    103    109    123    154
PromoThenNewPolicy(0.1)  79.4273     67     72     80     91     94     99    105
PromoThenNewPolicy(0.2)  79.5914     67     72     80     91     94     99    105
PromoThenNewPolicy(0.5)  79.5914     67     72     80     91     94     99    105
PromoThenNewPolicy(0.8)  79.617      67     72     81     91     94     99    105
PromoThenNewPolicy(0.9)  79.5999     67     72     80     91     94     99    105
NewThenPromoPolicy(0.1)  71.4453     19     52     78    103    110    122    158
NewThenPromoPolicy(0.2)  71.2819     19     51     78    102    109    124    152
NewThenPromoPolicy(0.5)  71.0014     18     51     78    102    109    123    145
NewThenPromoPolicy(0.8)  70.939      18     50     78    102    109    123    153
NewThenPromoPolicy(0.9)  71.5944     21     53     78    102    109    123    165

$ python sim.py          # 100 rounds
policy                      mean    p10    p20    p50    p90    p95    p99    max
-----------------------  -------  -----  -----  -----  -----  -----  -----  -----
NewOnlyPolicy()          184.625     19     53    194    326    342    371    411
PromoPolicy()            653.394    592    612    653    715    733    763    829
PromoOncePolicy()        412.127    353    379    421    482    500    535    613
ExpLegacyPolicy(0.2)     638.148    571    595    639    704    722    754    818
ExpLegacyPolicy(0.5)     539.97     457    484    541    624    647    687    798
ExpLegacyPolicy(0.9)     393.707    300    340    400    487    512    558    689
ExpLegacyPolicy(1.0)     363.19     250    308    375    463    487    534    659
ExpLegacyPolicy(2.0)     185.516     18     53    195    327    344    375    453
RandPolicy(0.1)          617.962    540    571    622    693    711    745    823
RandPolicy(0.2)          556.315    446    489    565    656    680    722    785
RandPolicy(0.5)          387.707    282    335    400    493    520    572    691
RandPolicy(0.8)          262.794     53    134    306    386    407    450    550
RandPolicy(0.9)          223.601     34     85    269    356    376    411    490
RandPolicy(1)            185.74      20     55    196    327    342    370    433
PromoThenNewPolicy(0.1)  652.421    590    612    653    714    730    760    814
PromoThenNewPolicy(0.2)  654.196    591    613    655    716    734    768    837
PromoThenNewPolicy(0.5)  652.942    592    612    652    716    734    766    821
PromoThenNewPolicy(0.8)  653.427    592    613    653    714    731    763    850
PromoThenNewPolicy(0.9)  652.717    590    611    652    717    733    767    815
NewThenPromoPolicy(0.1)  184.946     19     54    196    324    342    371    445
NewThenPromoPolicy(0.2)  184.909     17     50    196    326    343    372    436
NewThenPromoPolicy(0.5)  184.892     19     54    195    325    341    367    421
NewThenPromoPolicy(0.8)  186.865     19     56    200    327    342    372    435
NewThenPromoPolicy(0.9)  185.321     19     55    196    325    341    371    461
```

# dp
The value of the game with 10 rounds agrees with the `NewOnlyPolicy` in the
`sim.py`:
```
$ python dp.py
20.483601957243238
```

The program currently crashes with memory limits if the instance size exceeds
11.

## Optimization opportunities:
* implict score representation: the score is only needed for catastrophic
  failure penalty calculations. The probability of a catastrophic failure
  within one step is known (some independent binomial distribution tails
  multiplied). There might be an analytic way to telescope for multiple steps:
  * Fix `n` dice with `k` faces. Let `p := 1/k` and `q := 1-p`. Then,
  * probability of all 1's after one roll is is `p^n`
  * probability within two rolls is is `p^n (1+q)^n`
  * probability within three rolls is is `p^n (1+q(1 + q))^n`
  * probability within four rolls is is `p^n (1+q(1 + q(1+q)))^n`
  * ...
* dice representations:
  * currently allocate a slot in each dimension as if all dice were of the
    singular type and no failures are ever observed, it is impossibly for these
    to simultaneously be true
  * we could do indexing on the basis of the volume of lower-dimensional
    simplices (Erhardt polynomials) to get a dense representation
  * we also size the legacy dice as if they are independent of the revenue
    dice, but this wastes space (eg: can't have 10 revenue and legacy dice at
    the same time)
* representing legacy dice:
  * we allocate slots for the legacy dice in the value function as a space-time
    tradeoff so we do not need to do multiple rolls to figure out the value of
    the state
  * otherwise if we have revenue dice d4,d6,...,d20, we would end up "rolling"
    until we ended the game or had no legacy, effectively computing all paths
    (maybe down to some epsilon/tail probability or magnitude) to the end of
    the game
  * there may be a 10-d simplex we could use for the erhardt polynomial
    constriants. Maybe wolfram alpha can help with computing the polynomials
