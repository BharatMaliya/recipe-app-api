"""
Calculator function
"""


def add(x, y):
    """Add two numbers together"""
    return x + y


def subtract(x, y):
    """Subtract x from y and return value"""
    return x - y


def multiply(x, y):
    """Multiply x by y and return value"""
    return x * y


def divide(x, y):
    """Divide x by y and return value"""
    if y == 0:
        raise ValueError('Cannot divide by zero!')
    return x / y
# Compare this snippet from app/app/views.py:
