import time

from clicker_framework import Random

Random.ARRAY_SIZE = 10
Random.CHUNK_SIZE = 1024

r = Random()

# exit(0)

for i in range(9):
    for j in range(1024):
        r.random()
for i in range(960):
    r.random()

while 1:
    print(f"Random: {r.random()}")
    print(f"LIST STATUS: {r._list_it + 1} / {r._len_data}")
    print(f"VALUE STATUS: {r._value_it + 1} / {r._chunk_size}")
    time.sleep(0.5)
