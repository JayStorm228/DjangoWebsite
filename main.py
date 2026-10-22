from dataclasses import dataclass


@dataclass
class Test:
    arg1: int = 0
    arg2 = str


def main():

    print("Hello from test-django!")


if __name__ == "__main__":
    main()
