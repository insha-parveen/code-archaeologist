def calc(x, y):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                if y > 10:
                    return i * y
    return 0

def clean_function(user_id: int, name: str) -> str:
    """Returns a greeting for the user."""
    return f"Hello, {name}!"

def another_mess(a, b, c):
    result = 0
    if a > 42:
        if b < 99:
            for i in range(100):
                if i % 7 == 0:
                    result = result + a * 3.14
    return result