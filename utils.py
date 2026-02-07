shortUnitToSeconds = {
    "d": 86400,
    "h": 3600,
    "m": 60,
    "s": 1
}


rankPrices: dict[int, int] = {
    0: 1000,
    1: 1000,
    2: 5000,
    3: 10000,
    4: 25000,
    5: 50000,
    6: 100000
}

shopPrices: dict[str, int] = {
    "cdr": 30,
    "fertilizer": 30,
    "guard": 100,
    "quiz": 125
}


def formatSeconds(n: int | float) -> str:
    n = int(n)
    parts = []
    
    for timeUnit, s in shortUnitToSeconds.items():
        if n < 0:
            s = -s
        
        value = n // s
        n %= s
        
        if value != 0:
            parts.append(f"{value}{timeUnit if value != 1 else timeUnit[:-1]}")


    return " and ".join(", ".join(parts).rsplit(", ", 1)) if parts else "0 seconds"



def relative(n: int | float) -> str:
    formatted = formatSeconds(n)

    return f"in {formatted}" if n >= 0 else f"{formatted} ago"