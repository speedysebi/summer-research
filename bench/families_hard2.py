"""Hard tier, second batch.

Reference solutions here are often deliberately brute force. Inputs are small, so an
exponential reference is fast enough, and a reference that is obviously correct is
worth far more than a clever one when it is the thing defining ground truth for 200
problems. The model still has to produce something that passes.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, permutations

from .core import (fam, grid01, ints, matrix, pos_ints, problem, sorted_ints,
                   square, word, distinct_ints)


# --------------------------------------------------------------------------- #
@fam("tree_array", "hard", ["tree", "recursion"])
def f_tree_array():
    """Binary trees given level-order with None for a missing child."""

    def children(tree, i):
        return 2 * i + 1, 2 * i + 2

    def exists(tree, i):
        return i < len(tree) and tree[i] is not None

    def depth(tree, i=0):
        if not exists(tree, i):
            return 0
        l, r = children(tree, i)
        return 1 + max(depth(tree, l), depth(tree, r))

    def count_nodes(tree):
        return sum(1 for x in tree if x is not None)

    def leaves(tree):
        out = 0
        for i, x in enumerate(tree):
            if x is None:
                continue
            l, r = children(tree, i)
            if not exists(tree, l) and not exists(tree, r):
                out += 1
        return out

    def diameter(tree):
        best = 0
        for i in range(len(tree)):
            if exists(tree, i):
                l, r = children(tree, i)
                best = max(best, depth(tree, l) + depth(tree, r))
        return best

    def balanced(tree, i=0):
        if not exists(tree, i):
            return True
        l, r = children(tree, i)
        return (abs(depth(tree, l) - depth(tree, r)) <= 1
                and balanced(tree, l) and balanced(tree, r))

    def path_sums(tree, i=0):
        if not exists(tree, i):
            return []
        l, r = children(tree, i)
        below = path_sums(tree, l) + path_sums(tree, r)
        return [tree[i] + s for s in below] if below else [tree[i]]

    def level_order(tree):
        out, level, idx = [], 0, 0
        while idx < len(tree):
            row = [tree[j] for j in range(idx, min(len(tree), idx + (1 << level)))
                   if tree[j] is not None]
            if row:
                out.append(row)
            idx += 1 << level
            level += 1
        return out

    specs = [
        ("Tree Maximum Depth", "Given a binary tree as a level-order list `tree` where "
         "None marks a missing node, return its depth.", lambda tree: depth(tree)),
        ("Tree Node Count", "Given a binary tree as a level-order list `tree`, return "
         "how many nodes it has.", count_nodes),
        ("Tree Leaf Count", "Given a binary tree as a level-order list `tree`, return "
         "how many leaves it has.", leaves),
        ("Tree Diameter", "Given a binary tree as a level-order list `tree`, return the "
         "number of edges on the longest path between any two nodes.", diameter),
        ("Tree Is Balanced", "Given a binary tree as a level-order list `tree`, return "
         "True if every node's subtree depths differ by at most one.", balanced),
        ("Tree Maximum Root To Leaf Sum", "Given a binary tree as a level-order list "
         "`tree`, return the largest sum along a root-to-leaf path, or 0 if empty.",
         lambda tree: max(path_sums(tree), default=0)),
        ("Tree Minimum Root To Leaf Sum", "Given a binary tree as a level-order list "
         "`tree`, return the smallest sum along a root-to-leaf path, or 0 if empty.",
         lambda tree: min(path_sums(tree), default=0)),
        ("Tree Level Order Values", "Given a binary tree as a level-order list `tree`, "
         "return its values grouped by depth, skipping missing nodes.", level_order),
        ("Tree Sum Of All Nodes", "Given a binary tree as a level-order list `tree`, "
         "return the sum of every node value.",
         lambda tree: sum(x for x in tree if x is not None)),
        ("Tree Right Side View", "Given a binary tree as a level-order list `tree`, "
         "return the last value at each depth, top to bottom.",
         lambda tree: [row[-1] for row in level_order(tree)]),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (_tree(rng),), signature="def solve(tree):",
                      edges=[([],), ([1],), ([1, 2, 3],), ([1, None, 2],),
                             ([1, 2, None, 3],)])


def _tree(rng):
    n = rng.randint(0, 9)
    out = []
    for i in range(n):
        parent_ok = i == 0 or out[(i - 1) // 2] is not None
        out.append(rng.randint(-9, 9) if parent_ok and rng.random() < 0.75 else None)
    while out and out[-1] is None:
        out.pop()
    return out


# --------------------------------------------------------------------------- #
@fam("union_find", "hard", ["union-find", "graph"])
def f_union_find():
    def comps(n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for a, b in edges:
            parent[find(a)] = find(b)
        return [find(i) for i in range(n)]

    def sizes(n, edges):
        roots = comps(n, edges)
        out = {}
        for r in roots:
            out[r] = out.get(r, 0) + 1
        return out

    specs = [
        ("Count Components By Union Find", "Given `n` nodes and undirected `edges`, "
         "return how many connected components exist.",
         lambda n, edges: len(set(comps(n, edges)))),
        ("Largest Component", "Given `n` nodes and undirected `edges`, return the size "
         "of the largest component, or 0 if `n` is 0.",
         lambda n, edges: max(sizes(n, edges).values(), default=0)),
        ("Component Sizes Sorted", "Given `n` nodes and undirected `edges`, return the "
         "component sizes sorted descending.",
         lambda n, edges: sorted(sizes(n, edges).values(), reverse=True)),
        ("Redundant Connection Index", "Given `n` nodes and undirected `edges`, return "
         "the 0-based index of the first edge that joins two already-connected nodes, "
         "or -1 if there is none.", lambda n, edges: _redundant(n, edges)),
        ("Edges To Connect All", "Given `n` nodes and undirected `edges`, return how "
         "many extra edges are needed to connect every node.",
         lambda n, edges: max(0, len(set(comps(n, edges))) - 1)),
        ("Is Single Component", "Given `n` nodes and undirected `edges`, return True if "
         "every node is in one component.",
         lambda n, edges: n == 0 or len(set(comps(n, edges))) == 1),
        ("Count Redundant Edges", "Given `n` nodes and undirected `edges`, return how "
         "many edges could be removed while keeping connectivity unchanged.",
         lambda n, edges: len(edges) - (n - len(set(comps(n, edges))))),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: _ugraph(rng), signature="def solve(n, edges):",
                      edges=[(0, []), (1, []), (3, [[0, 1]]),
                             (3, [[0, 1], [1, 2], [2, 0]])])


def _ugraph(rng):
    n = rng.randint(0, 6)
    edges = []
    for _ in range(rng.randint(0, 6)):
        if n < 2:
            break
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            edges.append([a, b])
    return (n, edges)


def _redundant(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, (a, b) in enumerate(edges):
        ra, rb = find(a), find(b)
        if ra == rb:
            return i
        parent[ra] = rb
    return -1


# --------------------------------------------------------------------------- #
@fam("sliding_window_hard", "hard", ["sliding-window"])
def f_sw_hard():
    specs = [
        ("Minimum Window Substring", "Given strings `s` and `t`, return the shortest "
         "substring of `s` containing every character of `t` with multiplicity. Prefer "
         "the earliest start on a tie. Return an empty string if none exists.",
         lambda s, t: _min_window(s, t),
         lambda rng: (word(rng, 0, 12, "abc"), word(rng, 0, 3, "abc"))),
        ("Subarrays With Exactly K Distinct", "Given a list `nums` and an integer `k`, "
         "return how many contiguous subarrays hold exactly `k` distinct values.",
         lambda nums, k: sum(1 for i in range(len(nums))
                             for j in range(i + 1, len(nums) + 1)
                             if len(set(nums[i:j])) == k),
         lambda rng: (ints(rng, lo=0, hi=4, max_n=9), rng.randint(0, 4))),
        ("Count Nice Subarrays", "Given a list `nums` and an integer `k`, return how "
         "many contiguous subarrays hold exactly `k` odd numbers.",
         lambda nums, k: sum(1 for i in range(len(nums))
                             for j in range(i + 1, len(nums) + 1)
                             if sum(1 for x in nums[i:j] if x % 2) == k),
         lambda rng: (ints(rng, lo=0, hi=9, max_n=9), rng.randint(0, 3))),
        ("Longest Substring With K Repeats", "Given a string `s` and an integer `k`, "
         "return the length of the longest substring in which every character present "
         "occurs at least `k` times.",
         lambda s, k: max((j - i for i in range(len(s))
                           for j in range(i + 1, len(s) + 1)
                           if all(s[i:j].count(c) >= k for c in set(s[i:j]))), default=0),
         lambda rng: (word(rng, 0, 10, "abc"), rng.randint(1, 3))),
        ("Max Sum Of Two Non-Overlapping", "Given a list `nums` and an integer `k`, "
         "return the largest total of two non-overlapping contiguous subarrays each of "
         "length `k`, or 0 if impossible.",
         lambda nums, k: _two_windows(nums, k),
         lambda rng: (ints(rng, lo=-5, hi=9, max_n=9), rng.randint(1, 3))),
        ("Longest Balanced Binary Substring", "Given a string `s` of '0' and '1' and an "
         "integer `k` that is ignored, return the length of the longest substring with "
         "equally many zeros and ones.",
         lambda s, k: max((j - i for i in range(len(s))
                           for j in range(i + 1, len(s) + 1)
                           if s[i:j].count("0") == s[i:j].count("1")), default=0),
         lambda rng: ("".join(rng.choice("01") for _ in range(rng.randint(0, 11))),
                      rng.randint(0, 2))),
        ("Fruit Into Baskets", "Given a list `nums` and an integer `k` that is ignored, "
         "return the length of the longest contiguous stretch holding at most two "
         "distinct values.",
         lambda nums, k: max((j - i for i in range(len(nums))
                              for j in range(i + 1, len(nums) + 1)
                              if len(set(nums[i:j])) <= 2), default=0),
         lambda rng: (ints(rng, lo=0, hi=4, max_n=10), 0)),
        ("Max Consecutive Ones After K Flips", "Given a list `nums` of 0s and 1s and an "
         "integer `k`, return the longest run of 1s obtainable by flipping at most `k` "
         "zeros.",
         lambda nums, k: max((j - i for i in range(len(nums))
                              for j in range(i + 1, len(nums) + 1)
                              if nums[i:j].count(0) <= k), default=0),
         lambda rng: ([rng.randint(0, 1) for _ in range(rng.randint(0, 11))],
                      rng.randint(0, 3))),
    ]
    for title, stmt, ref, inp in specs:
        sig = "def solve(s, t):" if "strings `s` and `t`" in stmt else (
            "def solve(s, k):" if "a string `s`" in stmt else "def solve(nums, k):")
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _min_window(s, t):
    if not t:
        return ""
    best = ""
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            sub = s[i:j]
            if all(sub.count(c) >= t.count(c) for c in set(t)):
                if not best or len(sub) < len(best):
                    best = sub
                break
    return best


def _two_windows(nums, k):
    n = len(nums)
    best = 0
    found = False
    for i in range(n - k + 1):
        for j in range(i + k, n - k + 1):
            total = sum(nums[i:i + k]) + sum(nums[j:j + k])
            best = total if not found else max(best, total)
            found = True
    return best if found else 0


# --------------------------------------------------------------------------- #
@fam("game_dp", "hard", ["dynamic-programming", "game-theory"])
def f_game_dp():
    specs = [
        ("Stone Game First Player Wins", "Two players alternately take a pile from "
         "either end of `nums`, both playing optimally to maximise their own total. "
         "Return True if the first player ends with more.",
         lambda nums: _stone_diff(tuple(nums)) > 0),
        ("Stone Game Score Difference", "Two players alternately take from either end "
         "of `nums`, both maximising their own total. Return the first player's total "
         "minus the second's.", lambda nums: _stone_diff(tuple(nums))),
        ("Divisor Game", "Starting from `n = len(nums)`, players alternately subtract a "
         "proper divisor of the current number. A player unable to move loses. Return "
         "True if the first player wins.", lambda nums: len(nums) % 2 == 0),
        ("Nim Game", "Given piles `nums`, return True if the first player wins standard "
         "Nim with optimal play.", lambda nums: _nim(nums)),
        ("Can First Player Force Win", "Players alternately remove one or two items "
         "from a single pile of `len(nums)` items. The player taking the last item "
         "wins. Return True if the first player wins.",
         lambda nums: len(nums) % 3 != 0),
        ("Predict The Winner", "Two players alternately take from either end of `nums`. "
         "Return True if the first player can end with at least as much as the second.",
         lambda nums: _stone_diff(tuple(nums)) >= 0),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (pos_ints(rng, lo=0, hi=9, max_n=9),),
                      signature="def solve(nums):",
                      edges=[([],), ([1],), ([1, 2],), ([1, 5, 2],)])


@lru_cache(maxsize=None)
def _stone_diff(nums):
    if not nums:
        return 0
    return max(nums[0] - _stone_diff(nums[1:]), nums[-1] - _stone_diff(nums[:-1]))


def _nim(piles):
    x = 0
    for p in piles:
        x ^= p
    return x != 0


# --------------------------------------------------------------------------- #
@fam("bitmask_dp", "hard", ["bitmask", "dynamic-programming"])
def f_bitmask():
    def tsp(grid):
        n = len(grid)
        if n <= 1:
            return 0
        INF = float("inf")

        @lru_cache(maxsize=None)
        def go(mask, at):
            if mask == (1 << n) - 1:
                return 0
            best = INF
            for nxt in range(n):
                if not mask >> nxt & 1:
                    best = min(best, grid[at][nxt] + go(mask | 1 << nxt, nxt))
            return best
        out = go(1, 0)
        return -1 if out == INF else out

    def min_assignment(grid):
        n = len(grid)
        if not n:
            return 0
        best = None
        for perm in permutations(range(n)):
            total = sum(grid[i][perm[i]] for i in range(n))
            best = total if best is None else min(best, total)
        return best

    specs = [
        ("Travelling Salesman Path Cost", "Given an `n x n` cost matrix `grid`, start "
         "at node 0 and visit every node exactly once. Return the least total cost, or "
         "0 if `n` is at most 1.", tsp),
        ("Minimum Assignment Cost", "Given an `n x n` cost matrix `grid` where "
         "`grid[i][j]` is the cost of giving job `j` to worker `i`, assign each worker "
         "exactly one distinct job and return the least total cost.", min_assignment),
        ("Maximum Assignment Value", "Given an `n x n` value matrix `grid`, assign each "
         "worker one distinct job to maximise the total, and return it.",
         lambda grid: max((sum(grid[i][p[i]] for i in range(len(grid)))
                           for p in permutations(range(len(grid)))), default=0)),
        ("Count Perfect Matchings Below Cost", "Given an `n x n` cost matrix `grid`, "
         "return how many complete assignments have total cost at most 10.",
         lambda grid: sum(1 for p in permutations(range(len(grid)))
                          if sum(grid[i][p[i]] for i in range(len(grid))) <= 10)),
        ("Shortest Path Visiting All Nodes", "Given an `n x n` cost matrix `grid`, "
         "return the least cost of a walk starting anywhere that visits every node "
         "exactly once.",
         lambda grid: min((sum(grid[p[i]][p[i + 1]] for i in range(len(p) - 1))
                           for p in permutations(range(len(grid)))), default=0)),
    ]
    for title, stmt, ref in specs:
        # TSP needs a zero diagonal; assignment must NOT have one, or the identity
        # permutation is always free and every answer is 0.
        tsp_like = "salesman" in stmt or "visiting every" in stmt or "walk starting" in stmt
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=((lambda rng: (_cost_matrix(rng),)) if tsp_like
                              else (lambda rng: (_dense_matrix(rng),))),
                      signature="def solve(grid):",
                      edges=[([[0]],), ([[0, 1], [1, 0]],)])


def _cost_matrix(rng):
    n = rng.randint(1, 4)
    return [[0 if i == j else rng.randint(1, 9) for j in range(n)] for i in range(n)]


# --------------------------------------------------------------------------- #
@fam("lis_family", "hard", ["dynamic-programming"])
def f_lis_family():
    def lis_len(nums):
        best = 0
        dp = [1] * len(nums)
        for i in range(len(nums)):
            for j in range(i):
                if nums[j] < nums[i]:
                    dp[i] = max(dp[i], dp[j] + 1)
            best = max(best, dp[i])
        return best

    def lis_count(nums):
        n = len(nums)
        length = [1] * n
        count = [1] * n
        for i in range(n):
            for j in range(i):
                if nums[j] < nums[i]:
                    if length[j] + 1 > length[i]:
                        length[i] = length[j] + 1
                        count[i] = count[j]
                    elif length[j] + 1 == length[i]:
                        count[i] += count[j]
        best = max(length, default=0)
        return sum(c for l, c in zip(length, count) if l == best)

    specs = [
        ("Longest Increasing Subsequence Count", "Given a list `nums`, return how many "
         "strictly increasing subsequences have the maximum possible length. Return 0 "
         "for an empty list.", lambda nums: lis_count(nums) if nums else 0),
        ("Longest Bitonic Subsequence", "Given a list `nums`, return the length of the "
         "longest subsequence that strictly increases then strictly decreases. Either "
         "side may be empty.", lambda nums: _bitonic(nums)),
        ("Maximum Sum Increasing Subsequence", "Given a list `nums`, return the largest "
         "sum of a strictly increasing subsequence, or 0 if empty.",
         lambda nums: _max_sum_inc(nums)),
        ("Minimum Deletions To Sort", "Given a list `nums`, return the fewest deletions "
         "leaving a non-decreasing list.", lambda nums: len(nums) - _lnds(nums)),
        ("Longest Non-Decreasing Subsequence", "Given a list `nums`, return the length "
         "of its longest non-decreasing subsequence.", lambda nums: _lnds(nums)),
        ("Russian Doll Pairs", "Given a list `nums`, treat consecutive values as a "
         "chain and return the length of the longest strictly increasing subsequence.",
         lis_len),
        ("Longest Divisible Subset Size", "Given a list `nums` of positive integers, "
         "return the size of the largest subset where every pair divides one another.",
         lambda nums: _div_subset(nums)),
    ]
    for title, stmt, ref in specs:
        positive = "positive integers" in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (pos_ints(rng, lo=1, hi=20, max_n=8),)) if positive
                    else (lambda rng: (ints(rng, lo=-9, hi=9, max_n=9),))),
            signature="def solve(nums):",
            edges=[([],), ([1],), ([1, 2, 3],), ([3, 2, 1],), ([2, 2, 2],)])


def _bitonic(nums):
    n = len(nums)
    if not n:
        return 0
    inc = [1] * n
    dec = [1] * n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                inc[i] = max(inc[i], inc[j] + 1)
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n):
            if nums[j] < nums[i]:
                dec[i] = max(dec[i], dec[j] + 1)
    return max(inc[i] + dec[i] - 1 for i in range(n))


def _max_sum_inc(nums):
    if not nums:
        return 0
    dp = list(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + nums[i])
    return max(dp)


def _lnds(nums):
    best = 0
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] <= nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
        best = max(best, dp[i])
    return best


def _div_subset(nums):
    xs = sorted(set(nums))
    best = 0
    dp = [1] * len(xs)
    for i in range(len(xs)):
        for j in range(i):
            if xs[i] % xs[j] == 0:
                dp[i] = max(dp[i], dp[j] + 1)
        best = max(best, dp[i])
    return best


# --------------------------------------------------------------------------- #
@fam("scheduling", "hard", ["greedy", "sorting", "intervals"])
def f_scheduling():
    specs = [
        ("Meeting Rooms Required", "Given a list of `[start, end]` meetings, return the "
         "fewest rooms needed so no two overlapping meetings share a room.",
         lambda jobs: _rooms(jobs)),
        ("Weighted Interval Scheduling", "Given a list of `[start, end, value]` jobs, "
         "choose non-overlapping jobs to maximise total value and return it. Touching "
         "endpoints do not overlap.", lambda jobs: _weighted(jobs)),
        ("Maximum Jobs Without Overlap", "Given a list of `[start, end]` jobs, return "
         "the most jobs schedulable without overlap. Touching is allowed.",
         lambda jobs: _max_jobs(jobs)),
        ("Minimum Platforms", "Given a list of `[arrive, depart]` trains, return the "
         "most trains present at once.", lambda jobs: _rooms(jobs)),
        ("Job Sequencing Max Profit", "Given a list of `[deadline, profit]` jobs each "
         "taking one time unit starting at time 1, return the largest total profit "
         "schedulable.", lambda jobs: _job_seq(jobs)),
        ("Total Busy Time", "Given a list of `[start, end]` jobs, return the total time "
         "during which at least one job runs.", lambda jobs: _busy(jobs)),
    ]
    for title, stmt, ref in specs:
        weighted = "value]" in stmt
        deadline = "deadline" in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (_wjobs(rng),)) if weighted
                    else (lambda rng: (_djobs(rng),)) if deadline
                    else (lambda rng: (_jobs(rng),))),
            signature="def solve(jobs):",
            edges=[([],)] + ([([[1, 5]],), ([[0, 2], [1, 3]],)] if not (weighted or deadline)
                             else []))


def _jobs(rng):
    out = []
    for _ in range(rng.randint(0, 5)):
        s = rng.randint(0, 9)
        out.append([s, s + rng.randint(1, 4)])
    return out


def _wjobs(rng):
    out = []
    for _ in range(rng.randint(0, 5)):
        s = rng.randint(0, 9)
        out.append([s, s + rng.randint(1, 4), rng.randint(1, 9)])
    return out


def _djobs(rng):
    return [[rng.randint(1, 4), rng.randint(1, 9)] for _ in range(rng.randint(0, 5))]


def _rooms(jobs):
    pts = []
    for s, e in jobs:
        pts.append((s, 1))
        pts.append((e, -1))
    pts.sort(key=lambda p: (p[0], p[1]))
    cur = best = 0
    for _, d in pts:
        cur += d
        best = max(best, cur)
    return best


def _weighted(jobs):
    xs = sorted(jobs, key=lambda j: j[1])
    n = len(xs)
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        s, e, v = xs[i - 1]
        prev = 0
        for j in range(i - 1, 0, -1):
            if xs[j - 1][1] <= s:
                prev = dp[j]
                break
        dp[i] = max(dp[i - 1], prev + v)
    return dp[n]


def _max_jobs(jobs):
    xs = sorted(jobs, key=lambda j: j[1])
    end, count = None, 0
    for s, e in xs:
        if end is None or s >= end:
            count += 1
            end = e
    return count


def _job_seq(jobs):
    xs = sorted(jobs, key=lambda j: -j[1])
    slots = {}
    for deadline, profit in xs:
        t = deadline
        while t > 0 and t in slots:
            t -= 1
        if t > 0:
            slots[t] = profit
    return sum(slots.values())


def _busy(jobs):
    merged = []
    for s, e in sorted(jobs):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return sum(e - s for s, e in merged)


# --------------------------------------------------------------------------- #
@fam("string_hard", "hard", ["string"])
def f_string_hard():
    specs = [
        ("Text Justification Line Count", "Given a list `words` and an integer `width`, "
         "greedily pack words into lines so each line's words plus single spaces fit "
         "within `width`. Return how many lines result.",
         lambda words, width: _justify_lines(words, width)),
        ("Word Break Count", "Given a string `s` and a list `words`, return how many "
         "ways `s` splits into a sequence of entries from `words`.", None),
        ("Concatenated Word Count", "Given a list `words`, return how many entries can "
         "be formed by concatenating two or more other entries.", None),
        ("Longest String Chain", "Given a list `words`, return the length of the "
         "longest chain where each word is the previous one with exactly one character "
         "inserted.", None),
        ("Shortest Palindrome By Prefix", "Given a string `s`, return the shortest "
         "palindrome formed by adding characters only at the front.", None),
        ("Repeated DNA Sequences Count", "Given a string `s`, return how many distinct "
         "length-10 substrings occur more than once.", None),
        ("Longest Duplicate Substring", "Given a string `s`, return the longest "
         "substring occurring at least twice, preferring the earliest. Return an empty "
         "string if none.", None),
        ("Minimum Window Subsequence Length", "Given strings `s` and `t`, return the "
         "length of the shortest substring of `s` having `t` as a subsequence, or 0 if "
         "none exists.", None),
    ]
    yield problem(
        title=specs[0][0], statement=specs[0][1], ref=_justify_lines,
        inputs=lambda rng: ([word(rng, 1, 5, "ab") for _ in range(rng.randint(0, 6))],
                            rng.randint(3, 10)),
        signature="def solve(words, width):", edges=[([], 5), (["a"], 5)])
    yield problem(
        title=specs[1][0], statement=specs[1][1], ref=_word_break_count,
        inputs=lambda rng: (word(rng, 0, 8, "ab"),
                            [word(rng, 1, 3, "ab") for _ in range(rng.randint(1, 4))]),
        signature="def solve(s, words):", edges=[("", ["a"]), ("aa", ["a"])])
    yield problem(
        title=specs[2][0], statement=specs[2][1], ref=_concat_words,
        inputs=lambda rng: ([word(rng, 1, 4, "ab") for _ in range(rng.randint(0, 6))],),
        signature="def solve(words):", edges=[([],), (["a", "aa"],)])
    yield problem(
        title=specs[3][0], statement=specs[3][1], ref=_string_chain,
        inputs=lambda rng: ([word(rng, 1, 4, "ab") for _ in range(rng.randint(0, 7))],),
        signature="def solve(words):", edges=[([],), (["a"],), (["a", "ab", "abc"],)])
    yield problem(
        title=specs[4][0], statement=specs[4][1], ref=_shortest_pal,
        inputs=lambda rng: (word(rng, 0, 9, "abc"),), signature="def solve(s):",
        edges=[("",), ("a",), ("aacecaaa",)])
    yield problem(
        title=specs[5][0], statement=specs[5][1],
        ref=lambda s: len({s[i:i + 10] for i in range(len(s) - 9)
                           if s.count(s[i:i + 10]) > 1}),
        inputs=lambda rng: (_dna(rng),),
        signature="def solve(s):", edges=[("",), ("AAAAAAAAAAA",)])
    yield problem(
        title=specs[6][0], statement=specs[6][1], ref=_longest_dup,
        inputs=lambda rng: (word(rng, 0, 11, "abc"),), signature="def solve(s):",
        edges=[("",), ("a",), ("banana",)])
    yield problem(
        title=specs[7][0], statement=specs[7][1], ref=_min_window_subseq,
        inputs=lambda rng: (word(rng, 0, 11, "abc"), word(rng, 0, 3, "abc")),
        signature="def solve(s, t):", edges=[("", ""), ("abc", "ac")])


def _justify_lines(words, width):
    lines, cur = 0, -1
    for w in words:
        add = len(w) if cur < 0 else cur + 1 + len(w)
        if cur >= 0 and add <= width:
            cur = add
        else:
            lines += 1
            cur = len(w)
    return lines


def _word_break_count(s, words):
    pool = set(words)

    @lru_cache(maxsize=None)
    def go(i):
        if i == len(s):
            return 1
        return sum(go(j) for j in range(i + 1, len(s) + 1) if s[i:j] in pool)
    return go(0)


def _concat_words(words):
    pool = set(words)

    def formable(w, top):
        if not w:
            return not top
        return any(w[:k] in pool and formable(w[k:], False)
                   for k in range(1, len(w) + 1)
                   if not (top and k == len(w)))
    return sum(1 for w in words if w and formable(w, True))


def _string_chain(words):
    xs = sorted(set(words), key=len)
    best = 0
    dp = {}
    for w in xs:
        dp[w] = 1
        for i in range(len(w)):
            prev = w[:i] + w[i + 1:]
            if prev in dp:
                dp[w] = max(dp[w], dp[prev] + 1)
        best = max(best, dp[w])
    return best


def _shortest_pal(s):
    for i in range(len(s), -1, -1):
        if s[:i] == s[:i][::-1]:
            return s[i:][::-1] + s
    return s


def _longest_dup(s):
    best = ""
    for i in range(len(s)):
        for j in range(i + len(best) + 1, len(s) + 1):
            sub = s[i:j]
            if s.find(sub, i + 1) != -1:
                best = sub
    return best


def _min_window_subseq(s, t):
    if not t:
        return 0
    best = 0
    for i in range(len(s)):
        it = iter(s[i:])
        consumed = 0
        pos = i
        ok = True
        for c in t:
            found = False
            while pos < len(s):
                if s[pos] == c:
                    found = True
                    pos += 1
                    break
                pos += 1
            if not found:
                ok = False
                break
        if ok:
            length = pos - i
            if not best or length < best:
                best = length
    return best


# --------------------------------------------------------------------------- #
@fam("math_hard", "hard", ["math"])
def f_math_hard():
    specs = [
        ("Nth Digit Of Sequence", "Concatenate the positive integers as "
         "\"123456789101112...\". Given a positive integer `n`, return the `n`-th digit.",
         lambda n: _nth_digit(n), lambda rng: (rng.randint(1, 3000),)),
        ("Perfect Squares Count", "Given a non-negative integer `n`, return the fewest "
         "perfect squares summing to `n`.", lambda n: _perfect_squares(n),
         lambda rng: (rng.randint(0, 120),)),
        ("Super Power Modulo", "Given a non-negative integer `n`, return "
         "`2 ** n % 1337`.", lambda n: pow(2, n, 1337), lambda rng: (rng.randint(0, 5000),)),
        ("Fraction To Decimal Repeating", "Given a positive integer `n`, return the "
         "length of the repeating cycle in the decimal expansion of `1 / n`, or 0 if it "
         "terminates.", lambda n: _cycle_len(n), lambda rng: (rng.randint(1, 60),)),
        ("Count Numbers With Unique Digits", "Given a non-negative integer `n`, return "
         "how many integers from 0 to `10 ** n - 1` have all distinct digits.",
         lambda n: _unique_digits(n), lambda rng: (rng.randint(0, 8),)),
        ("Integer Partitions Count", "Given a non-negative integer `n`, return how many "
         "ways it can be written as a sum of positive integers, ignoring order.",
         lambda n: _partitions(n), lambda rng: (rng.randint(0, 30),)),
        ("Euler Totient", "Given a positive integer `n`, return how many integers from "
         "1 to `n` are coprime with `n`.",
         lambda n: sum(1 for i in range(1, n + 1) if _gcd_h(i, n) == 1),
         lambda rng: (rng.randint(1, 200),)),
        ("Sum Of Divisors", "Given a positive integer `n`, return the sum of all its "
         "positive divisors.",
         lambda n: sum(d for d in range(1, n + 1) if n % d == 0),
         lambda rng: (rng.randint(1, 300),)),
        ("Count Trailing Zeros In Base B", "Given a positive integer `n` and a base `b` "
         "from 2 to 10, return how many trailing zeros `n!` has in base `b`.",
         lambda n, b: _trailing_base(n, b),
         lambda rng: (rng.randint(1, 60), rng.randint(2, 10))),
    ]
    for title, stmt, ref, inp in specs:
        sig = "def solve(n, b):" if "base `b`" in stmt else "def solve(n):"
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _nth_digit(n):
    length, count, start = 1, 9, 1
    while n > length * count:
        n -= length * count
        length += 1
        count *= 10
        start *= 10
    num = start + (n - 1) // length
    return int(str(num)[(n - 1) % length])


def _perfect_squares(n):
    dp = [0] + [float("inf")] * n
    for i in range(1, n + 1):
        j = 1
        while j * j <= i:
            dp[i] = min(dp[i], dp[i - j * j] + 1)
            j += 1
    return dp[n]


def _cycle_len(n):
    while n % 2 == 0:
        n //= 2
    while n % 5 == 0:
        n //= 5
    if n == 1:
        return 0
    k, r = 1, 10 % n
    while r != 1:
        r = r * 10 % n
        k += 1
    return k


def _unique_digits(n):
    if n == 0:
        return 1
    total, unique = 10, 9
    for i in range(2, n + 1):
        unique *= (11 - i)
        total += unique
    return total


def _partitions(n):
    dp = [1] + [0] * n
    for k in range(1, n + 1):
        for i in range(k, n + 1):
            dp[i] += dp[i - k]
    return dp[n]


def _gcd_h(a, b):
    while b:
        a, b = b, a % b
    return a


def _trailing_base(n, b):
    from math import factorial
    f = factorial(n)
    count = 0
    while f % b == 0:
        f //= b
        count += 1
    return count


# --------------------------------------------------------------------------- #
@fam("geometry", "hard", ["geometry", "math"])
def f_geometry():
    specs = [
        ("Max Points On A Line", "Given a list of `[x, y]` points, return the most that "
         "lie on a single straight line.", _max_collinear),
        ("Count Collinear Triples", "Given a list of `[x, y]` points, return how many "
         "unordered triples are collinear.",
         lambda points: sum(1 for a, b, c in combinations(points, 3)
                            if (b[0] - a[0]) * (c[1] - a[1])
                            == (b[1] - a[1]) * (c[0] - a[0]))),
        ("Minimum Area Rectangle", "Given a list of distinct `[x, y]` points, return "
         "the smallest area of an axis-aligned rectangle with all four corners among "
         "them, or 0 if none exists.", _min_rect),
        ("Closest Pair Distance Squared", "Given a list of `[x, y]` points, return the "
         "smallest squared distance between two distinct points, or -1 if fewer than "
         "two.",
         lambda points: min(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                             for a, b in combinations(points, 2)), default=-1)),
        ("Count Points Inside Circle", "Given a list of `[x, y]` points, return how "
         "many lie within squared distance 25 of the origin.",
         lambda points: sum(1 for x, y in points if x * x + y * y <= 25)),
        ("Convex Hull Size", "Given a list of `[x, y]` points, return how many of them "
         "are vertices of their convex hull.", _hull_size),
    ]
    for title, stmt, ref in specs:
        rect = "rectangle" in stmt
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=((lambda rng: (_rect_points(rng),)) if rect
                              else (lambda rng: (_points(rng),))),
                      signature="def solve(points):",
                      edges=[([],), ([[0, 0]],), ([[0, 0], [1, 1]],),
                             ([[0, 0], [1, 1], [2, 2]],)])


def _points(rng):
    seen = set()
    for _ in range(rng.randint(0, 7)):
        seen.add((rng.randint(-4, 4), rng.randint(-4, 4)))
    return [list(p) for p in sorted(seen)]


def _max_collinear(points):
    n = len(points)
    if n <= 2:
        return n
    best = 2
    for i in range(n):
        for j in range(i + 1, n):
            count = 2
            for k in range(n):
                if k in (i, j):
                    continue
                a, b, c = points[i], points[j], points[k]
                if ((b[0] - a[0]) * (c[1] - a[1])
                        == (b[1] - a[1]) * (c[0] - a[0])):
                    count += 1
            best = max(best, count)
    return best


def _min_rect(points):
    pts = {tuple(p) for p in points}
    best = 0
    for (x1, y1), (x2, y2) in combinations(sorted(pts), 2):
        if x1 == x2 or y1 == y2:
            continue
        if (x1, y2) in pts and (x2, y1) in pts:
            area = abs(x2 - x1) * abs(y2 - y1)
            best = area if not best else min(best, area)
    return best


def _hull_size(points):
    pts = sorted({tuple(p) for p in points})
    if len(pts) <= 2:
        return len(pts)

    def cross(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1])
                - (a[1] - o[1]) * (b[0] - o[0]))

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return len(set(lower[:-1] + upper[:-1]))


# --------------------------------------------------------------------------- #
@fam("grid_dp_hard", "hard", ["dynamic-programming", "matrix"])
def f_grid_dp_hard():
    def min_falling(grid):
        if not grid or not grid[0]:
            return 0
        dp = list(grid[0])
        for row in grid[1:]:
            dp = [row[j] + min(dp[max(0, j - 1):j + 2]) for j in range(len(row))]
        return min(dp)

    def longest_increasing_path(grid):
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])

        @lru_cache(maxsize=None)
        def go(i, j):
            best = 1
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + a, j + b
                if 0 <= ni < rows and 0 <= nj < cols and grid[ni][nj] > grid[i][j]:
                    best = max(best, 1 + go(ni, nj))
            return best
        out = max(go(i, j) for i in range(rows) for j in range(cols))
        go.cache_clear()
        return out

    def count_squares(grid):
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        dp = [[0] * cols for _ in range(rows)]
        total = 0
        for i in range(rows):
            for j in range(cols):
                if grid[i][j]:
                    dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j],
                                       dp[i][j - 1]) if i and j else 1
                    total += dp[i][j]
        return total

    def dungeon(grid):
        if not grid or not grid[0]:
            return 1
        rows, cols = len(grid), len(grid[0])
        need = [[float("inf")] * (cols + 1) for _ in range(rows + 1)]
        need[rows][cols - 1] = need[rows - 1][cols] = 1
        for i in range(rows - 1, -1, -1):
            for j in range(cols - 1, -1, -1):
                req = min(need[i + 1][j], need[i][j + 1]) - grid[i][j]
                need[i][j] = max(1, req)
        return need[0][0]

    specs = [
        ("Minimum Falling Path Sum", "Given a matrix `grid`, fall from the top row to "
         "the bottom moving straight down or diagonally, and return the smallest sum.",
         min_falling, matrix),
        ("Longest Increasing Path In Matrix", "Given a matrix `grid`, return the length "
         "of the longest path moving to horizontally or vertically adjacent cells with "
         "strictly increasing values.", longest_increasing_path, matrix),
        ("Count Square Submatrices Of Ones", "Given a grid of 0s and 1s, return how "
         "many square submatrices consist entirely of 1s.", count_squares,
         lambda rng: grid01(rng, p=0.6)),
        ("Dungeon Minimum Health", "Given a matrix `grid` of health changes, move right "
         "or down from the top-left to the bottom-right. Return the least starting "
         "health that keeps the total strictly positive throughout.", dungeon, matrix),
        ("Cherry Pickup Two Passes", "Given a matrix `grid`, return the largest total "
         "from two separate top-left to bottom-right paths moving only right or down; "
         "a cell counts once even if both paths use it.", None, matrix),
        ("Paint House Minimum Cost", "Given a matrix `grid` with three columns giving "
         "the cost of painting each house one of three colours, return the least total "
         "cost with no two adjacent houses sharing a colour.", None, None),
        ("Maximum Sum Rectangle", "Given a matrix `grid`, return the largest sum of any "
         "non-empty rectangular submatrix.", _max_rect_sum, matrix),
    ]
    for title, stmt, ref, gen in specs:
        if title == "Cherry Pickup Two Passes":
            ref = _cherry
        if title == "Paint House Minimum Cost":
            yield problem(title=title, statement=stmt, ref=_paint_house,
                          inputs=lambda rng: (_three_cols(rng),),
                          signature="def solve(grid):",
                          edges=[([],), ([[1, 2, 3]],)])
            continue
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=(lambda rng, g=gen: (g(rng),)),
                      signature="def solve(grid):",
                      edges=[([[1]],), ([[1, 2], [3, 4]],)])


def _three_cols(rng):
    return [[rng.randint(1, 9) for _ in range(3)] for _ in range(rng.randint(0, 5))]


def _paint_house(grid):
    if not grid:
        return 0
    dp = list(grid[0])
    for row in grid[1:]:
        dp = [row[c] + min(dp[k] for k in range(3) if k != c) for c in range(3)]
    return min(dp)


def _max_rect_sum(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    best = None
    for top in range(rows):
        acc = [0] * cols
        for bottom in range(top, rows):
            for j in range(cols):
                acc[j] += grid[bottom][j]
            for i in range(cols):
                for j in range(i, cols):
                    total = sum(acc[i:j + 1])
                    best = total if best is None else max(best, total)
    return best or 0


def _cherry(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])

    @lru_cache(maxsize=None)
    def go(r1, c1, c2):
        r2 = r1 + c1 - c2
        if r1 >= rows or c1 >= cols or r2 >= rows or c2 >= cols:
            return float("-inf")
        val = grid[r1][c1] + (0 if (r1, c1) == (r2, c2) else grid[r2][c2])
        if r1 == rows - 1 and c1 == cols - 1:
            return val
        best = max(go(r1 + 1, c1, c2), go(r1, c1 + 1, c2),
                   go(r1 + 1, c1, c2 + 1), go(r1, c1 + 1, c2 + 1))
        return val + best if best != float("-inf") else float("-inf")
    out = go(0, 0, 0)
    go.cache_clear()
    return 0 if out == float("-inf") else out


# --------------------------------------------------------------------------- #
@fam("combinatorics_hard", "hard", ["combinatorics", "math"])
def f_comb_hard():
    specs = [
        ("Unique Binary Search Trees", "Given a non-negative integer `n`, return how "
         "many structurally distinct binary search trees hold values 1 to `n`.",
         lambda n: _cat(n), (0, 14)),
        ("Permutation Sequence Rank", "Given a non-negative integer `n` at most 8, "
         "return the sum of the digits of the lexicographically middle permutation of "
         "1..n, or 0 if `n` is 0.", lambda n: _mid_perm(n), (0, 8)),
        ("Derangement Count", "Given a non-negative integer `n`, return how many "
         "permutations of `n` items leave no item in its original position.",
         lambda n: _derange(n), (0, 12)),
        ("Bell Number", "Given a non-negative integer `n`, return how many ways a set "
         "of `n` items can be partitioned.", lambda n: _bell(n), (0, 11)),
        ("Stirling Second Kind Total", "Given a non-negative integer `n`, return the "
         "number of ways to partition `n` labelled items into exactly two non-empty "
         "groups, or 0 if `n` is below 2.",
         lambda n: (2 ** (n - 1) - 1) if n >= 2 else 0, (0, 20)),
        ("Count Binary Trees By Nodes", "Given a non-negative integer `n`, return how "
         "many distinct binary tree shapes have `n` nodes.", lambda n: _cat(n), (0, 14)),
        ("Multinomial Middle Coefficient", "Given a non-negative integer `n`, return "
         "the central binomial coefficient, that is `n` choose `n // 2`.",
         lambda n: _nck(n, n // 2), (0, 25)),
    ]
    for title, stmt, ref, (lo, hi) in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=(lambda rng, lo=lo, hi=hi: (rng.randint(lo, hi),)),
                      signature="def solve(n):", edges=[(lo,), (lo + 1,), (hi,)])


def _nck(n, k):
    if k < 0 or k > n:
        return 0
    out = 1
    for i in range(k):
        out = out * (n - i) // (i + 1)
    return out


def _cat(n):
    return _nck(2 * n, n) // (n + 1)


def _mid_perm(n):
    if n == 0:
        return 0
    from math import factorial
    perms = sorted(permutations(range(1, n + 1)))
    return sum(perms[factorial(n) // 2])


def _derange(n):
    a, b = 1, 0
    for i in range(2, n + 1):
        a, b = b, (i - 1) * (a + b)
    return b if n else 1


def _bell(n):
    row = [1]
    for _ in range(n):
        nxt = [row[-1]]
        for v in row:
            nxt.append(nxt[-1] + v)
        row = nxt
    return row[0]


# --------------------------------------------------------------------------- #
@fam("heap_hard", "hard", ["heap", "sorting"])
def f_heap_hard():
    specs = [
        ("Running Median Final", "Given a list `nums`, return the median after every "
         "prefix, each rounded to six decimals.",
         lambda nums, k: [_med(nums[:i + 1]) for i in range(len(nums))]),
        ("Merge K Sorted Lists Flat", "Given a list `nums` and an integer `k` that is "
         "ignored, return the values sorted ascending.",
         lambda nums, k: sorted(nums)),
        ("Smallest Range Covering", "Given a list `nums` and an integer `k`, return the "
         "smallest difference between the largest and smallest of any `k` values.",
         lambda nums, k: _smallest_range(nums, k)),
        ("Sliding Window Median", "Given a list `nums` and a positive integer `k`, "
         "return the median of each window of length `k`, each rounded to six decimals.",
         lambda nums, k: [_med(nums[i:i + k])
                          for i in range(len(nums) - k + 1)] if k <= len(nums) else []),
        ("Task Scheduler Intervals", "Given a list `nums` of task ids and a cooldown "
         "`k`, return the fewest time units to run every task with at least `k` units "
         "between identical tasks.", lambda nums, k: _scheduler(nums, k)),
        ("Maximum Capital After K Projects", "Given a list `nums` of project profits "
         "and an integer `k`, return the total from choosing at most `k` projects with "
         "the largest profits.", lambda nums, k: sum(sorted(nums, reverse=True)[:k])),
        ("Kth Largest Sum Of Subarrays", "Given a list `nums` and a 1-based `k`, return "
         "the `k`-th largest sum among all non-empty contiguous subarrays, or None if "
         "there are fewer than `k`.", lambda nums, k: _kth_subarray(nums, k)),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (ints(rng, lo=-9, hi=9, max_n=8),
                                          rng.randint(1, 4)),
                      signature="def solve(nums, k):",
                      edges=[([], 1), ([1], 1), ([3, 1, 2], 2)])


def _med(xs):
    if not xs:
        return None
    ys = sorted(xs)
    n = len(ys)
    return round(ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2, 6)


def _smallest_range(nums, k):
    xs = sorted(nums)
    if k <= 0 or k > len(xs):
        return 0
    return min(xs[i + k - 1] - xs[i] for i in range(len(xs) - k + 1))


def _scheduler(nums, k):
    if not nums:
        return 0
    counts = {}
    for x in nums:
        counts[x] = counts.get(x, 0) + 1
    top = max(counts.values())
    movers = sum(1 for v in counts.values() if v == top)
    return max(len(nums), (top - 1) * (k + 1) + movers)


def _kth_subarray(nums, k):
    sums = sorted((sum(nums[i:j]) for i in range(len(nums))
                   for j in range(i + 1, len(nums) + 1)), reverse=True)
    return sums[k - 1] if 1 <= k <= len(sums) else None


# --------------------------------------------------------------------------- #
@fam("trie_prefix", "hard", ["trie", "string"])
def f_trie():
    specs = [
        ("Count Words With Prefix", "Given a list `words` and a string `prefix`, return "
         "how many entries start with `prefix`.",
         lambda words, prefix: sum(1 for w in words if w.startswith(prefix))),
        ("Count Distinct Prefixes", "Given a list `words` and a string `prefix` that is "
         "ignored, return how many distinct non-empty prefixes the words have in total.",
         lambda words, prefix: len({w[:i] for w in words
                                    for i in range(1, len(w) + 1)})),
        ("Longest Common Prefix Of All", "Given a list `words` and a string `prefix` "
         "that is ignored, return the longest prefix shared by every word.",
         lambda words, prefix: _lcp_all(words)),
        ("Replace Words With Roots", "Given a list `words` used as roots and a string "
         "`prefix` holding a space-separated sentence, replace each word by its "
         "shortest matching root and return the sentence.",
         lambda words, prefix: _replace_roots(words, prefix)),
        ("Maximum XOR Pair", "Given a list `words` of binary strings and a string "
         "`prefix` that is ignored, return the largest XOR of any two values.",
         lambda words, prefix: _max_xor(words)),
        ("Words Matching Wildcard", "Given a list `words` and a string `prefix` where "
         "'.' matches any single character, return how many words of the same length "
         "match.", lambda words, prefix: _wildcard_count(words, prefix)),
    ]
    for title, stmt, ref in specs:
        binary = "binary strings" in stmt
        sentence_arg = "space-separated sentence" in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: ([("".join(rng.choice("01")
                                            for _ in range(rng.randint(1, 5))))
                                   for _ in range(rng.randint(0, 5))], "")) if binary
                    else (lambda rng: ([word(rng, 1, 4, "ab")
                                        for _ in range(rng.randint(0, 5))],
                                       " ".join(word(rng, 1, 4, "ab")
                                                for _ in range(rng.randint(0, 3)))))
                    if sentence_arg
                    else (lambda rng: ([word(rng, 1, 4, "ab")
                                        for _ in range(rng.randint(0, 6))],
                                       word(rng, 0, 2, "ab.")))),
            signature="def solve(words, prefix):",
            # edges must respect each variant's alphabet -- "ab" is not a binary string
            edges=([([], ""), (["1", "10"], "")] if binary else [([], ""), (["ab"], "a")]))


def _lcp_all(words):
    if not words:
        return ""
    out = ""
    for chars in zip(*words):
        if len(set(chars)) != 1:
            break
        out += chars[0]
    return out


def _replace_roots(words, sentence):
    roots = sorted(set(words), key=len)
    out = []
    for w in sentence.split():
        repl = next((r for r in roots if r and w.startswith(r)), w)
        out.append(repl)
    return " ".join(out)


def _max_xor(words):
    vals = [int(w, 2) for w in words if w]
    return max((a ^ b for a, b in combinations(vals, 2)), default=0)


def _wildcard_count(words, pattern):
    return sum(1 for w in words if len(w) == len(pattern)
               and all(p in (".", c) for p, c in zip(pattern, w)))


def _dense_matrix(rng):
    """No zero diagonal -- otherwise the identity assignment is free."""
    n = rng.randint(1, 4)
    return [[rng.randint(1, 9) for _ in range(n)] for _ in range(n)]


def _dna(rng):
    """Plant a repeated 10-mer half the time, so the answer is not always zero."""
    base = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 22)))
    if rng.random() < 0.6:
        motif = "".join(rng.choice("ACGT") for _ in range(10))
        return motif + base + motif
    return base


def _rect_points(rng):
    """Plant axis-aligned rectangles -- random points essentially never form one."""
    pts = set()
    for _ in range(rng.randint(0, 2)):
        x1, y1 = rng.randint(-4, 2), rng.randint(-4, 2)
        x2, y2 = x1 + rng.randint(1, 3), y1 + rng.randint(1, 3)
        pts.update({(x1, y1), (x1, y2), (x2, y1), (x2, y2)})
    for _ in range(rng.randint(0, 3)):
        pts.add((rng.randint(-4, 4), rng.randint(-4, 4)))
    return [list(p) for p in sorted(pts)]
