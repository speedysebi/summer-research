"""Easy tier: single pass, one idea, no auxiliary data structure required."""
from __future__ import annotations

from .core import (bits, edge_lists, fam, ints, matrix, mixed_text, pos_ints,
                   problem, sentence, sorted_ints, word)

# --------------------------------------------------------------------------- #
SUBSETS = {
    "all elements": (lambda xs: list(xs), "every element"),
    "the even-indexed elements": (lambda xs: xs[0::2], "the elements at even indices"),
    "the odd-indexed elements": (lambda xs: xs[1::2], "the elements at odd indices"),
    "the positive elements": (lambda xs: [x for x in xs if x > 0], "the elements greater than zero"),
    "the negative elements": (lambda xs: [x for x in xs if x < 0], "the elements less than zero"),
    "the even values": (lambda xs: [x for x in xs if x % 2 == 0], "the even values"),
    "the odd values": (lambda xs: [x for x in xs if x % 2 != 0], "the odd values"),
    "the distinct values": (lambda xs: sorted(set(xs)), "the distinct values"),
}

AGGS = {
    "sum": (lambda xs: sum(xs), "their sum", "0"),
    "product": (lambda xs: _product(xs), "their product", "1"),
    "maximum": (lambda xs: max(xs) if xs else 0, "the largest of them", "0"),
    "minimum": (lambda xs: min(xs) if xs else 0, "the smallest of them", "0"),
    "count": (lambda xs: len(xs), "how many there are", "0"),
    "range": (lambda xs: (max(xs) - min(xs)) if xs else 0,
              "the difference between the largest and smallest", "0"),
}


def _product(xs):
    out = 1
    for x in xs:
        out *= x
    return out


@fam("array_aggregate", "easy", ["array"])
def f_array_aggregate():
    for agg_name, (agg, agg_desc, empty) in AGGS.items():
        for sub_name, (sub, sub_desc) in SUBSETS.items():
            yield problem(
                title="%s of %s" % (agg_name.capitalize(), sub_name),
                statement="""
Given a list of integers `nums`, consider %s. Return %s.

If there are no such elements, return %s.
""" % (sub_desc, agg_desc, empty),
                ref=(lambda nums, a=agg, s=sub: a(s(nums))),
                inputs=lambda rng: (ints(rng),),
                edges=[(e,) for e in edge_lists()],
            )


# --------------------------------------------------------------------------- #
PREDICATES = {
    "even": lambda x: x % 2 == 0,
    "odd": lambda x: x % 2 != 0,
    "positive": lambda x: x > 0,
    "negative": lambda x: x < 0,
    "zero": lambda x: x == 0,
    "a multiple of 3": lambda x: x % 3 == 0,
    "a multiple of 5": lambda x: x % 5 == 0,
    "greater than 10": lambda x: x > 10,
    "a perfect square": lambda x: x >= 0 and int(x ** 0.5) ** 2 == x,
    "a two-digit number": lambda x: 10 <= abs(x) <= 99,
}


@fam("count_matching", "easy", ["array", "counting"])
def f_count_matching():
    for name, pred in PREDICATES.items():
        yield problem(
            title="Count Values That Are %s" % name.capitalize(),
            statement="""
Given a list of integers `nums`, return how many of its elements are %s.
""" % name,
            ref=(lambda nums, p=pred: sum(1 for x in nums if p(x))),
            inputs=lambda rng: (ints(rng),),
            edges=[(e,) for e in edge_lists()],
        )


@fam("filter_list", "easy", ["array"])
def f_filter_list():
    for name, pred in PREDICATES.items():
        yield problem(
            title="Keep Only Values That Are %s" % name.capitalize(),
            statement="""
Given a list of integers `nums`, return a new list containing only the elements
that are %s, in their original order.
""" % name,
            ref=(lambda nums, p=pred: [x for x in nums if p(x)]),
            inputs=lambda rng: (ints(rng),),
            edges=[(e,) for e in edge_lists()],
        )


# --------------------------------------------------------------------------- #
STR_OPS = {
    "reversed": (lambda s: s[::-1], "reversed"),
    "in upper case": (lambda s: s.upper(), "converted to upper case"),
    "in lower case": (lambda s: s.lower(), "converted to lower case"),
    "with case swapped": (lambda s: s.swapcase(), "with the case of every letter flipped"),
    "without vowels": (lambda s: "".join(c for c in s if c.lower() not in "aeiou"),
                       "with every vowel removed"),
    "without digits": (lambda s: "".join(c for c in s if not c.isdigit()),
                       "with every digit removed"),
    "without spaces": (lambda s: s.replace(" ", ""), "with every space removed"),
    "with characters sorted": (lambda s: "".join(sorted(s)),
                               "with its characters sorted in ascending order"),
    "with duplicates removed": (lambda s: _dedupe(s),
                                "keeping only the first occurrence of each character"),
    "with letters only": (lambda s: "".join(c for c in s if c.isalpha()),
                          "keeping only alphabetic characters"),
}


def _dedupe(s):
    seen, out = set(), []
    for c in s:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return "".join(out)


@fam("string_transform", "easy", ["string"])
def f_string_transform():
    for name, (op, desc) in STR_OPS.items():
        yield problem(
            title="String %s" % name.capitalize(),
            statement="""
Given a string `s`, return the string %s.
""" % desc,
            ref=(lambda s, o=op: o(s)),
            inputs=lambda rng: (mixed_text(rng),),
            signature="def solve(s):",
            edges=[("",), ("a",), ("AaBb",), ("hello world",), ("12345",),
                   ("  ",), ("Zebra 42!",)],
        )


# --------------------------------------------------------------------------- #
CHAR_CLASSES = {
    "vowels": lambda c: c.lower() in "aeiou",
    "consonants": lambda c: c.isalpha() and c.lower() not in "aeiou",
    "digits": lambda c: c.isdigit(),
    "upper-case letters": lambda c: c.isupper(),
    "lower-case letters": lambda c: c.islower(),
    "spaces": lambda c: c == " ",
    "alphanumeric characters": lambda c: c.isalnum(),
    "punctuation marks": lambda c: c in ".,!?;:",
}


@fam("string_count", "easy", ["string", "counting"])
def f_string_count():
    for name, pred in CHAR_CLASSES.items():
        yield problem(
            title="Count %s" % name.capitalize(),
            statement="""
Given a string `s`, return how many of its characters are %s.
""" % name,
            ref=(lambda s, p=pred: sum(1 for c in s if p(c))),
            inputs=lambda rng: (mixed_text(rng),),
            signature="def solve(s):",
            edges=[("",), ("a",), ("Hello, World! 42",), ("   ",), ("AEIOU",)],
        )


# --------------------------------------------------------------------------- #
DIGIT_OPS = {
    "digit sum": (lambda n: sum(int(c) for c in str(abs(n))),
                  "the sum of its decimal digits"),
    "digit product": (lambda n: _product([int(c) for c in str(abs(n))]),
                      "the product of its decimal digits"),
    "digit count": (lambda n: len(str(abs(n))), "how many decimal digits it has"),
    "largest digit": (lambda n: max(int(c) for c in str(abs(n))), "its largest digit"),
    "smallest digit": (lambda n: min(int(c) for c in str(abs(n))), "its smallest digit"),
    "reversed digits": (lambda n: int(str(abs(n))[::-1]) * (-1 if n < 0 else 1),
                        "the integer formed by reversing its digits, keeping the sign"),
    "digits ascending": (lambda n: int("".join(sorted(str(abs(n))))),
                         "the integer formed by sorting its digits in ascending order"),
    "digits descending": (lambda n: int("".join(sorted(str(abs(n)), reverse=True))),
                          "the integer formed by sorting its digits in descending order"),
    "alternating digit sum": (lambda n: sum(int(c) * (1 if i % 2 == 0 else -1)
                                            for i, c in enumerate(str(abs(n)))),
                              "the alternating sum of its digits, starting with a plus"),
    "count even digits": (lambda n: sum(1 for c in str(abs(n)) if int(c) % 2 == 0),
                          "how many of its digits are even"),
}


@fam("digit_math", "easy", ["math"])
def f_digit_math():
    for name, (op, desc) in DIGIT_OPS.items():
        yield problem(
            title="Integer %s" % name.capitalize(),
            statement="""
Given an integer `n`, return %s.
""" % desc,
            ref=(lambda n, o=op: o(n)),
            inputs=lambda rng: (rng.randint(-99999, 99999),),
            signature="def solve(n):",
            edges=[(0,), (7,), (-7,), (10,), (100,), (999,), (-1024,), (505,)],
        )


# --------------------------------------------------------------------------- #
@fam("sequences", "easy", ["math", "simulation"])
def f_sequences():
    def fib(n):
        a, b, out = 0, 1, []
        for _ in range(n):
            out.append(a)
            a, b = b, a + b
        return out

    def primes(n):
        out = []
        x = 2
        while len(out) < n:
            if all(x % d for d in range(2, int(x ** 0.5) + 1)):
                out.append(x)
            x += 1
        return out

    def collatz(n):
        steps = 0
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            steps += 1
        return steps

    specs = [
        ("First N Fibonacci Numbers", "the first `n` Fibonacci numbers, starting 0, 1",
         fib, (0, 12)),
        ("First N Square Numbers", "a list of the first `n` perfect squares, starting at 1",
         lambda n: [i * i for i in range(1, n + 1)], (0, 12)),
        ("First N Cubes", "a list of the first `n` cubes, starting at 1",
         lambda n: [i ** 3 for i in range(1, n + 1)], (0, 10)),
        ("First N Triangular Numbers", "a list of the first `n` triangular numbers",
         lambda n: [i * (i + 1) // 2 for i in range(1, n + 1)], (0, 12)),
        ("First N Powers Of Two", "a list of the first `n` powers of two, starting at 1",
         lambda n: [2 ** i for i in range(n)], (0, 12)),
        ("First N Primes", "a list of the first `n` prime numbers", primes, (0, 10)),
        ("Factorial", "the factorial of `n`",
         lambda n: _product(range(1, n + 1)), (0, 12)),
        ("Collatz Steps", "how many steps the Collatz process takes to reach 1 from `n`",
         collatz, (1, 60)),
        ("Sum To N", "the sum of every integer from 1 to `n` inclusive",
         lambda n: n * (n + 1) // 2, (0, 500)),
        ("Count Digits Total", "the total number of digits used writing 1 through `n`",
         lambda n: sum(len(str(i)) for i in range(1, n + 1)), (1, 200)),
    ]
    for title, desc, ref, (lo, hi) in specs:
        yield problem(
            title=title,
            statement="Given a non-negative integer `n`, return %s." % desc,
            ref=ref,
            inputs=(lambda rng, lo=lo, hi=hi: (rng.randint(lo, hi),)),
            signature="def solve(n):",
            edges=[(lo,), (lo + 1,), (hi,)],
        )


# --------------------------------------------------------------------------- #
@fam("list_search", "easy", ["array", "search"])
def f_list_search():
    specs = [
        ("Index Of Target", "the index of the first occurrence of `target` in `nums`, "
         "or -1 if it does not appear",
         lambda nums, target: nums.index(target) if target in nums else -1),
        ("Last Index Of Target", "the index of the last occurrence of `target` in `nums`, "
         "or -1 if it does not appear",
         lambda nums, target: (len(nums) - 1 - nums[::-1].index(target))
         if target in nums else -1),
        ("Count Occurrences", "how many times `target` appears in `nums`",
         lambda nums, target: nums.count(target)),
        ("Contains Target", "True if `target` appears in `nums`, otherwise False",
         lambda nums, target: target in nums),
        ("Count Greater Than Target", "how many elements of `nums` are greater than `target`",
         lambda nums, target: sum(1 for x in nums if x > target)),
        ("Closest To Target", "the element of `nums` closest to `target`; if two are "
         "equally close return the smaller one. Return None for an empty list.",
         lambda nums, target: min(nums, key=lambda x: (abs(x - target), x))
         if nums else None),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a list of integers `nums` and an integer `target`, "
                      "return %s." % desc,
            ref=ref,
            inputs=lambda rng: (ints(rng, lo=-9, hi=9), rng.randint(-9, 9)),
            signature="def solve(nums, target):",
            edges=[([], 1), ([1], 1), ([1], 2), ([3, 3, 3], 3), ([1, 2, 3, 2, 1], 2)],
        )


@fam("list_extremes", "easy", ["array"])
def f_list_extremes():
    specs = [
        ("Index Of Maximum", "the index of the largest element; if it appears more "
         "than once return the first such index",
         lambda nums: nums.index(max(nums)) if nums else -1),
        ("Index Of Minimum", "the index of the smallest element; if it appears more "
         "than once return the first such index",
         lambda nums: nums.index(min(nums)) if nums else -1),
        ("Second Largest Distinct", "the second largest distinct value, or None if "
         "there are fewer than two distinct values",
         lambda nums: sorted(set(nums))[-2] if len(set(nums)) >= 2 else None),
        ("Second Smallest Distinct", "the second smallest distinct value, or None if "
         "there are fewer than two distinct values",
         lambda nums: sorted(set(nums))[1] if len(set(nums)) >= 2 else None),
        ("Missing Number", "the one value from 0 to len(nums) that does not appear; "
         "`nums` holds len(nums) distinct values from that range",
         lambda nums: (len(nums) * (len(nums) + 1) // 2) - sum(nums)),
        ("Find The Duplicate", "the value that appears more than once, or None if "
         "every value is distinct",
         lambda nums: next((x for i, x in enumerate(nums) if x in nums[:i]), None)),
    ]
    for title, desc, ref in specs:
        is_missing = title == "Missing Number"
        yield problem(
            title=title,
            statement="Given a list of integers `nums`, return %s." % desc,
            ref=ref,
            inputs=((lambda rng: (_missing_case(rng),)) if is_missing
                    else (lambda rng: (ints(rng, lo=-9, hi=9),))),
            edges=([([0],), ([1, 0],), ([0, 2],)] if is_missing
                   else [(e,) for e in edge_lists()]),
        )


def _missing_case(rng):
    n = rng.randint(1, 9)
    pool = list(range(n + 1))
    pool.pop(rng.randrange(len(pool)))
    rng.shuffle(pool)
    return pool


# --------------------------------------------------------------------------- #
@fam("list_predicates", "easy", ["array", "logic"])
def f_list_predicates():
    def is_arith(xs):
        if len(xs) < 2:
            return True
        d = xs[1] - xs[0]
        return all(xs[i + 1] - xs[i] == d for i in range(len(xs) - 1))

    specs = [
        ("All Even", "True if every element is even", lambda xs: all(x % 2 == 0 for x in xs)),
        ("Any Negative", "True if at least one element is negative",
         lambda xs: any(x < 0 for x in xs)),
        ("Is Sorted Ascending", "True if the list is sorted in non-decreasing order",
         lambda xs: all(xs[i] <= xs[i + 1] for i in range(len(xs) - 1))),
        ("Is Sorted Descending", "True if the list is sorted in non-increasing order",
         lambda xs: all(xs[i] >= xs[i + 1] for i in range(len(xs) - 1))),
        ("All Distinct", "True if no value appears twice", lambda xs: len(set(xs)) == len(xs)),
        ("All Same", "True if every element is equal", lambda xs: len(set(xs)) <= 1),
        ("Is Arithmetic", "True if consecutive elements have a constant difference",
         is_arith),
        ("Sums To Zero", "True if the elements sum to zero", lambda xs: sum(xs) == 0),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a list of integers `nums`, return %s, otherwise False."
                      % desc,
            ref=ref,
            inputs=lambda rng: (_structured_list(rng),),
            edges=[(e,) for e in edge_lists()],
        )


def _structured_list(rng):
    """Half random, half structured -- otherwise "is sorted" is always False."""
    kind = rng.randrange(4)
    n = rng.randint(0, 8)
    if kind == 0:
        return sorted(ints(rng, n, -6, 6))
    if kind == 1:
        return sorted(ints(rng, n, -6, 6), reverse=True)
    if kind == 2:
        start, step = rng.randint(-6, 6), rng.randint(-3, 3)
        return [start + i * step for i in range(n)]
    return ints(rng, n, -6, 6)


# --------------------------------------------------------------------------- #
@fam("list_reshape", "easy", ["array"])
def f_list_reshape():
    specs = [
        ("Rotate Left By K", "the list rotated left by `k` positions",
         lambda nums, k: nums[k % len(nums):] + nums[:k % len(nums)] if nums else []),
        ("Rotate Right By K", "the list rotated right by `k` positions",
         lambda nums, k: nums[-(k % len(nums)):] + nums[:-(k % len(nums))]
         if nums and k % len(nums) else list(nums)),
        ("First K Elements", "the first `k` elements; if `k` exceeds the length "
         "return the whole list", lambda nums, k: nums[:k]),
        ("Last K Elements", "the last `k` elements; if `k` exceeds the length "
         "return the whole list", lambda nums, k: nums[len(nums) - k:] if k else []),
        ("Every Kth Element", "every `k`-th element starting from index 0; `k` is at least 1",
         lambda nums, k: nums[::max(1, k)]),
        ("Drop Every Kth", "the list with every `k`-th element (1-indexed) removed; "
         "`k` is at least 1",
         lambda nums, k: [x for i, x in enumerate(nums, 1) if i % max(1, k) != 0]),
        ("Repeat Each K Times", "a list where each element is repeated `k` times in place",
         lambda nums, k: [x for x in nums for _ in range(k)]),
        ("Chunk Into Size K", "a list of consecutive chunks of length `k`; the final "
         "chunk may be shorter. `k` is at least 1",
         lambda nums, k: [nums[i:i + max(1, k)] for i in range(0, len(nums), max(1, k))]),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a list of integers `nums` and a non-negative integer `k`, "
                      "return %s." % desc,
            ref=ref,
            inputs=lambda rng: (ints(rng, min_n=1), rng.randint(1, 5)),
            signature="def solve(nums, k):",
            edges=[([1, 2, 3], 1), ([1, 2, 3], 3), ([1, 2, 3, 4], 2), ([7], 1)],
        )


# --------------------------------------------------------------------------- #
@fam("running_totals", "easy", ["array", "prefix-sum"])
def f_running_totals():
    def running(xs, f):
        out, acc = [], None
        for x in xs:
            acc = x if acc is None else f(acc, x)
            out.append(acc)
        return out

    specs = [
        ("Running Sum", "the running sum", lambda a, b: a + b),
        ("Running Maximum", "the running maximum", lambda a, b: max(a, b)),
        ("Running Minimum", "the running minimum", lambda a, b: min(a, b)),
        ("Running Product", "the running product", lambda a, b: a * b),
    ]
    for title, desc, f in specs:
        yield problem(
            title=title,
            statement="Given a list of integers `nums`, return a list of the same "
                      "length holding %s, where element `i` covers `nums[0..i]`." % desc,
            ref=(lambda nums, f=f: running(nums, f)),
            inputs=lambda rng: (ints(rng, lo=-9, hi=9),),
            edges=[(e,) for e in edge_lists()],
        )

    yield problem(
        title="Adjacent Differences",
        statement="Given a list of integers `nums`, return a list of the differences "
                  "between each pair of adjacent elements, `nums[i+1] - nums[i]`.",
        ref=lambda nums: [nums[i + 1] - nums[i] for i in range(len(nums) - 1)],
        inputs=lambda rng: (ints(rng, lo=-9, hi=9),),
        edges=[(e,) for e in edge_lists()],
    )
    yield problem(
        title="Adjacent Sums",
        statement="Given a list of integers `nums`, return a list of the sums of each "
                  "pair of adjacent elements.",
        ref=lambda nums: [nums[i] + nums[i + 1] for i in range(len(nums) - 1)],
        inputs=lambda rng: (ints(rng, lo=-9, hi=9),),
        edges=[(e,) for e in edge_lists()],
    )


# --------------------------------------------------------------------------- #
@fam("frequency", "easy", ["hash-table", "counting"])
def f_frequency():
    def counts(xs):
        d = {}
        for x in xs:
            d[x] = d.get(x, 0) + 1
        return d

    specs = [
        ("Most Frequent Value", "the value that appears most often; break ties by "
         "choosing the smallest such value. Return None for an empty list.",
         lambda xs: min((v for v in set(xs) if xs.count(v) == max(counts(xs).values())))
         if xs else None),
        ("Least Frequent Value", "the value that appears least often; break ties by "
         "choosing the smallest such value. Return None for an empty list.",
         lambda xs: min((v for v in set(xs) if xs.count(v) == min(counts(xs).values())))
         if xs else None),
        ("Count Distinct Values", "how many distinct values appear",
         lambda xs: len(set(xs))),
        ("Values Appearing Once", "a sorted list of the values that appear exactly once",
         lambda xs: sorted(v for v in set(xs) if xs.count(v) == 1)),
        ("Values Appearing More Than Once", "a sorted list of the values that appear "
         "at least twice", lambda xs: sorted(v for v in set(xs) if xs.count(v) > 1)),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a list of integers `nums`, return %s." % desc,
            ref=ref,
            inputs=lambda rng: (ints(rng, lo=-5, hi=5),),
            edges=[(e,) for e in edge_lists()],
        )


# --------------------------------------------------------------------------- #
@fam("string_checks", "easy", ["string"])
def f_string_checks():
    specs = [
        ("Is Palindrome", "True if `s` reads the same forwards and backwards",
         lambda s: s == s[::-1]),
        ("Is All Digits", "True if `s` is non-empty and every character is a digit",
         lambda s: s.isdigit()),
        ("Is All Letters", "True if `s` is non-empty and every character is a letter",
         lambda s: s.isalpha()),
        ("Has Repeated Character", "True if any character appears more than once",
         lambda s: len(set(s)) != len(s)),
        ("Is Pangram", "True if `s` contains every letter of the English alphabet at "
         "least once, ignoring case",
         lambda s: set("abcdefghijklmnopqrstuvwxyz") <= set(s.lower())),
        ("Starts And Ends Same", "True if `s` is non-empty and its first and last "
         "characters are equal", lambda s: bool(s) and s[0] == s[-1]),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a string `s`, return %s, otherwise False." % desc,
            ref=ref,
            inputs=lambda rng: (_varied_string(rng),),
            signature="def solve(s):",
            edges=[("",), ("a",), ("ab",), ("racecar",), ("abc123",), ("4021",),
                   ("the quick brown fox jumps over the lazy dog",)],
        )


def _varied_string(rng):
    """Cover the branches: digits, letters, palindromes and the odd pangram."""
    kind = rng.randrange(5)
    if kind == 0:
        return "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 6)))
    if kind == 1:
        half = word(rng, 1, 3, "abc")
        return half + (rng.choice(["", rng.choice("abc")])) + half[::-1]
    if kind == 2:
        base = "the quick brown fox jumps over the lazy dog"
        return base if rng.random() < 0.5 else base.replace("z", "")
    if kind == 3:
        return word(rng, 0, 7, "aabbc")
    return word(rng, 1, 7, "abc123")


@fam("word_ops", "easy", ["string"])
def f_word_ops():
    specs = [
        ("Longest Word", "the longest whitespace-separated word; if several tie return "
         "the first. Return an empty string if there are no words.",
         lambda s: max(s.split(), key=len) if s.split() else ""),
        ("Shortest Word", "the shortest whitespace-separated word; if several tie "
         "return the first. Return an empty string if there are no words.",
         lambda s: min(s.split(), key=len) if s.split() else ""),
        ("Count Words", "how many whitespace-separated words it contains",
         lambda s: len(s.split())),
        ("Capitalise Each Word", "the string with the first letter of each word "
         "upper-cased and the rest lower-cased",
         lambda s: " ".join(w.capitalize() for w in s.split())),
        ("Reverse Each Word", "the string with the characters of each word reversed "
         "but the word order kept",
         lambda s: " ".join(w[::-1] for w in s.split())),
        ("Reverse Word Order", "the words in reverse order, separated by single spaces",
         lambda s: " ".join(reversed(s.split()))),
        ("Word Lengths", "a list of the lengths of the words",
         lambda s: [len(w) for w in s.split()]),
        ("Sort Words Alphabetically", "the words sorted alphabetically and joined by "
         "single spaces", lambda s: " ".join(sorted(s.split()))),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a string `s` of words separated by spaces, return %s." % desc,
            ref=ref,
            inputs=lambda rng: (sentence(rng, 0, 7),),
            signature="def solve(s):",
            edges=[("",), ("one",), ("a bb ccc",), ("  spaced   out  ",)],
        )


# --------------------------------------------------------------------------- #
@fam("matrix_basic", "easy", ["matrix"])
def f_matrix_basic():
    specs = [
        ("Row Sums", "a list holding the sum of each row",
         lambda g: [sum(r) for r in g]),
        ("Column Sums", "a list holding the sum of each column",
         lambda g: [sum(r[c] for r in g) for c in range(len(g[0]))] if g and g[0] else []),
        ("Matrix Total", "the sum of every element", lambda g: sum(sum(r) for r in g)),
        ("Flatten", "a single list of all elements in row-major order",
         lambda g: [x for r in g for x in r]),
        ("Transpose", "the transpose of the matrix",
         lambda g: [list(c) for c in zip(*g)] if g else []),
        ("Largest Element", "the largest element, or None if the matrix is empty",
         lambda g: max((x for r in g for x in r), default=None)),
        ("Count Zeros", "how many elements equal zero",
         lambda g: sum(1 for r in g for x in r if x == 0)),
        ("Row With Largest Sum", "the index of the row with the largest sum; break "
         "ties by the smallest index. Return -1 for an empty matrix.",
         lambda g: max(range(len(g)), key=lambda i: sum(g[i])) if g else -1),
    ]
    for title, desc, ref in specs:
        yield problem(
            title="Matrix %s" % title,
            statement="Given a rectangular matrix `grid` of integers, return %s." % desc,
            ref=ref,
            inputs=lambda rng: (matrix(rng),),
            signature="def solve(grid):",
            edges=[([[1]],), ([[1, 2], [3, 4]],), ([[0, 0], [0, 0]],),
                   ([[-1, 2, -3]],), ([[1], [2], [3]],)],
        )


@fam("matrix_diagonals", "easy", ["matrix"])
def f_matrix_diagonals():
    specs = [
        ("Main Diagonal Sum", "the sum of the elements on the main diagonal",
         lambda g: sum(g[i][i] for i in range(len(g)))),
        ("Anti-Diagonal Sum", "the sum of the elements on the anti-diagonal",
         lambda g: sum(g[i][len(g) - 1 - i] for i in range(len(g)))),
        ("Main Diagonal", "the elements on the main diagonal, top-left to bottom-right",
         lambda g: [g[i][i] for i in range(len(g))]),
        ("Anti-Diagonal", "the elements on the anti-diagonal, top-right to bottom-left",
         lambda g: [g[i][len(g) - 1 - i] for i in range(len(g))]),
    ]
    for title, desc, ref in specs:
        yield problem(
            title="Square Matrix %s" % title,
            statement="Given an `n x n` matrix `grid` of integers, return %s." % desc,
            ref=ref,
            inputs=lambda rng: (square(rng),),
            signature="def solve(grid):",
            edges=[([[1]],), ([[1, 2], [3, 4]],), ([[1, 2, 3], [4, 5, 6], [7, 8, 9]],)],
        )


def square(rng, n=None, lo=-9, hi=9):
    from .core import square as _sq
    return _sq(rng, n, lo, hi)


# --------------------------------------------------------------------------- #
@fam("divisibility", "easy", ["math"])
def f_divisibility():
    specs = [
        ("Multiples Up To N", "a list of every positive multiple of `k` that is at "
         "most `n`", lambda n, k: list(range(k, n + 1, k)) if k else []),
        ("Sum Of Multiples", "the sum of every positive multiple of `k` that is at "
         "most `n`", lambda n, k: sum(range(k, n + 1, k)) if k else 0),
        ("Count Multiples", "how many positive multiples of `k` are at most `n`",
         lambda n, k: n // k if k else 0),
        ("Greatest Common Divisor", "the greatest common divisor of `n` and `k`",
         lambda n, k: _gcd(n, k)),
        ("Least Common Multiple", "the least common multiple of `n` and `k`",
         lambda n, k: abs(n * k) // _gcd(n, k) if n and k else 0),
        ("Divisors Of N", "a sorted list of every positive divisor of `n`",
         lambda n, k: [d for d in range(1, n + 1) if n % d == 0] if n > 0 else []),
        ("Count Divisors", "how many positive divisors `n` has",
         lambda n, k: sum(1 for d in range(1, n + 1) if n % d == 0) if n > 0 else 0),
        ("Is Prime", "True if `n` is a prime number, otherwise False",
         lambda n, k: n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given positive integers `n` and `k`, return %s." % desc,
            ref=ref,
            inputs=lambda rng: (rng.randint(1, 60), rng.randint(1, 9)),
            signature="def solve(n, k):",
            edges=[(1, 1), (12, 3), (13, 5), (36, 6), (2, 2), (60, 7)],
        )


def _gcd(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


# --------------------------------------------------------------------------- #
@fam("fizzbuzz_family", "easy", ["math", "string"])
def f_fizzbuzz():
    def fb(n, a, b, wa, wb):
        out = []
        for i in range(1, n + 1):
            s = ""
            if i % a == 0:
                s += wa
            if i % b == 0:
                s += wb
            out.append(s or str(i))
        return out

    combos = [(3, 5, "Fizz", "Buzz"), (2, 3, "Even", "Tri"), (4, 6, "Quad", "Hex"),
              (3, 7, "Fizz", "Sept"), (5, 10, "Pent", "Dec")]
    for a, b, wa, wb in combos:
        yield problem(
            title="FizzBuzz %d/%d" % (a, b),
            statement="""
Given a positive integer `n`, return a list of length `n`. For each integer `i`
from 1 to `n`, the entry is "%s" if `i` is divisible by %d, "%s" if divisible by
%d, "%s%s" if divisible by both, and the string form of `i` otherwise.
""" % (wa, a, wb, b, wa, wb),
            ref=(lambda n, a=a, b=b, wa=wa, wb=wb: fb(n, a, b, wa, wb)),
            inputs=lambda rng: (rng.randint(1, 30),),
            signature="def solve(n):",
            edges=[(1,), (15,), (20,)],
        )


# --------------------------------------------------------------------------- #
@fam("clamp_scale", "easy", ["array", "math"])
def f_clamp_scale():
    specs = [
        ("Absolute Values", "a list of the absolute value of each element",
         lambda nums, k: [abs(x) for x in nums]),
        ("Signs", "a list holding -1, 0 or 1 for each element according to its sign",
         lambda nums, k: [(x > 0) - (x < 0) for x in nums]),
        ("Cap At K", "a list where every element greater than `k` is replaced by `k`",
         lambda nums, k: [min(x, k) for x in nums]),
        ("Floor At K", "a list where every element less than `k` is replaced by `k`",
         lambda nums, k: [max(x, k) for x in nums]),
        ("Scale By K", "a list with every element multiplied by `k`",
         lambda nums, k: [x * k for x in nums]),
        ("Offset By K", "a list with `k` added to every element",
         lambda nums, k: [x + k for x in nums]),
        ("Modulo K", "a list of each element modulo `k`; `k` is at least 1",
         lambda nums, k: [x % max(1, k) for x in nums]),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given a list of integers `nums` and an integer `k`, return %s."
                      % desc,
            ref=ref,
            inputs=lambda rng: (ints(rng, lo=-20, hi=20), rng.randint(1, 9)),
            signature="def solve(nums, k):",
            edges=[([], 3), ([0], 1), ([-5, 0, 5], 2), ([10, -10], 4)],
        )


# --------------------------------------------------------------------------- #
@fam("two_lists", "easy", ["array"])
def f_two_lists():
    specs = [
        ("Element-wise Sum", "a list holding the element-wise sum; if the lists differ "
         "in length stop at the shorter one",
         lambda a, b: [x + y for x, y in zip(a, b)]),
        ("Element-wise Product", "a list holding the element-wise product; stop at the "
         "shorter list", lambda a, b: [x * y for x, y in zip(a, b)]),
        ("Element-wise Maximum", "a list holding the larger of each pair; stop at the "
         "shorter list", lambda a, b: [max(x, y) for x, y in zip(a, b)]),
        ("Common Values", "a sorted list of the distinct values appearing in both lists",
         lambda a, b: sorted(set(a) & set(b))),
        ("Values Only In First", "a sorted list of the distinct values in `a` that do "
         "not appear in `b`", lambda a, b: sorted(set(a) - set(b))),
        ("Interleave", "the two lists interleaved, starting with `a`; once one runs out "
         "append the remainder of the other",
         lambda a, b: [x for pair in zip(a, b) for x in pair]
         + (a[len(b):] if len(a) > len(b) else b[len(a):])),
        ("Concatenate Distinct", "the elements of `a` followed by those of `b`, keeping "
         "only the first occurrence of each value",
         lambda a, b: _dedupe_list(a + b)),
        ("Dot Product", "the sum of the element-wise products; stop at the shorter list",
         lambda a, b: sum(x * y for x, y in zip(a, b))),
    ]
    for title, desc, ref in specs:
        yield problem(
            title=title,
            statement="Given two lists of integers `a` and `b`, return %s." % desc,
            ref=ref,
            inputs=lambda rng: (ints(rng, lo=-9, hi=9), ints(rng, lo=-9, hi=9)),
            signature="def solve(a, b):",
            edges=[([], []), ([1], []), ([], [1]), ([1, 2, 3], [4, 5, 6]),
                   ([1, 2], [2, 3, 4])],
        )


def _dedupe_list(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# --------------------------------------------------------------------------- #
@fam("simple_rules", "easy", ["logic", "math"])
def f_simple_rules():
    def grade(score):
        for cutoff, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
            if score >= cutoff:
                return letter
        return "F"

    specs = [
        ("Leap Year", "True if year `n` is a leap year in the Gregorian calendar",
         lambda n: n % 4 == 0 and (n % 100 != 0 or n % 400 == 0), (1, 2400)),
        ("Letter Grade", "the letter grade for a score `n` out of 100 using the "
         "cutoffs 90/80/70/60 for A/B/C/D and F below that", grade, (0, 100)),
        ("Hours To Minutes", "how many whole minutes are in `n` hours",
         lambda n: n * 60, (0, 48)),
        ("Seconds To HMS", "a list `[hours, minutes, seconds]` for `n` seconds",
         lambda n: [n // 3600, (n % 3600) // 60, n % 60], (0, 100000)),
        ("Celsius To Fahrenheit Floor", "the temperature in Fahrenheit for `n` degrees "
         "Celsius, rounded down to an integer",
         lambda n: (n * 9) // 5 + 32, (-50, 50)),
        ("Is Power Of Two", "True if `n` is a positive power of two",
         lambda n: n > 0 and n & (n - 1) == 0, (0, 300)),
    ]
    for title, desc, ref, (lo, hi) in specs:
        yield problem(
            title=title,
            statement="Given an integer `n`, return %s." % desc,
            ref=ref,
            inputs=(lambda rng, lo=lo, hi=hi: (rng.randint(lo, hi),)),
            signature="def solve(n):",
            edges=[(lo,), (0,), (1,), (hi,)],
        )


# --------------------------------------------------------------------------- #
@fam("binary_strings", "easy", ["string", "bit-manipulation"])
def f_binary_strings():
    specs = [
        ("Count Ones", "how many '1' characters it contains", lambda s: s.count("1")),
        ("Binary To Decimal", "the decimal value of the binary string",
         lambda s: int(s, 2) if s else 0),
        ("Longest Run Of Ones", "the length of the longest consecutive run of '1's",
         lambda s: max((len(r) for r in s.split("0")), default=0)),
        ("Flip Bits", "the string with every bit flipped",
         lambda s: "".join("1" if c == "0" else "0" for c in s)),
        ("Is Alternating", "True if no two adjacent characters are equal",
         lambda s: all(s[i] != s[i + 1] for i in range(len(s) - 1))),
    ]
    for title, desc, ref in specs:
        yield problem(
            title="Binary String %s" % title,
            statement="Given a string `s` containing only the characters '0' and '1', "
                      "return %s." % desc,
            ref=ref,
            inputs=lambda rng: (bits(rng),),
            signature="def solve(s):",
            edges=[("0",), ("1",), ("1111",), ("0000",), ("101010",), ("110011",)],
        )
