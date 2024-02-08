vs = [4,6,8,12,20]

print(" | ".join(["i", "vs[i]", "1/vs[i]", "1/vs[i] - 1/vs[i+1]"]))
for i,v in enumerate(vs):
    p = 1/v
    reduction = (1/v - 1/vs[i+1] if i+1 < len(vs) else 0)
    print(f"{i:1} | {v:>5} | {1/v:>7.3f} | {reduction:>19.4f}")
