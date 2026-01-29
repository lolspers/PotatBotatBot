unitToSeconds = {
    "hours": 3600,
    "minutes": 60,
    "seconds": 1
}


rankPrices: dict[int, int] = {
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


farmingCommands: list[str] = ["potato", "steal", "trample", "cdr", "quiz"]
shopItems: list[str] = [f"shop-{i}" for i in shopPrices.keys()]



def rankPrice(prestige: int, rank: int) -> int:
    if rank == 6:
        return prestigePrice(prestige)
    
    return rankPrices[rank]



def prestigePrice(prestige: int) -> int:
    return 100_000 + (20_000 * prestige)



def shopItemPrice(item: str, rank: int) -> int:
    return shopPrices[item] * rank



def formatSeconds(n: int | float) -> str:
    n = int(n)
    parts = []
    
    for timeUnit, s in unitToSeconds.items():
        if n < 0:
            s = -s
        
        value = n // s
        n %= s
        
        if value != 0:
            parts.append(f"{value} {timeUnit if value != 1 else timeUnit[:-1]}")


    return " and ".join(", ".join(parts).rsplit(", ", 1)) if parts else "0 seconds"



def relative(n: int | float) -> str:
    formatted = formatSeconds(n)

    return f"in {formatted}" if n >= 0 else f"{formatted} ago"