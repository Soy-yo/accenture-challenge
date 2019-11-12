import random

MAX = 10 ** 9
P = [
    1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
    43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97
]
TESTS = 100
FILENAME = "TEST.txt"


def main():
    with open(FILENAME, 'w') as file:
        file.write("ID|TARGET|PRIMO\n")
        for i in range(TESTS):
            file.write(f"{i + 1}|{random.randint(0, MAX)}|{P[random.randint(0, len(P) - 1)]}\n")
        file.close()


if __name__ == '__main__':
    main()
