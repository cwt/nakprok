# INVALID - This should fail type checking (missing annotations)


def add(a, b):  # ERROR: missing type annotations
    return a + b


def greet(name):  # ERROR: missing type annotation
    return f"Hello, {name}!"


def factorial(n):  # ERROR: missing return type and param type
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)


def main():  # ERROR: missing return type
    result = add(10, 20)  # ERROR: untyped variable
    print(result)

    greeting = greet("World")  # ERROR: untyped variable
    print(greeting)
