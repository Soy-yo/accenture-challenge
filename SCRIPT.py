#!/usr/bin/env python

"""
Script for Accenture's challenge. It reads a list of test cases from IN_FILENAME file where every test case is
composed by its id, a target number and a prime number. The script has to reach the target number using simple
operations: sum, difference, product and division, with the minimum amount of primes below 100 (and 1). Then it will
write the output (expression and number of primes used) for every test case in OUT_FILENAME file.
"""

from datetime import datetime
from heapq import heappush, heappop
from time import time

__author__ = "Pablo Sanz Sanz"

""" Datetime of the exact execution beginning """
START_MOMENT = datetime.now()

""" Maximum number of secs available for the algorithm to finish """
MAX_TIME = 240

""" Name of the input file """
IN_FILENAME = "TEST.txt"

""" Name of the output file """
OUT_FILENAME = "SCORE.txt"

""" First field of every solution in the output file (using id card number as I'm not in a team) """
TEAM_NAME = "50361137S"

""" Ordered list with all available prime numbers """
PRIMES = [
    1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
    43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97
]

""" First number that cannot be decomposed with three or less primes """
MIN_NON_DECOMPOSABLE = 269

""" Set with all numbers between 1 (included) and MIN_NON_DECOMPOSABLE (excluded) """
NUMBERS = {x for x in range(1, MIN_NON_DECOMPOSABLE)}

""" Dictionary that maps a number with its factorization with two primes """
CROSS_PRODUCTS = {p * q: (p, q) for p in PRIMES for q in PRIMES if p > 1 and q > 1 and p * q < MIN_NON_DECOMPOSABLE}

""" Constant r = NUM/DEN used to check when to call find_some_solution function """
NUM, DEN = 3, 1


def get_unreachable_numbers():
    """
    Returns a dictionary matching every prime number with the set of numbers that couldn't be reached with two prime
    numbers if we removed that prime number.
    :return: a dictionary {p: {n_1, ..., n_p}} in which p is a prime number and {n_1, ..., n_p} is the set of numbers
    between 1 and 97 that couldn't be reached with two or less prime numbers if we removed p
    """
    result = {}
    for p in PRIMES:
        primes = [q for q in PRIMES if q != p]
        sums_set = {x + y for x in primes for y in primes}
        diff_set = {x - y for x in primes for y in primes}
        prod_set = {x * y for x in primes for y in primes}
        all_sets = sums_set.union(diff_set).union(prod_set).union(primes)
        result[p] = NUMBERS.difference(all_sets)
    return result


""" Dictionary that maps every prime number with a subset of NUMBERS that can't be decomposed with only two primes if we
    don't use that prime number """
UNREACHABLE = get_unreachable_numbers()


class Node:
    """
    Node for the branch and bound algorithm. It contains the expression, parentheses' depth, prime count and lower
    bound at a point of the search tree. The expression is a reversed list of strings where every element is either a
    prime number or an operator (or parentheses).
    """

    def __init__(self, expression, depth, count, min_result):
        """
        Constructs a node.
        :param expression: a list containing a valid partial expression
        :param depth: current parentheses' depth in the expression
        :param count: number of primes in the expression
        :param min_result: lower bound of the result
        """
        self._expression = expression
        self._depth = depth
        self._count = count
        self._min = min_result

    def expression(self):
        """
        Expression getter.
        :return: a list containing the valid partial expression of this node
        """
        return self._expression

    def depth(self):
        """
        Depth getter.
        :return: parentheses' depth in the expression of this node
        """
        return self._depth

    def count(self):
        """
        Count getter.
        :return: number of primes in the expression of this node
        """
        return self._count

    def __lt__(self, other):
        return self._min < other._min or self._min == other._min and self._expression[-1] < other._expression[-1]

    def __le__(self, other):
        return self._min <= other._min or self._min == other._min and self._expression[-1] <= other._expression[-1]

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)


def find_expression(n, primes, prime):
    """
    Main algorithm to solve the problem. Finds the expression with primes in primes excluding prime that evaluates to n.
    Returns the string with the formula and the number of primes involved.
    :param n: target number to be decomposed
    :param primes: ordered list with all available primes
    :param prime: unused prime
    :return: a pair (expression, count), where expression is a string with an evaluable expression that evaluates to
    n and count is the number of primes used in the expression
    """
    # Special case
    if n == 0:
        p = primes[0] if primes[0] != prime else primes[1]
        return f"{p}-{p}", 2
    prime_set = {p for p in primes if p != prime}
    if n in prime_set:
        return f"{n}", 1
    unreachable = UNREACHABLE[prime]
    if n < MIN_NON_DECOMPOSABLE:
        expression, count = decompose(n, prime_set, unreachable)
        return "".join(reversed(expression)), count
    expression_result = []
    operand_count_result = n + 1
    valid_result = False
    seen = dict()
    queue = [Node([f"{n}"], 1, 1, 1)]
    while queue:
        node = heappop(queue)
        depth = node.depth()
        count = node.count()
        # Won't get a better solution; prune this branch
        if count > operand_count_result or count == operand_count_result and valid_result:
            continue
        expression = node.expression()
        current = int(expression.pop())
        # seen[current] has been updated in other branch and now there's a better result for current
        if current in seen and count - 1 > seen[current]:
            continue
        for p in primes:
            # Ignore removed prime or 1
            if p == prime or p == 1:
                continue
            # Can't do current / p
            if p > current:
                continue
            bound = get_remainders_bound(p, PRIMES[-1], MIN_NON_DECOMPOSABLE)
            remainders = get_possible_remainders(p, current, count, bound, prime_set, seen, unreachable)
            while remainders:
                new_count, quot, rem = heappop(remainders)
                # If it's not remainder it is excess
                is_remainder = p * quot + rem == current
                new_expression = expression.copy()
                new_expression.append(")")
                if rem != 0:
                    if rem in prime_set:
                        new_expression.append(f"{rem}")
                    else:
                        expr, _ = decompose(rem, prime_set, unreachable)
                        new_expression.append(")")
                        new_expression.extend(expr)
                        new_expression.append("(")
                    new_expression.append("+" if is_remainder else "-")
                new_expression.append(f"{p}")
                if quot != 1:
                    new_expression.append("*")
                    new_expression.append(f"{quot}")
                    new_count += 1
                # No solution here: prune branch
                if new_count > operand_count_result or new_count == operand_count_result and valid_result:
                    continue
                # Finished
                if quot == 1 or quot in prime_set:
                    if new_count <= operand_count_result:
                        expression_result = new_expression + (["("] * depth)
                        operand_count_result = new_count
                        valid_result = True
                    continue
                if quot < MIN_NON_DECOMPOSABLE:
                    # Remove the quotient previously added
                    new_expression.pop()
                    expr, extra = decompose(quot, prime_set, unreachable)
                    new_expression.append(")")
                    new_expression.extend(expr)
                    new_expression.append("(")
                    new_count += extra - 1
                    if new_count <= operand_count_result:
                        expression_result = new_expression + (["("] * depth)
                        operand_count_result = new_count
                        valid_result = True
                    continue
                min_count = new_count + estimation(quot, primes, prime)
                # Won't get a better solution
                if min_count > operand_count_result or min_count == operand_count_result and valid_result:
                    continue
                if operand_count_result * DEN >= min_count * NUM:
                    expr, max_count = find_random_solution(quot, primes, prime, len(primes) - 1, prime_set, unreachable)
                    max_count += new_count
                    # Update the solution with new one but don't prune this branch
                    if max_count < operand_count_result:
                        temp = new_expression.copy()
                        temp.pop()
                        temp.extend(expr)
                        expression_result = temp + (["("] * depth)
                        operand_count_result = max_count
                        valid_result = True
                # New node to the tree
                heappush(queue, Node(new_expression, depth + 1, new_count, min_count))
    return "".join(reversed(expression_result)), operand_count_result


def get_remainders_bound(p, lower_bound, upper_bound):
    """
    Returns the maximum "remainder" between lower_bound and upper_bound (exclusive) to be considered in the division
    n/p for any n to ensure low branching factor. Uses linear interpolation to achieve this.
    :param p: divisor in the division
    :param lower_bound: minimum remainder that can be considered
    :param upper_bound: maximum remainder that can be considered (exclusive)
    :return: a boundary for the remainder that ensures a correct branching factor
    """
    num, den = p - PRIMES[0], PRIMES[-1]
    return (num * upper_bound + (den - num) * lower_bound) / den


def get_possible_remainders(p, current, count, bound, prime_set, seen, unreachable):
    """
    Returns a heap with all possible "remainders" we're considering (from -bound to bound inclusive):
    current = p * quot + rem.
    :param p: prime divisor
    :param current: dividend
    :param count: current count of primes used
    :param bound: absolute value of maximum remainder
    :param prime_set: set containing all valid primes
    :param seen: dictionary that maps every seen quotient to its minimal path length
    :param unreachable: set with all non-decomposable numbers in this conditions between 1 and 97 with 2 primes
    :return: a list representing a heap of triplets (count, quotient, remainder) where count is the number of primes
    used in the decomposition current = p * quotient + remainder plus the previous count at this point
    """
    # current = quot * p + rem
    remainders = []
    quot = current // p
    rem = current % p
    while rem <= bound:
        new_count = count
        if rem != 0:
            new_count += 1 if rem in prime_set else 2 if rem not in unreachable else 3
        # Add to heap only if we can find a better solution
        if quot not in seen or seen[quot] > new_count:
            seen[quot] = new_count
            heappush(remainders, (new_count, quot, rem))
        rem += p
        quot -= 1
    # current = quot * p - rem
    quot = current // p + 1
    rem = p - (current % p)
    while rem <= bound:
        # rem != 0 for sure
        new_count = count + (1 if rem in prime_set else 2 if rem not in unreachable else 3)
        if quot not in seen or seen[quot] > new_count:
            seen[quot] = new_count
            heappush(remainders, (new_count, quot, rem))
        rem += p
        quot += 1
    return remainders


def find_random_solution(n, primes, prime, index, prime_set, unreachable):
    """
    Returns a solution of the problem using the same algorithm but only with the prime at index or lower so it can
    find a solution faster than the real algorithm.
    :param n: target number
    :param primes: ordered list with all available primes
    :param prime: unused prime
    :param index: index in primes for the prime that will be used to decompose n
    :param prime_set: set containing all valid primes
    :param unreachable: set with all non-decomposable numbers between 1 and 97 with 2 primes in this conditions
    :return: a list containing a valid expression that evaluates to n
    """
    div = primes[index] if primes[index] != prime else primes[index - 1]
    count = 1
    depth = 0
    expression = [f"{n}"]
    finished = False
    while not finished:
        n = int(expression.pop())
        while n < div:
            index = index - 1
            if primes[index] == prime:
                index -= 1
            div = primes[index]
        quot = n // div
        rem = n % div
        expression.append(")")
        depth += 1
        if rem != 0:
            if rem in prime_set:
                expression.append(f"{rem}")
                count += 1
            # We will find a two-operand decomposition for sure
            else:
                expr = decompose2(rem, prime_set)
                expression.append(")")
                expression.extend(expr)
                expression.append("(")
                count += 2
            expression.append("+")
        expression.append(f"{div}")
        if quot != 1:
            expression.append("*")
            expression.append(f"{quot}")
            count += 1
        # Finished
        if quot == 1 or quot in prime_set:
            expression.extend(["("] * depth)
            finished = True
        elif quot < MIN_NON_DECOMPOSABLE:
            # Remove the quotient previously added
            expression.pop()
            expr, extra = decompose(quot, prime_set, unreachable)
            expression.append(")")
            expression.extend(expr)
            expression.append("(")
            expression.extend(["("] * depth)
            count += extra - 1
            finished = True
    return expression, count


def decompose(n, primes, unreachable):
    """
    Decompose the given number n in 2 or 3 primes assuming it's possible.
    :param n: target number to be decomposed (must ensure n < MIN_NON_DECOMPOSABLE)
    :param primes: set with all usable primes
    :param unreachable: set with all non-decomposable numbers in this conditions between 1 and MIN_NON_DECOMPOSABLE with
    2 primes
    :return: a pair with a list with the correct expression that decomposes the target number n (or [] if couldn't
    decompose) and the number of primes used (2 or 3)
    """
    return (decompose2(n, primes), 2) if n not in unreachable else \
        (decompose3(n, primes, unreachable), 3)


def decompose2(n, primes):
    """
    Decompose the given number n in 2 primes assuming it's possible.
    :param n: target number to be decomposed (must ensure n < MIN_NON_DECOMPOSABLE)
    :param primes: set with all usable primes
    :return: a list with the correct expression that decomposes the target number n with 2 primes or [] if couldn't
    decompose
    """
    p, q = CROSS_PRODUCTS.get(n, (0, 0))
    if p in primes and q in primes:
        return [f"{q}", "*", f"{p}"]
    for p in primes:
        if p < n:
            q = n - p
            if q in primes:
                return [f"{q}", "+", f"{p}"]
        # p > n
        else:
            q = p - n
            if q in primes:
                return [f"{q}", "-", f"{p}"]
    return []


def decompose3(n, primes, unreachable):
    """
    Decompose the given number n in 3 primes assuming it's possible.
    :param n: target number to be decomposed (must ensure n < MIN_NON_DECOMPOSABLE)
    :param primes: set with all usable primes
    :param unreachable: set with all non-decomposable numbers in this conditions between 1 and MIN_NON_DECOMPOSABLE
    with 2 primes
    :return: a list with the correct expression that decomposes the target number n with 3 primes or [] if couldn't
    decompose
    """
    for x in NUMBERS.difference(unreachable):
        if x < n:
            q = n - x
            if q in primes:
                return [f"{q}", "+"] + decompose2(x, primes)
        # x > n
        else:
            q = x - n
            if q in primes:
                return [f"{q}", "-"] + decompose2(x, primes)
    return []


def estimation(n, primes, prime):
    """
    Returns a lower bound of the primes needed to decompose n. We assume we can divide the given number by the
    maximum available prime and get no remainder every time.
    :param n: target number to decompose with primes
    :param primes: ordered list with the available primes
    :param prime: unused prime
    :return: a lower bound of the number of primes needed to decompose the target number n
    """
    max_prime = primes[-1] if prime != primes[-1] else primes[-2]
    x = n
    min_count = 0
    while x > max_prime:
        x //= max_prime
        min_count += 1
    return min_count


def read_file(filename):
    """
    Reads the file given the filename assuming it has the contest structure.
    :param filename: name of the file to be read
    :return: a list of triplets (ID, TARGET, PRIME)
    """
    result = []
    with open(filename, 'r') as file:
        for line in file:
            if "ID" in line:
                continue
            result.append(tuple(map(int, line.split('|'))))
            # Lower targets before
            result.sort(key = lambda itp: itp[1])
        file.close()
    return result


def write_result(file, test_id, count, expression, flush = False):
    """
    Writes the given test result into the given file.
    :param file: file where to write the results
    :param test_id: id of the test
    :param count: number of primes used to solve the test
    :param expression: string expression used to solve the test
    :param flush: determines whether to flush the file or not (False by default)
    :return: nothing
    """
    file.write(f"{TEAM_NAME}|{test_id}|{count}|{expression}\n")
    # Flush to make sure the file gets saved
    if flush:
        file.flush()


def write_timestamp(file, date = None):
    """
    Prints the current timestamp with format YYYY-MM-DD-HH:MM:SS.SSSS to the given file.
    :param file: file where to print the timestamp
    :param date: date to be written (datetime.now() by default)
    :return: nothing
    """
    date = (date or datetime.now()).strftime("%Y-%m-%d-%H:%M:%S.%f")[:-2] + "\n"
    file.write(date)


def main():
    """
    Function that read the file, launches the algorithm on multiple threads and writes the result.
    :return: nothing
    """
    start_time = time()
    entries = read_file(IN_FILENAME)
    with open(OUT_FILENAME, 'w') as out_file:
        write_timestamp(out_file, START_MOMENT)
        for test_id, target, prime in entries:
            expression, count = find_expression(target, PRIMES, prime)
            # Flush only if we are running out of time
            write_result(out_file, test_id, count, expression, flush = time() - start_time > MAX_TIME - 15)
        write_timestamp(out_file)
        out_file.close()


if __name__ == '__main__':
    main()
