import logging 

logger = logging.getLogger("blackjack")
logger.info("Starting blackjack...")

import sys
import random
from asyncio import sleep
from datetime import datetime
from . import functions

# Imagine a language without enforced constants LUL

PLAYER_LIMIT = 6 #max players in one game
PLAY = "PLAY"
WIN = "WIN"
PUSH = "PUSH"
LOSE = "LOSE"


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
        string = "\n--\n\n"
        allPlayers = list(iter(self.currentPlayers))
        string += self.dealer.getName() + "'s hand:\n" + self.dealer.handHideStr() + "\n\n"
        for player in allPlayers:
            string += player.getName() + "'s hands:\n" + player.allHandsStr()
        return string + "--\n"


    def allResultsStr(self):
        string = "\n--\n\n"
        allPlayers = list(iter(self.currentPlayers))
        string += self.dealer.getName() + "'s hand:\n " + self.dealer.handShowStr() + "\n\n"
        for player in allPlayers:
            string += player.getName() + "'s hands:\n " + player.allResultsStr()
        return string + "--\n"


    def shuffleShoe(self):
        self.shoe.shuffle()
        self.shoe.shuffle() # twice for good luck


    async def createPlayers(self, rawPlayers):
        for player in rawPlayers:
            self.cursor.execute("select wallet from money where id = ?", (player.id,))
            wallet = self.cursor.fetchone()
            if wallet:
                withdraw = wallet[0]
                if withdraw <= 0: # just in case negative money comes up somehow
                    withdraw = 100
                    newPlayer = Player(player.name, player.id, withdraw)
                    await self.ctx.send("Welcome back, {0}! You ran out of money, but you sold us your car for 100 feelbucks!".format(player.name, withdraw))
                else:
                    newPlayer = Player(player.name, player.id, withdraw)
                    await self.ctx.send("Welcome back, {0}! You currently have {1} feelbucks!".format(player.name, withdraw))
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
            if message.content.lower() == "join" and message.author not in rawPlayers and message.author.id not in self.allPlayerSet:
                rawPlayers.append(message.author)
                self.allPlayerSet.add(message.author.id)
        await self.createPlayers(rawPlayers)


    def cashOut(self, player):
        self.cursor.execute("update money set wallet = ? where id = ?", (player.getWallet(), player.getID()))


    def remove(self, player):
        self.cashOut(player)
        self.playerDict.pop(player.getID())
        self.allPlayerSet.discard(player.getID())


    async def removeIdlePlayer(self, player, removeSet, message):
        if player.getID() in removeSet:
            self.remove(player)
            await self.ctx.send(message)
            await sleep(2)


    async def removePlayers(self):
        removeSet = set(iter(self.currentPlayerIDs))
        removeMessage = await self.ctx.send('This hand is over, but we\'ll start again in 15 seconds. Type "stay" to remain at the table.')
        await sleep(15)

        messages = await self.ctx.history(after=removeMessage, before=datetime.utcnow()).flatten()
        for message in messages:
            if message.author.id in self.currentPlayerIDs and message.content.lower() == "stay":
                removeSet.discard(message.author.id)

        for player in list(iter(self.currentPlayers)):
            if player.getWallet() == 0:
                await self.removeIdlePlayer(player, set([player.getID()]), "{0}, you ran out of feelbucks, I know that feel... If you join again you'll get 100 feelbucks... for a price.".format(player.getName()))
            else:
                await self.removeIdlePlayer(player, removeSet, "{0}, you'll be leaving with {1} feelbucks. See ya next time!".format(player.getName(), player.getWallet()))

        if self.playerDict:
            await self.ctx.send("The remaining players are:\n{0}".format(self.allPlayersStr()))


    # slightly different from regular remove or removeIdle. Also should be redundant, but you never know...
    def removeAllPlayers(self): 
        for player in self.currentPlayers:
            self.cashOut(player)
            self.allPlayerSet.remove(player.getID())
        self.playerDict = dict()


    def resetHands(self):
        self.dealer.resetHand()
        for player in self.currentPlayers:
            player.resetHands()

   
    def hasPlayable(self):
        for player in self.currentPlayers:
            if player.hasPlayable():
                return True
        return False


    def isValidBet(self, message):
        if len(message) == 2 and message[0].lower() == "bet":
            try:
                value = int(message[1])
                if value > 0:
                    return True
            except ValueError:
                return False


    async def gatherBets(self):
        removeSet = set(iter(self.currentPlayerIDs))
        betMessage = await self.ctx.send('Time to place your bets! Values greater than your wallet will bet your entire remaining balance. Betting ends in 15 seconds!\n**Type "bet <value>" to place your bet**' + self.allWalletsStr())
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
                    removeSet.discard(message.author.id)
        for player in list(iter(self.currentPlayers)):
            await self.removeIdlePlayer(player, removeSet, "Sorry {0}, you were removed for inactivity...".format(player.name))


    async def dealCards(self):
        for x in range(0, 2):
            for player in self.currentPlayers:
                player.hit(self.shoe.draw())
            self.dealer.hit(self.shoe.draw())
        await self.ctx.send("The cards have been dealt, let's see what we got..." + self.allHandsStr() + "Take your time to inspect the table! The game continues in 15 seconds...")
        await sleep(15)
        

    async def checkNaturals(self):
        await sleep(3)
        if self.dealer.getHandValue() == 21:
            await self.ctx.send("Woblakjak! Any players who failed to get a natural will lose their bet...\n" + self.dealer.handShowStr())
            await sleep(3)
            for player in self.currentPlayers:
                if player.getHandValue() < 21:
                    await self.ctx.send("{0}, you have lost your bet...".format(player.getName()))
                    await sleep(3)
                    player.loseHand()
                elif player.getHandValue() == 21:
                    await self.ctx.send("{0}, you got blackjack too! Looks like we push...".format(player.getName()))
                    await sleep(3)
                    player.pushHand()
            return True
        for player in self.currentPlayers:
            if player.getHandValue() == 21:
                await self.ctx.send("Congrats {0}, you got blackjack, you win your bet!".format(player.getName()))
                player.winHand()
        return False


    async def checkBust(self, player):
        if player.getHandValue() > 21:
            await self.ctx.send("You bust! You lose your bet...\n{0}".format(player.currentHandStr()))
            await sleep(3)
            return True
        return False


    async def playHands(self, player):
        await self.ctx.send("It's your turn, {0}! You have 10 seconds for each choice.\n{1} Wojak's hand\n--".format(player.getName(), self.dealer.handHideStr()))
        await sleep(2)
        while player.stillPlaying():
            idle = True
            optionMessage = await self.ctx.send("{0}\nOptions: {1}".format(player.currentHandStr(), player.optionsStr()))
            await sleep(10)

            messages = await self.ctx.history(after=optionMessage, before=datetime.utcnow()).flatten()
            for message in messages:
                if message.author.id == player.getID():
                    if message.content.lower() == "hit":
                        player.hit(self.shoe.draw())
                        if await self.checkBust(player):
                            player.loseHand()
                        else:
                            await self.ctx.send("Hit!")
                            await sleep(1)
                        idle = False
                        break

                    elif message.content.lower() == "stay":
                        player.stay()
                        await sleep(3)
                        idle = False
                        break

                    elif message.content.lower() == "double" and player.canDouble(): 
                        await self.ctx.send("Double down! Your bet is doubled, but you must receive one card and stay")
                        await sleep(3)
                        player.double()
                        player.hit(self.shoe.draw())
                        if await self.checkBust(player):
                            player.loseHand()
                        await self.ctx.send("Your hand will stay at\n{0}".format(player.currentHandStr()))
                        player.stay()
                        await sleep(3)
                        idle = False
                        break

                    elif message.content.lower() == "split" and player.canSplit():
                        player.split()
                        await self.ctx.send("Split! Your two hands are now:\n{0}\nYou will play each hand regularly, in succession...".format(player.allHandsStr()))
                        await sleep(3)
                        idle = False
                        break

                    elif message.content.lower() == "think" and player.canThink():
                        player.think()
                        await self.ctx.send("Take your time, think carefully...")
                        await sleep(3)
                        idle = False
                        break

            if idle:
                await self.removeIdlePlayer(player, set([player.getID()]), "Sorry {0}, you were removed for inactivity and current bets have been lost...".format(player.name))
                break
 

    async def servePlayers(self):
        for player in list(iter(self.currentPlayers)):
            if player.stillPlaying():
                await self.playHands(player)
    

    async def dealerBust(self):
        for player in self.currentPlayers:
            player.resetCurrentHand()
            while player.stillPlaying():
                if player.getHandState() == PLAY:
                    player.winHand()
                else:
                    player.stay()


    async def resolveOutcome(self):
        for player in self.currentPlayers:
            player.resetCurrentHand()
            while player.stillPlaying():
                if player.getHandState() == PLAY:
                    if player.getHandValue() > self.dealer.getHandValue():
                        player.winHand()
                    elif player.getHandValue() == self.dealer.getHandValue():
                        player.pushHand()
                    else:
                        player.loseHand()
                else:
                    player.stay()


    async def serveDealer(self):
        await self.ctx.send("My turn! I stay on soft 17 or higher...\n{0}".format(self.dealer.handShowStr()))
        await sleep(3)
        busted = False
        while self.dealer.stillPlaying():
            self.dealer.hit(self.shoe.draw())
            await self.ctx.send("{0} Hit!".format(self.dealer.handShowStr()))
            if self.dealer.getHandValue() > 21:
                await self.ctx.send("I bust! Players who didn't bust will win their bet!\n{0}".format(self.dealer.handShowStr()))
                await self.dealerBust()
                await sleep(3)
            elif self.dealer.getHandValue() >= 17:
                await self.ctx.send("The hand to beat...\n{0}".format(self.dealer.handShowStr()))
                await sleep(3)
            else:
                await sleep(3)


    async def showOutcome(self):
        await self.ctx.send("Here's the outcome of all the hands played!" + self.allResultsStr())
        await sleep(3)
        await self.ctx.send("Let's see the damage to your wallets..." + self.allWalletsStr())
        await sleep(3)


    async def playBlackjack(self):
        await self.ctx.send("Alright, the players are rounded up. The order of play will be:\n{0}".format(self.allPlayersStr()))
        await sleep(2)
        await self.ctx.send("From here on out, idle players will be removed from the game and lose their bets. Pay attention!\n")
        await sleep(2)

        await self.gatherBets()
        
        if not self.playerDict: # ensure all players were not idle before continuing
            return
        
        self.shuffleShoe()
        await self.dealCards()
        
        if await self.checkNaturals(): # returns True if dealer got natural, meaning current hand ends immediately
            await self.showOutcome()
            self.resetHands()
            return
        
        await self.servePlayers()
        
        if not self.playerDict: # again check to make sure all players were not idle
            return
        
        if self.hasPlayable():
            await self.serveDealer()
            await self.resolveOutcome()
        else:
            await self.ctx.send("Looks like no playable hands are left, so I don't need to draw...")
            await sleep(3)
    
        await self.showOutcome()
        self.resetHands()


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


    def stillPlaying(self):
        return self.hand.getValue() < 17


    def getName(self):
        return self.name


    def getHandValue(self):
        return self.hand.getValue()


    def resetHand(self):
        self.hand = Hand()


    def handStr(self):
        return "{0}".format(self.hand.dealerHideStr())


    def handHideStr(self):
        return self.hand.dealerHideStr()

    
    def handShowStr(self):
        return self.hand.dealerShowStr()


class Player:
    def __init__(self, name, ID = 0, wallet = 100):
        self.name = name
        self.ID = ID
        self.wallet = wallet
        self.hands = [Hand()]
        self.currentHand = 0


    def hit(self, card):
        self.hands[self.currentHand].add(card)


    def stay(self):
        self.currentHand += 1


    def hasPlayable(self):
        for hand in self.hands:
            if hand.getState() == PLAY:
                return True
        return False


    def canSplit(self):
        return self.hands[self.currentHand].canSplit() and self.hands[self.currentHand].getBet() < self.wallet

            
    def split(self):
        amount = self.hands[self.currentHand].getBet()
        self.wallet -= amount
        card = self.hands[self.currentHand].split()
        splitHand = Hand()
        splitHand.add(card)
        splitHand.placeBet(amount)
        self.hands.append(splitHand)


    def getHandValue(self):
        return self.hands[self.currentHand].getValue()

    
    def getHandState(self):
        return self.hands[self.currentHand].getState()


    def placeBet(self, amount):
        self.wallet -= amount
        self.hands[self.currentHand].placeBet(amount)

    
    def canDouble(self):
        return self.hands[self.currentHand].canDouble() and self.hands[self.currentHand].getBet() < self.wallet


    def double(self):
        amount = self.hands[self.currentHand].getBet()
        self.wallet -= amount
        self.hands[self.currentHand].double()


    def canThink(self):
        return self.hands[self.currentHand].canThink() > 0


    def think(self):
        self.hands[self.currentHand].think()
    

    def winHand(self):
        self.hands[self.currentHand].win()
        amount = self.hands[self.currentHand].getBet()
        self.wallet += (amount * 2)
        self.currentHand += 1


    def pushHand(self):
        self.hands[self.currentHand].push()
        amount = self.hands[self.currentHand].getBet()
        self.wallet += (amount)
        self.currentHand += 1


    def loseHand(self):
        self.hands[self.currentHand].lose()
        self.currentHand += 1


    def resetHands(self):
        self.hands = [Hand()]
        self.currentHand = 0


    def resetCurrentHand(self):
        self.currentHand = 0


    def stillPlaying(self):
        return self.currentHand < len(self.hands)


    def getThinkCounter(self):
        return self.hands[self.currentHand].getThinkCounter()


    def getID(self):
        return self.ID


    def getWallet(self):
        return self.wallet


    def getName(self):
        return self.name

    
    def optionsStr(self):
        string = "(   hit   stay   "
        if self.canDouble():
            string += "double   "
        if self.canSplit():
            string += "split   "
        if self.canThink():
            string += "think [{0} left]   ".format(self.getThinkCounter())
        return string + ")"
        


    def currentHandStr(self):
        return str(self.hands[self.currentHand])


    def allHandsStr(self):
        string = ""
        for hand in self.hands:
            string += ("{0}\n\n".format(str(hand)))
        return string 


    def allResultsStr(self):
        string = ""
        for hand in self.hands:
            string += ("{0}\n\n".format(hand.resultStr()))
        return string


class Hand:
    def __init__(self):
        self.cards = []
        self.softAces = 0
        self.value = 0
        self.bet = 0
        self.thinkCounter = 2
        self.state = PLAY


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

    
    def canDouble(self):
        return len(self.cards) == 2 and self.value in [9, 10, 11]


    def double(self):
        self.bet *= 2


    def canSplit(self):
        return len(self.cards) == 2 and self.cards[0].getName() == self.cards[1].getName()


    def split(self):
        card = self.cards.pop()
        self.value = card.getValue()
        if card.getValue() == 11:
            self.softAces = 1
        return card


    def canThink(self):
        return self.thinkCounter > 0

    
    def think(self):
        self.thinkCounter -= 1


    def getBet(self):
        return self.bet


    def lose(self):
        self.state = LOSE
        return self.state


    def push(self):
        self.state = PUSH
        return self.state


    def win(self):
        self.state = WIN
        return self.state


    def getValue(self):
        return self.value


    def getState(self):
        return self.state


    def getThinkCounter(self):
        return self.thinkCounter


    def dealerHideStr(self):
        string = "[ (??)   "
        for card in self.cards[1:] if len(self.cards) >= 2 else list():
            string += "{0} ".format(str(card))
        return string + "]"


    def dealerShowStr(self):
        return allCardStr(self.cards) + "  " + str(self.value) 


    def resultStr(self):
        return allCardStr(self.cards) + "  " + str(self.value) + "     //  Bet: " + str(self.bet) + "    " + self.state


    def __str__(self):
        return allCardStr(self.cards) + "  " + str(self.value) + "     //  Bet: " + str(self.bet)


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
            for suit in SUITS:        
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


    def getName(self):
        return self.name
    

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

