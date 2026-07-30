"""Hard tier: two-dimensional DP, search with pruning, graphs with weights."""
from __future__ import annotations

from functools import lru_cache

from .core import (fam, grid01, ints, matrix, pos_ints, problem, sorted_ints,
                   word, distinct_ints)


# --------------------------------------------------------------------------- #
@fam("dp_2d_strings", "hard", ["dynamic-programming", "string"])
def f_dp_2d_strings():
    def distinct_subseq(s, t):
        dp = [1] + [0] * len(t)
        for c in s:
            for j in range(len(t) - 1, -1, -1):
                if t[j] == c:
                    dp[j + 1] += dp[j]
        return dp[len(t)]

    def interleaving(a, b, c):
        if len(a) + len(b) != len(c):
            return False
        dp = [[False] * (len(b) + 1) for _ in range(len(a) + 1)]
        dp[0][0] = True
        for i in range(len(a) + 1):
            for j in range(len(b) + 1):
                if i and dp[i - 1][j] and a[i - 1] == c[i + j - 1]:
                    dp[i][j] = True
                if j and dp[i][j - 1] and b[j - 1] == c[i + j - 1]:
                    dp[i][j] = True
        return dp[len(a)][len(b)]

    def wildcard(s, p):
        dp = [[False] * (len(p) + 1) for _ in range(len(s) + 1)]
        dp[0][0] = True
        for j in range(1, len(p) + 1):
            dp[0][j] = dp[0][j - 1] and p[j - 1] == "*"
        for i in range(1, len(s) + 1):
            for j in range(1, len(p) + 1):
                if p[j - 1] == "*":
                    dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
                elif p[j - 1] in ("?", s[i - 1]):
                    dp[i][j] = dp[i - 1][j - 1]
        return dp[len(s)][len(p)]

    def regex(s, p):
        @lru_cache(maxsize=None)
        def go(i, j):
            if j == len(p):
                return i == len(s)
            first = i < len(s) and p[j] in (s[i], ".")
            if j + 1 < len(p) and p[j + 1] == "*":
                return go(i, j + 2) or (first and go(i + 1, j))
            return first and go(i + 1, j + 1)
        return go(0, 0)

    def lps(s):
        n = len(s)
        if not n:
            return 0
        dp = [[0] * n for _ in range(n)]
        for i in range(n - 1, -1, -1):
            dp[i][i] = 1
            for j in range(i + 1, n):
                dp[i][j] = dp[i + 1][j - 1] + 2 if s[i] == s[j] \
                    else max(dp[i + 1][j], dp[i][j - 1])
        return dp[0][n - 1]

    specs = [
        ("Distinct Subsequences Count",
         "Given strings `s` and `t`, return how many distinct subsequences of `s` equal "
         "`t`.", distinct_subseq,
         lambda rng: (word(rng, 0, 8, "ab"), word(rng, 0, 3, "ab")), "def solve(s, t):"),
        ("Interleaving Strings",
         "Given strings `a`, `b` and `c`, return True if `c` can be formed by "
         "interleaving `a` and `b` while preserving the order within each.",
         interleaving, lambda rng: _interleave_case(rng), "def solve(a, b, c):"),
        ("Wildcard Pattern Matching",
         "Given a string `s` and a pattern `p` where '?' matches any single character "
         "and '*' matches any sequence including empty, return True if `p` matches all "
         "of `s`.", wildcard,
         lambda rng: (word(rng, 0, 6, "ab"), word(rng, 0, 5, "ab?*")), "def solve(s, p):"),
        ("Regular Expression Matching",
         "Given a string `s` and a pattern `p` where '.' matches any single character "
         "and '*' repeats the preceding element zero or more times, return True if `p` "
         "matches all of `s`.", regex,
         lambda rng: (word(rng, 0, 5, "ab"), _regex_pat(rng)), "def solve(s, p):"),
        ("Longest Palindromic Subsequence",
         "Given a string `s`, return the length of its longest palindromic subsequence.",
         lps, lambda rng: (word(rng, 0, 10, "abc"),), "def solve(s):"),
        ("Minimum Insertions For Palindrome",
         "Given a string `s`, return the fewest characters to insert to make it a "
         "palindrome.", lambda s: len(s) - lps(s),
         lambda rng: (word(rng, 0, 9, "abc"),), "def solve(s):"),
        ("Shortest Common Supersequence Length",
         "Given strings `a` and `b`, return the length of the shortest string having "
         "both as subsequences.",
         lambda a, b: len(a) + len(b) - _lcs_len(a, b),
         lambda rng: (word(rng, 0, 7, "abc"), word(rng, 0, 7, "abc")),
         "def solve(a, b):"),
        ("Edit Distance With Costs",
         "Given strings `a` and `b` and costs `ins`, `dele` and `sub`, return the least "
         "total cost to turn `a` into `b`.", _edit_cost,
         lambda rng: (word(rng, 0, 5, "ab"), word(rng, 0, 5, "ab"),
                      rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4)),
         "def solve(a, b, ins, dele, sub):"),
        ("Longest Repeated Substring Length",
         "Given a string `s`, return the length of the longest substring occurring at "
         "least twice; occurrences may overlap.", _longest_repeat,
         lambda rng: (word(rng, 0, 10, "abc"),), "def solve(s):"),
        ("Palindrome Partition Minimum Cuts",
         "Given a string `s`, return the fewest cuts so every piece is a palindrome.",
         _min_cuts, lambda rng: (word(rng, 0, 9, "aab"),), "def solve(s):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _interleave_case(rng):
    a = word(rng, 0, 4, "ab")
    b = word(rng, 0, 4, "cd")
    if rng.random() < 0.5:
        merged, i, j = [], 0, 0
        while i < len(a) or j < len(b):
            if j >= len(b) or (i < len(a) and rng.random() < 0.5):
                merged.append(a[i])
                i += 1
            else:
                merged.append(b[j])
                j += 1
        return (a, b, "".join(merged))
    return (a, b, word(rng, 0, 7, "abcd"))


def _regex_pat(rng):
    out = []
    for _ in range(rng.randint(0, 4)):
        out.append(rng.choice("ab."))
        if rng.random() < 0.4:
            out.append("*")
    return "".join(out)


def _lcs_len(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            dp[i][j] = dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] \
                else max(dp[i - 1][j], dp[i][j - 1])
    return dp[len(a)][len(b)]


def _edit_cost(a, b, ins, dele, sub):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        for j in range(len(b) + 1):
            if not i:
                dp[i][j] = j * ins
            elif not j:
                dp[i][j] = i * dele
            elif a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i][j - 1] + ins, dp[i - 1][j] + dele,
                               dp[i - 1][j - 1] + sub)
    return dp[len(a)][len(b)]


def _longest_repeat(s):
    best = 0
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            sub = s[i:j]
            if s.count(sub) > 1 or s.find(sub, i + 1) != -1:
                best = max(best, len(sub))
    return best


def _min_cuts(s):
    n = len(s)
    if n <= 1:
        return 0
    pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            pal[i][j] = s[i] == s[j] and (j - i < 2 or pal[i + 1][j - 1])
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = min((dp[j] + 1 for j in range(i) if pal[j][i - 1]), default=i)
    return dp[n] - 1


# --------------------------------------------------------------------------- #
@fam("knapsack", "hard", ["dynamic-programming"])
def f_knapsack():
    def zero_one(weights, values, cap):
        dp = [0] * (cap + 1)
        for w, v in zip(weights, values):
            for c in range(cap, w - 1, -1):
                dp[c] = max(dp[c], dp[c - w] + v)
        return dp[cap]

    def unbounded(weights, values, cap):
        dp = [0] * (cap + 1)
        for c in range(cap + 1):
            for w, v in zip(weights, values):
                if w <= c:
                    dp[c] = max(dp[c], dp[c - w] + v)
        return dp[cap]

    specs = [
        ("Knapsack Maximum Value", "Given lists `weights` and `values` of equal length "
         "and a capacity `cap`, choose each item at most once to maximise total value "
         "without exceeding `cap`. Return that value.", zero_one),
        ("Unbounded Knapsack", "As the 0/1 knapsack, but each item may be chosen any "
         "number of times. Return the maximum value.", unbounded),
        ("Knapsack Minimum Weight For Value", "Given `weights`, `values` and a target "
         "value `cap`, return the least total weight achieving a value of at least "
         "`cap`, or -1 if impossible. Each item is used at most once.", None),
        ("Count Knapsack Combinations", "Given `weights`, `values` and a capacity "
         "`cap`, return how many distinct subsets of items have total weight exactly "
         "`cap`.", None),
        ("Knapsack Item Count", "Given `weights`, `values` and a capacity `cap`, return "
         "the fewest items whose weights sum to exactly `cap`, or -1 if impossible. "
         "Items may repeat.", None),
        ("Subset Sum Reachable", "Given `weights`, `values` and a capacity `cap`, "
         "return True if some subset of `weights` sums to exactly `cap`.", None),
        ("Partition Into Two Equal Weights", "Given `weights`, `values` and `cap`, "
         "ignore `values` and `cap` and return True if `weights` splits into two groups "
         "of equal sum.", None),
        ("Target Sum Assignments", "Given `weights`, `values` and `cap`, assign a plus "
         "or minus to each weight and return how many assignments total exactly `cap`.",
         None),
        ("Bounded Knapsack Two Copies", "As the 0/1 knapsack, but each item may be "
         "taken at most twice. Return the maximum value.", None),
    ]
    refs = {
        "Knapsack Minimum Weight For Value": lambda w, v, cap: _min_weight(w, v, cap),
        "Count Knapsack Combinations": lambda w, v, cap: sum(
            1 for m in range(1 << len(w))
            if sum(w[i] for i in range(len(w)) if m >> i & 1) == cap),
        "Knapsack Item Count": lambda w, v, cap: _min_items(w, cap),
        "Subset Sum Reachable": lambda w, v, cap: any(
            sum(w[i] for i in range(len(w)) if m >> i & 1) == cap
            for m in range(1 << len(w))),
        "Partition Into Two Equal Weights": lambda w, v, cap: (
            sum(w) % 2 == 0 and any(
                sum(w[i] for i in range(len(w)) if m >> i & 1) == sum(w) // 2
                for m in range(1 << len(w)))),
        "Target Sum Assignments": lambda w, v, cap: sum(
            1 for m in range(1 << len(w))
            if sum(w[i] * (1 if m >> i & 1 else -1) for i in range(len(w))) == cap),
        "Bounded Knapsack Two Copies": lambda w, v, cap: _bounded(w, v, cap, 2),
    }
    for title, stmt, ref in specs:
        yield problem(
            title=title, statement=stmt, ref=ref or refs[title],
            inputs=lambda rng: _knap(rng), signature="def solve(weights, values, cap):",
            edges=[([], [], 0), ([1], [5], 1), ([2, 3], [3, 4], 5)],
        )


def _knap(rng):
    n = rng.randint(0, 6)
    w = [rng.randint(1, 6) for _ in range(n)]
    v = [rng.randint(1, 9) for _ in range(n)]
    return (w, v, rng.randint(0, 12))


def _min_weight(weights, values, cap):
    best = None
    for m in range(1 << len(weights)):
        val = sum(values[i] for i in range(len(weights)) if m >> i & 1)
        wt = sum(weights[i] for i in range(len(weights)) if m >> i & 1)
        if val >= cap and (best is None or wt < best):
            best = wt
    return -1 if best is None else best


def _min_items(weights, cap):
    INF = float("inf")
    dp = [0] + [INF] * cap
    for c in range(1, cap + 1):
        for w in weights:
            if w <= c:
                dp[c] = min(dp[c], dp[c - w] + 1)
    return -1 if dp[cap] == INF else dp[cap]


def _bounded(weights, values, cap, copies):
    dp = [0] * (cap + 1)
    for w, v in zip(weights, values):
        for _ in range(copies):
            for c in range(cap, w - 1, -1):
                dp[c] = max(dp[c], dp[c - w] + v)
    return dp[cap]


# --------------------------------------------------------------------------- #
@fam("graph_weighted", "hard", ["graph", "shortest-path"])
def f_graph_weighted():
    def dijkstra(n, edges, src):
        INF = float("inf")
        dist = [INF] * n
        if not (0 <= src < n):
            return [-1] * n
        dist[src] = 0
        adj = {i: [] for i in range(n)}
        for a, b, w in edges:
            adj[a].append((b, w))
            adj[b].append((a, w))
        seen = set()
        for _ in range(n):
            u = min((i for i in range(n) if i not in seen), key=lambda i: dist[i],
                    default=None)
            if u is None or dist[u] == INF:
                break
            seen.add(u)
            for v, w in adj[u]:
                dist[v] = min(dist[v], dist[u] + w)
        return [-1 if d == INF else d for d in dist]

    def mst_cost(n, edges, src):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        total, used = 0, 0
        for a, b, w in sorted(edges, key=lambda e: e[2]):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                total += w
                used += 1
        return total if used == n - 1 else -1

    def bellman_k(n, edges, src):
        INF = float("inf")
        dist = [INF] * n
        if not (0 <= src < n):
            return -1
        dist[src] = 0
        for _ in range(n - 1):
            for a, b, w in edges:
                if dist[a] + w < dist[b]:
                    dist[b] = dist[a] + w
                if dist[b] + w < dist[a]:
                    dist[a] = dist[b] + w
        finite = [d for d in dist if d != INF]
        return max(finite) if len(finite) == n else -1

    specs = [
        ("Shortest Path Weights", "Given `n` nodes, a list of undirected weighted "
         "`edges` as `[a, b, w]` with non-negative `w`, and a source `src`, return the "
         "shortest distance to every node, using -1 for unreachable nodes.", dijkstra),
        ("Minimum Spanning Tree Cost", "Given `n` nodes and undirected weighted "
         "`edges`, return the total weight of a minimum spanning tree, or -1 if the "
         "graph is not connected. The `src` argument is unused.", mst_cost),
        ("Network Delay Time", "Given `n` nodes, undirected weighted `edges` and a "
         "source `src`, return the time for a signal to reach every node, or -1 if any "
         "node is unreachable.", bellman_k),
        ("Count Reachable Within Budget", "Given `n` nodes, undirected weighted `edges`, "
         "and a source `src`, return how many nodes lie within total distance 10 of "
         "`src`, counting `src` itself.",
         lambda n, edges, src: sum(1 for d in dijkstra(n, edges, src)
                                   if 0 <= d <= 10)),
        ("Path Exists Within Weight", "Given `n` nodes, undirected weighted `edges` and "
         "a source `src`, return True if every node is reachable from `src`.",
         lambda n, edges, src: all(d != -1 for d in dijkstra(n, edges, src))),
        ("Maximum Edge On Shortest Path", "Given `n` nodes, undirected weighted `edges` "
         "and a source `src`, return the largest shortest-path distance from `src` to "
         "any reachable node.",
         lambda n, edges, src: max((d for d in dijkstra(n, edges, src) if d >= 0),
                                   default=-1)),
        ("Second Shortest Distance", "Given `n` nodes, undirected weighted `edges` and "
         "a source `src`, return the second smallest distinct shortest-path distance "
         "from `src`, or -1 if there are fewer than two.",
         lambda n, edges, src: (lambda ds: sorted(ds)[1] if len(ds) > 1 else -1)(
             {d for d in dijkstra(n, edges, src) if d >= 0})),
        ("Total Shortest Path Weight", "Given `n` nodes, undirected weighted `edges` "
         "and a source `src`, return the sum of the shortest distances to all "
         "reachable nodes.",
         lambda n, edges, src: sum(d for d in dijkstra(n, edges, src) if d >= 0)),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: _wgraph(rng),
                      signature="def solve(n, edges, src):",
                      edges=[(1, [], 0), (2, [[0, 1, 3]], 0), (3, [[0, 1, 2]], 0)])


def _wgraph(rng):
    n = rng.randint(1, 5)
    seen, edges = set(), []
    for _ in range(rng.randint(0, 6)):
        a, b = rng.randrange(n), rng.randrange(n)
        if a == b or (min(a, b), max(a, b)) in seen:
            continue
        seen.add((min(a, b), max(a, b)))
        edges.append([min(a, b), max(a, b), rng.randint(1, 9)])
    return (n, edges, 0)


# --------------------------------------------------------------------------- #
@fam("backtracking", "hard", ["backtracking"])
def f_backtracking():
    def n_queens(n):
        count = 0
        cols, d1, d2 = set(), set(), set()

        def place(r):
            nonlocal count
            if r == n:
                count += 1
                return
            for c in range(n):
                if c in cols or r - c in d1 or r + c in d2:
                    continue
                cols.add(c)
                d1.add(r - c)
                d2.add(r + c)
                place(r + 1)
                cols.remove(c)
                d1.remove(r - c)
                d2.remove(r + c)
        place(0)
        return count

    def word_search(grid, w):
        if not w:
            return True
        rows, cols = len(grid), len(grid[0]) if grid else 0

        def go(i, j, k, used):
            if k == len(w):
                return True
            if not (0 <= i < rows and 0 <= j < cols) or (i, j) in used:
                return False
            if grid[i][j] != w[k]:
                return False
            used.add((i, j))
            ok = any(go(i + a, j + b, k + 1, used)
                     for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            used.remove((i, j))
            return ok
        return any(go(i, j, 0, set()) for i in range(rows) for j in range(cols))

    yield problem(
        title="N Queens Solution Count",
        statement="Given a non-negative integer `n`, return how many ways `n` queens "
                  "can be placed on an `n x n` board with no two attacking each other.",
        ref=n_queens, inputs=lambda rng: (rng.randint(0, 7),), signature="def solve(n):",
        edges=[(0,), (1,), (4,), (6,)])
    yield problem(
        title="Word Search In Grid",
        statement="Given a grid of single characters and a string `word`, return True "
                  "if `word` can be traced through horizontally or vertically adjacent "
                  "cells without reusing a cell.",
        ref=word_search, inputs=lambda rng: (_char_grid(rng), word(rng, 0, 4, "ab")),
        signature="def solve(grid, word):",
        edges=[([["a"]], "a"), ([["a"]], "b"), ([["a", "b"]], "ab")])
    yield problem(
        title="Combination Sum Count",
        statement="Given a list `candidates` of distinct positive integers and a "
                  "`target`, return how many distinct multisets of candidates sum to "
                  "`target`. Each candidate may repeat.",
        ref=lambda candidates, target: _comb_sum(sorted(set(candidates)), target),
        inputs=lambda rng: (sorted(set(pos_ints(rng, lo=1, hi=7, min_n=1, max_n=4))),
                            rng.randint(0, 14)),
        signature="def solve(candidates, target):",
        edges=[([], 0), ([1], 3), ([2, 3], 7)])
    yield problem(
        title="Permutations Count With Duplicates",
        statement="Given a list `nums` that may contain duplicates, return how many "
                  "distinct orderings of its elements exist.",
        ref=lambda nums: _perm_distinct(nums),
        inputs=lambda rng: (ints(rng, lo=0, hi=3, max_n=7),), signature="def solve(nums):",
        edges=[([],), ([1],), ([1, 1],), ([1, 2, 2],)])
    yield problem(
        title="Restore IP Addresses Count",
        statement="Given a string `s` of digits, return how many ways it splits into "
                  "four parts each between 0 and 255 with no leading zeros.",
        ref=_restore_ip,
        inputs=lambda rng: ("".join(rng.choice("0125")
                                    for _ in range(rng.randint(0, 9))),),
        signature="def solve(s):", edges=[("",), ("1111",), ("25525511135",)])
    yield problem(
        title="Palindrome Partitions Count",
        statement="Given a string `s`, return how many ways it splits into contiguous "
                  "pieces that are all palindromes.",
        ref=_pal_parts, inputs=lambda rng: (word(rng, 0, 8, "aab"),),
        signature="def solve(s):", edges=[("",), ("a",), ("aab",)])
    yield problem(
        title="Partition Into K Equal Sums",
        statement="Given a list `nums` and an integer `k` at least 1, return True if "
                  "`nums` splits into `k` groups with equal sums.",
        ref=_k_partition,
        inputs=lambda rng: (pos_ints(rng, lo=1, hi=6, max_n=7), rng.randint(1, 3)),
        signature="def solve(nums, k):", edges=[([], 1), ([1, 1], 2), ([1, 2], 2)])
    yield problem(
        title="Letter Case Permutation Count",
        statement="Given a string `s`, return how many strings can be produced by "
                  "independently upper- or lower-casing each alphabetic character.",
        ref=lambda s: 1 << sum(1 for c in s if c.isalpha()),
        inputs=lambda rng: (word(rng, 0, 8, "a1b2"),), signature="def solve(s):",
        edges=[("",), ("a",), ("1",), ("a1b",)])
    yield problem(
        title="Generate Parentheses Count",
        statement="Given a non-negative integer `n`, return how many well-formed "
                  "strings of `n` pairs of parentheses exist.",
        ref=lambda n: _catalan_h(n), inputs=lambda rng: (rng.randint(0, 11),),
        signature="def solve(n):", edges=[(0,), (1,), (3,)])
    yield problem(
        title="Sudoku Row Validity",
        statement="Given a 9x9 grid of integers 0-9 where 0 means empty, return True if "
                  "no row, column or 3x3 box contains a repeated non-zero value.",
        ref=_valid_sudoku, inputs=lambda rng: (_sudoku(rng),), signature="def solve(grid):",
        edges=[([[0] * 9 for _ in range(9)],)])


def _char_grid(rng):
    r, c = rng.randint(1, 3), rng.randint(1, 3)
    return [[rng.choice("ab") for _ in range(c)] for _ in range(r)]


def _comb_sum(cands, target):
    @lru_cache(maxsize=None)
    def go(i, rem):
        if rem == 0:
            return 1
        if i >= len(cands) or rem < 0:
            return 0
        return go(i + 1, rem) + go(i, rem - cands[i])
    return go(0, target)


def _perm_distinct(nums):
    from math import factorial
    counts = {}
    for x in nums:
        counts[x] = counts.get(x, 0) + 1
    total = factorial(len(nums))
    for c in counts.values():
        total //= factorial(c)
    return total


def _restore_ip(s):
    count = 0
    n = len(s)
    for a in range(1, 4):
        for b in range(1, 4):
            for c in range(1, 4):
                d = n - a - b - c
                if d < 1 or d > 3:
                    continue
                parts = [s[:a], s[a:a + b], s[a + b:a + b + c], s[a + b + c:]]
                if all(p and (p == "0" or not p.startswith("0")) and int(p) <= 255
                       for p in parts):
                    count += 1
    return count


def _pal_parts(s):
    @lru_cache(maxsize=None)
    def go(i):
        if i == len(s):
            return 1
        return sum(go(j) for j in range(i + 1, len(s) + 1)
                   if s[i:j] == s[i:j][::-1])
    return go(0)


def _k_partition(nums, k):
    total = sum(nums)
    if k <= 0 or total % k or (nums and max(nums) > total // k):
        return False
    target = total // k
    buckets = [0] * k
    xs = sorted(nums, reverse=True)

    def go(i):
        if i == len(xs):
            return all(b == target for b in buckets)
        seen = set()
        for j in range(k):
            if buckets[j] + xs[i] <= target and buckets[j] not in seen:
                seen.add(buckets[j])
                buckets[j] += xs[i]
                if go(i + 1):
                    return True
                buckets[j] -= xs[i]
        return False
    return go(0)


def _catalan_h(n):
    out = 1
    for i in range(n):
        out = out * (2 * n - i) // (i + 1)
    return out // (n + 1)


def _sudoku(rng):
    g = [[0] * 9 for _ in range(9)]
    for _ in range(rng.randint(0, 12)):
        g[rng.randrange(9)][rng.randrange(9)] = rng.randint(1, 9)
    return g


def _valid_sudoku(grid):
    def ok(vals):
        vals = [v for v in vals if v]
        return len(vals) == len(set(vals))
    if not all(ok(r) for r in grid):
        return False
    if not all(ok([grid[r][c] for r in range(9)]) for c in range(9)):
        return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            if not ok([grid[br + i][bc + j] for i in range(3) for j in range(3)]):
                return False
    return True


# --------------------------------------------------------------------------- #
@fam("monotonic_stack", "hard", ["stack", "monotonic-stack"])
def f_monotonic():
    def largest_rectangle(heights):
        best, st = 0, []
        for i, h in enumerate(heights + [0]):
            while st and heights[st[-1]] >= h:
                height = heights[st.pop()]
                width = i if not st else i - st[-1] - 1
                best = max(best, height * width)
            st.append(i)
        return best

    def trap(height):
        if not height:
            return 0
        left = [0] * len(height)
        right = [0] * len(height)
        run = 0
        for i, h in enumerate(height):
            run = max(run, h)
            left[i] = run
        run = 0
        for i in range(len(height) - 1, -1, -1):
            run = max(run, height[i])
            right[i] = run
        return sum(min(left[i], right[i]) - height[i] for i in range(len(height)))

    specs = [
        ("Largest Rectangle In Histogram", "Given a list `heights` of non-negative "
         "integers, return the area of the largest rectangle fitting under the "
         "histogram.", largest_rectangle),
        ("Trapping Rain Water", "Given a list `heights` of non-negative integers, "
         "return how many units of water are trapped after raining.", trap),
        ("Sum Of Subarray Minimums", "Given a list `heights`, return the sum of the "
         "minimum of every non-empty contiguous subarray.",
         lambda heights: sum(min(heights[i:j]) for i in range(len(heights))
                             for j in range(i + 1, len(heights) + 1))),
        ("Sum Of Subarray Maximums", "Given a list `heights`, return the sum of the "
         "maximum of every non-empty contiguous subarray.",
         lambda heights: sum(max(heights[i:j]) for i in range(len(heights))
                             for j in range(i + 1, len(heights) + 1))),
        ("Maximal Rectangle Of Ones", "Given a grid of 0s and 1s given as `heights` "
         "rows, return the area of the largest all-ones rectangle.", None),
        ("Remove Duplicate Letters Smallest", "Given a string given as `heights`, "
         "ignore it and return 0. (placeholder)", None),
        ("Previous Smaller Elements", "Given a list `heights`, return a list where "
         "entry `i` is the nearest element to the left that is strictly smaller, or -1.",
         lambda heights: [next((heights[j] for j in range(i - 1, -1, -1)
                                if heights[j] < heights[i]), -1)
                          for i in range(len(heights))]),
        ("Count Visible Bars", "Given a list `heights`, return how many bars are "
         "strictly taller than every bar to their left.",
         lambda heights: sum(1 for i, h in enumerate(heights)
                             if all(h > x for x in heights[:i]))),
    ]
    for title, stmt, ref in specs:
        if title == "Maximal Rectangle Of Ones":
            yield problem(
                title=title,
                statement="Given a grid of 0s and 1s, return the area of the largest "
                          "rectangle containing only 1s.",
                ref=_maximal_rect, inputs=lambda rng: (grid01(rng, p=0.6),),
                signature="def solve(grid):",
                edges=[([[0]],), ([[1]],), ([[1, 1], [1, 1]],)])
            continue
        if title == "Remove Duplicate Letters Smallest":
            yield problem(
                title="Lexicographically Smallest Distinct Subsequence",
                statement="Given a string `s`, remove duplicate letters so every letter "
                          "appears once and the result is the smallest possible in "
                          "lexicographic order.",
                ref=_remove_dup_letters, inputs=lambda rng: (word(rng, 0, 9, "abc"),),
                signature="def solve(s):", edges=[("",), ("bcabc",), ("cbacdcbc",)])
            continue
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (pos_ints(rng, lo=0, hi=9),),
                      signature="def solve(heights):",
                      edges=[([],), ([0],), ([3],), ([2, 1, 2],), ([0, 1, 0, 2],)])


def _maximal_rect(grid):
    if not grid or not grid[0]:
        return 0
    best = 0
    cols = len(grid[0])
    heights = [0] * cols
    for row in grid:
        for j in range(cols):
            heights[j] = heights[j] + 1 if row[j] else 0
        st = []
        for i, h in enumerate(heights + [0]):
            while st and heights[st[-1]] >= h:
                height = heights[st.pop()]
                width = i if not st else i - st[-1] - 1
                best = max(best, height * width)
            st.append(i)
    return best


def _remove_dup_letters(s):
    last = {c: i for i, c in enumerate(s)}
    st, seen = [], set()
    for i, c in enumerate(s):
        if c in seen:
            continue
        while st and st[-1] > c and last[st[-1]] > i:
            seen.discard(st.pop())
        st.append(c)
        seen.add(c)
    return "".join(st)


# --------------------------------------------------------------------------- #
@fam("binary_search_answer", "hard", ["binary-search", "greedy"])
def f_bs_answer():
    specs = [
        ("Median Of Two Sorted Lists", "Given lists `a` and `b` each sorted ascending, "
         "return the median of their combined elements, rounded to six decimals, or "
         "None if both are empty.",
         lambda a, b: _median_two(a, b),
         lambda rng: (sorted_ints(rng, lo=-9, hi=9, min_n=0),
                      sorted_ints(rng, lo=-9, hi=9, min_n=0)), "def solve(a, b):"),
        ("Kth Smallest Pair Distance", "Given a list `nums` and a 1-based `k`, return "
         "the `k`-th smallest absolute difference among all pairs, or -1 if there are "
         "fewer than `k` pairs.",
         lambda nums, k: _kth_pair(nums, k),
         lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(1, 6)), "def solve(nums, k):"),
        ("Minimum Days For Bouquets", "Given a list `bloom` of bloom days and integers "
         "`m` and `k`, return the earliest day `m` bouquets can be made, each needing "
         "`k` adjacent flowers bloomed. Return -1 if impossible.",
         lambda bloom, m, k: _bouquets(bloom, m, k),
         lambda rng: (pos_ints(rng, lo=1, hi=9), rng.randint(1, 3), rng.randint(1, 3)),
         "def solve(bloom, m, k):"),
        ("Maximum Minimum Distance", "Given a sorted list `positions` and an integer "
         "`k` at least 2, place `k` items at those positions to maximise the smallest "
         "gap between consecutive chosen positions, and return that gap. Return 0 if "
         "impossible.", lambda positions, k: _max_min_dist(positions, k),
         lambda rng: (sorted(set(pos_ints(rng, lo=0, hi=30, min_n=2))), rng.randint(2, 4)),
         "def solve(positions, k):"),
        ("Minimum Capacity To Ship", "Given a list `weights` and an integer `days` at "
         "least 1, return the least capacity per day to ship all packages in order "
         "within `days` days.", lambda weights, days: _ship(weights, days),
         lambda rng: (pos_ints(rng, lo=1, hi=9, min_n=1), rng.randint(1, 4)),
         "def solve(weights, days):"),
        ("Smallest Divisor Within Threshold", "Given a list `nums` of positive integers "
         "and an integer `threshold` at least `len(nums)`, return the smallest positive "
         "divisor `d` with `sum(ceil(x / d)) <= threshold`.",
         lambda nums, threshold: _divisor(nums, threshold),
         lambda rng: (pos_ints(rng, lo=1, hi=15, min_n=1), rng.randint(1, 25)),
         "def solve(nums, threshold):"),
        ("Kth Smallest In Sorted Matrix", "Given a matrix `grid` whose rows and columns "
         "are each sorted ascending and a 1-based `k`, return the `k`-th smallest "
         "element, or None if out of range.",
         lambda grid, k: _kth_matrix(grid, k),
         lambda rng: (_sorted_matrix(rng), rng.randint(1, 6)), "def solve(grid, k):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _median_two(a, b):
    xs = sorted(list(a) + list(b))
    if not xs:
        return None
    n = len(xs)
    return round(xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2, 6)


def _kth_pair(nums, k):
    ds = sorted(abs(nums[i] - nums[j]) for i in range(len(nums))
                for j in range(i + 1, len(nums)))
    return ds[k - 1] if 1 <= k <= len(ds) else -1


def _bouquets(bloom, m, k):
    def ok(day):
        made, run = 0, 0
        for b in bloom:
            if b <= day:
                run += 1
                if run == k:
                    made += 1
                    run = 0
            else:
                run = 0
        return made >= m
    if m * k > len(bloom):
        return -1
    lo, hi = min(bloom), max(bloom)
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def _max_min_dist(positions, k):
    xs = sorted(positions)
    if k > len(xs) or k < 2:
        return 0

    def ok(gap):
        count, last = 1, xs[0]
        for x in xs[1:]:
            if x - last >= gap:
                count += 1
                last = x
        return count >= k
    lo, hi = 0, xs[-1] - xs[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if ok(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def _ship(weights, days):
    def ok(cap):
        used, cur = 1, 0
        for w in weights:
            if w > cap:
                return False
            if cur + w > cap:
                used += 1
                cur = 0
            cur += w
        return used <= days
    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def _divisor(nums, threshold):
    d = 1
    while True:
        if sum(-(-x // d) for x in nums) <= max(threshold, len(nums)):
            return d
        d += 1


def _sorted_matrix(rng):
    r, c = rng.randint(1, 3), rng.randint(1, 3)
    vals = sorted(rng.randint(-9, 9) for _ in range(r * c))
    return [sorted(vals[i * c:(i + 1) * c]) for i in range(r)]


def _kth_matrix(grid, k):
    flat = sorted(x for row in grid for x in row)
    return flat[k - 1] if 1 <= k <= len(flat) else None


# --------------------------------------------------------------------------- #
@fam("advanced_array", "hard", ["array"])
def f_advanced_array():
    specs = [
        ("Maximum Gap After Sorting", "Given a list `nums`, return the largest "
         "difference between consecutive elements once sorted, or 0 if fewer than two.",
         lambda nums: max((b - a for a, b in zip(sorted(nums), sorted(nums)[1:])),
                          default=0)),
        ("Best Time To Buy And Sell Twice", "Given a list `prices`, return the largest "
         "profit from at most two non-overlapping buy-then-sell transactions.",
         lambda nums: _two_trades(nums)),
        ("Best Time With Cooldown", "Given a list `prices`, return the largest profit "
         "with unlimited transactions where you must skip one day after each sale.",
         lambda nums: _cooldown(nums)),
        ("Count Smaller After Self", "Given a list `nums`, return a list where entry "
         "`i` counts the elements to the right of `i` that are strictly smaller.",
         lambda nums: [sum(1 for x in nums[i + 1:] if x < nums[i])
                       for i in range(len(nums))]),
        ("Count Reverse Pairs", "Given a list `nums`, return how many pairs `i < j` "
         "have `nums[i] > 2 * nums[j]`.",
         lambda nums: sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums))
                          if nums[i] > 2 * nums[j])),
        ("Longest Consecutive Sequence", "Given a list `nums`, return the length of the "
         "longest run of consecutive integers formable from its values.",
         lambda nums: _longest_consec(nums)),
        ("Candy Distribution", "Given a list `ratings`, give each child at least one "
         "sweet and more than any lower-rated immediate neighbour. Return the fewest "
         "sweets needed.", lambda nums: _candy(nums)),
        ("Maximum Product Subarray", "Given a list `nums`, return the largest product "
         "of a non-empty contiguous subarray, or 0 if the list is empty.",
         lambda nums: _max_prod(nums)),
        ("Shortest Unsorted Window", "Given a list `nums`, return the length of the "
         "shortest contiguous stretch that, if sorted, would sort the whole list.",
         lambda nums: _unsorted_window(nums)),
        ("Longest Turbulent Subarray", "Given a list `nums`, return the length of the "
         "longest contiguous stretch where the comparison between adjacent elements "
         "flips every step.", lambda nums: _turbulent(nums)),
    ]
    for title, stmt, ref in specs:
        yield problem(title=title, statement=stmt, ref=ref,
                      inputs=lambda rng: (ints(rng, lo=-9, hi=9, max_n=9),),
                      signature="def solve(nums):",
                      edges=[([],), ([1],), ([1, 2, 3],), ([3, 2, 1],), ([2, 2, 2],)])


def _two_trades(prices):
    best = 0
    for split in range(len(prices) + 1):
        best = max(best, _one_trade(prices[:split]) + _one_trade(prices[split:]))
    return best


def _one_trade(prices):
    best, low = 0, None
    for p in prices:
        low = p if low is None else min(low, p)
        best = max(best, p - low)
    return best


def _cooldown(prices):
    hold, sold, rest = float("-inf"), float("-inf"), 0
    for p in prices:
        hold, sold, rest = max(hold, rest - p), hold + p, max(rest, sold)
    return max(sold, rest, 0)


def _longest_consec(nums):
    s, best = set(nums), 0
    for x in s:
        if x - 1 not in s:
            y = x
            while y + 1 in s:
                y += 1
            best = max(best, y - x + 1)
    return best


def _candy(ratings):
    n = len(ratings)
    if not n:
        return 0
    out = [1] * n
    for i in range(1, n):
        if ratings[i] > ratings[i - 1]:
            out[i] = out[i - 1] + 1
    for i in range(n - 2, -1, -1):
        if ratings[i] > ratings[i + 1]:
            out[i] = max(out[i], out[i + 1] + 1)
    return sum(out)


def _max_prod(nums):
    if not nums:
        return 0
    best = hi = lo = nums[0]
    for x in nums[1:]:
        cands = (x, hi * x, lo * x)
        hi, lo = max(cands), min(cands)
        best = max(best, hi)
    return best


def _unsorted_window(nums):
    s = sorted(nums)
    diff = [i for i in range(len(nums)) if nums[i] != s[i]]
    return diff[-1] - diff[0] + 1 if diff else 0


def _turbulent(nums):
    if not nums:
        return 0
    best = up = down = 1
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            up, down = down + 1, 1
        elif nums[i] < nums[i - 1]:
            down, up = up + 1, 1
        else:
            up = down = 1
        best = max(best, up, down)
    return best
