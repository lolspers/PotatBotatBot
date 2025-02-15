potatPrefix: str = "#"
rankupCosts: dict = {
    1: 1000,
    2: 5000,
    3: 10000,
    4: 25000,
    5: 50000,
    6: 100000
}
loopDelay: int = 1
twitchApi = "https://api.twitch.tv/helix/"
potatApi = "https://api.potat.app/"
allFarmingCommands = ["potato", "steal", "trample", "cdr", "quiz"]
allShopItems = ["shop-fertilizer", "shop-guard", "shop-cdr", "shop-quiz"]

executedCommand: bool = True
boughtShopItem: bool = True
executions = 0