import logging 

logger = logging.getLogger("blackjack")
logger.info("Starting blackjack...")

import sys
import random
from asyncio import sleep
from datetime import datetime
from . import functions

PLAYER_LIMIT = 6 #max players in one game

class Game:
    def __init__(self, ctx, dbpath, channelSet, allPlayerSet):
        self.playerDict = dict()
        self.currentPlayers = self.playerDict.values()
        self.currentPlayerIDs = self.playerDict.keys()
        self.channelID = ctx.channel.id
        self.ctx = ctx
        self.channelSet = channelSet
        self.allPlayerSet = allPlayerSet
        self.conn = functions.createConnection(dbpath)
        self.conn.isolation_level = None
        self.cursor = self.conn.cursor()
        self.isFirstGame = True
        self.shoe = Shoe()
        self.dealer = Dealer("Wojak") #needs no id or wallet


    def allPlayersStr(self):
        string = ""
        allPlayers = list(iter(self.currentPlayers))
        for player in allPlayers[:-1]:
            string += player.getName() + " -> "
        return string + allPlayers[-1].getName() + ", and me as the dealer."


    def allWalletsStr(self):
        string = "\n--\nYour wallets are as follows:\n"
        allPlayers = list(iter(self.currentPlayers))
        for player in allPlayers:
            string += player.getName() + ": " + str(player.getWallet()) + "\n"
        return string + "--\n"


    def allHandsStr(self):
        string = "\n--\n"
        allPlayers = list(iter(self.currentPlayers))
        string += self.dealer.handStr()
        for player in allPlayers:
            string += player.allHandsStr()
        return string + "--\n"


    def shuffleShoe(self):
        self.shoe.shuffle()
        self.shoe.shuffle() # twice for good luck


    async def createPlayers(self, rawPlayers):
        for player in rawPlayers:
            self.cursor.execute("select wallet from money where id = ?", (player.id,))
            wallet = self.cursor.fetchone()
            if wallet:
                newPlayer = Player(player.name, player.id, wallet[0])
                await self.ctx.send("Welcome back, {0}! You currently have {1} feelbucks!".format(player.name, wallet[0]))
            else:
                newPlayer = Player(player.name, player.id, 100)
                self.cursor.execute("insert into money values (?, ?)", (player.id, 100))
                await self.ctx.send("Looks like you're new here, {0}. You'll start with 100 feelbucks!".format(player.name))
            self.playerDict[player.id] = newPlayer
            await sleep(2)

        
    async def gatherPlayers(self, isFirstGame):
        rawPlayers = []
        if isFirstGame: # add person who started game first, but only on first game played
            initiator = self.ctx.message.author
            rawPlayers.append(initiator)
            self.allPlayerSet.add(initiator.id)
        gatherMessage = await self.ctx.send('A new blackjack game is starting in 15 seconds! Type "join" to enter! Max number of players is ' + str(PLAYER_LIMIT) + ".")
        await sleep(15)
        messages = await self.ctx.history(after=gatherMessage, before=datetime.utcnow()).flatten()
        for message in messages:
            if (len(self.playerDict) + len(rawPlayers)) >= PLAYER_LIMIT:
                break
            if message.content == "join" and message.author not in rawPlayers and message.author.id not in self.allPlayerSet:
                rawPlayers.append(message.author)
                self.allPlayerSet.add(message.author.id)
        await self.createPlayers(rawPlayers)


    def cashOut(self, player):
        self.cursor.execute("update money set wallet = ? where id = ?", (player.getWallet(), player.getID()))


    def remove(self, player):
        self.cashOut(player)
        self.playerDict.pop(player.getID())
        self.allPlayerSet.remove(player.getID())


    async def removeIdlePlayer(self, player, removeSet, message):
        if player.getID() in removeSet:
            self.remove(player)
            await self.ctx.send(message)
            await sleep(2)


    async def removePlayers(self):
        removeSet = set(iter(self.currentPlayerIDs))
        removeMessage = await self.ctx.send('This hand is over, but we\'ll start again in 10 seconds. Type "stay" to remain at the table.')
        await sleep(10)

        messages = await self.ctx.history(after=removeMessage, before=datetime.utcnow()).flatten()
        for message in messages:
            if message.author.id in self.currentPlayerIDs and message.content == "stay":
                removeSet.remove(message.author.id)

        for player in list(iter(self.currentPlayers)):
            await self.removeIdlePlayer(player, removeSet, "{0}, you'll be leaving with {1} feelbucks. See ya next time!".format(player.getName(), player.getWallet()))

        if self.playerDict:
            await self.ctx.send("The remaining players are:\n{0}".format(self.allPlayersStr()))


    # slightly different from regular remove or removeIdle. Also should be redundant, but you never know...
    def removeAllPlayers(self): 
        for player in self.currentPlayers:
            self.cashOut(player)
            self.allPlayerSet.remove(player.getID())
        self.playerDict = dict()


    def isValidBet(self, message):
        if len(message) == 2 and message[0] == "bet":
            try:
                value = int(message[1])
                if value > 0:
                    return True
            except ValueError:
                return False


    async def gatherBets(self):
        removeSet = set(iter(self.currentPlayerIDs))
        betMessage = await self.ctx.send('Time to place your bets! Type "bet <value>" to bet. Values greater than your wallet will bet your entire remaining balance. Betting ends in 15 seconds!' + self.allWalletsStr())
        await sleep(15)
        messages = await self.ctx.history(after=betMessage, before=datetime.utcnow()).flatten()
        for message in messages:
            if message.author.id in removeSet:
                newBet = message.content.split()
                if self.isValidBet(newBet):
                    betValue = int(newBet[1])
                    player = self.playerDict[message.author.id]
                    if betValue > player.getWallet():
                        betValue = player.getWallet()
                    player.placeBet(betValue)
                    removeSet.remove(message.author.id)
        for player in list(iter(self.currentPlayers)):
            await self.removeIdlePlayer(player, removeSet, "Sorry {0}, you were removed for inactivity and current bets have been lost...".format(player.name))


    async def dealCards(self):
        for x in range(0, 2):
            for player in self.currentPlayers:
                player.hit(self.shoe.draw())
            self.dealer.hit(self.shoe.draw())
        await self.ctx.send("The cards have been dealt, let's see what we got..." + self.allHandsStr() + "\n Take your time to inspect the table! The game continues in 30 seconds")
        await sleep(30)

        
    async def playBlackjack(self):
        await self.ctx.send("Alright, the players are rounded up. The order of play will be:\n{0}\nFrom here on out, idle players will be removed from the game and lose their bets. Pay attention!\n".format(self.allPlayersStr()))
        await sleep(3)

        await self.gatherBets()
        
        if not self.playerDict: # ensure all players were not idle before continuing
            return
        
        self.shuffleShoe()
        await self.dealCards()


    async def runGame(self):
        try:
            while True: # continue playing games while players remain
                await self.gatherPlayers(self.isFirstGame)
                await self.playBlackjack()
                if self.playerDict:
                    await self.removePlayers()
                    if not self.playerDict:
                        break
                else: # game stops when no players remain
                    break
                self.isFirstGame = False 
            await self.ctx.send("Looks like that's all for this game! Come play again soon!")

        finally: # paranoid redundant checks 
            self.channelSet.remove(self.channelID)
            self.removeAllPlayers()
            self.conn.close()


class Dealer:
    def __init__(self, name):
        self.name = name
        self.hand = Hand()


    def hit(self, card):
        self.hand.add(card)
        return self.hand.getValue() > 21


    def getHandValue(self):
        return self.hand.getValue()


    def handStr(self):
        return self.name + "'s hand (dealer) :\n" + "{0}\n\n".format(self.hand.dealerStr())


class Player:
    def __init__(self, name, ID = 0, wallet = 100):
        self.name = name
        self.ID = ID
        self.wallet = wallet
        self.hands = [Hand()]
        self.currentHand = 0
        self.totalBet = 0


    def hit(self, card):
        self.hands[self.currentHand].add(card)
        return self.hands[self.currentHand].getValue() > 21


    def nextHand(self):
        self.currentHand += 1
        return self.currentHand < len(self.hands)

            
    def split(self):
        card = self.hands[self.currentHand].split()
        splitHand = Hand()
        splitHand.add(card)
        self.hands.append(splitHand)


    def getHandValue(self):
        return self.hands[self.currentHand].getValue()

    
    def placeBet(self, amount):
        #self.wallet -= amount
        self.totalBet += amount
        self.hands[self.currentHand].placeBet(amount)


    def double(self):
        amount = self.hands[self.currentHand].getBet()
        self.wallet -= amount
        self.hands[self.currentHand].double()


    def winsHand(self):
        amount = self.hands[self.currentHand].getBet()
        self.wallet += (amount * 2)
        self.totalBet -= amount


    def resetHands(self):
        self.hands = [Hand()]
        self.currentHand = 0


    def getID(self):
        return self.ID


    def getWallet(self):
        return self.wallet


    def getName(self):
        return self.name


    def allHandsStr(self):
        string = self.name + "'s hands:\n"
        for hand in self.hands:
            string += ("{0}\n\n".format(str(hand)))
        return string 


class Hand:
    def __init__(self):
        self.cards = []
        self.softAces = 0
        self.value = 0
        self.bet = 0


    def add(self, card):
        self.cards.append(card)
        self.value += card.getValue()
        if card.getValue() == 11:
            self.softAces += 1
        while self.value > 21 and self.softAces > 0:
            self.softAces -= 1
            self.value -= 10


    def placeBet(self, amount):
        self.bet = amount


    def double(self):
        self.bet *= 2


    def split(self):
        card = self.cards.pop()
        if card == self.cards[0]:
            self.value = card.getValue()
            if card.getValue() == 11:
                self.softAces = 1
        return card


    def getBet(self):
        return self.bet


    def getValue(self):
        return self.value


    def dealerStr(self):
        string = "[ (??)  "
        for card in self.cards[1:] if len(self.cards) >= 2 else list():
            string += "{0} ".format(str(card))
        return string + "]"


    def __str__(self):
        return allCardStr(self.cards) + "  " + str(self.value) + "    // Bet: " + str(self.bet)


class Shoe:
    def __init__(self):
        self.cards = []
        self.position = 0


        # Shoe initialization...
        NUMBER_CARDS = [2, 3, 4, 5, 6, 7, 8, 9, 10]
        FACE_CARDS = ["J", "Q", "K"]
        SUITS = [":spades:", ":hearts:", ":diamonds:", ":clubs:"]
        for i in range(0, 4):
            for value in NUMBER_CARDS:
                for suit in SUITS:
                    self.cards.append(Card(str(value), value, suit))
            for name in FACE_CARDS:
                for suit in SUITS:
                    self.cards.append(Card(name, 10, suit))
            self.cards.append(Card("A", 11, suit))


    def draw(self):
        card = self.cards[self.position].getCopy()
        self.position += 1
        return card

    
    def shuffle(self):
        random.shuffle(self.cards)
        self.position = 0

    
    def __str__(self):
        return allCardStr(self.cards)


class Card:
    def __init__(self, name, value, suit):
        self.name = name
        self.value = value
        self.suit = suit


    def getCopy(self):
        return Card(self.name, self.value, self.suit)


    def getValue(self):
        return self.value

    
    def __eq__(self, rt):
        return isinstance(rt, Card) and self.name == rt.name


    def __ne__(self, rt):
        return not self.__eq__(rt)


    def __str__(self):
        return "{0}{1}".format(self.name, self.suit)


def allCardStr(cards):
    string = "[ "
    for card in cards:
        string += ("{0} ".format(str(card)))
    return string + "]"

