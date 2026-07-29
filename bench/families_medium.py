"""Medium tier: needs a data structure, a second pass, or a non-obvious invariant."""
from __future__ import annotations

from .core import (bits, fam, ints, matrix, pos_ints, problem, sentence,
                   sorted_ints, word, grid01, distinct_ints)


@fam("two_pointers", "medium", ["array", "two-pointers"])
def f_two_pointers():
    def two_sum_sorted(nums, target):
        i, j = 0, len(nums) - 1
        while i < j:
            s = nums[i] + nums[j]
            if s == target:
                return [i, j]
            if s < target:
                i += 1
            else:
                j -= 1
        return []

    def pair_with_diff(nums, k):
        s = set(nums)
        return sorted(x for x in s if x + k in s) if k else sorted(
            x for x in s if nums.count(x) > 1)

    def max_water(h):
        i, j, best = 0, len(h) - 1, 0
        while i < j:
            best = max(best, min(h[i], h[j]) * (j - i))
            if h[i] < h[j]:
                i += 1
            else:
                j -= 1
        return best

    specs = [
        ("Two Sum On Sorted Input",
         "Given a list `nums` sorted in non-decreasing order and an integer `target`, "
         "return the indices `[i, j]` with `i < j` of two elements summing to `target`. "
         "If several pairs work return the one with the smallest `i`. Return `[]` if "
         "none exists.",
         two_sum_sorted, lambda rng: (sorted_ints(rng, lo=-9, hi=9), rng.randint(-9, 9)),
         "def solve(nums, target):"),
        ("Pairs With Difference K",
         "Given a list `nums` and a non-negative integer `k`, return a sorted list of "
         "the distinct values `x` such that both `x` and `x + k` appear in `nums`. "
         "When `k` is 0, return the distinct values that appear at least twice.",
         pair_with_diff, lambda rng: (ints(rng, lo=-8, hi=8), rng.randint(0, 4)),
         "def solve(nums, k):"),
        ("Container With Most Water",
         "Given a list `height` of non-negative integers, pick two positions and return "
         "the largest area `min(height[i], height[j]) * (j - i)`. Return 0 if fewer "
         "than two positions exist.",
         lambda height: max_water(height), lambda rng: (pos_ints(rng, lo=0, hi=15),),
         "def solve(height):"),
        ("Move Zeros To End",
         "Given a list `nums`, return a list with every zero moved to the end while the "
         "relative order of the non-zero elements is preserved.",
         lambda nums: [x for x in nums if x != 0] + [0] * nums.count(0),
         lambda rng: (ints(rng, lo=-3, hi=3),), "def solve(nums):"),
        ("Remove Duplicates From Sorted",
         "Given a list `nums` sorted in non-decreasing order, return the list with "
         "duplicates removed, still sorted.",
         lambda nums: sorted(set(nums)), lambda rng: (sorted_ints(rng, lo=-6, hi=6),),
         "def solve(nums):"),
        ("Sort Colours",
         "Given a list `nums` containing only 0, 1 and 2, return it sorted in "
         "non-decreasing order.",
         lambda nums: sorted(nums),
         lambda rng: ([rng.randint(0, 2) for _ in range(rng.randint(0, 10))],),
         "def solve(nums):"),
        ("Valid Palindrome Ignoring Non-Alphanumeric",
         "Given a string `s`, return True if it reads the same forwards and backwards "
         "once non-alphanumeric characters are dropped and case is ignored.",
         lambda s: (lambda t: t == t[::-1])(
             "".join(c.lower() for c in s if c.isalnum())),
         lambda rng: (word(rng, 0, 10, "aA bB,1"),), "def solve(s):"),
        ("Reverse Only Vowels",
         "Given a string `s`, return it with the vowels reversed in place and every "
         "other character left alone. Vowels are aeiouAEIOU.",
         lambda s: _rev_vowels(s), lambda rng: (word(rng, 0, 10, "aeiobcdAE"),),
         "def solve(s):"),
        ("Merge Two Sorted Lists",
         "Given two lists `a` and `b`, each sorted in non-decreasing order, return a "
         "single sorted list containing all their elements.",
         lambda a, b: sorted(a + b),
         lambda rng: (sorted_ints(rng, lo=-9, hi=9), sorted_ints(rng, lo=-9, hi=9)),
         "def solve(a, b):"),
        ("Squares Of A Sorted List",
         "Given a list `nums` sorted in non-decreasing order, return a sorted list of "
         "the squares of its elements.",
         lambda nums: sorted(x * x for x in nums),
         lambda rng: (sorted_ints(rng, lo=-9, hi=9),), "def solve(nums):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _rev_vowels(s):
    v = [c for c in s if c in "aeiouAEIOU"][::-1]
    it = iter(v)
    return "".join(next(it) if c in "aeiouAEIOU" else c for c in s)


# --------------------------------------------------------------------------- #
@fam("hash_table", "medium", ["hash-table"])
def f_hash_table():
    def group_anagrams(words):
        groups = {}
        for w in words:
            groups.setdefault("".join(sorted(w)), []).append(w)
        return [sorted(g) for _, g in sorted(groups.items())]

    def top_k(nums, k):
        c = {}
        for x in nums:
            c[x] = c.get(x, 0) + 1
        return [v for v, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]

    def longest_consecutive(nums):
        s, best = set(nums), 0
        for x in s:
            if x - 1 not in s:
                y = x
                while y + 1 in s:
                    y += 1
                best = max(best, y - x + 1)
        return best

    def isomorphic(a, b):
        if len(a) != len(b):
            return False
        f, g = {}, {}
        for x, y in zip(a, b):
            if f.setdefault(x, y) != y or g.setdefault(y, x) != x:
                return False
        return True

    specs = [
        ("Group Anagrams",
         "Given a list of lower-case strings `words`, group them so that strings using "
         "the same letters with the same counts are together. Return a list of groups, "
         "each group sorted alphabetically, and the groups ordered by their sorted-letter "
         "key.", group_anagrams,
         lambda rng: ([word(rng, 1, 4, "abc") for _ in range(rng.randint(0, 7))],),
         "def solve(words):"),
        ("First Unique Character",
         "Given a string `s`, return the index of the first character that appears "
         "exactly once, or -1 if there is none.",
         lambda s: next((i for i, c in enumerate(s) if s.count(c) == 1), -1),
         lambda rng: (word(rng, 0, 10, "aabbcd"),), "def solve(s):"),
        ("Top K Frequent Values",
         "Given a list `nums` and an integer `k`, return the `k` most frequent values, "
         "most frequent first. Break ties by the smaller value.",
         top_k, lambda rng: (ints(rng, lo=-5, hi=5, min_n=1), rng.randint(1, 3)),
         "def solve(nums, k):"),
        ("Count Subarrays Summing To K",
         "Given a list `nums` and an integer `k`, return how many contiguous non-empty "
         "subarrays sum to exactly `k`.",
         lambda nums, k: sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)
                             if sum(nums[i:j]) == k),
         lambda rng: (ints(rng, lo=-4, hi=4, max_n=9), rng.randint(-4, 4)),
         "def solve(nums, k):"),
        ("Longest Consecutive Run",
         "Given a list `nums`, return the length of the longest run of consecutive "
         "integers that can be formed from its values, ignoring order and duplicates.",
         longest_consecutive, lambda rng: (ints(rng, lo=-8, hi=8),), "def solve(nums):"),
        ("Intersection Of Two Lists",
         "Given lists `a` and `b`, return a sorted list of the distinct values that "
         "appear in both.", lambda a, b: sorted(set(a) & set(b)),
         lambda rng: (ints(rng, lo=-6, hi=6), ints(rng, lo=-6, hi=6)), "def solve(a, b):"),
        ("Isomorphic Strings",
         "Given strings `a` and `b`, return True if the characters of `a` can be "
         "consistently replaced to produce `b`, with no two characters mapping to the "
         "same character.", isomorphic,
         lambda rng: _iso_pair(rng), "def solve(a, b):"),
        ("Ransom Note",
         "Given strings `note` and `pool`, return True if `note` can be built using the "
         "characters of `pool`, each character used at most as many times as it appears.",
         lambda note, pool: all(note.count(c) <= pool.count(c) for c in set(note)),
         lambda rng: (word(rng, 0, 5, "abc"), word(rng, 0, 8, "abc")),
         "def solve(note, pool):"),
        ("Majority Element",
         "Given a list `nums`, return the value appearing strictly more than half the "
         "time, or None if no value does.",
         lambda nums: next((x for x in set(nums) if nums.count(x) * 2 > len(nums)), None),
         lambda rng: (ints(rng, lo=-3, hi=3),), "def solve(nums):"),
        ("Two Sum Unsorted",
         "Given a list `nums` and an integer `target`, return the indices `[i, j]` with "
         "`i < j` of two elements summing to `target`, choosing the smallest `i` then "
         "the smallest `j`. Return `[]` if none exists.",
         lambda nums, target: next(
             ([i, j] for i in range(len(nums)) for j in range(i + 1, len(nums))
              if nums[i] + nums[j] == target), []),
         lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(-9, 9)),
         "def solve(nums, target):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


# --------------------------------------------------------------------------- #
@fam("sliding_window", "medium", ["sliding-window"])
def f_sliding_window():
    def longest_unique(s):
        best, start, last = 0, 0, {}
        for i, c in enumerate(s):
            if c in last and last[c] >= start:
                start = last[c] + 1
            last[c] = i
            best = max(best, i - start + 1)
        return best

    def min_subarray_len(nums, target):
        best, start, total = float("inf"), 0, 0
        for i, x in enumerate(nums):
            total += x
            while total >= target:
                best = min(best, i - start + 1)
                total -= nums[start]
                start += 1
        return 0 if best == float("inf") else best

    def at_most_k_distinct(s, k):
        best, start, count = 0, 0, {}
        for i, c in enumerate(s):
            count[c] = count.get(c, 0) + 1
            while len(count) > k:
                count[s[start]] -= 1
                if not count[s[start]]:
                    del count[s[start]]
                start += 1
            best = max(best, i - start + 1)
        return best

    specs = [
        ("Maximum Sum Of Size K",
         "Given a list `nums` and a positive integer `k`, return the largest sum of any "
         "contiguous subarray of length exactly `k`, or 0 if the list is shorter than `k`.",
         lambda nums, k: max((sum(nums[i:i + k]) for i in range(len(nums) - k + 1)),
                             default=0),
         lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(1, 4)), "def solve(nums, k):"),
        ("Longest Substring Without Repeats",
         "Given a string `s`, return the length of the longest substring containing no "
         "repeated character.", lambda s: longest_unique(s),
         lambda rng: (word(rng, 0, 12, "abcd"),), "def solve(s):"),
        ("Minimum Size Subarray Sum",
         "Given a list `nums` of positive integers and a positive integer `target`, "
         "return the length of the shortest contiguous subarray whose sum is at least "
         "`target`, or 0 if none exists.", min_subarray_len,
         lambda rng: (pos_ints(rng, lo=1, hi=9), rng.randint(1, 25)),
         "def solve(nums, target):"),
        ("Longest Substring With At Most K Distinct",
         "Given a string `s` and a non-negative integer `k`, return the length of the "
         "longest substring containing at most `k` distinct characters.",
         at_most_k_distinct, lambda rng: (word(rng, 0, 12, "abcd"), rng.randint(0, 3)),
         "def solve(s, k):"),
        ("Maximum Average Of Size K",
         "Given a list `nums` and a positive integer `k`, return the largest average of "
         "any contiguous subarray of length exactly `k`, rounded to six decimal places. "
         "Return 0 if the list is shorter than `k`.",
         lambda nums, k: round(max((sum(nums[i:i + k]) / k
                                    for i in range(len(nums) - k + 1)), default=0), 6),
         lambda rng: (ints(rng, lo=-9, hi=9, min_n=1), rng.randint(1, 3)),
         "def solve(nums, k):"),
        ("Count Anagram Occurrences",
         "Given strings `s` and `p`, return how many substrings of `s` with length "
         "`len(p)` are anagrams of `p`.",
         lambda s, p: sum(1 for i in range(len(s) - len(p) + 1)
                          if sorted(s[i:i + len(p)]) == sorted(p)) if p else 0,
         lambda rng: (word(rng, 0, 10, "abc"), word(rng, 1, 3, "abc")),
         "def solve(s, p):"),
        ("Longest Repeating Character Replacement",
         "Given a string `s` and an integer `k`, return the length of the longest "
         "substring that can be made of a single repeated character by changing at most "
         "`k` characters.", lambda s, k: _lrcr(s, k),
         lambda rng: (word(rng, 0, 10, "abc"), rng.randint(0, 3)), "def solve(s, k):"),
        ("Count Subarrays With Sum Below K",
         "Given a list `nums` of positive integers and an integer `k`, return how many "
         "non-empty contiguous subarrays have a sum strictly less than `k`.",
         lambda nums, k: sum(1 for i in range(len(nums))
                             for j in range(i + 1, len(nums) + 1) if sum(nums[i:j]) < k),
         lambda rng: (pos_ints(rng, lo=1, hi=8, max_n=9), rng.randint(1, 20)),
         "def solve(nums, k):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _lrcr(s, k):
    best = 0
    for c in set(s) or {""}:
        start, bad = 0, 0
        for i, ch in enumerate(s):
            if ch != c:
                bad += 1
            while bad > k:
                if s[start] != c:
                    bad -= 1
                start += 1
            best = max(best, i - start + 1)
    return best


# --------------------------------------------------------------------------- #
@fam("intervals", "medium", ["intervals", "sorting"])
def f_intervals():
    def merge(iv):
        out = []
        for s, e in sorted(iv):
            if out and s <= out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out

    def max_overlap(iv):
        pts = []
        for s, e in iv:
            pts.append((s, 1))
            pts.append((e, -1))
        pts.sort(key=lambda p: (p[0], p[1]))
        cur = best = 0
        for _, d in pts:
            cur += d
            best = max(best, cur)
        return best

    def erase_overlap(iv):
        if not iv:
            return 0
        iv = sorted(iv, key=lambda x: x[1])
        end, kept = iv[0][1], 1
        for s, e in iv[1:]:
            if s >= end:
                kept += 1
                end = e
        return len(iv) - kept

    specs = [
        ("Merge Overlapping Intervals",
         "Given a list of `[start, end]` intervals, merge every pair that overlaps or "
         "touches and return the merged intervals sorted by start.", merge),
        ("Total Covered Length",
         "Given a list of `[start, end]` intervals, return the total length of the "
         "number line they cover, counting overlaps once.",
         lambda iv: sum(e - s for s, e in merge(iv))),
        ("Maximum Concurrent Intervals",
         "Given a list of `[start, end]` intervals, return the largest number that "
         "overlap at any single point. An interval that ends where another begins does "
         "not overlap it.", max_overlap),
        ("Minimum Removals For Disjoint",
         "Given a list of `[start, end]` intervals, return the fewest intervals to "
         "remove so that none of the rest overlap. Touching endpoints are allowed.",
         erase_overlap),
        ("Count Non-Overlapping Kept",
         "Given a list of `[start, end]` intervals, return the largest number of "
         "pairwise non-overlapping intervals that can be kept. Touching is allowed.",
         lambda iv: len(iv) - erase_overlap(iv)),
        ("Gaps Between Intervals",
         "Given a list of `[start, end]` intervals, return the gaps between consecutive "
         "merged intervals as `[start, end]` pairs, sorted by start.",
         lambda iv: [[merge(iv)[i][1], merge(iv)[i + 1][0]]
                     for i in range(len(merge(iv)) - 1)]),
        ("Interval With Largest Span",
         "Given a list of `[start, end]` intervals, return the one with the largest "
         "`end - start`; break ties by the smaller start. Return `[]` if empty.",
         lambda iv: max(iv, key=lambda x: (x[1] - x[0], -x[0])) if iv else []),
        ("Point Covered Count",
         "Given a list of `[start, end]` intervals and an integer `p`, return how many "
         "intervals contain `p`, where an interval covers `start <= p < end`.",
         lambda iv, p: sum(1 for s, e in iv if s <= p < e)),
    ]
    for spec in specs:
        title, stmt, ref = spec
        takes_point = "and an integer `p`" in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (_intervals(rng), rng.randint(0, 12))) if takes_point
                    else (lambda rng: (_intervals(rng),))),
            signature="def solve(intervals, p):" if takes_point else "def solve(intervals):",
            edges=([([], 1), ([[0, 5]], 3)] if takes_point
                   else [([],), ([[0, 1]],), ([[0, 3], [1, 4]],), ([[0, 1], [1, 2]],)]),
        )


def _intervals(rng):
    out = []
    for _ in range(rng.randint(0, 5)):
        s = rng.randint(0, 10)
        out.append([s, s + rng.randint(0, 5)])
    return out


# --------------------------------------------------------------------------- #
@fam("stack", "medium", ["stack"])
def f_stack():
    def valid_parens(s):
        pairs = {")": "(", "]": "[", "}": "{"}
        st = []
        for c in s:
            if c in "([{":
                st.append(c)
            elif c in pairs:
                if not st or st.pop() != pairs[c]:
                    return False
        return not st

    def next_greater(nums):
        out, st = [-1] * len(nums), []
        for i, x in enumerate(nums):
            while st and nums[st[-1]] < x:
                out[st.pop()] = x
            st.append(i)
        return out

    def daily_temps(t):
        out, st = [0] * len(t), []
        for i, x in enumerate(t):
            while st and t[st[-1]] < x:
                j = st.pop()
                out[j] = i - j
            st.append(i)
        return out

    def eval_rpn(tokens):
        st = []
        for t in tokens:
            if t in "+-*/":
                b, a = st.pop(), st.pop()
                st.append(a + b if t == "+" else a - b if t == "-" else
                          a * b if t == "*" else int(a / b) if b else 0)
            else:
                st.append(int(t))
        return st[-1] if st else 0

    def remove_k_digits(s, k):
        st = []
        for c in s:
            while st and k and st[-1] > c:
                st.pop()
                k -= 1
            st.append(c)
        st = st[:len(st) - k] if k else st
        return str(int("".join(st))) if st and int("".join(st) or 0) else "0"

    def backspace_compare(a, b):
        def build(t):
            out = []
            for c in t:
                if c == "#":
                    if out:
                        out.pop()
                else:
                    out.append(c)
            return out
        return build(a) == build(b)

    specs = [
        ("Valid Bracket Sequence",
         "Given a string `s` of bracket characters, return True if every bracket is "
         "closed by the matching kind in the right order.", valid_parens,
         lambda rng: (word(rng, 0, 8, "()[]{}"),), "def solve(s):"),
        ("Next Greater Element",
         "Given a list `nums`, return a list where entry `i` is the first element to the "
         "right of `i` that is strictly larger, or -1 if there is none.", next_greater,
         lambda rng: (ints(rng, lo=-9, hi=9),), "def solve(nums):"),
        ("Days Until Warmer",
         "Given a list `temps`, return a list where entry `i` is how many positions "
         "ahead the next strictly warmer temperature is, or 0 if there is none.",
         daily_temps, lambda rng: (pos_ints(rng, lo=30, hi=45),), "def solve(temps):"),
        ("Evaluate Reverse Polish Notation",
         "Given a list `tokens` of integers-as-strings and the operators + - * /, "
         "evaluate the expression. Division truncates toward zero. Return 0 for an "
         "empty list.", eval_rpn, lambda rng: (_rpn(rng),), "def solve(tokens):"),
        ("Remove K Digits For Minimum",
         "Given a string `s` of digits and an integer `k`, remove exactly `k` digits so "
         "the remaining number is as small as possible. Return it as a string with no "
         "leading zeros, or \"0\" if nothing remains.", remove_k_digits,
         lambda rng: ("".join(rng.choice("0123456789") for _ in range(rng.randint(1, 7))),
                      rng.randint(0, 3)), "def solve(s, k):"),
        ("Backspace String Compare",
         "Given strings `a` and `b` where '#' means a backspace, return True if they "
         "are equal once the backspaces are applied.", backspace_compare,
         lambda rng: (word(rng, 0, 7, "ab#"), word(rng, 0, 7, "ab#")),
         "def solve(a, b):"),
        ("Longest Valid Parentheses Prefix",
         "Given a string `s` of '(' and ')', return the length of the longest prefix "
         "that is a balanced bracket sequence.",
         lambda s: _longest_balanced_prefix(s), lambda rng: (word(rng, 0, 10, "()"),),
         "def solve(s):"),
        ("Score Of Parentheses",
         "Given a balanced string `s` of '(' and ')', score it: \"()\" is 1, `AB` is "
         "the sum of the scores of `A` and `B`, and `(A)` is twice the score of `A`.",
         lambda s: _paren_score(s), lambda rng: (_balanced(rng),), "def solve(s):"),
        ("Remove Adjacent Duplicates",
         "Given a string `s`, repeatedly remove adjacent equal characters until none "
         "remain adjacent, and return the result.", lambda s: _remove_adj(s),
         lambda rng: (word(rng, 0, 10, "abc"),), "def solve(s):"),
        ("Simplify Unix Path",
         "Given an absolute Unix-style path `path`, return its canonical form: no "
         "trailing slash (unless root), no '.' components, and '..' removing the "
         "previous component.", lambda path: _simplify(path),
         lambda rng: (_path(rng),), "def solve(path):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _rpn(rng):
    toks = [str(rng.randint(1, 9))]
    for _ in range(rng.randint(0, 3)):
        toks.append(str(rng.randint(1, 9)))
        toks.append(rng.choice("+-*"))
    return toks


def _longest_balanced_prefix(s):
    depth, best = 0, 0
    for i, c in enumerate(s):
        depth += 1 if c == "(" else -1
        if depth < 0:
            break
        if depth == 0:
            best = i + 1
    return best


def _balanced(rng):
    n = rng.randint(1, 4)
    s = ""
    for _ in range(n):
        s = "(" + s + ")" if rng.random() < 0.5 else s + "()"
    return s


def _paren_score(s):
    st = [0]
    for c in s:
        if c == "(":
            st.append(0)
        else:
            v = st.pop()
            st[-1] += max(2 * v, 1)
    return st[0]


def _remove_adj(s):
    st = []
    for c in s:
        if st and st[-1] == c:
            st.pop()
        else:
            st.append(c)
    return "".join(st)


def _path(rng):
    parts = [rng.choice(["a", "b", "..", ".", ""]) for _ in range(rng.randint(0, 5))]
    return "/" + "/".join(parts)


def _simplify(path):
    out = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if out:
                out.pop()
        else:
            out.append(part)
    return "/" + "/".join(out)


# --------------------------------------------------------------------------- #
@fam("binary_search", "medium", ["binary-search"])
def f_binary_search():
    def search_rotated(nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[lo] <= nums[mid]:
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1
        return -1

    specs = [
        ("Search In Rotated Sorted List",
         "Given a list `nums` of distinct values, sorted ascending then rotated, and an "
         "integer `target`, return its index or -1.", search_rotated,
         lambda rng: (_rotated(rng), rng.randint(-9, 9)), "def solve(nums, target):"),
        ("Find Minimum In Rotated List",
         "Given a non-empty list `nums` of distinct values, sorted ascending then "
         "rotated, return the smallest value.", lambda nums: min(nums),
         lambda rng: (_rotated(rng, min_n=1),), "def solve(nums):"),
        ("First And Last Position",
         "Given a list `nums` sorted ascending and an integer `target`, return "
         "`[first, last]` indices of `target`, or `[-1, -1]` if absent.",
         lambda nums, target: [nums.index(target),
                               len(nums) - 1 - nums[::-1].index(target)]
         if target in nums else [-1, -1],
         lambda rng: (sorted_ints(rng, lo=-6, hi=6), rng.randint(-6, 6)),
         "def solve(nums, target):"),
        ("Insert Position",
         "Given a list `nums` sorted ascending and an integer `target`, return the index "
         "where `target` is, or where it would be inserted to keep the list sorted.",
         lambda nums, target: sum(1 for x in nums if x < target),
         lambda rng: (sorted_ints(rng, lo=-9, hi=9), rng.randint(-9, 9)),
         "def solve(nums, target):"),
        ("Integer Square Root",
         "Given a non-negative integer `n`, return the largest integer `r` with "
         "`r * r <= n`.", lambda n: int(n ** 0.5),
         lambda rng: (rng.randint(0, 10 ** 6),), "def solve(n):"),
        ("Find Peak Index",
         "Given a list `nums` where no two adjacent values are equal, return the index "
         "of any element strictly greater than both neighbours; ends count as having a "
         "single neighbour. Return the smallest such index, or -1 if empty.",
         lambda nums: next((i for i in range(len(nums))
                            if (i == 0 or nums[i] > nums[i - 1])
                            and (i == len(nums) - 1 or nums[i] > nums[i + 1])), -1),
         lambda rng: (_no_adjacent_equal(rng),), "def solve(nums):"),
        ("Minimum Eating Speed",
         "Given a list `piles` of positive integers and an integer `hours` at least "
         "`len(piles)`, return the smallest `k` such that "
         "`sum(ceil(p / k) for p in piles) <= hours`.",
         lambda piles, hours: _min_speed(piles, hours),
         lambda rng: (_piles(rng), 0), "def solve(piles, hours):"),
        ("Split Array Largest Sum",
         "Given a list `nums` of non-negative integers and an integer `k` at least 1, "
         "split it into `k` contiguous parts so the largest part sum is as small as "
         "possible, and return that sum.", lambda nums, k: _split_largest(nums, k),
         lambda rng: (pos_ints(rng, lo=0, hi=9, min_n=1, max_n=8), rng.randint(1, 3)),
         "def solve(nums, k):"),
        ("Single Element In Sorted Pairs",
         "Given a sorted list `nums` where every value appears twice except one, return "
         "the value appearing once.",
         lambda nums: next(x for x in set(nums) if nums.count(x) == 1),
         lambda rng: (_single_pairs(rng),), "def solve(nums):"),
        ("Count Values Below Target",
         "Given a list `nums` sorted ascending and an integer `target`, return how many "
         "values are strictly less than `target`.",
         lambda nums, target: sum(1 for x in nums if x < target),
         lambda rng: (sorted_ints(rng, lo=-9, hi=9), rng.randint(-9, 9)),
         "def solve(nums, target):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _rotated(rng, min_n=0):
    xs = sorted(distinct_ints(rng, min_n=max(1, min_n), max_n=9, lo=-9, hi=9))
    if not xs:
        return []
    k = rng.randrange(len(xs))
    return xs[k:] + xs[:k]


def _no_adjacent_equal(rng):
    xs = ints(rng, lo=-9, hi=9)
    out = []
    for x in xs:
        if not out or out[-1] != x:
            out.append(x)
    return out


def _piles(rng):
    return pos_ints(rng, lo=1, hi=12, min_n=1, max_n=5)


def _min_speed(piles, hours):
    hours = max(hours, len(piles))
    k = 1
    while True:
        if sum(-(-p // k) for p in piles) <= hours:
            return k
        k += 1


def _split_largest(nums, k):
    k = max(1, min(k, len(nums) or 1))

    def ok(cap):
        parts, cur = 1, 0
        for x in nums:
            if x > cap:
                return False
            if cur + x > cap:
                parts += 1
                cur = 0
            cur += x
        return parts <= k
    lo, hi = (max(nums) if nums else 0), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def _single_pairs(rng):
    vals = distinct_ints(rng, min_n=1, max_n=5, lo=-9, hi=9)
    single = vals[0]
    out = []
    for v in vals[1:]:
        out += [v, v]
    out.append(single)
    return sorted(out)


# --------------------------------------------------------------------------- #
@fam("dp_1d", "medium", ["dynamic-programming"])
def f_dp_1d():
    def coin_change(coins, amount):
        INF = float("inf")
        dp = [0] + [INF] * amount
        for a in range(1, amount + 1):
            for c in coins:
                if c <= a:
                    dp[a] = min(dp[a], dp[a - c] + 1)
        return -1 if dp[amount] == INF else dp[amount]

    def lis(nums):
        best = 0
        dp = [1] * len(nums)
        for i in range(len(nums)):
            for j in range(i):
                if nums[j] < nums[i]:
                    dp[i] = max(dp[i], dp[j] + 1)
            best = max(best, dp[i])
        return best

    def word_break(s, words):
        dp = [True] + [False] * len(s)
        for i in range(1, len(s) + 1):
            dp[i] = any(dp[j] and s[j:i] in words for j in range(i))
        return dp[len(s)]

    specs = [
        ("Climbing Stairs",
         "Given a non-negative integer `n`, return how many distinct ways there are to "
         "climb `n` steps taking 1 or 2 steps at a time.",
         lambda n: _climb(n), lambda rng: (rng.randint(0, 25),), "def solve(n):"),
        ("House Robber",
         "Given a list `nums` of non-negative values, return the largest sum obtainable "
         "with no two chosen elements adjacent.", lambda nums: _rob(nums),
         lambda rng: (pos_ints(rng, lo=0, hi=20),), "def solve(nums):"),
        ("Coin Change Minimum Coins",
         "Given a list `coins` of positive denominations and a non-negative `amount`, "
         "return the fewest coins summing to `amount`, or -1 if impossible.",
         coin_change, lambda rng: (sorted(set(pos_ints(rng, lo=1, hi=9, min_n=1,
                                                       max_n=3))), rng.randint(0, 20)),
         "def solve(coins, amount):"),
        ("Maximum Subarray Sum",
         "Given a list `nums`, return the largest sum of any non-empty contiguous "
         "subarray, or 0 if the list is empty.", lambda nums: _max_sub(nums),
         lambda rng: (ints(rng, lo=-9, hi=9),), "def solve(nums):"),
        ("Longest Increasing Subsequence",
         "Given a list `nums`, return the length of its longest strictly increasing "
         "subsequence.", lis, lambda rng: (ints(rng, lo=-9, hi=9),), "def solve(nums):"),
        ("Decode Ways",
         "A string of digits maps to letters with 1->A through 26->Z. Given a string "
         "`s`, return how many ways it decodes. A part may not have a leading zero.",
         lambda s: _decode(s),
         lambda rng: ("".join(rng.choice("0123") for _ in range(rng.randint(0, 6))),),
         "def solve(s):"),
        ("Word Break",
         "Given a string `s` and a list `words`, return True if `s` can be split into a "
         "sequence of entries from `words`, each usable any number of times.",
         lambda s, words: word_break(s, set(words)),
         lambda rng: (word(rng, 0, 8, "ab"),
                      [word(rng, 1, 3, "ab") for _ in range(rng.randint(1, 4))]),
         "def solve(s, words):"),
        ("Jump Game Reachable",
         "Given a list `nums` where `nums[i]` is the furthest you may jump from index "
         "`i`, return True if the last index is reachable from index 0.",
         lambda nums: _can_jump(nums),
         lambda rng: (pos_ints(rng, lo=0, hi=4, min_n=1),), "def solve(nums):"),
        ("Minimum Cost Climbing Stairs",
         "Given a list `cost`, you may start at index 0 or 1 and step 1 or 2 places. "
         "Return the least total cost to step beyond the last index.",
         lambda cost: _min_cost_climb(cost),
         lambda rng: (pos_ints(rng, lo=0, hi=15, min_n=2),), "def solve(cost):"),
        ("Count Ways To Make Amount",
         "Given a list `coins` of distinct positive denominations and a non-negative "
         "`amount`, return how many distinct multisets of coins sum to `amount`.",
         lambda coins, amount: _count_ways(coins, amount),
         lambda rng: (sorted(set(pos_ints(rng, lo=1, hi=6, min_n=1, max_n=3))),
                      rng.randint(0, 15)), "def solve(coins, amount):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _climb(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _rob(nums):
    prev = cur = 0
    for x in nums:
        prev, cur = cur, max(cur, prev + x)
    return cur


def _max_sub(nums):
    if not nums:
        return 0
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def _decode(s):
    if not s:
        return 1
    dp = [0] * (len(s) + 1)
    dp[0] = 1
    for i in range(1, len(s) + 1):
        if s[i - 1] != "0":
            dp[i] += dp[i - 1]
        if i > 1 and 10 <= int(s[i - 2:i]) <= 26:
            dp[i] += dp[i - 2]
    return dp[len(s)]


def _can_jump(nums):
    reach = 0
    for i, x in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + x)
    return True


def _min_cost_climb(cost):
    a = b = 0
    for x in cost:
        a, b = b, min(a, b) + x
    return min(a, b)


def _count_ways(coins, amount):
    dp = [1] + [0] * amount
    for c in coins:
        for a in range(c, amount + 1):
            dp[a] += dp[a - c]
    return dp[amount]


# --------------------------------------------------------------------------- #
@fam("matrix_medium", "medium", ["matrix"])
def f_matrix_medium():
    def spiral(g):
        out = []
        g = [row[:] for row in g]
        while g:
            out += g.pop(0)
            g = [list(r) for r in zip(*g)][::-1] if g else []
        return out

    def rotate(g):
        return [list(r) for r in zip(*g[::-1])]

    def set_zeros(g):
        rows = {i for i, r in enumerate(g) for x in r if x == 0}
        cols = {j for r in g for j, x in enumerate(r) if x == 0}
        return [[0 if i in rows or j in cols else x for j, x in enumerate(r)]
                for i, r in enumerate(g)]

    specs = [
        ("Spiral Order", "Given a rectangular matrix `grid`, return its elements in "
         "clockwise spiral order starting at the top-left.", spiral, matrix),
        ("Rotate Image Clockwise", "Given an `n x n` matrix `grid`, return it rotated "
         "90 degrees clockwise.", rotate, lambda rng: _sq(rng)),
        ("Set Matrix Zeros", "Given a matrix `grid`, return it with every row and "
         "column that contained a zero set entirely to zero.", set_zeros, matrix),
        ("Pascal Triangle Rows", "Given a non-negative integer `n`, return the first "
         "`n` rows of Pascal's triangle.", lambda n: _pascal(n), None),
        ("Search Sorted Matrix", "Given a matrix `grid` whose rows are sorted ascending "
         "and whose first element of each row exceeds the last of the previous, and an "
         "integer `target`, return True if `target` appears.", None, None),
        ("Count Negatives", "Given a matrix `grid`, return how many of its elements are "
         "negative.", lambda grid: sum(1 for r in grid for x in r if x < 0), matrix),
        ("Reshape Matrix", "Given a matrix `grid` and integers `r` and `c`, return the "
         "elements reshaped into `r x c` in row-major order, or the original matrix if "
         "the sizes do not match.", None, None),
        ("Matrix Diagonal Order", "Given a matrix `grid`, return its elements grouped by "
         "anti-diagonal: all cells with `i + j == 0`, then 1, and so on.", None, None),
    ]
    yield problem(title="Spiral Order", statement=specs[0][1], ref=spiral,
                  inputs=lambda rng: (matrix(rng),), signature="def solve(grid):",
                  edges=[([[1]],), ([[1, 2], [3, 4]],), ([[1, 2, 3]],)])
    yield problem(title="Rotate Image Clockwise", statement=specs[1][1], ref=rotate,
                  inputs=lambda rng: (_sq(rng),), signature="def solve(grid):",
                  edges=[([[1]],), ([[1, 2], [3, 4]],)])
    yield problem(title="Set Matrix Zeros", statement=specs[2][1], ref=set_zeros,
                  inputs=lambda rng: (matrix(rng, lo=0, hi=3),),
                  signature="def solve(grid):",
                  edges=[([[1]],), ([[0]],), ([[1, 0], [1, 1]],)])
    yield problem(title="Pascal Triangle Rows", statement=specs[3][1],
                  ref=lambda n: _pascal(n), inputs=lambda rng: (rng.randint(0, 8),),
                  signature="def solve(n):", edges=[(0,), (1,), (5,)])
    yield problem(
        title="Search Sorted Matrix", statement=specs[4][1],
        ref=lambda grid, target: any(target in r for r in grid),
        inputs=lambda rng: (_row_sorted(rng), rng.randint(0, 30)),
        signature="def solve(grid, target):",
        edges=[([[1]], 1), ([[1]], 2), ([[1, 3], [5, 7]], 5)])
    yield problem(
        title="Count Negative Elements", statement=specs[5][1],
        ref=lambda grid: sum(1 for r in grid for x in r if x < 0),
        inputs=lambda rng: (matrix(rng),), signature="def solve(grid):",
        edges=[([[1]],), ([[-1]],), ([[-1, 2], [3, -4]],)])
    yield problem(
        title="Reshape Matrix", statement=specs[6][1], ref=_reshape,
        inputs=lambda rng: (matrix(rng), rng.randint(1, 4), rng.randint(1, 4)),
        signature="def solve(grid, r, c):",
        edges=[([[1, 2], [3, 4]], 1, 4), ([[1, 2], [3, 4]], 4, 1),
               ([[1, 2], [3, 4]], 3, 3)])
    yield problem(
        title="Anti-Diagonal Groups", statement=specs[7][1], ref=_antidiag,
        inputs=lambda rng: (matrix(rng),), signature="def solve(grid):",
        edges=[([[1]],), ([[1, 2], [3, 4]],)])


def _sq(rng):
    from .core import square
    return square(rng)


def _row_sorted(rng):
    n = rng.randint(1, 3)
    vals = sorted(distinct_ints(rng, n=n * rng.randint(1, 3), lo=0, hi=30))
    cols = max(1, len(vals) // n)
    return [vals[i:i + cols] for i in range(0, len(vals), cols)]


def _pascal(n):
    rows = []
    for i in range(n):
        row = [1] * (i + 1)
        for j in range(1, i):
            row[j] = rows[i - 1][j - 1] + rows[i - 1][j]
        rows.append(row)
    return rows


def _reshape(grid, r, c):
    flat = [x for row in grid for x in row]
    if len(flat) != r * c:
        return grid
    return [flat[i * c:(i + 1) * c] for i in range(r)]


def _antidiag(grid):
    groups = {}
    for i, row in enumerate(grid):
        for j, x in enumerate(row):
            groups.setdefault(i + j, []).append(x)
    return [groups[k] for k in sorted(groups)]


# --------------------------------------------------------------------------- #
@fam("string_medium", "medium", ["string"])
def f_string_medium():
    specs = [
        ("Longest Palindromic Substring Length",
         "Given a string `s`, return the length of its longest palindromic substring.",
         lambda s: max((j - i for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                        if s[i:j] == s[i:j][::-1]), default=0),
         lambda rng: (word(rng, 0, 10, "aab"),)),
        ("Run Length Encode",
         "Given a string `s`, return its run-length encoding: each run becomes the "
         "character followed by its length only when the run is longer than one.",
         lambda s: _rle(s), lambda rng: (word(rng, 0, 10, "aab"),)),
        ("Count And Say",
         "Starting from \"1\", each term describes the previous one by reading off runs "
         "as count then digit. Given `n` at least 1, return the `n`-th term.",
         lambda n: _count_and_say(n), lambda rng: (rng.randint(1, 8),)),
        ("Add Binary Strings",
         "Given binary strings `a` and `b`, return their sum as a binary string.",
         lambda a, b: bin(int(a or "0", 2) + int(b or "0", 2))[2:],
         lambda rng: (bits(rng), bits(rng))),
        ("Multiply Digit Strings",
         "Given non-negative integers as strings `a` and `b`, return their product as a "
         "string.", lambda a, b: str(int(a or "0") * int(b or "0")),
         lambda rng: ("".join(rng.choice("0123456789") for _ in range(rng.randint(1, 4))),
                      "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 4))))),
        ("Roman To Integer",
         "Given a valid Roman numeral string `s` using I V X L C D M, return its value.",
         lambda s: _roman_to_int(s), lambda rng: (_roman(rng),)),
        ("Integer To Roman",
         "Given an integer `n` between 1 and 3999, return its Roman numeral.",
         lambda n: _int_to_roman(n), lambda rng: (rng.randint(1, 3999),)),
        ("Compare Version Numbers",
         "Given dotted version strings `a` and `b`, return -1, 0 or 1 according to "
         "whether `a` is less than, equal to, or greater than `b`. Missing components "
         "count as zero.", lambda a, b: _cmp_version(a, b),
         lambda rng: (_version(rng), _version(rng))),
        ("Reverse Words With Single Spaces",
         "Given a string `s`, return its whitespace-separated words in reverse order, "
         "joined by single spaces, with no leading or trailing space.",
         lambda s: " ".join(reversed(s.split())), lambda rng: (sentence(rng, 0, 6),)),
        ("Longest Common Prefix",
         "Given a list of strings `words`, return the longest string that is a prefix "
         "of every one of them, or an empty string.",
         lambda words: _lcp(words),
         lambda rng: ([word(rng, 0, 5, "ab") for _ in range(rng.randint(0, 5))],)),
    ]
    sigs = {"Add Binary Strings": "def solve(a, b):",
            "Multiply Digit Strings": "def solve(a, b):",
            "Compare Version Numbers": "def solve(a, b):",
            "Count And Say": "def solve(n):",
            "Integer To Roman": "def solve(n):",
            "Longest Common Prefix": "def solve(words):"}
    for title, stmt, ref, inp in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp,
                      signature=sigs.get(title, "def solve(s):"))


def _rle(s):
    if not s:
        return ""
    out, prev, n = [], s[0], 1
    for c in s[1:] + "\0":
        if c == prev:
            n += 1
        else:
            out.append(prev if n == 1 else prev + str(n))
            prev, n = c, 1
    return "".join(out)


def _count_and_say(n):
    s = "1"
    for _ in range(n - 1):
        out, prev, k = [], s[0], 1
        for c in s[1:] + "\0":
            if c == prev:
                k += 1
            else:
                out.append(str(k) + prev)
                prev, k = c, 1
        s = "".join(out)
    return s


ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
         (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _int_to_roman(n):
    out = []
    for v, sym in ROMAN:
        while n >= v:
            out.append(sym)
            n -= v
    return "".join(out)


def _roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, c in enumerate(s):
        if i + 1 < len(s) and vals[c] < vals[s[i + 1]]:
            total -= vals[c]
        else:
            total += vals[c]
    return total


def _roman(rng):
    return _int_to_roman(rng.randint(1, 500))


def _version(rng):
    return ".".join(str(rng.randint(0, 12)) for _ in range(rng.randint(1, 3)))


def _cmp_version(a, b):
    pa = [int(x) for x in a.split(".")]
    pb = [int(x) for x in b.split(".")]
    n = max(len(pa), len(pb))
    pa += [0] * (n - len(pa))
    pb += [0] * (n - len(pb))
    return (pa > pb) - (pa < pb)


def _lcp(words):
    if not words:
        return ""
    out = ""
    for chars in zip(*words):
        if len(set(chars)) != 1:
            break
        out += chars[0]
    return out


# --------------------------------------------------------------------------- #
@fam("bit_manipulation", "medium", ["bit-manipulation"])
def f_bits():
    specs = [
        ("Single Number", "Given a list `nums` where every value appears twice except "
         "one, return the value appearing once.",
         lambda nums: next(x for x in set(nums) if nums.count(x) == 1),
         lambda rng: (_pairs_plus_one(rng),), "def solve(nums):"),
        ("Counting Bits", "Given a non-negative integer `n`, return a list where entry "
         "`i` is the number of set bits in `i`, for `i` from 0 to `n`.",
         lambda n: [bin(i).count("1") for i in range(n + 1)],
         lambda rng: (rng.randint(0, 40),), "def solve(n):"),
        ("Hamming Distance", "Given non-negative integers `a` and `b`, return how many "
         "bit positions differ.", lambda a, b: bin(a ^ b).count("1"),
         lambda rng: (rng.randint(0, 999), rng.randint(0, 999)), "def solve(a, b):"),
        ("Count Set Bits", "Given a non-negative integer `n`, return how many bits are "
         "set in its binary representation.", lambda n: bin(n).count("1"),
         lambda rng: (rng.randint(0, 10 ** 5),), "def solve(n):"),
        ("Reverse Bits In Byte", "Given an integer `n` from 0 to 255, return the value "
         "obtained by reversing its eight bits.",
         lambda n: int(format(n, "08b")[::-1], 2), lambda rng: (rng.randint(0, 255),),
         "def solve(n):"),
        ("Missing Number By XOR", "Given a list `nums` holding all but one of the "
         "integers from 0 to len(nums), return the missing one.",
         lambda nums: _missing_xor(nums), lambda rng: (_missing_case_m(rng),),
         "def solve(nums):"),
        ("Is Power Of Four", "Given an integer `n`, return True if it is a power of "
         "four.", lambda n: n > 0 and n & (n - 1) == 0 and (n - 1) % 3 == 0,
         # powers of four are needles in randint(0, 300) -- draw them deliberately
         lambda rng: (rng.choice([1, 4, 16, 64, 256, 2, 8, 32, rng.randint(0, 300)]),),
         "def solve(n):"),
        ("Bitwise AND Of Range", "Given non-negative integers `a` and `b` with "
         "`a <= b`, return the bitwise AND of every integer in `[a, b]`.",
         lambda a, b: _range_and(a, b),
         lambda rng: tuple(sorted((rng.randint(0, 60), rng.randint(0, 60)))),
         "def solve(a, b):"),
        ("Swap Odd And Even Bits", "Given a non-negative integer `n` below 256, return "
         "the value with each even-indexed bit swapped with its odd-indexed neighbour.",
         lambda n: ((n & 0xAA) >> 1) | ((n & 0x55) << 1),
         lambda rng: (rng.randint(0, 255),), "def solve(n):"),
        ("XOR Of Range", "Given a non-negative integer `n`, return the XOR of every "
         "integer from 0 to `n` inclusive.",
         lambda n: _xor_upto(n), lambda rng: (rng.randint(0, 200),), "def solve(n):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _pairs_plus_one(rng):
    vals = distinct_ints(rng, min_n=1, max_n=5, lo=-9, hi=9)
    out = [vals[0]]
    for v in vals[1:]:
        out += [v, v]
    rng.shuffle(out)
    return out


def _missing_case_m(rng):
    n = rng.randint(1, 9)
    pool = list(range(n + 1))
    pool.pop(rng.randrange(len(pool)))
    rng.shuffle(pool)
    return pool


def _missing_xor(nums):
    x = len(nums)
    for i, v in enumerate(nums):
        x ^= i ^ v
    return x


def _range_and(a, b):
    shift = 0
    while a < b:
        a, b, shift = a >> 1, b >> 1, shift + 1
    return a << shift


def _xor_upto(n):
    return [n, 1, n + 1, 0][n % 4]


# --------------------------------------------------------------------------- #
@fam("math_medium", "medium", ["math"])
def f_math_medium():
    specs = [
        ("Power Function", "Given an integer `base` and a non-negative integer `exp`, "
         "return `base ** exp`.", lambda base, exp: base ** exp,
         lambda rng: (rng.randint(-5, 5), rng.randint(0, 8)), "def solve(base, exp):"),
        ("Happy Number", "Repeatedly replace `n` by the sum of the squares of its "
         "digits. Return True if this reaches 1.", lambda n: _happy(n),
         lambda rng: (rng.randint(1, 200),), "def solve(n):"),
        ("Trailing Zeros In Factorial", "Given a non-negative integer `n`, return how "
         "many trailing zeros `n!` has.", lambda n: _trailing(n),
         lambda rng: (rng.randint(0, 200),), "def solve(n):"),
        ("Excel Column Title", "Given a positive integer `n`, return the spreadsheet "
         "column name: 1 is A, 26 is Z, 27 is AA.", lambda n: _excel(n),
         lambda rng: (rng.randint(1, 1000),), "def solve(n):"),
        ("Excel Column Number", "Given a spreadsheet column name `s`, return its "
         "1-based number.",
         lambda s: sum((ord(c) - 64) * 26 ** i for i, c in enumerate(reversed(s))),
         lambda rng: (_col(rng),), "def solve(s):"),
        ("Count Primes Below N", "Given a non-negative integer `n`, return how many "
         "primes are strictly below `n`.", lambda n: _count_primes(n),
         lambda rng: (rng.randint(0, 300),), "def solve(n):"),
        ("Perfect Number", "Given an integer `n`, return True if it equals the sum of "
         "its positive divisors below itself.",
         lambda n: n > 1 and sum(d for d in range(1, n) if n % d == 0) == n,
         lambda rng: (rng.choice([6, 28, 496, 12, 27, 100, rng.randint(1, 600)]),),
         "def solve(n):"),
        ("Integer Break Product", "Given an integer `n` at least 2, split it into at "
         "least two positive integers summing to `n` and return the largest possible "
         "product.", lambda n: _int_break(n), lambda rng: (rng.randint(2, 20),),
         "def solve(n):"),
        ("Base Conversion", "Given a non-negative integer `n` and a base `b` from 2 to "
         "16, return `n` written in base `b` using lower-case digits.",
         lambda n, b: _to_base(n, b),
         lambda rng: (rng.randint(0, 5000), rng.randint(2, 16)), "def solve(n, b):"),
        ("Sum Of Digits Until Single", "Given a non-negative integer `n`, repeatedly "
         "replace it by the sum of its digits until one digit remains, and return it.",
         lambda n: 0 if n == 0 else 1 + (n - 1) % 9,
         lambda rng: (rng.randint(0, 10 ** 6),), "def solve(n):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _happy(n):
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = sum(int(c) ** 2 for c in str(n))
    return n == 1


def _trailing(n):
    c, p = 0, 5
    while p <= n:
        c += n // p
        p *= 5
    return c


def _excel(n):
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def _col(rng):
    return _excel(rng.randint(1, 1000))


def _count_primes(n):
    if n < 3:
        return 0
    sieve = [True] * n
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n, i):
                sieve[j] = False
    return sum(sieve)


def _int_break(n):
    best = 0
    for i in range(1, n):
        best = max(best, i * (n - i), i * _int_break(n - i) if n - i > 1 else 0)
    return best


def _to_base(n, b):
    digits = "0123456789abcdef"
    if n == 0:
        return "0"
    out = ""
    while n:
        n, r = divmod(n, b)
        out = digits[r] + out
    return out


# --------------------------------------------------------------------------- #
@fam("prefix_sum", "medium", ["prefix-sum", "array"])
def f_prefix_sum():
    specs = [
        ("Product Except Self", "Given a list `nums`, return a list where entry `i` is "
         "the product of every element except `nums[i]`.",
         lambda nums: [_prod(nums[:i] + nums[i + 1:]) for i in range(len(nums))],
         lambda rng: (ints(rng, lo=-4, hi=4, max_n=7),), "def solve(nums):"),
        ("Pivot Index", "Given a list `nums`, return the smallest index where the sum "
         "to its left equals the sum to its right, or -1.",
         lambda nums: next((i for i in range(len(nums))
                            if sum(nums[:i]) == sum(nums[i + 1:])), -1),
         lambda rng: (ints(rng, lo=-4, hi=4),), "def solve(nums):"),
        ("Range Sum Queries", "Given a list `nums` and a list of `[i, j]` query pairs, "
         "return a list of the sums `nums[i..j]` inclusive.",
         lambda nums, queries: [sum(nums[i:j + 1]) for i, j in queries],
         lambda rng: (lambda xs: (xs, _queries(rng, len(xs))))(ints(rng, min_n=1, max_n=8)),
         "def solve(nums, queries):"),
        ("Count Subarrays Divisible By K", "Given a list `nums` and a positive integer "
         "`k`, return how many non-empty contiguous subarrays have a sum divisible by "
         "`k`.",
         lambda nums, k: sum(1 for i in range(len(nums))
                             for j in range(i + 1, len(nums) + 1)
                             if sum(nums[i:j]) % k == 0),
         lambda rng: (ints(rng, lo=-5, hi=5, max_n=8), rng.randint(1, 5)),
         "def solve(nums, k):"),
        ("Maximum Circular Subarray Sum", "Given a list `nums`, return the largest sum "
         "of a non-empty subarray that may wrap around the end. Return 0 if empty.",
         lambda nums: _circ_max(nums), lambda rng: (ints(rng, lo=-8, hi=8, max_n=8),),
         "def solve(nums):"),
        ("Equilibrium Count", "Given a list `nums`, return how many indices have equal "
         "sums to their left and right.",
         lambda nums: sum(1 for i in range(len(nums))
                          if sum(nums[:i]) == sum(nums[i + 1:])),
         lambda rng: (ints(rng, lo=-3, hi=3),), "def solve(nums):"),
        ("Prefix Sums", "Given a list `nums`, return a list of length `len(nums) + 1` "
         "where entry `i` is the sum of the first `i` elements.",
         lambda nums: [sum(nums[:i]) for i in range(len(nums) + 1)],
         lambda rng: (ints(rng, lo=-9, hi=9),), "def solve(nums):"),
        ("Subarray Sum Exists", "Given a list `nums` and an integer `target`, return "
         "True if some non-empty contiguous subarray sums to `target`.",
         lambda nums, target: any(sum(nums[i:j]) == target for i in range(len(nums))
                                  for j in range(i + 1, len(nums) + 1)),
         lambda rng: (ints(rng, lo=-5, hi=5, max_n=8), rng.randint(-8, 8)),
         "def solve(nums, target):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _prod(xs):
    out = 1
    for x in xs:
        out *= x
    return out


def _queries(rng, n):
    out = []
    for _ in range(rng.randint(0, 4)):
        i = rng.randrange(n)
        j = rng.randrange(i, n)
        out.append([i, j])
    return out


def _circ_max(nums):
    if not nums:
        return 0
    best = float("-inf")
    n = len(nums)
    for i in range(n):
        total = 0
        for L in range(1, n + 1):
            total += nums[(i + L - 1) % n]
            best = max(best, total)
    return best


# --------------------------------------------------------------------------- #
@fam("sorting_impl", "medium", ["sorting"])
def f_sorting_impl():
    specs = [
        ("Sort By Frequency Then Value", "Given a list `nums`, return it sorted by "
         "descending frequency, breaking ties by ascending value.",
         lambda nums: sorted(nums, key=lambda x: (-nums.count(x), x))),
        ("Sort By Absolute Value", "Given a list `nums`, return it sorted by absolute "
         "value, breaking ties by putting the negative first.",
         lambda nums: sorted(nums, key=lambda x: (abs(x), x))),
        ("Sort Even Before Odd", "Given a list `nums`, return the even values in "
         "ascending order followed by the odd values in ascending order.",
         lambda nums: sorted(x for x in nums if x % 2 == 0)
         + sorted(x for x in nums if x % 2)),
        ("Sort By Digit Sum", "Given a list of non-negative integers `nums`, return it "
         "sorted by digit sum, breaking ties by ascending value.",
         lambda nums: sorted(nums, key=lambda x: (sum(int(c) for c in str(x)), x))),
        ("K Closest To Zero", "Given a list `nums` and an integer `k`, return the `k` "
         "values closest to zero, sorted ascending. Ties prefer the smaller value.",
         lambda nums, k: sorted(sorted(nums, key=lambda x: (abs(x), x))[:k])),
        ("Kth Smallest Value", "Given a list `nums` and a 1-based integer `k`, return "
         "the `k`-th smallest value, or None if `k` is out of range.",
         lambda nums, k: sorted(nums)[k - 1] if 1 <= k <= len(nums) else None),
        ("Largest Concatenated Number", "Given a list of non-negative integers `nums`, "
         "order them so their concatenation is the largest possible, and return it as "
         "a string. Return \"0\" if the result would be all zeros.",
         lambda nums: _largest_concat(nums)),
    ]
    for spec in specs:
        title, stmt, ref = spec
        takes_k = "`k`" in stmt
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(1, 4))) if takes_k
                    else (lambda rng: (pos_ints(rng, lo=0, hi=40) if "non-negative" in stmt
                                       else ints(rng, lo=-9, hi=9),))),
            signature="def solve(nums, k):" if takes_k else "def solve(nums):",
        )


def _largest_concat(nums):
    import functools
    if not nums:
        return "0"
    strs = [str(x) for x in nums]
    strs.sort(key=functools.cmp_to_key(
        lambda a, b: (a + b < b + a) - (a + b > b + a)))
    out = "".join(strs)
    return "0" if out.lstrip("0") == "" else out.lstrip("0")


# --------------------------------------------------------------------------- #
@fam("graph_basic", "medium", ["graph", "bfs"])
def f_graph_basic():
    def components(n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        return len({find(i) for i in range(n)})

    def bfs_dist(n, edges, src):
        adj = {i: [] for i in range(n)}
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        dist = [-1] * n
        if not (0 <= src < n):
            return dist
        dist[src] = 0
        queue = [src]
        while queue:
            cur = queue.pop(0)
            for nxt in adj[cur]:
                if dist[nxt] == -1:
                    dist[nxt] = dist[cur] + 1
                    queue.append(nxt)
        return dist

    def has_cycle(n, edges):
        return components(n, edges) + len(edges) != n

    def is_bipartite(n, edges):
        adj = {i: [] for i in range(n)}
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        colour = {}
        for s in range(n):
            if s in colour:
                continue
            colour[s] = 0
            stack = [s]
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if v not in colour:
                        colour[v] = 1 - colour[u]
                        stack.append(v)
                    elif colour[v] == colour[u]:
                        return False
        return True

    specs = [
        ("Count Connected Components", "Given `n` nodes numbered 0 to n-1 and a list of "
         "undirected `edges`, return how many connected components there are.",
         components),
        ("Shortest Distances From Source", "Given `n` nodes, a list of undirected "
         "`edges` and a start node `src`, return a list of the fewest edges from `src` "
         "to each node, using -1 for unreachable nodes.", None),
        ("Graph Has Cycle", "Given `n` nodes and a list of undirected `edges` with no "
         "repeated edge, return True if the graph contains a cycle.", has_cycle),
        ("Is Bipartite", "Given `n` nodes and a list of undirected `edges`, return True "
         "if the nodes can be two-coloured so no edge joins same-coloured nodes.",
         is_bipartite),
        ("Largest Component Size", "Given `n` nodes and undirected `edges`, return the "
         "number of nodes in the largest connected component, or 0 if `n` is 0.", None),
        ("Is Connected Tree", "Given `n` nodes and undirected `edges`, return True if "
         "the graph is a single tree: connected and with no cycle.", None),
        ("Count Isolated Nodes", "Given `n` nodes and undirected `edges`, return how "
         "many nodes have no edges at all.", None),
        ("Degree Sequence", "Given `n` nodes and undirected `edges`, return a list of "
         "each node's degree, indexed by node.", None),
    ]
    yield problem(title=specs[0][0], statement=specs[0][1], ref=components,
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(1, []), (2, []), (3, [[0, 1]])])
    yield problem(title=specs[1][0], statement=specs[1][1], ref=bfs_dist,
                  inputs=lambda rng: _graph(rng) + (0,),
                  signature="def solve(n, edges, src):",
                  edges=[(1, [], 0), (3, [[0, 1]], 0)])
    yield problem(title=specs[2][0], statement=specs[2][1], ref=has_cycle,
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(1, []), (3, [[0, 1], [1, 2], [2, 0]])])
    yield problem(title=specs[3][0], statement=specs[3][1], ref=is_bipartite,
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(1, []), (3, [[0, 1], [1, 2], [2, 0]])])
    yield problem(title=specs[4][0], statement=specs[4][1],
                  ref=lambda n, edges: _largest_comp(n, edges),
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(0, []), (3, [[0, 1]])])
    yield problem(title=specs[5][0], statement=specs[5][1],
                  ref=lambda n, edges: components(n, edges) == 1 and len(edges) == n - 1,
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(1, []), (2, [[0, 1]]), (3, [[0, 1]])])
    yield problem(title=specs[6][0], statement=specs[6][1],
                  ref=lambda n, edges: sum(
                      1 for i in range(n)
                      if not any(i in e for e in edges)),
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(3, []), (3, [[0, 1]])])
    yield problem(title=specs[7][0], statement=specs[7][1],
                  ref=lambda n, edges: [sum(e.count(i) for e in edges) for i in range(n)],
                  inputs=lambda rng: _graph(rng), signature="def solve(n, edges):",
                  edges=[(3, []), (3, [[0, 1], [1, 2]])])


def _graph(rng):
    n = rng.randint(1, 6)
    seen = set()
    edges = []
    for _ in range(rng.randint(0, 6)):
        a, b = rng.randrange(n), rng.randrange(n)
        if a == b:
            continue
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        edges.append([key[0], key[1]])
    return (n, edges)


def _largest_comp(n, edges):
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen, best = set(), 0
    for s in range(n):
        if s in seen:
            continue
        stack, size = [s], 0
        seen.add(s)
        while stack:
            u = stack.pop()
            size += 1
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        best = max(best, size)
    return best


# --------------------------------------------------------------------------- #
@fam("recursion_counting", "medium", ["recursion", "combinatorics"])
def f_recursion_counting():
    specs = [
        ("Count Subsets Summing To Target", "Given a list `nums` and an integer "
         "`target`, return how many subsets (by position) sum to `target`.",
         lambda nums, target: sum(1 for m in range(1 << len(nums))
                                  if sum(nums[i] for i in range(len(nums))
                                         if m >> i & 1) == target),
         lambda rng: (ints(rng, lo=-4, hi=4, max_n=8), rng.randint(-4, 8))),
        ("Count Permutations Of Distinct", "Given a list `nums`, return how many "
         "distinct orderings of its elements exist.",
         lambda nums, target: _perm_count(nums), None),
        ("Tower Of Hanoi Moves", "Given a non-negative integer `n`, return the fewest "
         "moves to solve Towers of Hanoi with `n` disks.",
         lambda n: (1 << n) - 1, lambda rng: (rng.randint(0, 20),)),
        ("Nth Catalan Number", "Given a non-negative integer `n`, return the `n`-th "
         "Catalan number.", lambda n: _catalan(n), lambda rng: (rng.randint(0, 12),)),
        ("Count Balanced Bracket Strings", "Given a non-negative integer `n`, return "
         "how many balanced strings of `n` pairs of brackets exist.",
         lambda n: _catalan(n), lambda rng: (rng.randint(0, 10),)),
        ("Count Binary Strings Without Adjacent Ones", "Given a non-negative integer "
         "`n`, return how many binary strings of length `n` have no two adjacent 1s.",
         lambda n: _climb(n + 1), lambda rng: (rng.randint(0, 20),)),
        ("Combinations Count", "Given non-negative integers `n` and `k`, return the "
         "number of ways to choose `k` items from `n`.",
         lambda n, k: _choose(n, k),
         lambda rng: (rng.randint(0, 15), rng.randint(0, 15))),
        ("Count Paths In Grid", "Given positive integers `rows` and `cols`, return how "
         "many paths move from the top-left to the bottom-right using only right and "
         "down steps.", lambda rows, cols: _choose(rows + cols - 2, rows - 1),
         lambda rng: (rng.randint(1, 8), rng.randint(1, 8))),
    ]
    sigs = {"Count Subsets Summing To Target": "def solve(nums, target):",
            "Count Permutations Of Distinct": "def solve(nums):",
            "Combinations Count": "def solve(n, k):",
            "Count Paths In Grid": "def solve(rows, cols):"}
    for title, stmt, ref, inp in specs:
        if title == "Count Permutations Of Distinct":
            ref = lambda nums: _perm_count(nums)
            inp = lambda rng: (ints(rng, lo=-3, hi=3, max_n=7),)
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp,
                      signature=sigs.get(title, "def solve(n):"))


def _perm_count(nums):
    from math import factorial
    counts = {}
    for x in nums:
        counts[x] = counts.get(x, 0) + 1
    total = factorial(len(nums))
    for c in counts.values():
        total //= factorial(c)
    return total


def _catalan(n):
    return _choose(2 * n, n) // (n + 1)


def _choose(n, k):
    if k < 0 or k > n:
        return 0
    out = 1
    for i in range(k):
        out = out * (n - i) // (i + 1)
    return out


# --------------------------------------------------------------------------- #
@fam("array_medium", "medium", ["array"])
def f_array_medium():
    specs = [
        ("Find All Duplicates", "Given a list `nums`, return a sorted list of the "
         "values appearing more than once.",
         lambda nums: sorted(v for v in set(nums) if nums.count(v) > 1)),
        ("Next Permutation", "Given a list `nums`, return the next lexicographically "
         "greater ordering of its elements, or the smallest ordering if none exists.",
         lambda nums: _next_perm(nums)),
        ("Count Triplets Summing To Zero", "Given a list `nums`, return how many index "
         "triples `i < j < k` have `nums[i] + nums[j] + nums[k] == 0`.",
         lambda nums: sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums))
                          for k in range(j + 1, len(nums))
                          if nums[i] + nums[j] + nums[k] == 0)),
        ("First Missing Positive", "Given a list `nums`, return the smallest positive "
         "integer that does not appear.",
         lambda nums: next(i for i in range(1, len(nums) + 2) if i not in set(nums))),
        ("Longest Mountain Length", "Given a list `nums`, return the length of the "
         "longest contiguous stretch that strictly rises then strictly falls, with at "
         "least one of each. Return 0 if there is none.",
         lambda nums: _mountain(nums)),
        ("Product Sign", "Given a list `nums`, return 1, -1 or 0 according to the sign "
         "of the product of its elements.",
         lambda nums: 0 if 0 in nums else (-1 if sum(1 for x in nums if x < 0) % 2 else 1)),
        ("Sort By Parity Stable", "Given a list `nums`, return the even values in their "
         "original order followed by the odd values in their original order.",
         lambda nums: [x for x in nums if x % 2 == 0] + [x for x in nums if x % 2]),
        ("Max Difference After Smaller", "Given a list `nums`, return the largest "
         "`nums[j] - nums[i]` with `i < j`, or 0 if no such pair is positive.",
         lambda nums: max((nums[j] - nums[i] for i in range(len(nums))
                           for j in range(i + 1, len(nums))), default=0) if nums else 0),
        ("Count Inversions", "Given a list `nums`, return how many pairs `i < j` have "
         "`nums[i] > nums[j]`.",
         lambda nums: sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums))
                          if nums[i] > nums[j])),
        ("Rearrange Alternating Sign", "Given a list `nums` with equally many positive "
         "and negative values, return them alternating, starting with a positive, each "
         "group keeping its original relative order.",
         lambda nums: _alternate(nums)),
    ]
    for title, stmt, ref in specs:
        alt = title == "Rearrange Alternating Sign"
        yield problem(
            title=title, statement=stmt, ref=ref,
            inputs=((lambda rng: (_balanced_signs(rng),)) if alt
                    else (lambda rng: (ints(rng, lo=-6, hi=6, max_n=8),))),
            signature="def solve(nums):",
        )


def _next_perm(nums):
    xs = list(nums)
    i = len(xs) - 2
    while i >= 0 and xs[i] >= xs[i + 1]:
        i -= 1
    if i < 0:
        return sorted(xs)
    j = len(xs) - 1
    while xs[j] <= xs[i]:
        j -= 1
    xs[i], xs[j] = xs[j], xs[i]
    return xs[:i + 1] + xs[i + 1:][::-1]


def _mountain(nums):
    best = 0
    for i in range(1, len(nums) - 1):
        if nums[i - 1] < nums[i] > nums[i + 1]:
            L = i
            while L > 0 and nums[L - 1] < nums[L]:
                L -= 1
            R = i
            while R < len(nums) - 1 and nums[R] > nums[R + 1]:
                R += 1
            best = max(best, R - L + 1)
    return best


def _balanced_signs(rng):
    n = rng.randint(0, 4)
    pos = [rng.randint(1, 9) for _ in range(n)]
    neg = [-rng.randint(1, 9) for _ in range(n)]
    both = pos + neg
    rng.shuffle(both)
    return both


def _alternate(nums):
    pos = [x for x in nums if x > 0]
    neg = [x for x in nums if x < 0]
    out = []
    for a, b in zip(pos, neg):
        out += [a, b]
    return out + pos[len(neg):] + neg[len(pos):]


# --------------------------------------------------------------------------- #
@fam("simulation", "medium", ["simulation"])
def f_simulation():
    specs = [
        ("Robot Returns To Origin", "Given a string `moves` of the characters U D L R, "
         "return True if the robot ends where it started.",
         lambda moves: moves.count("U") == moves.count("D")
         and moves.count("L") == moves.count("R"),
         # a random UDLR walk essentially never returns to the origin
         lambda rng: (_walk(rng),), "def solve(moves):"),
        ("Final Position", "Given a string `moves` of U D L R, return the final "
         "`[x, y]` starting from `[0, 0]`, where R adds 1 to x and U adds 1 to y.",
         lambda moves: [moves.count("R") - moves.count("L"),
                        moves.count("U") - moves.count("D")],
         lambda rng: (word(rng, 0, 10, "UDLR"),), "def solve(moves):"),
        ("Candy Crush Once", "Given a list `nums`, remove every maximal run of three or "
         "more equal adjacent values once, and return what remains.",
         lambda nums: _crush_once(nums),
         lambda rng: ([rng.randint(0, 2) for _ in range(rng.randint(0, 10))],),
         "def solve(nums):"),
        ("Running Average Window", "Given a list `nums` and a positive integer `k`, "
         "return the average of the most recent up-to-`k` values after each element, "
         "each rounded to six decimals.",
         lambda nums, k: [round(sum(nums[max(0, i - k + 1):i + 1])
                                / len(nums[max(0, i - k + 1):i + 1]), 6)
                          for i in range(len(nums))],
         lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(1, 4)), "def solve(nums, k):"),
        ("Circular Queue Operations", "Given a list `ops` of integers, push each "
         "non-negative value onto a queue and pop the front for each -1, ignoring pops "
         "on an empty queue. Return the final queue.",
         lambda ops: _queue_sim(ops),
         lambda rng: ([rng.choice([-1] + list(range(5))) for _ in range(rng.randint(0, 9))],),
         "def solve(ops):"),
        ("Stack Operations", "Given a list `ops` of integers, push each non-negative "
         "value onto a stack and pop the top for each -1, ignoring pops on an empty "
         "stack. Return the final stack from bottom to top.",
         lambda ops: _stack_sim(ops),
         lambda rng: ([rng.choice([-1] + list(range(5))) for _ in range(rng.randint(0, 9))],),
         "def solve(ops):"),
        ("Josephus Survivor", "Given positive integers `n` and `k`, people numbered 0 "
         "to n-1 stand in a circle and every `k`-th is removed. Return the index of the "
         "last remaining person.", lambda n, k: _josephus(n, k),
         lambda rng: (rng.randint(1, 20), rng.randint(1, 6)), "def solve(n, k):"),
        ("Game Of Life Step", "Given a grid of 0s and 1s, return the grid after one "
         "step of Conway's Game of Life.", lambda grid: _life(grid),
         lambda rng: (grid01(rng),), "def solve(grid):"),
    ]
    for title, stmt, ref, inp, sig in specs:
        yield problem(title=title, statement=stmt, ref=ref, inputs=inp, signature=sig)


def _crush_once(nums):
    out, i = [], 0
    while i < len(nums):
        j = i
        while j < len(nums) and nums[j] == nums[i]:
            j += 1
        if j - i < 3:
            out += nums[i:j]
        i = j
    return out


def _queue_sim(ops):
    q = []
    for op in ops:
        if op == -1:
            if q:
                q.pop(0)
        else:
            q.append(op)
    return q


def _stack_sim(ops):
    st = []
    for op in ops:
        if op == -1:
            if st:
                st.pop()
        else:
            st.append(op)
    return st


def _josephus(n, k):
    r = 0
    for i in range(2, n + 1):
        r = (r + k) % i
    return r


def _life(grid):
    rows, cols = len(grid), len(grid[0]) if grid else 0
    out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            live = sum(grid[a][b]
                       for a in range(max(0, i - 1), min(rows, i + 2))
                       for b in range(max(0, j - 1), min(cols, j + 2))
                       if (a, b) != (i, j))
            row.append(1 if (grid[i][j] and live in (2, 3)) or
                       (not grid[i][j] and live == 3) else 0)
        out.append(row)
    return out


def _iso_pair(rng):
    """Half genuinely isomorphic, half not -- random pairs are always False."""
    a = word(rng, 1, 6, "abc")
    if rng.random() < 0.5:
        mapping = {}
        pool = list("xyzw")
        rng.shuffle(pool)
        for c in dict.fromkeys(a):
            mapping[c] = pool.pop() if pool else "q"
        return (a, "".join(mapping[c] for c in a))
    return (a, word(rng, 1, 6, "xyz"))


def _walk(rng):
    """Half the walks are balanced by construction, half are free."""
    if rng.random() < 0.5:
        n = rng.randint(0, 3)
        moves = list("UD" * n + "LR" * rng.randint(0, 2))
        rng.shuffle(moves)
        return "".join(moves)
    return word(rng, 0, 9, "UDLR")
