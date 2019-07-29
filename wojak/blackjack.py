import logging 

logger = logging.getLogger("blackjack")
logger.info("Starting blackjack...")

import sys
import random
from asyncio import sleep
from datetime import datetime
from . import functions


class Game:
    def __init__(self, ctx, dbpath, channelSet, allPlayerSet):
        self.players = []
        self.channelID = ctx.channel.id
        self.ctx = ctx
        self.channelSet = channelSet
        self.allPlayerSet = allPlayerSet
        self.thisPlayerSet = set()
        self.conn = functions.createConnection(dbpath)
        self.conn.isolation_level = None
        self.cursor = self.conn.cursor()
        self.playerLimit = 6 # for now...
        self.isFirstGame = True

    def allPlayersStr(self):
        string = ""
        for player in self.players[:-1]:
            string += player.getName() + " -> "
        return string + self.players[-1].getName() + ", and me as the dealer."

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
            self.players.append(newPlayer)
            await sleep(2)
        
    async def gatherPlayers(self, isFirstGame):
        rawPlayers = []
        if isFirstGame:
            initiator = self.ctx.message.author
            rawPlayers.append(initiator)
            self.thisPlayerSet.add(initiator.id)
            self.allPlayerSet.add(initiator.id)
        gatherMessage = await self.ctx.send('A new blackjack game is starting in 15 seconds! Type "join" to enter! ')
        await sleep(15)
        messages = await self.ctx.history(after=gatherMessage, before=datetime.utcnow()).flatten()
        for message in messages:
            if message.content == "join" and message.author not in rawPlayers and message.author.id not in self.allPlayerSet:
                rawPlayers.append(message.author)
                self.thisPlayerSet.add(message.author.id)
                self.allPlayerSet.add(message.author.id)
            if len(self.thisPlayerSet) >= self.playerLimit:
                break
        await self.createPlayers(rawPlayers)

    def cashOut(self, player):
        self.cursor.execute("update money set wallet = ? where id = ?", (player.getWallet(), player.getID()))

    #TODO: async def removeIdlePlayer(self, player)

    async def removePlayers(self):
        staySet = set()
        removeSet = set()
        removeMessage = await self.ctx.send('This hand is over, but we\'ll start again in 10 seconds. Type "stay" to remain at the table.')
        await sleep(10)
        messages = await self.ctx.history(after=removeMessage, before=datetime.utcnow()).flatten()
        for message in messages:
            if message.author.id in self.thisPlayerSet and message.content == "stay":
                staySet.add(message.author.id)
        for player in self.players:
            if player.getID() not in staySet:
                removeSet.add(player)
        for player in removeSet:
            await self.ctx.send("{0}, you'll be leaving with {1} feelbucks. See ya next time!".format(player.getName(), player.getWallet()))
            self.cashOut(player)
            self.players.remove(player)
            self.thisPlayerSet.remove(player.getID())
            self.allPlayerSet.remove(player.getID())
            await sleep(2)
        if self.players:
            await self.ctx.send("The remaining players are:\n{0}".format(self.allPlayersStr()))

    def removeAllPlayers(self):
        for player in self.players:
            self.cashOut(player)
            self.thisPlayerSet.remove(player.getID())
            self.allPlayerSet.remove(player.getID())
        self.players = []

    async def runGame(self):
        try:
            while True: # continue playing games while players remain
                await self.gatherPlayers(self.isFirstGame)
                await self.ctx.send("Alright, the players are rounded up. The order of play will be:\n{0}".format(self.allPlayersStr()))
                await sleep(2)
                await self.removePlayers()
                if not self.players:
                    break
                self.isFirstGame = False
            await self.ctx.send("Looks like that's all for this game! Come play again soon!")

        finally: # paranoid redundant checks 
            self.channelSet.remove(self.channelID)
            self.removeAllPlayers()
            self.conn.close()


class Player:
    def __init__(self, name, ID = 0, wallet = 100):
        self.name = name
        self.ID = ID
        self.wallet = wallet
        self.hands = [Hand()]
        self.currentHand = 0

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
    
    def bet(self, amount):
        self.wallet -= amount
        self.hands[self.currentHand].bet(amount)

    def double(self):
        amount = self.hands[self.currentHand].getBet()
        self.wallet -= amount
        self.hands[self.currentHand].double()

    def winsHand(self):
        amount = self.hands[self.currentHand].getBet()
        self.wallet += (amount * 2)

    def getID(self):
        return self.ID

    def getWallet(self):
        return self.wallet

    def getName(self):
        return self.name

    def allHandsStr(self):
        string = self.name + "'s hands:\n"
        for hand in self.hands:
            string += ("{0}\n".format(str(hand)))
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

    def bet(self, amount):
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

    def __str__(self):
        return allCardStr(self.cards) + str(self.value) + " // Bet: " + str(self.bet)


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



