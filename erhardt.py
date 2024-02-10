from itertools import product

def erhardt_val(dim, R):
    tot = 0
    for xs in product(range(R+1), repeat=dim):
        w = 0
        for i in range(dim):
            w += xs[i] * (i + 1)
        if w <= R:
            tot += 1
    return tot

print("dim |   R | er_val(dim,R) | delta er_val(dim,R)")
for dim in range(5):
    print("--------------------------------------------")
    for R in range(30):
        print(f"{dim:>3} | {R:>3} | {erhardt_val(dim,R):>13} | {erhardt_val(dim,R+1) - erhardt_val(dim,R):>18}")
