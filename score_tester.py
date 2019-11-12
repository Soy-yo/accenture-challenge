import re
import sys

from colorama import init, Fore

init(autoreset = True, convert = True)

IN_FILENAME = "TEST"
OUT_FILENAME = "SCORE"
EXTENSION = "txt"
COMPARE_RESULTS = len(sys.argv) > 1 and sys.argv[1] == "-c"


def main():
    better = 0
    worst = 0
    with open(f"{IN_FILENAME}.{EXTENSION}", 'r') as test_file:
        with open(f"{OUT_FILENAME}.{EXTENSION}", 'r') as score_file:
            tests = {test_id: (int(target), int(prime)) for test_id, target, prime in
                     [tuple(line.split('|')) for line in test_file if "ID" not in line]}
            solutions = {test_id: (int(number), expression) for _, test_id, number, expression in
                         [tuple(line.split('|')) for line in score_file if '|' in line]}
            cmp_file = open(f"{OUT_FILENAME}_cmp.{EXTENSION}", 'r') if COMPARE_RESULTS else None
            numbers = {test_id: int(number) for _, test_id, number, _ in
                       [tuple(line.split('|')) for line in cmp_file if '|' in line]} \
                if cmp_file and cmp_file.mode == 'r' else None
            avg = 0
            for test_id in tests:
                target, prime = tests[test_id]
                number, expression = solutions[test_id]
                expression = expression.replace('\n', '')
                result = int(eval(expression))
                numbers_used = [int(s) for s in re.split('[\(\)\+\-*\/]+', expression) if s]
                actual_numbers = len(numbers_used)
                avg += number
                # Error cases
                if result != target:
                    print(f"{Fore.RED}ERROR: Test {test_id} failed!\nExpected {target} and got {expression} = {result}")
                    continue
                if prime in numbers_used:
                    print(f"{Fore.RED}ERROR: Test {test_id} failed!\n{prime} should not be in {expression}")
                    continue
                if number != actual_numbers:
                    print(f"{Fore.RED}ERROR: Test {test_id} failed!\nCalculated numbers {number} does not match with "
                          f"actual numbers {actual_numbers}")
                    continue
                # Correct cases
                if COMPARE_RESULTS and number > numbers[test_id]:
                    print(
                        f"{Fore.YELLOW}WARNING: Test {test_id} passed but using more primes ({number} > {numbers[test_id]})")
                    worst += 1
                elif COMPARE_RESULTS and number < numbers[test_id]:
                    print(
                        f"{Fore.CYAN}CORRECT: Test {test_id} passed successfully using less primes ({number} < {numbers[test_id]})")
                    better += 1
                else:
                    pass
                    print(f"{Fore.LIGHTGREEN_EX}CORRECT: Test {test_id} passed successfully ({number} primes)")
            avg /= len(tests)
            print(f"\nAverage primes used: {avg}")
            if COMPARE_RESULTS:
                cmp_file.close()
                print(f"\nBETTER RESULTS: {better}\nWORST RESULTS: {worst}")


if __name__ == '__main__':
    main()
