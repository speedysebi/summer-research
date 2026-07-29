"""Medium tier, second batch: greedy, selection, grid DP, parsing, sets."""
from __future__ import annotations

from .core import (fam, grid01, ints, matrix, pos_ints, problem, sentence,
                   sorted_ints, word)


@fam("greedy", "medium", ["greedy"])
def f_greedy():
    def jump_min(nums):
        if len(nums) <= 1:
            return 0
        jumps, cur_end, far = 0, 0, 0
        for i in range(len(nums) - 1):
            far = max(far, i + nums[i])
            if i == cur_end:
                jumps += 1
                cur_end = far
                if cur_end >= len(nums) - 1:
                    break
        return jumps if cur_end >= len(nums) - 1 else -1

    def gas_station(gas, cost):
        if sum(gas) < sum(cost):
            return -1
        start, tank = 0, 0
        for i in range(len(gas)):
            tank += gas[i] - cost[i]
            if tank < 0:
                start, tank = i + 1, 0
        return start

    def partition_labels(s):
        last = {c: i for i, c in enumerate(s)}
        out, start, end = [], 0, 0
        for i, c in enumerate(s):
            end = max(end, last[c])
            if i == end:
                out.append(end - start + 1)
                start = i + 1
        return out

    specs = [
        ("Minimum Jumps To End",
         "Given a list `nums` where `nums[i]` is the furthest jump from index `i`, "
         "return the fewest jumps to reach the last index, or -1 if unreachable.",
         jump_min, lambda rng: (pos_ints(rng, lo=0, hi=4, min_n=1),), "def solve(nums):"),
        ("Gas Station Start",
         "Given lists `gas` and `cost` of equal length, return the starting index from "
         "which you can travel the whole circle, or -1 if impossible. A unique answer "
         "exists when one exists.", gas_station,
         lambda rng: _gas(rng), "def solve(gas, cost):"),
        ("Partition Labels",
         "Given a string `s`, split it into as many parts as possible so no letter "
         "appears in more than one part, and return the part lengths in order.",
         partition_labels, lambda rng: (word(rng, 0, 12, "abcd"),), "def solve(s):"),
        ("Minimum Arrows To Burst",
         "Given a list of `[start, end]` intervals, return the fewest points needed so "
         "every interval contains at least one point.",
         lambda intervals: _min_arrows(intervals), lambda rng: (_ivals(rng),),
         "def solve(intervals):"),
        ("Boats To Save People",
         "Given a list `people` of weights and an integer `limit`, each boat carries at "
         "most two people with total weight at most `limit`. Return the fewest boats.",
         lambda people, limit: _boats(people, limit),
         lambda rng: (pos_ints(rng, lo=1, hi=10), rng.randint(10, 20)),
         "def solve(people, limit):"),
        ("Assign Cookies",
         "Given lists `greed` and `sizes`, give each child at most one cookie whose "
         "size is at least their greed. Return the most children that can be satisfied.",
         lambda greed, sizes: _cookies(greed, sizes),
         lambda rng: (pos_ints(rng, lo=1, hi=9), pos_ints(rng, lo=1, hi=9)),
         "def solve(greed, sizes):"),
        ("Maximum Units On Truck",
         "Given a list of `[boxes, units_per_box]` pairs and an integer `capacity`, "
         "return the most units loadable taking at most `capacity` boxes.",
         lambda boxes, capacity: _max_units(boxes, capacity),
         lambda rng: ([[rng.randint(1, 5), rng.randint(1, 9)]
                       for _ in range(rng.randint(0, 5))], rng.randint(0, 12)),
         "def solve(boxes, capacity):"),
        ("Largest Sum After K Negations",
         "Given a list `nums` and an integer `k`, negate exactly `k` elements (the same "
         "element may be negated more than once) to maximise the sum, and return it.",
         lambda nums, k: _k_negate(nums, k),
         lambda rng: (ints(rng, lo=-9, hi=9, min_n=1), rng.randint(0, 5)),
         "def solve(nums, k):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _gas(rng):
    n = rng.randint(1, 6)
    gas = [rng.randint(0, 8) for _ in range(n)]
    cost = [rng.randint(0, 8) for _ in range(n)]
    return (gas, cost)


def _ivals(rng):
    out = []
    for _ in range(rng.randint(0, 5)):
        s = rng.randint(0, 10)
        out.append([s, s + rng.randint(0, 4)])
    return out


def _min_arrows(intervals):
    if not intervals:
        return 0
    arrows, end = 1, sorted(intervals, key=lambda x: x[1])[0][1]
    for s, e in sorted(intervals, key=lambda x: x[1])[1:]:
        if s > end:
            arrows += 1
            end = e
    return arrows


def _boats(people, limit):
    xs = sorted(people)
    i, j, boats = 0, len(xs) - 1, 0
    while i <= j:
        if xs[i] + xs[j] <= limit:
            i += 1
        j -= 1
        boats += 1
    return boats


def _cookies(greed, sizes):
    g, s = sorted(greed), sorted(sizes)
    i = j = count = 0
    while i < len(g) and j < len(s):
        if s[j] >= g[i]:
            count += 1
            i += 1
        j += 1
    return count


def _max_units(boxes, capacity):
    total = 0
    for count, units in sorted(boxes, key=lambda b: -b[1]):
        take = min(count, capacity)
        total += take * units
        capacity -= take
        if not capacity:
            break
    return total


def _k_negate(nums, k):
    xs = sorted(nums)
    i = 0
    while k and i < len(xs) and xs[i] < 0:
        xs[i] = -xs[i]
        i += 1
        k -= 1
    if k % 2:
        xs[xs.index(min(xs))] *= -1
    return sum(xs)


# --------------------------------------------------------------------------- #
@fam("selection", "medium", ["heap", "sorting"])
def f_selection():
    specs = [
        ("Kth Largest Value", "Given a list `nums` and a 1-based integer `k`, return "
         "the `k`-th largest value counting duplicates, or None if out of range.",
         lambda nums, k: sorted(nums, reverse=True)[k - 1] if 1 <= k <= len(nums) else None),
        ("K Largest Values", "Given a list `nums` and an integer `k`, return the `k` "
         "largest values sorted descending.",
         lambda nums, k: sorted(nums, reverse=True)[:k]),
        ("K Smallest Values", "Given a list `nums` and an integer `k`, return the `k` "
         "smallest values sorted ascending.", lambda nums, k: sorted(nums)[:k]),
        ("Last Stone Weight", "Repeatedly take the two largest values, remove both and "
         "push back their difference if non-zero. Return the final remaining value, or "
         "0 if none remain.", lambda nums, k: _stones(nums)),
        ("Kth Largest Distinct", "Given a list `nums` and a 1-based `k`, return the "
         "`k`-th largest distinct value, or None if there are fewer than `k`.",
         lambda nums, k: (sorted(set(nums), reverse=True)[k - 1]
                          if 1 <= k <= len(set(nums)) else None)),
        ("Median Of List", "Given a list `nums`, return its median, rounded to six "
         "decimals. Return None for an empty list.", lambda nums, k: _median(nums)),
        ("Minimum Cost To Connect Sticks", "Repeatedly combine the two smallest values "
         "at a cost equal to their sum. Return the total cost to combine all into one.",
         lambda nums, k: _connect(nums)),
        ("Sliding Window Maximum", "Given a list `nums` and a positive integer `k`, "
         "return the maximum of each contiguous window of length `k`.",
         lambda nums, k: [max(nums[i:i + k])
                          for i in range(len(nums) - k + 1)] if k <= len(nums) else []),
    ]
    for title, stmt, ref in specs:
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(1, 4)),
            signature="def solve(nums, k):",
            edges=[([], 1), ([5], 1), ([3, 1, 2], 2), ([4, 4, 4], 2)],
        )


def _stones(nums):
    xs = sorted(nums, key=abs)
    xs = sorted(abs(x) for x in nums)
    while len(xs) > 1:
        a, b = xs.pop(), xs.pop()
        if a != b:
            xs.append(a - b)
            xs.sort()
    return xs[0] if xs else 0


def _median(nums):
    if not nums:
        return None
    xs = sorted(nums)
    n = len(xs)
    return round(xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2, 6)


def _connect(nums):
    xs = sorted(nums)
    total = 0
    while len(xs) > 1:
        a, b = xs.pop(0), xs.pop(0)
        total += a + b
        xs.append(a + b)
        xs.sort()
    return total


# --------------------------------------------------------------------------- #
@fam("grid_dp", "medium", ["dynamic-programming", "matrix"])
def f_grid_dp():
    def unique_paths(rows, cols):
        dp = [[1] * cols for _ in range(rows)]
        for i in range(1, rows):
            for j in range(1, cols):
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
        return dp[rows - 1][cols - 1] if rows and cols else 0

    def paths_with_obstacles(grid):
        if not grid or not grid[0] or grid[0][0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        dp = [[0] * cols for _ in range(rows)]
        dp[0][0] = 1
        for i in range(rows):
            for j in range(cols):
                if grid[i][j]:
                    dp[i][j] = 0
                    continue
                if i:
                    dp[i][j] += dp[i - 1][j]
                if j:
                    dp[i][j] += dp[i][j - 1]
        return dp[rows - 1][cols - 1]

    def min_path_sum(grid):
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        dp = [[0] * cols for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                best = min([dp[i - 1][j] if i else float("inf"),
                            dp[i][j - 1] if j else float("inf")], default=0)
                dp[i][j] = grid[i][j] + (0 if best == float("inf") else best)
        return dp[rows - 1][cols - 1]

    def maximal_square(grid):
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        dp = [[0] * cols for _ in range(rows)]
        best = 0
        for i in range(rows):
            for j in range(cols):
                if grid[i][j]:
                    dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1]) \
                        if i and j else 1
                    best = max(best, dp[i][j])
        return best * best

    def count_islands(grid):
        if not grid or not grid[0]:
            return 0
        seen = set()
        rows, cols = len(grid), len(grid[0])
        count = 0
        for i in range(rows):
            for j in range(cols):
                if grid[i][j] and (i, j) not in seen:
                    count += 1
                    stack = [(i, j)]
                    seen.add((i, j))
                    while stack:
                        a, b = stack.pop()
                        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            na, nb = a + da, b + db
                            if (0 <= na < rows and 0 <= nb < cols
                                    and grid[na][nb] and (na, nb) not in seen):
                                seen.add((na, nb))
                                stack.append((na, nb))
        return count

    yield problem(
        title="Unique Paths In Grid",
        statement="Given positive integers `rows` and `cols`, return how many paths go "
                  "from the top-left to the bottom-right moving only right or down.",
        ref=unique_paths, inputs=lambda rng: (rng.randint(1, 7), rng.randint(1, 7)),
        signature="def solve(rows, cols):", edges=[(1, 1), (2, 2), (3, 4)])
    yield problem(
        title="Unique Paths With Obstacles",
        statement="Given a grid of 0s and 1s where 1 marks an obstacle, return how many "
                  "paths go from the top-left to the bottom-right moving only right or "
                  "down without entering an obstacle.",
        ref=paths_with_obstacles, inputs=lambda rng: (grid01(rng, p=0.25),),
        signature="def solve(grid):", edges=[([[0]],), ([[1]],), ([[0, 0], [0, 0]],)])
    yield problem(
        title="Minimum Path Sum",
        statement="Given a grid of non-negative integers, return the smallest sum along "
                  "a path from the top-left to the bottom-right moving only right or down.",
        ref=min_path_sum, inputs=lambda rng: (matrix(rng, lo=0, hi=9),),
        signature="def solve(grid):", edges=[([[5]],), ([[1, 2], [3, 4]],)])
    yield problem(
        title="Maximal Square Area",
        statement="Given a grid of 0s and 1s, return the area of the largest square "
                  "made entirely of 1s.",
        ref=maximal_square, inputs=lambda rng: (grid01(rng, p=0.6),),
        signature="def solve(grid):", edges=[([[0]],), ([[1]],), ([[1, 1], [1, 1]],)])
    yield problem(
        title="Count Islands",
        statement="Given a grid of 0s and 1s, return how many groups of 1s are "
                  "connected horizontally or vertically.",
        ref=count_islands, inputs=lambda rng: (grid01(rng, p=0.45),),
        signature="def solve(grid):", edges=[([[0]],), ([[1]],), ([[1, 0], [0, 1]],)])
    yield problem(
        title="Triangle Minimum Path",
        statement="Given a triangle as a list of rows where row `i` has `i + 1` values, "
                  "return the smallest top-to-bottom path sum, moving to an adjacent "
                  "index on each step.",
        ref=_triangle, inputs=lambda rng: (_tri(rng),), signature="def solve(triangle):",
        edges=[([[1]],), ([[1], [2, 3]],)])
    yield problem(
        title="Max Points Collected",
        statement="Given a grid of integers, return the largest sum along a path from "
                  "the top-left to the bottom-right moving only right or down.",
        ref=_max_path, inputs=lambda rng: (matrix(rng),), signature="def solve(grid):",
        edges=[([[5]],), ([[1, -2], [-3, 4]],)])
    yield problem(
        title="Count Paths With Exactly K Turns",
        statement="Given positive `rows` and `cols`, return how many right/down paths "
                  "from the top-left to the bottom-right change direction exactly "
                  "`k` times.",
        ref=_paths_k_turns,
        inputs=lambda rng: (rng.randint(1, 5), rng.randint(1, 5), rng.randint(0, 3)),
        signature="def solve(rows, cols, k):", edges=[(1, 1, 0), (2, 2, 1)])


def _tri(rng):
    n = rng.randint(1, 5)
    return [[rng.randint(-9, 9) for _ in range(i + 1)] for i in range(n)]


def _triangle(triangle):
    if not triangle:
        return 0
    dp = list(triangle[-1])
    for row in reversed(triangle[:-1]):
        dp = [row[i] + min(dp[i], dp[i + 1]) for i in range(len(row))]
    return dp[0]


def _max_path(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            best = max([dp[i - 1][j] if i else float("-inf"),
                        dp[i][j - 1] if j else float("-inf")])
            dp[i][j] = grid[i][j] + (0 if best == float("-inf") else best)
    return dp[rows - 1][cols - 1]


def _paths_k_turns(rows, cols, k):
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def go(i, j, direction, turns):
        if turns > k:
            return 0
        if i == rows - 1 and j == cols - 1:
            return 1 if turns == k else 0
        total = 0
        if i + 1 < rows:
            total += go(i + 1, j, 0, turns + (direction == 1))
        if j + 1 < cols:
            total += go(i, j + 1, 1, turns + (direction == 0))
        return total

    if rows == 1 and cols == 1:
        return 1 if k == 0 else 0
    out = 0
    if rows > 1:
        out += go(1, 0, 0, 0)
    if cols > 1:
        out += go(0, 1, 1, 0)
    return out


# --------------------------------------------------------------------------- #
@fam("string_parsing", "medium", ["string", "parsing"])
def f_string_parsing():
    specs = [
        ("Parse Integer With Sign", "Given a string `s`, skip leading spaces, read an "
         "optional sign then digits, and return the integer. Return 0 if no digits "
         "follow. Clamp to the range -2147483648..2147483647.",
         lambda s: _atoi(s), lambda rng: (word(rng, 0, 8, " -+12a"),)),
        ("Valid Number", "Given a string `s`, return True if it is a valid decimal "
         "number: optional sign, digits with at most one dot, and at least one digit.",
         lambda s: _valid_number(s), lambda rng: (word(rng, 0, 6, "12.-+e"),)),
        ("Split Balanced Strings", "Given a string `s` of 'L' and 'R' with equal "
         "counts, return how many balanced pieces it splits into when scanning left to "
         "right.", lambda s: _balanced_count(s),
         lambda rng: (_lr(rng),)),
        ("Licence Key Formatting", "Given a string `s` of alphanumerics and dashes and "
         "an integer `k`, remove the dashes, upper-case the rest, then group from the "
         "right into chunks of `k` joined by dashes. The first group may be shorter.",
         None, None),
        ("Count Valid Words", "Given a string `s`, return how many whitespace-separated "
         "tokens consist only of letters.",
         lambda s: sum(1 for w in s.split() if w.isalpha()),
         lambda rng: (word(rng, 0, 12, "ab1 c"),)),
        ("Most Common Word", "Given a string `s`, return the most frequent lower-cased "
         "alphabetic word, breaking ties alphabetically. Return an empty string if "
         "there are none.", lambda s: _most_common_word(s),
         lambda rng: (sentence(rng, 0, 7),)),
        ("Detect Capital Use", "Given a string `s`, return True if it is all upper "
         "case, all lower case, or only the first letter is upper case.",
         lambda s: s.isupper() or s.islower() or s.istitle() or s == "",
         lambda rng: (word(rng, 0, 6, "aAbB"),)),
        ("Reverse Vowels Order", "Given a string `s`, return the vowels it contains in "
         "reverse order, as a string.",
         lambda s: "".join(c for c in s if c.lower() in "aeiou")[::-1],
         lambda rng: (word(rng, 0, 10, "aeiobc"),)),
    ]
    for title, stmt, ref, inp in specs:
        if title == "Licence Key Formatting":
            ref = _licence
            inp = lambda rng: (word(rng, 0, 9, "ab-12"), rng.randint(1, 4))
            sig = "def solve(s, k):"
        else:
            sig = "def solve(s):"
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _atoi(s):
    i, n = 0, len(s)
    while i < n and s[i] == " ":
        i += 1
    sign = 1
    if i < n and s[i] in "+-":
        sign = -1 if s[i] == "-" else 1
        i += 1
    out = 0
    while i < n and s[i].isdigit():
        out = out * 10 + int(s[i])
        i += 1
    out *= sign
    return max(-2147483648, min(2147483647, out))


def _valid_number(s):
    t = s.strip()
    if t[:1] in "+-":
        t = t[1:]
    if t.count(".") > 1 or not t:
        return False
    return t.replace(".", "").isdigit()


def _lr(rng):
    n = rng.randint(0, 4)
    s = list("LR" * n)
    rng.shuffle(s)
    return "".join(s)


def _balanced_count(s):
    bal = count = 0
    for c in s:
        bal += 1 if c == "L" else -1
        if bal == 0:
            count += 1
    return count


def _licence(s, k):
    clean = s.replace("-", "").upper()
    if not clean:
        return ""
    head = len(clean) % k
    parts = ([clean[:head]] if head else []) + \
        [clean[i:i + k] for i in range(head, len(clean), k)]
    return "-".join(parts)


def _most_common_word(s):
    words = [w.lower() for w in s.split() if w.isalpha()]
    if not words:
        return ""
    return min(sorted(set(words)), key=lambda w: (-words.count(w), w))


# --------------------------------------------------------------------------- #
@fam("subsets", "medium", ["combinatorics", "backtracking"])
def f_subsets():
    specs = [
        ("Count Subsets With Even Sum", "Given a list `nums`, return how many of its "
         "subsets (by position, including the empty one) have an even sum.",
         lambda nums: sum(1 for m in range(1 << len(nums))
                          if sum(nums[i] for i in range(len(nums)) if m >> i & 1) % 2 == 0)),
        ("Largest Subset Sum Below K", "Given a list `nums` of non-negative values and "
         "an integer `k`, return the largest achievable subset sum that does not "
         "exceed `k`.", None),
        ("Count Distinct Subset Sums", "Given a list `nums`, return how many distinct "
         "sums its subsets can produce, including the empty subset.",
         lambda nums: len({sum(nums[i] for i in range(len(nums)) if m >> i & 1)
                           for m in range(1 << len(nums))})),
        ("Can Partition Into Equal Halves", "Given a list `nums`, return True if it "
         "splits into two groups with equal sums.",
         lambda nums: sum(nums) % 2 == 0 and any(
             sum(nums[i] for i in range(len(nums)) if m >> i & 1) == sum(nums) // 2
             for m in range(1 << len(nums)))),
        ("Minimum Subset Sum Difference", "Given a list `nums` of non-negative values, "
         "split it into two groups and return the smallest possible absolute difference "
         "of their sums.",
         lambda nums: min(abs(sum(nums) - 2 * sum(nums[i] for i in range(len(nums))
                                                  if m >> i & 1))
                          for m in range(1 << len(nums))) if nums else 0),
        ("Count Subsets Of Size K", "Given a list `nums` and an integer `k`, return how "
         "many subsets by position have exactly `k` elements.", None),
    ]
    for title, stmt, ref in specs:
        takes_k = "`k`" in stmt
        if title == "Largest Subset Sum Below K":
            ref = lambda nums, k: max(
                (s for s in {sum(nums[i] for i in range(len(nums)) if m >> i & 1)
                             for m in range(1 << len(nums))} if s <= k), default=0)
        if title == "Count Subsets Of Size K":
            ref = lambda nums, k: sum(1 for m in range(1 << len(nums))
                                      if bin(m).count("1") == k)
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (ints(rng, lo=0, hi=9, max_n=8), rng.randint(0, 20)))
                    if takes_k else (lambda rng: (ints(rng, lo=-5, hi=9, max_n=9),))),
            signature="def solve(nums, k):" if takes_k else "def solve(nums):",
        )


# --------------------------------------------------------------------------- #
@fam("misc_medium", "medium", ["array", "string"])
def f_misc_medium():
    specs = [
        ("Longest Common Subsequence Length", "Given strings `a` and `b`, return the "
         "length of their longest common subsequence.", _lcs,
         lambda rng: (word(rng, 0, 7, "abc"), word(rng, 0, 7, "abc")),
         "def solve(a, b):"),
        ("Edit Distance", "Given strings `a` and `b`, return the fewest single-character "
         "insertions, deletions or substitutions turning `a` into `b`.", _edit,
         lambda rng: (word(rng, 0, 6, "abc"), word(rng, 0, 6, "abc")),
         "def solve(a, b):"),
        ("Is Subsequence", "Given strings `a` and `b`, return True if `a` is a "
         "subsequence of `b`.", lambda a, b: _is_subseq(a, b),
         lambda rng: (word(rng, 0, 4, "abc"), word(rng, 0, 8, "abc")),
         "def solve(a, b):"),
        ("Number Of Distinct Substrings", "Given a string `s`, return how many distinct "
         "non-empty substrings it has.",
         lambda s: len({s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)}),
         lambda rng: (word(rng, 0, 8, "abc"),), "def solve(s):"),
        ("Rotate String Check", "Given strings `a` and `b`, return True if `b` is a "
         "rotation of `a`.",
         lambda a, b: len(a) == len(b) and b in (a + a),
         lambda rng: _rot_pair(rng), "def solve(a, b):"),
        ("Count Palindromic Substrings", "Given a string `s`, return how many of its "
         "contiguous non-empty substrings are palindromes, counting repeats separately.",
         lambda s: sum(1 for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                       if s[i:j] == s[i:j][::-1]),
         lambda rng: (word(rng, 0, 9, "aab"),), "def solve(s):"),
        ("Minimum Insertions For Palindrome", "Given a string `s`, return the fewest "
         "characters to insert anywhere to make it a palindrome.",
         lambda s: len(s) - _lcs(s, s[::-1]), lambda rng: (word(rng, 0, 8, "abc"),),
         "def solve(s):"),
        ("Longest Word In Dictionary Subsequence", "Given a string `s` and a list "
         "`words`, return the longest entry of `words` that is a subsequence of `s`, "
         "breaking ties alphabetically. Return an empty string if none is.",
         lambda s, words: _longest_sub(s, words),
         lambda rng: (word(rng, 0, 10, "abc"),
                      [word(rng, 1, 4, "abc") for _ in range(rng.randint(0, 4))]),
         "def solve(s, words):"),
        ("Group Shifted Strings Count", "Given a list `words` of lower-case strings, "
         "group those that are shifts of one another (each letter advanced by the same "
         "amount, wrapping from z to a) and return the number of groups.",
         lambda words: len({_shift_key(w) for w in words}),
         lambda rng: ([word(rng, 1, 4, "abcz") for _ in range(rng.randint(0, 6))],),
         "def solve(words):"),
        ("Valid Anagram Pairs", "Given a list `words`, return how many unordered pairs "
         "of distinct positions hold anagrams of each other.",
         lambda words: sum(1 for i in range(len(words))
                           for j in range(i + 1, len(words))
                           if sorted(words[i]) == sorted(words[j])),
         lambda rng: ([word(rng, 1, 3, "ab") for _ in range(rng.randint(0, 6))],),
         "def solve(words):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _lcs(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            dp[i][j] = dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] \
                else max(dp[i - 1][j], dp[i][j - 1])
    return dp[len(a)][len(b)]


def _edit(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        for j in range(len(b) + 1):
            if not i:
                dp[i][j] = j
            elif not j:
                dp[i][j] = i
            elif a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[len(a)][len(b)]


def _is_subseq(a, b):
    it = iter(b)
    return all(c in it for c in a)


def _rot_pair(rng):
    a = word(rng, 0, 6, "abc")
    if a and rng.random() < 0.5:
        k = rng.randrange(len(a))
        return (a, a[k:] + a[:k])
    return (a, word(rng, 0, 6, "abc"))


def _longest_sub(s, words):
    best = ""
    for w in sorted(words):
        if _is_subseq(w, s) and len(w) > len(best):
            best = w
    return best


def _shift_key(w):
    if not w:
        return ()
    d = ord(w[0]) - ord("a")
    return tuple((ord(c) - ord("a") - d) % 26 for c in w)
