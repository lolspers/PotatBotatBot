from classes.command import Command, ShopItem
from utils import rankPrices



class Potato(Command):
    def __init__(self) -> None:
        self.trigger: str = "potato"
        self.usage: int = 0


class Steal(Command):
    def __init__(self) -> None:
        self.trigger: str = "steal"
        self.usage: int = 0
        self.stolenCount: int = 0


class Trample(Command):
    def __init__(self) -> None:
        self.trigger: str = "trample"
        self.usage: int = 0
        self.trampledCount: int = 0


class Cdr(Command):
    def __init__(self) -> None:
        self.trigger: str = "cdr"
        self.baseCost: int = 15
    
    @property
    def cost(self) -> int:
        return int(self.baseCost * self.rank * (1 + self.prestige * 0.1))


class Quiz(Command):
    def __init__(self) -> None:
        self.trigger: str = "quiz"
        self.attempted: int = 0
        self.completed: int = 0



class Rankup(Command):
    def __init__(self) -> None:
        self.trigger = "rankup"
        self.ready = True
    
    @property
    def cost(self) -> int:
        return rankPrices[self.rank]
    
    @property
    def enabled(self) -> bool:
        return bool(self.rank < 6)
    

class Prestige(Command):
    def __init__(self) -> None:
        self.trigger = "prestige"
        self.ready = True

    @property
    def cost(self) -> int:
        return rankPrices[6] + 20_000 * self.prestige
    
    @property
    def enabled(self) -> bool:
        return bool(self.rank == 6)
    


class ShopCdr(ShopItem):
    def __init__(self) -> None:
        self.trigger: str = "shop cdr"
        self.baseCost: int = 30


class ShopFertilizer(ShopItem):
    def __init__(self) -> None:
        self.trigger: str = "shop fertilizer"
        self.baseCost: int = 30


class ShopGuard(ShopItem):
    def __init__(self) -> None:
        self.trigger: str = "shop guard"
        self.baseCost: int = 100


class ShopQuiz(ShopItem):
    def __init__(self) -> None:
        self.trigger: str = "shop quiz"
        self.baseCost: int = 125



# only used for stats
class Gamble:
    def __init__(self) -> None:
        self.wins: int = 0
        self.losses: int = 0
        self.earned: int = 0
        self.lost: int = 0


class Duel:
    def __init__(self) -> None:
        self.wins: int = 0
        self.losses: int = 0
        self.earned: int = 0
        self.lost: int = 0
        self.caughtLosses: int = 0



class Commands:
    def __init__(self) -> None:
        self.potato: Potato = Potato()
        self.steal: Steal = Steal()
        self.trample: Trample = Trample()
        self.cdr: Cdr = Cdr()
        self.quiz: Quiz = Quiz()
        self.rankup: Rankup = Rankup()
        self.prestige: Prestige = Prestige()

        self.shopCdr: ShopCdr = ShopCdr()
        self.shopFertilizer: ShopFertilizer = ShopFertilizer()
        self.shopGuard: ShopGuard = ShopGuard()
        self.shopQuiz: ShopQuiz = ShopQuiz()

        self.gamble: Gamble = Gamble()
        self.duel: Duel = Duel()

        self.executable: list[Command] = [
            self.potato,
            self.steal,
            self.trample,
            self.cdr,
            self.quiz,
            self.rankup,
            self.prestige,
            self.shopCdr,
            self.shopFertilizer,
            self.shopGuard,
            self.shopQuiz
        ]