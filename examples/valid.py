# VALID - This should pass type checking


def add(a: int, b: int) -> int:
    return a + b


def greet(name: str) -> str:
    return f"Hello, {name}!"


def factorial(n: int) -> int:
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)


def main() -> None:
    result: int = add(10, 20)
    print(result)

    greeting: str = greet("World")
    print(greeting)

    fact: int = factorial(5)
    print(f"5! = {fact}")


if __name__ == "__main__":
    main()
