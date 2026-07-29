"""Shared machinery for the problem banks.

A problem is defined once, as a *family* with a parameterised reference solution.
Expected outputs are never written by hand -- they are computed by running the
reference against generated inputs. That is the only way a bank this size stays
correct, and it means a broken problem fails at build time rather than silently
scoring a model wrong for eight hours.

Every generated problem asks for the same entry point, `solve(...)`. Uniformity
costs a little realism and buys automated evaluation of 600 problems.
"""
from __future__ import annotations

import random

DIFFICULTIES = ("easy", "medium", "hard")


def fam(key, difficulty, topics):
    """Decorator: register a generator function as a problem family."""
    def wrap(fn):
        fn.family_key = key
        fn.difficulty = difficulty
        fn.topics = list(topics)
        fn.is_family = True
        return fn
    return wrap


def problem(title, statement, ref, inputs, signature="def solve(nums):",
            edges=(), topics=None, note=""):
    """One concrete problem inside a family.

    ref     callable implementing the correct answer
    inputs  callable(rng) -> tuple of arguments, used to generate random cases
    edges   explicit argument tuples covering the boundaries that matter
    """
    return {
        "title": title,
        "statement": statement.strip(),
        "signature": signature,
        "ref": ref,
        "inputs": inputs,
        "edges": list(edges),
        "topics": list(topics or []),
        "note": note,
    }


# --------------------------------------------------------------------------- #
# Input generators
# --------------------------------------------------------------------------- #
def ints(rng, n=None, lo=-50, hi=50, min_n=0, max_n=12):
    n = rng.randint(min_n, max_n) if n is None else n
    return [rng.randint(lo, hi) for _ in range(n)]


def pos_ints(rng, n=None, lo=1, hi=50, min_n=1, max_n=12):
    return ints(rng, n, lo, hi, min_n, max_n)


def sorted_ints(rng, n=None, lo=-50, hi=50, min_n=1, max_n=12):
    return sorted(ints(rng, n, lo, hi, min_n, max_n))


def distinct_ints(rng, n=None, lo=-60, hi=60, min_n=1, max_n=10):
    n = rng.randint(min_n, max_n) if n is None else n
    n = min(n, hi - lo + 1)
    return rng.sample(range(lo, hi + 1), n)


LOWER = "abcdefghijklmnopqrstuvwxyz"
ALNUM = LOWER + LOWER.upper() + "0123456789"
SENTENCE_WORDS = ("the quick brown fox jumps over a lazy dog while nine red "
                  "kites drift past twelve silent grey towers").split()


def word(rng, min_n=1, max_n=8, alphabet=LOWER):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(min_n, max_n)))


def small_word(rng):
    return word(rng, 1, 6, "abcde")


def sentence(rng, min_w=1, max_w=8):
    return " ".join(rng.choice(SENTENCE_WORDS) for _ in range(rng.randint(min_w, max_w)))


def mixed_text(rng, min_n=0, max_n=16):
    pool = ALNUM + "   .,!?"
    return "".join(rng.choice(pool) for _ in range(rng.randint(min_n, max_n)))


def matrix(rng, rows=None, cols=None, lo=-9, hi=9):
    r = rng.randint(1, 4) if rows is None else rows
    c = rng.randint(1, 4) if cols is None else cols
    return [[rng.randint(lo, hi) for _ in range(c)] for _ in range(r)]


def square(rng, n=None, lo=-9, hi=9):
    n = rng.randint(1, 4) if n is None else n
    return matrix(rng, n, n, lo, hi)


def grid01(rng, rows=None, cols=None, p=0.4):
    r = rng.randint(1, 5) if rows is None else rows
    c = rng.randint(1, 5) if cols is None else cols
    return [[1 if rng.random() < p else 0 for _ in range(c)] for _ in range(r)]


def bits(rng, min_n=1, max_n=10):
    return "".join(rng.choice("01") for _ in range(rng.randint(min_n, max_n)))


def edge_lists():
    """The array boundaries that break naive solutions."""
    return [[], [0], [1], [-1], [5, 5, 5], [1, 2, 3, 4, 5], [5, 4, 3, 2, 1],
            [-3, 0, 3], [7], [0, 0, 0, 0], [2, -2, 2, -2]]


def collect(module):
    """Pull every registered family out of a module, in definition order."""
    fams = [obj for obj in vars(module).values()
            if callable(obj) and getattr(obj, "is_family", False)]
    fams.sort(key=lambda f: f.__code__.co_firstlineno)
    return fams


def expand(families):
    """Run each family, tagging its problems with family key, difficulty, topics."""
    out = []
    for f in families:
        for p in f():
            p = dict(p)
            p["family"] = f.family_key
            p["difficulty"] = f.difficulty
            p["topics"] = sorted(set(p.get("topics") or []) | set(f.topics))
            out.append(p)
    return out


def interleave(problems):
    """Round-robin across families so a truncated bank stays diverse.

    Taking the first 200 of a flat list would take forty problems from one family
    and none from the next; this takes one from each family in turn.
    """
    buckets = {}
    order = []
    for p in problems:
        if p["family"] not in buckets:
            buckets[p["family"]] = []
            order.append(p["family"])
        buckets[p["family"]].append(p)
    out = []
    i = 0
    while len(out) < len(problems):
        added = False
        for key in order:
            if i < len(buckets[key]):
                out.append(buckets[key][i])
                added = True
        if not added:
            break
        i += 1
    return out


def make_cases(p, seed, n_random=10, max_cases=16, max_edges=6):
    """Build concrete test cases by running the reference solution.

    Edges are capped. A family that supplies eleven boundary cases would otherwise
    crowd out every random one, and a predicate like "greater than 10" would look
    constant because all the hand-written boundaries are small.
    """
    rng = random.Random(seed)
    args_list = []
    seen = set()

    for e in p["edges"][:max_edges]:
        key = repr(e)
        if key not in seen:
            seen.add(key)
            args_list.append(tuple(e))

    guard = 0
    while len(args_list) < max_cases and guard < n_random * 20:
        guard += 1
        args = tuple(p["inputs"](rng))
        key = repr(args)
        if key in seen:
            continue
        seen.add(key)
        args_list.append(args)

    cases = []
    for args in args_list[:max_cases]:
        out = p["ref"](*_copy_args(args))
        cases.append({"input": _jsonable(args), "output": _jsonable(out)})
    return cases


def _copy_args(args):
    """The reference must not see mutations made by an earlier call."""
    import copy
    return tuple(copy.deepcopy(a) for a in args)


def _jsonable(v):
    if isinstance(v, tuple):
        return [_jsonable(x) for x in v]
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, set):
        return sorted(_jsonable(x) for x in v)
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, float):
        return round(v, 6)
    return v
