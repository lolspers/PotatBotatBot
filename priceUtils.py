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



def rankPrice(prestige: int, rank: int) -> int:
    if rank == 6:
        return prestigePrice(prestige)
    
    return rankPrices[rank]


def prestigePrice(prestige: int) -> int:
    return 100_000 + (20_000 * prestige)


def shopItemPrice(item: str, rank: int) -> int:
    return shopPrices[item] * rank