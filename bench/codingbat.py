"""CodingBat-style warmups.

Short, tightly specified exercises in the style of the CodingBat sections. These are
original statements and solutions written to the same shape, not copies: small inputs,
one idea each, and an answer that is either exactly right or obviously wrong.

They serve two purposes here. They are the warm-up tier of the corpus -- below `easy`,
useful for establishing whether a very small model can do anything at all before you
spend a night on it. And they are what the test suite runs the evaluator against,
because a problem set whose answers are this unambiguous makes a good fixture.
"""
from __future__ import annotations

from .core import fam, ints, problem, word


def _s(rng, n_lo=0, n_hi=8, alpha="abcxy"):
    return word(rng, n_lo, n_hi, alpha)


# --------------------------------------------------------------------------- #
@fam("cb_warmup1", "warmup", ["codingbat", "logic"])
def f_warmup1():
    specs = [
        ("Sleep In", "Given booleans `weekday` and `vacation`, return True if we sleep "
         "in: we sleep in unless it is a weekday and not a vacation.",
         lambda weekday, vacation: not weekday or vacation, "bool2"),
        ("Monkey Trouble", "Given booleans `a` and `b` for whether each monkey is "
         "smiling, return True if we are in trouble: both smiling or neither smiling.",
         lambda a, b: a == b, "bool2"),
        ("Sum Double", "Given integers `a` and `b`, return their sum, but return double "
         "the sum if they are equal.",
         lambda a, b: (a + b) * 2 if a == b else a + b, "int2"),
        ("Diff 21", "Given an integer `n`, return the absolute difference from 21, but "
         "return double that difference if `n` is over 21.",
         lambda n: (n - 21) * 2 if n > 21 else 21 - n, "int1"),
        ("Parrot Trouble", "Given a boolean `talking` and an integer `hour`, return True "
         "if we are in trouble: the parrot is talking and the hour is before 7 or after "
         "20.", lambda talking, hour: talking and (hour < 7 or hour > 20), "bool_int"),
        ("Makes Ten", "Given integers `a` and `b`, return True if either is 10 or their "
         "sum is 10.", lambda a, b: a == 10 or b == 10 or a + b == 10, "int2"),
        ("Near Hundred", "Given an integer `n`, return True if it is within 10 of 100 "
         "or of 200.", lambda n: abs(100 - n) <= 10 or abs(200 - n) <= 10, "int1"),
        ("Pos Neg", "Given integers `a` and `b` and a boolean `negative`, return True "
         "if one is positive and one negative. If `negative` is True, return True only "
         "if both are negative.",
         lambda a, b, negative: (a < 0 and b < 0) if negative
         else ((a < 0) != (b < 0)), "int2bool"),
        ("Not String", "Given a string `s`, return it prefixed with \"not \" unless it "
         "already begins with \"not\".",
         lambda s: s if s.startswith("not") else "not " + s, "str1"),
        ("Missing Char", "Given a string `s` and an index `n`, return the string with "
         "the character at `n` removed.",
         lambda s, n: s[:n] + s[n + 1:], "str_idx"),
        ("Front Back", "Given a string `s`, return it with the first and last "
         "characters swapped. Strings shorter than two characters are unchanged.",
         lambda s: s[-1] + s[1:-1] + s[0] if len(s) >= 2 else s, "str1"),
        ("Front Three", "Given a string `s`, return its first three characters repeated "
         "three times. If it is shorter than three characters, use whatever is there.",
         lambda s: s[:3] * 3, "str1"),
        ("Back Around", "Given a string `s`, return it with the last character added to "
         "both the front and the back. Return the empty string unchanged.",
         lambda s: s[-1] + s + s[-1] if s else s, "str1"),
        ("Or 35", "Given an integer `n`, return True if it is divisible by 3 or by 5.",
         lambda n: n % 3 == 0 or n % 5 == 0, "int1"),
        ("Front Again", "Given a string `s`, return True if its first two characters "
         "equal its last two.",
         lambda s: len(s) >= 2 and s[:2] == s[-2:], "str1"),
    ]
    yield from _emit(specs)


@fam("cb_warmup2", "warmup", ["codingbat", "string", "array"])
def f_warmup2():
    specs = [
        ("String Times", "Given a string `s` and a non-negative integer `n`, return `s` "
         "repeated `n` times.", lambda s, n: s * n, "str_n"),
        ("Front Times", "Given a string `s` and a non-negative integer `n`, return the "
         "first three characters of `s` repeated `n` times.",
         lambda s, n: s[:3] * n, "str_n"),
        ("Count XX", "Given a string `s`, return how many times \"xx\" appears, "
         "counting overlaps.",
         lambda s: sum(1 for i in range(len(s) - 1) if s[i:i + 2] == "xx"), "str1"),
        ("Double X", "Given a string `s`, return True if the first \"x\" is "
         "immediately followed by another \"x\".",
         lambda s: "x" in s and s[s.index("x"):s.index("x") + 2] == "xx", "str1"),
        ("String Bits", "Given a string `s`, return a string made of its characters at "
         "even indices.", lambda s: s[::2], "str1"),
        ("String Splosion", "Given a string `s`, return the concatenation of each of "
         "its prefixes, shortest first.",
         lambda s: "".join(s[:i + 1] for i in range(len(s))), "str1"),
        ("Last Two Count", "Given a string `s`, return how many times its final two "
         "characters appear earlier in the string, counting overlaps and excluding the "
         "final pair itself.",
         lambda s: sum(1 for i in range(len(s) - 2) if s[i:i + 2] == s[-2:])
         if len(s) >= 2 else 0, "str1"),
        ("Array Count Nine", "Given a list `nums`, return how many times 9 appears.",
         lambda nums: nums.count(9), "list1"),
        ("Array Front Nine", "Given a list `nums`, return True if 9 appears among its "
         "first four elements.", lambda nums: 9 in nums[:4], "list1"),
        ("Array123", "Given a list `nums`, return True if it contains 1, 2, 3 in "
         "consecutive positions.",
         lambda nums: any(nums[i:i + 3] == [1, 2, 3] for i in range(len(nums) - 2)),
         "list1"),
        ("String Match", "Given strings `a` and `b`, return how many positions hold the "
         "same two-character substring in both.",
         lambda a, b: sum(1 for i in range(min(len(a), len(b)) - 1)
                          if a[i:i + 2] == b[i:i + 2]), "str2"),
        ("String X", "Given a string `s`, return it with every \"x\" removed except a "
         "leading or trailing one.",
         lambda s: s[:1] + s[1:-1].replace("x", "") + s[-1:] if len(s) >= 2
         else s, "str1"),
    ]
    yield from _emit(specs)


# --------------------------------------------------------------------------- #
@fam("cb_string1", "warmup", ["codingbat", "string"])
def f_string1():
    specs = [
        ("Hello Name", "Given a string `name`, return \"Hello \" followed by it and an "
         "exclamation mark.", lambda s: "Hello " + s + "!", "str1"),
        ("Make Abba", "Given strings `a` and `b`, return `a` then `b` then `b` then `a`.",
         lambda a, b: a + b + b + a, "str2"),
        ("Make Tags", "Given strings `a` and `b`, return `b` wrapped in angle-bracket "
         "tags named `a`.", lambda a, b: "<%s>%s</%s>" % (a, b, a), "str2"),
        ("Insert Word", "Given strings `a` and `b`, insert `b` into the middle of `a` "
         "when `a` has exactly four characters, otherwise return `a`.",
         lambda a, b: a[:2] + b + a[2:] if len(a) == 4 else a, "str2"),
        ("Multiple Endings", "Given a string `s`, return its last two characters "
         "repeated three times.", lambda s: s[-2:] * 3, "str1"),
        ("First Half", "Given a string `s` of even length, return its first half.",
         lambda s: s[:len(s) // 2], "str1"),
        ("Without End", "Given a string `s`, return it without its first and last "
         "characters.", lambda s: s[1:-1], "str1"),
        ("Combo String", "Given strings `a` and `b`, return the shorter, then the "
         "longer, then the shorter again. If they are equal in length use `a` as the "
         "shorter.",
         lambda a, b: (a + b + a) if len(a) <= len(b) else (b + a + b), "str2"),
        ("Non Start", "Given strings `a` and `b`, return them joined with the first "
         "character of each removed.", lambda a, b: a[1:] + b[1:], "str2"),
        ("Left Two", "Given a string `s`, return it with its first two characters moved "
         "to the end.", lambda s: s[2:] + s[:2], "str1"),
        ("Right Two", "Given a string `s`, return it with its last two characters moved "
         "to the front.", lambda s: s[-2:] + s[:-2] if len(s) >= 2 else s, "str1"),
        ("The End", "Given a string `s` and a boolean `front`, return its first "
         "character if `front` is True, otherwise its last.",
         lambda s, front: (s[:1] if front else s[-1:]), "str_bool"),
        ("Without End Two", "Given a string `s`, return its middle with the first and "
         "last two characters removed.", lambda s: s[2:-2] if len(s) > 4 else "", "str1"),
        ("Middle Two", "Given a string `s` of even length, return its middle two "
         "characters.",
         lambda s: s[len(s) // 2 - 1:len(s) // 2 + 1] if len(s) >= 2 else s, "str1"),
        ("Ends Ly", "Given a string `s`, return True if it ends in \"ly\".",
         lambda s: s.endswith("ly"), "str_ly"),
    ]
    yield from _emit(specs)


@fam("cb_string2", "warmup", ["codingbat", "string"])
def f_string2():
    specs = [
        ("Double Char", "Given a string `s`, return it with every character doubled.",
         lambda s: "".join(c * 2 for c in s), "str1"),
        ("Count Hi", "Given a string `s`, return how many times \"hi\" appears.",
         lambda s: sum(1 for i in range(len(s) - 1) if s[i:i + 2] == "hi"), "str_hi"),
        ("Cat Dog", "Given a string `s`, return True if it contains \"cat\" and \"dog\" "
         "the same number of times.",
         lambda s: sum(1 for i in range(len(s) - 2) if s[i:i + 3] == "cat")
         == sum(1 for i in range(len(s) - 2) if s[i:i + 3] == "dog"), "str_catdog"),
        ("Count Code", "Given a string `s`, return how many substrings of length four "
         "look like \"co\", any character, then \"e\".",
         lambda s: sum(1 for i in range(len(s) - 3)
                       if s[i:i + 2] == "co" and s[i + 3] == "e"), "str_code"),
        ("End Other", "Given strings `a` and `b`, return True if either ends with the "
         "other, ignoring case.",
         lambda a, b: a.lower().endswith(b.lower()) or b.lower().endswith(a.lower()),
         "str2"),
        ("Xyz There", "Given a string `s`, return True if \"xyz\" appears somewhere not "
         "immediately preceded by a full stop.", lambda s: _xyz_there(s), "str_xyz"),
        ("Bob There", "Given a string `s`, return True if it contains \"b\", any "
         "character, then \"b\".",
         lambda s: any(s[i] == "b" and s[i + 2] == "b" for i in range(len(s) - 2)),
         "str1"),
        ("Xy Balance", "Given a string `s`, return True if every \"x\" is followed "
         "somewhere later by a \"y\".",
         lambda s: s.rfind("x") < s.rfind("y") or "x" not in s, "str1"),
        ("Mix String", "Given strings `a` and `b`, return them interleaved, appending "
         "the remainder of the longer.",
         lambda a, b: "".join(x + y for x, y in zip(a, b))
         + (a[len(b):] if len(a) > len(b) else b[len(a):]), "str2"),
        ("Repeat Front", "Given a string `s` and an integer `n`, return the "
         "concatenation of its first `n` prefixes, longest first.",
         lambda s, n: "".join(s[:i] for i in range(n, 0, -1)), "str_n_small"),
        ("Prefix Again", "Given a string `s` and an integer `n`, return True if the "
         "first `n` characters appear again later in the string.",
         lambda s, n: n <= len(s) and s[:n] in s[1:], "str_n_small"),
        ("Count Triple", "Given a string `s`, return how many positions start three "
         "identical characters in a row.",
         lambda s: sum(1 for i in range(len(s) - 2)
                       if s[i] == s[i + 1] == s[i + 2]), "str1"),
    ]
    yield from _emit(specs)


def _xyz_there(s):
    for i in range(len(s) - 2):
        if s[i:i + 3] == "xyz" and (i == 0 or s[i - 1] != "."):
            return True
    return False


# --------------------------------------------------------------------------- #
@fam("cb_list1", "warmup", ["codingbat", "array"])
def f_list1():
    specs = [
        ("First Last Six", "Given a list `nums`, return True if it starts or ends "
         "with 6.", lambda nums: bool(nums) and (nums[0] == 6 or nums[-1] == 6), "list1"),
        ("Same First Last", "Given a list `nums`, return True if it is non-empty and "
         "its first and last elements are equal.",
         lambda nums: bool(nums) and nums[0] == nums[-1], "list1"),
        ("Ends Sum", "Given a list `nums`, return the sum of its first and last "
         "elements, or 0 if it is empty.",
         lambda nums: (nums[0] + nums[-1]) if nums else 0, "list1"),
        ("Common End", "Given lists `a` and `b`, return True if they share a first "
         "element or share a last element.",
         lambda a, b: bool(a) and bool(b) and (a[0] == b[0] or a[-1] == b[-1]), "list2"),
        ("Sum Three", "Given a list `nums`, return the sum of its first three elements.",
         lambda nums: sum(nums[:3]), "list1"),
        ("Rotate Left Three", "Given a list `nums`, return it rotated left by one.",
         lambda nums: nums[1:] + nums[:1], "list1"),
        ("Reverse Three", "Given a list `nums`, return its first three elements "
         "reversed.", lambda nums: nums[:3][::-1], "list1"),
        ("Max End", "Given a list `nums`, return it with every element replaced by the "
         "larger of its first and last.",
         lambda nums: [max(nums[0], nums[-1])] * len(nums) if nums else [], "list1"),
        ("Sum Two", "Given a list `nums`, return the sum of its first two elements.",
         lambda nums: sum(nums[:2]), "list1"),
        ("Middle Way", "Given lists `a` and `b` of length three, return a list of their "
         "middle elements.",
         lambda a, b: [a[1], b[1]] if len(a) > 1 and len(b) > 1 else [], "list2"),
        ("Make Ends", "Given a list `nums`, return a list of its first and last "
         "elements.", lambda nums: [nums[0], nums[-1]] if nums else [], "list1"),
        ("Has23", "Given a list `nums`, return True if it contains a 2 or a 3.",
         lambda nums: 2 in nums or 3 in nums, "list1"),
    ]
    yield from _emit(specs)


@fam("cb_list2", "warmup", ["codingbat", "array"])
def f_list2():
    specs = [
        ("Count Evens", "Given a list `nums`, return how many of its elements are even.",
         lambda nums: sum(1 for x in nums if x % 2 == 0), "list1"),
        ("Big Diff", "Given a list `nums`, return the difference between its largest "
         "and smallest elements, or 0 if it is empty.",
         lambda nums: max(nums) - min(nums) if nums else 0, "list1"),
        ("Centered Average", "Given a list `nums`, return the integer average of its "
         "elements ignoring one copy each of the largest and smallest, rounding toward "
         "negative infinity. Return 0 if fewer than three elements.",
         lambda nums: _centered(nums), "list1"),
        ("Sum13", "Given a list `nums`, return the sum of its elements, ignoring every "
         "13 and the element immediately after each 13.",
         lambda nums: _sum13(nums), "list1"),
        ("Sum67", "Given a list `nums`, return the sum of its elements, ignoring every "
         "stretch that starts with a 6 and ends with the next 7.",
         lambda nums: _sum67(nums), "list1"),
        ("Has22", "Given a list `nums`, return True if it contains two adjacent 2s.",
         lambda nums: any(nums[i] == 2 and nums[i + 1] == 2
                          for i in range(len(nums) - 1)), "list1"),
        ("Lucky13", "Given a list `nums`, return True if it contains no 1 and no 3.",
         lambda nums: 1 not in nums and 3 not in nums, "list1"),
        ("Sum28", "Given a list `nums`, return True if the 2s in it sum to exactly 8.",
         lambda nums: nums.count(2) * 2 == 8, "list_twos"),
        ("More14", "Given a list `nums`, return True if it holds strictly more 1s than "
         "4s.", lambda nums: nums.count(1) > nums.count(4), "list1"),
        ("Only14", "Given a list `nums`, return True if every element is a 1 or a 4.",
         lambda nums: all(x in (1, 4) for x in nums), "list1"),
    ]
    yield from _emit(specs)


def _centered(nums):
    if len(nums) < 3:
        return 0
    xs = sorted(nums)[1:-1]
    return sum(xs) // len(xs)


def _sum13(nums):
    total, skip = 0, False
    for x in nums:
        if skip:
            skip = False
            continue
        if x == 13:
            skip = True
            continue
        total += x
    return total


def _sum67(nums):
    total, skipping = 0, False
    for x in nums:
        if skipping:
            if x == 7:
                skipping = False
            continue
        if x == 6:
            skipping = True
            continue
        total += x
    return total


# --------------------------------------------------------------------------- #
@fam("cb_logic", "warmup", ["codingbat", "logic"])
def f_logic():
    specs = [
        ("Cigar Party", "Given an integer `n` and a boolean `weekend`, the party is "
         "successful with at least 40 cigars and, unless it is the weekend, at most 60.",
         lambda n, weekend: n >= 40 and (weekend or n <= 60), "int_bool"),
        ("Date Fashion", "Given integers `you` and `date` from 0 to 10, return 2 if "
         "either is at least 8, 0 if either is at most 2, and 1 otherwise.",
         lambda a, b: 0 if (a <= 2 or b <= 2) else (2 if (a >= 8 or b >= 8) else 1),
         "int2_small"),
        ("Squirrel Play", "Given an integer `temp` and a boolean `summer`, they play "
         "when the temperature is between 60 and 90 inclusive, or up to 100 in summer.",
         lambda n, summer: 60 <= n <= (100 if summer else 90), "int_bool"),
        ("Caught Speeding", "Given an integer `speed` and a boolean `birthday`, return "
         "0 up to 60, 1 up to 80 and 2 above that. A birthday raises every limit by 5.",
         lambda n, birthday: _speeding(n, birthday), "int_bool"),
        ("Sorta Sum", "Given integers `a` and `b`, return their sum, but return 20 if "
         "the sum falls between 10 and 19 inclusive.",
         lambda a, b: 20 if 10 <= a + b <= 19 else a + b, "int2_small"),
        ("Alarm Clock", "Given an integer `day` from 0 to 6 and a boolean `vacation`, "
         "return \"7:00\" on weekdays and \"10:00\" at weekends; on vacation return "
         "\"10:00\" on weekdays and \"off\" at weekends. Day 0 and 6 are the weekend.",
         lambda n, vacation: _alarm(n, vacation), "day_bool"),
        ("Love6", "Given integers `a` and `b`, return True if either is 6, or their sum "
         "or difference is 6.",
         lambda a, b: a == 6 or b == 6 or a + b == 6 or abs(a - b) == 6, "int2_small"),
        ("In1To10", "Given an integer `n` and a boolean `outside_mode`, return True if "
         "`n` is between 1 and 10 inclusive; in outside mode return True if it is at "
         "most 1 or at least 10.",
         lambda n, outside_mode: (n <= 1 or n >= 10) if outside_mode
         else (1 <= n <= 10), "int_bool"),
        ("Special Eleven", "Given an integer `n`, return True if it leaves a remainder "
         "of 0 or 1 when divided by 11.", lambda n: n % 11 in (0, 1), "int1"),
        ("Answer Cell", "Given booleans `morning`, `asleep` and `mom`, we answer the "
         "phone unless we are asleep, and never in the morning unless it is mum.",
         lambda morning, asleep, mom: (not asleep) and (mom or not morning), "bool3"),
        ("Twenty Difference", "Given integers `a` and `b`, return whichever is closer "
         "to 20, or 0 if they tie.",
         lambda a, b: 0 if abs(20 - a) == abs(20 - b)
         else (a if abs(20 - a) < abs(20 - b) else b), "int2_small"),
        ("Near Ten", "Given an integer `n`, return True if it is within 2 of a multiple "
         "of 10.", lambda n: n % 10 <= 2 or n % 10 >= 8, "int1"),
    ]
    yield from _emit(specs)


def _speeding(speed, birthday):
    if birthday:
        speed -= 5
    return 0 if speed <= 60 else (1 if speed <= 80 else 2)


def _alarm(day, vacation):
    weekend = day in (0, 6)
    if vacation:
        return "off" if weekend else "10:00"
    return "10:00" if weekend else "7:00"


# --------------------------------------------------------------------------- #
@fam("cb_array", "warmup", ["codingbat", "array"])
def f_array():
    specs = [
        ("Double23", "Given a list `nums`, return True if it holds two adjacent equal "
         "values.", lambda nums: any(nums[i] == nums[i + 1]
                                     for i in range(len(nums) - 1)), "list1"),
        ("Fix23", "Given a list `nums`, return it with any 3 that immediately follows a "
         "2 replaced by 0.", lambda nums: _fix23(nums), "list1"),
        ("Start1", "Given lists `a` and `b`, return how many of them begin with 1.",
         lambda a, b: (1 if a[:1] == [1] else 0) + (1 if b[:1] == [1] else 0), "list2"),
        ("Biggest Two", "Given a list `nums`, return its two largest values sorted "
         "ascending, or the whole list if it is shorter.",
         lambda nums: sorted(sorted(nums)[-2:]), "list1"),
        ("Mid Three", "Given a list `nums` of odd length, return its middle three "
         "elements.",
         lambda nums: nums[len(nums) // 2 - 1:len(nums) // 2 + 2]
         if len(nums) >= 3 else nums, "list1"),
        ("Get Mid Point", "Given a list `nums`, return its middle element, or None if "
         "it is empty.", lambda nums: nums[len(nums) // 2] if nums else None, "list1"),
        ("No Triples", "Given a list `nums`, return True if no value appears three "
         "times in a row.",
         lambda nums: not any(nums[i] == nums[i + 1] == nums[i + 2]
                              for i in range(len(nums) - 2)), "list1"),
        ("Pattern51", "Given a list `nums`, return True if some element is followed by "
         "a value exactly 5 larger, then one exactly 1 larger than that.",
         lambda nums: any(nums[i + 1] == nums[i] + 5 and nums[i + 2] == nums[i] + 6
                          for i in range(len(nums) - 2)), "list_pattern"),
        ("Post4", "Given a list `nums`, return the elements after the last 4.",
         lambda nums: nums[len(nums) - 1 - nums[::-1].index(4):][1:]
         if 4 in nums else [], "list1"),
        ("Not Alone", "Given a list `nums` and an integer `val`, replace every `val` "
         "that is strictly between two larger values by the larger neighbour.",
         lambda nums, val: _not_alone(nums, val), "list_val"),
        ("Zero Front", "Given a list `nums`, return it with every zero moved to the "
         "front, other values keeping their order.",
         lambda nums: [0] * nums.count(0) + [x for x in nums if x != 0], "list1"),
        ("Only Positive", "Given a list `nums`, return it with negative values replaced "
         "by zero.", lambda nums: [max(x, 0) for x in nums], "list1"),
    ]
    yield from _emit(specs)


def _fix23(nums):
    out = list(nums)
    for i in range(len(out) - 1):
        if out[i] == 2 and out[i + 1] == 3:
            out[i + 1] = 0
    return out


def _not_alone(nums, val):
    out = list(nums)
    for i in range(1, len(out) - 1):
        if out[i] == val and (out[i - 1] > val or out[i + 1] > val):
            out[i] = max(out[i - 1], out[i + 1])
    return out


# --------------------------------------------------------------------------- #
@fam("cb_map", "warmup", ["codingbat", "hash-table"])
def f_map():
    specs = [
        ("Word Count", "Given a list `words`, return a dictionary mapping each word to "
         "how many times it appears.", lambda words: _counts(words), "words"),
        ("Word Length", "Given a list `words`, return a dictionary mapping each word to "
         "its length.", lambda words: {w: len(w) for w in words}, "words"),
        ("First Char Groups", "Given a list `words`, return a dictionary mapping each "
         "first character to a list of the words starting with it, in order.",
         lambda words: _first_char(words), "words"),
        ("Words Appearing Once", "Given a list `words`, return a sorted list of those "
         "appearing exactly once.",
         lambda words: sorted(w for w in set(words) if words.count(w) == 1), "words"),
        ("Word Multiple", "Given a list `words`, return a dictionary mapping each word "
         "to True when it appears more than once.",
         lambda words: {w: words.count(w) > 1 for w in words}, "words"),
        ("Pairs By Ends", "Given a list `words`, return a dictionary mapping each "
         "word's first character to its last character, later words winning.",
         lambda words: {w[0]: w[-1] for w in words if w}, "words"),
        ("All Swap", "Given a list `words`, keep only words whose first character is "
         "unique across the list, and return them in order.",
         lambda words: [w for w in words
                        if sum(1 for o in words if o and w and o[0] == w[0]) == 1],
         "words"),
        ("Char Frequency", "Given a list `words`, return a dictionary mapping each "
         "character appearing in any word to its total count.",
         lambda words: _counts("".join(words)), "words"),
        ("Longest Word Per Letter", "Given a list `words`, return a dictionary mapping "
         "each first character to the longest word starting with it, earlier words "
         "winning ties.", lambda words: _longest_per(words), "words"),
        ("Sum By Length", "Given a list `words`, return a dictionary mapping each word "
         "length to how many words have it.",
         lambda words: _counts([len(w) for w in words]), "words"),
    ]
    yield from _emit(specs)


def _counts(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out


def _first_char(words):
    out = {}
    for w in words:
        if w:
            out.setdefault(w[0], []).append(w)
    return out


def _longest_per(words):
    out = {}
    for w in words:
        if not w:
            continue
        if w[0] not in out or len(w) > len(out[w[0]]):
            out[w[0]] = w
    return out


# --------------------------------------------------------------------------- #
# Input shapes. Each spec names one; this keeps the specs above one line each.
# --------------------------------------------------------------------------- #
GENS = {
    "int1": (lambda rng: (rng.randint(-5, 210),), "def solve(n):",
             [(0,), (21,), (22,), (100,), (11,)]),
    "int2": (lambda rng: (rng.randint(-5, 12), rng.randint(-5, 12)), "def solve(a, b):",
             [(1, 1), (10, 0), (5, 5), (3, 7)]),
    "int2_small": (lambda rng: (rng.randint(0, 22), rng.randint(0, 22)),
                   "def solve(a, b):", [(0, 0), (8, 2), (10, 10), (6, 6)]),
    "int_bool": (lambda rng: (rng.randint(0, 105), rng.random() < 0.5),
                 "def solve(n, flag):", [(40, False), (60, True), (0, False)]),
    "day_bool": (lambda rng: (rng.randint(0, 6), rng.random() < 0.5),
                 "def solve(n, flag):", [(0, False), (3, False), (6, True)]),
    "bool2": (lambda rng: (rng.random() < 0.5, rng.random() < 0.5),
              "def solve(a, b):", [(True, True), (True, False), (False, False)]),
    "bool3": (lambda rng: (rng.random() < 0.5, rng.random() < 0.5, rng.random() < 0.5),
              "def solve(a, b, c):", [(True, True, True), (False, False, False)]),
    "bool_int": (lambda rng: (rng.random() < 0.5, rng.randint(0, 23)),
                 "def solve(flag, hour):", [(True, 6), (True, 12), (False, 23)]),
    "int2bool": (lambda rng: (rng.randint(-5, 5), rng.randint(-5, 5), rng.random() < 0.5),
                 "def solve(a, b, flag):", [(1, -1, False), (-1, -1, True)]),
    "str1": (lambda rng: (_s(rng),), "def solve(s):",
             [("",), ("a",), ("ab",), ("abc",), ("xxyx",)]),
    "str2": (lambda rng: (_s(rng), _s(rng)), "def solve(a, b):",
             [("", ""), ("a", "b"), ("abcd", "xy")]),
    "str_n": (lambda rng: (_s(rng, 1, 5), rng.randint(0, 4)), "def solve(s, n):",
              [("a", 0), ("abc", 2)]),
    "str_n_small": (lambda rng: (_s(rng, 1, 6), rng.randint(0, 3)), "def solve(s, n):",
                    [("abc", 1), ("abcabc", 3)]),
    "str_idx": (lambda rng: (lambda t: (t, rng.randrange(len(t))))(_s(rng, 1, 7)),
                "def solve(s, n):", [("abc", 0), ("abc", 2)]),
    "str_bool": (lambda rng: (_s(rng, 1, 6), rng.random() < 0.5), "def solve(s, front):",
                 [("abc", True), ("abc", False)]),
    "str_hi": (lambda rng: (word(rng, 0, 8, "hiab"),), "def solve(s):",
               [("",), ("hi",), ("hihi",), ("ahia",)]),
    "str_xyz": (lambda rng: (word(rng, 0, 8, "xyz."),), "def solve(s):",
                [("",), ("xyz",), (".xyz",), ("abcxyz",)]),
    "str_catdog": (lambda rng: (word(rng, 0, 9, "catdog"),), "def solve(s):",
                   [("",), ("catdog",), ("cat",)]),
    "str_code": (lambda rng: (word(rng, 0, 9, "code"),), "def solve(s):",
                 [("",), ("code",), ("coxe",)]),
    "list1": (lambda rng: (ints(rng, lo=0, hi=9),), "def solve(nums):",
              [([],), ([1],), ([1, 2, 3],), ([6, 1, 6],), ([2, 2, 2],)]),
    "list2": (lambda rng: (ints(rng, lo=0, hi=9), ints(rng, lo=0, hi=9)),
              "def solve(a, b):", [([], []), ([1, 2, 3], [1, 2, 3])]),
    "list_val": (lambda rng: (ints(rng, lo=0, hi=5), rng.randint(0, 5)),
                 "def solve(nums, val):", [([], 1), ([1, 2, 1], 2)]),
    "str_ly": (lambda rng: (_ly(rng),), "def solve(s):",
               [("",), ("ly",), ("only",), ("ab",)]),
    "list_twos": (lambda rng: (_twos(rng),), "def solve(nums):",
                  [([],), ([2, 2, 2, 2],), ([2, 2],)]),
    "list_pattern": (lambda rng: (_pattern51(rng),), "def solve(nums):",
                     [([],), ([1, 6, 7],), ([1, 2, 3],)]),
    "words": (lambda rng: ([word(rng, 1, 4, "abc") for _ in range(rng.randint(0, 6))],),
              "def solve(words):", [([],), (["a"],), (["ab", "ab", "c"],)]),
}


def _ly(rng):
    """Half the strings end in "ly" -- the base alphabet never produces one."""
    base = word(rng, 0, 6, "abcl")
    return base + "ly" if rng.random() < 0.5 else base


def _twos(rng):
    """Sometimes exactly four 2s, so the sum-to-8 answer is not always False."""
    n2 = rng.choice([0, 1, 4, 4, rng.randint(0, 5)])
    xs = [2] * n2 + [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]
    xs = [x for x in xs if x != 2 or xs.index(x) < n2 or True]
    rng.shuffle(xs)
    return xs


def _pattern51(rng):
    """Plant the n, n+5, n+6 run half the time."""
    xs = ints(rng, lo=0, hi=9)
    if rng.random() < 0.5:
        base = rng.randint(0, 3)
        pos = rng.randint(0, len(xs))
        xs = xs[:pos] + [base, base + 5, base + 6] + xs[pos:]
    return xs


def _emit(specs):
    for title, stmt, ref, shape in specs:
        gen, sig, edges = GENS[shape]
        yield problem(title=title, statement=stmt, ref=ref, inputs=gen,
                      signature=sig, edges=edges)
