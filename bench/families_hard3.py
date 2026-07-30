"""Hard tier, third batch: matrix manipulation, partition DP, counting."""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from .core import (fam, grid01, ints, matrix, pos_ints, problem, square, word)


@fam("matrix_hard", "hard", ["matrix"])
def f_matrix_hard():
    def rotate_k(grid, k):
        out = [row[:] for row in grid]
        for _ in range(k % 4):
            out = [list(r) for r in zip(*out[::-1])]
        return out

    def spiral_layers(grid):
        out, g = [], [row[:] for row in grid]
        while g:
            out.append(g.pop(0))
            g = [list(r) for r in zip(*g)][::-1] if g else []
        return out

    def diagonal_sort(grid):
        if not grid or not grid[0]:
            return grid
        rows, cols = len(grid), len(grid[0])
        diags = {}
        for i in range(rows):
            for j in range(cols):
                diags.setdefault(i - j, []).append(grid[i][j])
        for key in diags:
            diags[key].sort(reverse=True)
        out = [[0] * cols for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                out[i][j] = diags[i - j].pop()
        return out

    specs = [
        ("Rotate Matrix K Times", "Given an `n x n` matrix `grid` and an integer `k`, "
         "return it rotated 90 degrees clockwise `k` times.", rotate_k, True),
        ("Spiral Layers", "Given a matrix `grid` and an integer `k` that is ignored, "
         "return its elements grouped by the order a clockwise spiral peels them off, "
         "one list per peel.", lambda grid, k: spiral_layers(grid), True),
        ("Sort Matrix Diagonals", "Given a matrix `grid` and an integer `k` that is "
         "ignored, return it with each top-left to bottom-right diagonal sorted "
         "ascending.", lambda grid, k: diagonal_sort(grid), True),
        ("Count Submatrices Summing To K", "Given a matrix `grid` and an integer `k`, "
         "return how many non-empty rectangular submatrices sum to exactly `k`.",
         lambda grid, k: _count_submatrices(grid, k), True),
        ("Maximum Side Length With Sum Below K", "Given a matrix `grid` of non-negative "
         "values and an integer `k`, return the largest side length of a square "
         "submatrix whose sum is at most `k`.",
         lambda grid, k: _max_side(grid, k), True),
        ("Transpose And Reverse Rows", "Given a matrix `grid` and an integer `k` that "
         "is ignored, return its transpose with every row reversed.",
         lambda grid, k: [list(reversed(r)) for r in zip(*grid)] if grid else [], True),
        ("Count Distinct Rows", "Given a matrix `grid` and an integer `k` that is "
         "ignored, return how many distinct rows it has.",
         lambda grid, k: len({tuple(r) for r in grid}), True),
    ]
    for title, stmt, ref, _ in specs:
        square_only = "n x n" in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (square(rng), rng.randint(0, 5))) if square_only
                    else (lambda rng: (matrix(rng, lo=0, hi=5), rng.randint(0, 8)))),
            signature="def solve(grid, k):",
            edges=[([[1]], 1), ([[1, 2], [3, 4]], 2)])


def _count_submatrices(grid, k):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0
    for r1 in range(rows):
        for r2 in range(r1, rows):
            for c1 in range(cols):
                for c2 in range(c1, cols):
                    total = sum(grid[i][j] for i in range(r1, r2 + 1)
                                for j in range(c1, c2 + 1))
                    if total == k:
                        count += 1
    return count


def _max_side(grid, k):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    best = 0
    for size in range(1, min(rows, cols) + 1):
        for i in range(rows - size + 1):
            for j in range(cols - size + 1):
                total = sum(grid[a][b] for a in range(i, i + size)
                            for b in range(j, j + size))
                if total <= k:
                    best = max(best, size)
    return best


# --------------------------------------------------------------------------- #
@fam("partition_dp", "hard", ["dynamic-programming"])
def f_partition_dp():
    specs = [
        ("Split Into K Parts Minimum Largest", "Given a list `nums` of non-negative "
         "values and an integer `k` at least 1, split it into `k` contiguous parts and "
         "return the smallest possible largest part sum.", _min_largest),
        ("Split Into K Parts Maximum Smallest", "Given a list `nums` of non-negative "
         "values and an integer `k` at least 1, split it into `k` contiguous parts and "
         "return the largest possible smallest part sum.", _max_smallest),
        ("Minimum Cost To Cut Into K", "Given a list `nums` and an integer `k`, split "
         "it into `k` contiguous parts and return the smallest total of each part's "
         "range, that is its max minus its min.", _min_range_cost),
        ("Partition For Maximum Sum Of Maxima", "Given a list `nums` and an integer "
         "`k`, split it into contiguous groups of at most `k` elements, replace every "
         "element by its group's maximum, and return the largest possible total.",
         _max_after_partition),
        ("Count Ways To Split Into K Parts", "Given a list `nums` and an integer `k`, "
         "return how many ways it splits into `k` non-empty contiguous parts.",
         lambda nums, k: _nck2(len(nums) - 1, k - 1) if nums and k >= 1 else 0),
        ("Minimum Difference Of Two Parts", "Given a list `nums` and an integer `k` "
         "that is ignored, split it into two groups and return the smallest possible "
         "absolute difference of sums.",
         lambda nums, k: min((abs(sum(nums) - 2 * sum(nums[i] for i in range(len(nums))
                                                      if m >> i & 1))
                              for m in range(1 << len(nums))), default=0)),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (pos_ints(rng, lo=0, hi=9, max_n=8),
                                          rng.randint(1, 3)),
                      signature="def solve(nums, k):",
                      edges=[([], 1), ([5], 1), ([1, 2, 3], 2)])


def _parts(nums, k):
    """Every way to split nums into exactly k non-empty contiguous parts."""
    n = len(nums)
    if k < 1 or k > n:
        return []
    out = []
    for cuts in combinations(range(1, n), k - 1):
        bounds = (0,) + cuts + (n,)
        out.append([nums[bounds[i]:bounds[i + 1]] for i in range(k)])
    return out


def _min_largest(nums, k):
    options = _parts(nums, k)
    if not options:
        return sum(nums) if nums else 0
    return min(max(sum(p) for p in split) for split in options)


def _max_smallest(nums, k):
    options = _parts(nums, k)
    if not options:
        return sum(nums) if nums else 0
    return max(min(sum(p) for p in split) for split in options)


def _min_range_cost(nums, k):
    options = _parts(nums, k)
    if not options:
        return (max(nums) - min(nums)) if nums else 0
    return min(sum(max(p) - min(p) for p in split) for split in options)


def _max_after_partition(nums, k):
    n = len(nums)
    k = max(1, k)

    @lru_cache(maxsize=None)
    def go(i):
        if i == n:
            return 0
        best = 0
        top = 0
        for j in range(i, min(n, i + k)):
            top = max(top, nums[j])
            best = max(best, top * (j - i + 1) + go(j + 1))
        return best
    out = go(0)
    go.cache_clear()
    return out


def _nck2(n, k):
    if k < 0 or k > n:
        return 0
    out = 1
    for i in range(k):
        out = out * (n - i) // (i + 1)
    return out


# --------------------------------------------------------------------------- #
@fam("interval_hard", "hard", ["intervals"])
def f_interval_hard():
    specs = [
        ("Interval List Intersections", "Given two lists of disjoint sorted "
         "`[start, end]` intervals `a` and `b`, return their intersections sorted by "
         "start.", _intersections),
        ("Employee Free Time", "Given two lists of disjoint sorted `[start, end]` "
         "intervals `a` and `b`, return the gaps where neither is busy, between the "
         "earliest start and the latest end.", _free_time),
        ("Remove Covered Intervals", "Given lists `a` and `b`, combine them and return "
         "how many intervals remain after removing any interval fully covered by "
         "another.", _remove_covered),
        ("Union Length Of Two Sets", "Given lists `a` and `b` of `[start, end]` "
         "intervals, return the total length covered by their union.", _union_len),
        ("Intersection Total Length", "Given lists `a` and `b` of `[start, end]` "
         "intervals, return the total length covered by both.",
         lambda a, b: sum(e - s for s, e in _intersections(a, b))),
        ("Count Overlapping Pairs", "Given lists `a` and `b` of `[start, end]` "
         "intervals, return how many pairs with one from each overlap in more than a "
         "single point.",
         lambda a, b: sum(1 for s1, e1 in a for s2, e2 in b
                          if min(e1, e2) > max(s1, s2))),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (_disjoint(rng), _disjoint(rng)),
                      signature="def solve(a, b):",
                      edges=[([], []), ([[0, 2]], [[1, 3]]), ([[0, 1]], [[2, 3]])])


def _disjoint(rng):
    out, cur = [], rng.randint(0, 3)
    for _ in range(rng.randint(0, 4)):
        start = cur + rng.randint(0, 2)
        end = start + rng.randint(1, 3)
        out.append([start, end])
        cur = end
    return out


def _intersections(a, b):
    out = []
    for s1, e1 in a:
        for s2, e2 in b:
            lo, hi = max(s1, s2), min(e1, e2)
            if lo < hi:
                out.append([lo, hi])
    return sorted(out)


def _merge_all(iv):
    out = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def _free_time(a, b):
    merged = _merge_all(list(a) + list(b))
    return [[merged[i][1], merged[i + 1][0]] for i in range(len(merged) - 1)]


def _remove_covered(a, b):
    iv = list(a) + list(b)
    return sum(1 for i, (s1, e1) in enumerate(iv)
               if not any(j != i and s2 <= s1 and e1 <= e2 and (s2, e2) != (s1, e1)
                          for j, (s2, e2) in enumerate(iv)))


def _union_len(a, b):
    return sum(e - s for s, e in _merge_all(list(a) + list(b)))


# --------------------------------------------------------------------------- #
@fam("counting_hard", "hard", ["counting", "math"])
def f_counting_hard():
    specs = [
        ("Count Distinct Subsequences", "Given a string `s`, return how many distinct "
         "non-empty subsequences it has.", _distinct_subseq),
        ("Count Good Substrings", "Given a string `s`, return how many contiguous "
         "substrings of length three have three distinct characters.",
         lambda s: sum(1 for i in range(len(s) - 2) if len(set(s[i:i + 3])) == 3)),
        ("Count Homogenous Substrings", "Given a string `s`, return how many non-empty "
         "contiguous substrings consist of a single repeated character.",
         lambda s: sum(1 for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                       if len(set(s[i:j])) == 1)),
        ("Count Substrings With All Three", "Given a string `s` over the characters a, "
         "b and c, return how many contiguous substrings contain all three.",
         lambda s: sum(1 for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                       if set("abc") <= set(s[i:j]))),
        ("Count Unique Character Sum", "Given a string `s`, return the total over all "
         "substrings of how many characters appear exactly once in that substring.",
         lambda s: sum(sum(1 for c in set(s[i:j]) if s[i:j].count(c) == 1)
                       for i in range(len(s)) for j in range(i + 1, len(s) + 1))),
        ("Count Vowel Permutation Length", "Given a string `s`, return how many of its "
         "contiguous substrings begin and end with a vowel.",
         lambda s: sum(1 for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                       if s[i] in "aeiou" and s[j - 1] in "aeiou")),
        ("Count Binary Substrings", "Given a string `s` of '0' and '1', return how many "
         "substrings have equal numbers of consecutive 0s and 1s grouped together.",
         _count_binary_substrings),
    ]
    for title, stmt, ref in specs:
        binary = "'0' and '1'" in stmt
        abc = "characters a, " in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: ("".join(rng.choice("01")
                                          for _ in range(rng.randint(0, 11))),)) if binary
                    else (lambda rng: (word(rng, 0, 9, "abc"),)) if abc
                    else (lambda rng: (word(rng, 0, 9, "aabe"),))),
            signature="def solve(s):",
            edges=[("",), ("a",), ("aa",), ("abc",)])


def _distinct_subseq(s):
    seen = {""}
    for c in s:
        seen |= {t + c for t in seen}
    return len(seen) - 1


def _count_binary_substrings(s):
    groups = []
    for c in s:
        if groups and groups[-1][0] == c:
            groups[-1][1] += 1
        else:
            groups.append([c, 1])
    return sum(min(groups[i][1], groups[i + 1][1]) for i in range(len(groups) - 1))


# --------------------------------------------------------------------------- #
@fam("flow_matching", "hard", ["graph", "matching"])
def f_flow_matching():
    specs = [
        ("Maximum Bipartite Matching", "Given `n` left nodes and a list `edges` of "
         "`[left, right]` pairs, return the largest number of edges with no shared "
         "endpoint.", _max_matching),
        ("Minimum Vertex Cover Size", "Given `n` left nodes and `edges` of "
         "`[left, right]` pairs, return the size of a minimum vertex cover of the "
         "bipartite graph, which equals the maximum matching.", _max_matching),
        ("Count Perfect Matchings", "Given `n` left nodes and `edges` of "
         "`[left, right]` pairs, return how many matchings cover every left node "
         "exactly once using distinct right nodes.", _count_matchings),
        ("Maximum Independent Set Bipartite", "Given `n` left nodes and `edges`, return "
         "the size of the largest set of nodes with no edge between any two, counting "
         "both sides.", _max_independent),
        ("Has Perfect Matching", "Given `n` left nodes and `edges`, return True if "
         "every left node can be matched to a distinct right node.",
         lambda n, edges: _max_matching(n, edges) == n),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: _bipartite(rng),
                      signature="def solve(n, edges):",
                      edges=[(0, []), (1, []), (2, [[0, 0], [1, 0]])])


def _bipartite(rng):
    n = rng.randint(0, 4)
    m = rng.randint(0, 4)
    seen = set()
    for _ in range(rng.randint(0, 6)):
        if not n or not m:
            break
        seen.add((rng.randrange(n), rng.randrange(m)))
    return (n, [list(e) for e in sorted(seen)])


def _adj(n, edges):
    out = {i: [] for i in range(n)}
    for a, b in edges:
        if a in out:
            out[a].append(b)
    return out


def _max_matching(n, edges):
    adj = _adj(n, edges)
    match = {}

    def try_assign(u, seen):
        for v in adj[u]:
            if v in seen:
                continue
            seen.add(v)
            if v not in match or try_assign(match[v], seen):
                match[v] = u
                return True
        return False

    count = 0
    for u in range(n):
        if try_assign(u, set()):
            count += 1
    return count


def _count_matchings(n, edges):
    adj = _adj(n, edges)

    def go(u, used):
        if u == n:
            return 1
        return sum(go(u + 1, used | {v}) for v in adj[u] if v not in used)
    return go(0, frozenset())


def _max_independent(n, edges):
    rights = {b for _, b in edges}
    total = n + len(rights)
    return total - _max_matching(n, edges)


# --------------------------------------------------------------------------- #
@fam("state_dp", "hard", ["dynamic-programming"])
def f_state_dp():
    specs = [
        ("Max Profit With K Transactions", "Given a list `prices` and an integer `k`, "
         "return the largest profit from at most `k` non-overlapping buy-then-sell "
         "transactions.", _k_trades),
        ("House Robber Circular", "Given a list `prices` of non-negative values arranged "
         "in a circle and an integer `k` that is ignored, return the largest sum with no "
         "two chosen elements adjacent, treating first and last as adjacent.",
         lambda prices, k: _rob_circle(prices)),
        ("Delete And Earn", "Given a list `prices` and an integer `k` that is ignored, "
         "earning a value deletes every copy of it and every value one away. Return the "
         "largest total earnable.", lambda prices, k: _delete_earn(prices)),
        ("Minimum Swaps To Sort", "Given a list `prices` of distinct values and an "
         "integer `k` that is ignored, return the fewest swaps of any two positions "
         "needed to sort it ascending.", lambda prices, k: _min_swaps(prices)),
        ("Paint Fence Ways", "Given an integer `k` of colours and a list `prices` whose "
         "length is the number of posts, return how many ways the posts can be painted "
         "with no three adjacent sharing a colour.",
         lambda prices, k: _paint_fence(len(prices), k)),
        ("Longest Arithmetic Subsequence", "Given a list `prices` and an integer `k` "
         "that is ignored, return the length of its longest arithmetic subsequence.",
         lambda prices, k: _longest_arith(prices)),
        ("Max Alternating Subsequence Sum", "Given a list `prices` and an integer `k` "
         "that is ignored, return the largest alternating sum of a subsequence, adding "
         "the first, subtracting the second, and so on.",
         lambda prices, k: _alt_sum(prices)),
        ("Min Steps To Equal Elements", "Given a list `prices` and an integer `k` that "
         "is ignored, return the fewest unit increments or decrements to make every "
         "element equal.", lambda prices, k: _min_steps(prices)),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (ints(rng, lo=-9, hi=9, max_n=8),
                                          rng.randint(1, 4)),
                      signature="def solve(prices, k):",
                      edges=[([], 1), ([5], 1), ([1, 2, 3], 2), ([3, 1, 2], 1)])


def _k_trades(prices, k):
    if not prices or k <= 0:
        return 0
    n = len(prices)
    dp = [[0] * n for _ in range(k + 1)]
    for t in range(1, k + 1):
        best = -prices[0]
        for i in range(1, n):
            dp[t][i] = max(dp[t][i - 1], prices[i] + best)
            best = max(best, dp[t - 1][i] - prices[i])
    return dp[k][n - 1]


def _rob_line(xs):
    prev = cur = 0
    for x in xs:
        prev, cur = cur, max(cur, prev + max(x, 0))
    return cur


def _rob_circle(xs):
    if not xs:
        return 0
    if len(xs) == 1:
        return max(xs[0], 0)
    return max(_rob_line(xs[:-1]), _rob_line(xs[1:]))


def _delete_earn(xs):
    if not xs:
        return 0
    totals = {}
    for x in xs:
        totals[x] = totals.get(x, 0) + x
    keys = sorted(totals)
    prev_key = None
    skip = take = 0
    for key in keys:
        if prev_key is not None and key - prev_key == 1:
            skip, take = max(skip, take), skip + totals[key]
        else:
            skip, take = max(skip, take), max(skip, take) + totals[key]
        prev_key = key
    return max(skip, take)


def _min_swaps(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    seen = [False] * len(xs)
    swaps = 0
    for i in range(len(xs)):
        if seen[i] or order[i] == i:
            continue
        size, j = 0, i
        while not seen[j]:
            seen[j] = True
            j = order[j]
            size += 1
        swaps += size - 1
    return swaps


def _paint_fence(n, k):
    if n == 0:
        return 0
    if n == 1:
        return k
    same, diff = k, k * (k - 1)
    for _ in range(3, n + 1):
        same, diff = diff, (same + diff) * (k - 1)
    return same + diff


def _longest_arith(xs):
    n = len(xs)
    if n <= 2:
        return n
    best = 2
    dp = [{} for _ in range(n)]
    for i in range(n):
        for j in range(i):
            d = xs[i] - xs[j]
            dp[i][d] = dp[j].get(d, 1) + 1
            best = max(best, dp[i][d])
    return best


def _alt_sum(xs):
    even = odd = 0
    for x in xs:
        even, odd = max(even, odd + x), max(odd, even - x)
    return max(even, odd)


def _min_steps(xs):
    if not xs:
        return 0
    med = sorted(xs)[len(xs) // 2]
    return sum(abs(x - med) for x in xs)
