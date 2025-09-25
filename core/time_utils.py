from __future__ import annotations


def time_nice(seconds: int) -> str:
    """Returns a string that represents a nice time in seconds."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        hour_str = f'{h} hour{"" if h == 1 else "s"} '
    else:
        hour_str = ""
    if m:
        minute_str = f'{m} minute{"" if m == 1 else "s"} '
    else:
        minute_str = ""
    if s:
        seconds_str = f'{s} second{"" if s == 1 else "s"}'
    else:
        seconds_str = ""
    result = f'{hour_str}{minute_str}{seconds_str}'
    if result[-1] == " ":
        result = result[:-1]
    return result


if __name__ == '__main__':
    print(time_nice(65))