import secrets

from clicker_common import Random

lo = 31234
hi = 285000

x = 270_000
y = 280_000

t = 5
c = 1000

rngs = {
    'CUSTOM': Random(t, c, autofill=False),
    'SystemRandom': secrets.SystemRandom()
}

for a in range(t):
    print(f"ITER: {a}")

    for rng in rngs.items():
        print(f"\t{rng[0]}:")
        m = 0
        for i in range(c):
            v = rng[1].randint(lo, hi)
            # print(v)
            if x <= v <= y:
                m += 1
        print(f"\t\tMATCHES: {m}")
