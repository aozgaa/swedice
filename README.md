
Explorations for Ben Rady's SWE dice game:
https://www.benrady.com/2023/01/the-software-engineering-game.html

* sim: environment for playing the game including some sample policies
* TODO: solver for optimal strategy (dynamic programming?)

# Varying Rounds

The sample policies greatly vary in their performance if the number of rounds changes:

```
$ python sim.py # 10 rounds
NewOnlyPolicy     :   20.4393
PromoPolicy       :   11.4569
PromoOncePolicy   :   17.5295
RandPolicy        :   16.7925

$ python sim.py # 100 rounds
NewOnlyPolicy     :  186.3073
PromoPolicy       :  653.2839
PromoOncePolicy   :  411.1291
RandPolicy        :  431.6202
```

