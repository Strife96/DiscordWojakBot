import sys
import random

class Game:
    def __init__(self, channel):
        self.players = []
        self.channel = channel
    
    def addPlayer(self, player):
        self.players.append(player)

    def runGame(self):
        pass

class Player:
    def __init__(self, name, ID = 0, wallet = 100):
        self.name = name
        self.ID = ID
        self.wallet = wallet
        self.hands = [Hand()]
        self.currentHand = 0

    def addHand(self, hand):
        self.hands.append(hand)

    def hit(self, card):
        self.hands[self.currentHand].add(card)
        return self.hands[self.currentHand].getValue() > 21

    def nextHand(self):
        self.currentHand += 1
        return self.currentHand < len(self.hands)
            
    def split(self):
        card = self.hands[self.currentHand].split()
        hand = Hand()
        hand.add(card)
        self.addHand(hand)

    def currentHandValue(self):
        return self.hands[self.currentHand].getValue()

    def __str__(self):
        string = self.name + "'s hands:\n"
        for hand in self.hands:
            string += ("{0}\n".format(str(hand)))
        return string


class Hand:
    def __init__(self):
        self.cards = []
        self.softAces = 0
        self.value = 0

    def add(self, card):
        self.cards.append(card)
        self.value += card.getValue()
        if card.getValue() == 11:
            self.softAces += 1
        while self.value > 21 and self.softAces > 0:
            self.softAces -= 1
            self.value -= 10

    def split(self):
        card = self.cards.pop()
        if card == self.cards[0]:
            self.value = card.getValue()
            if card.getValue() == 11:
                self.softAces = 1
        return card

    def getValue(self):
        return self.value

    

    def __str__(self):
        return allCardString(self.cards) + str(self.value)

class Shoe:
    def __init__(self):
        self.cards = []
        self.position = 0

        # Shoe initialization...
        NUMBER_CARDS = [2, 3, 4, 5, 6, 7, 8, 9, 10]
        FACE_CARDS = ["J", "Q", "K"]
        SUITS = ["♠", "♥", "♦", "♣"]
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
    
    def __str__(self):
        return allCardString(self.cards)


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


def allCardString(cards):
    string = "[ "
    for card in cards:
        string += ("{0} ".format(str(card)))
    return string + "]"

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    shoe = Shoe()
    shoe.shuffle()
    shoe.shuffle()
    shoe.shuffle()
    print(str(shoe) + "\n")
    player = Player("Wojak")
    print(str(player.hit(shoe.draw())) + "\n")
    print(str(player) + "\n")
    print(str(player.hit(shoe.draw())) + "\n")
    print(str(player) + "\n")
    print(str(player.hit(shoe.draw())) + "\n")
    print(str(player) + "\n")
    print(str(player.hit(shoe.draw())) + "\n")
    print(str(player) + "\n")
    print(str(player.hit(shoe.draw())) + "\n")
    print(str(player) + "\n")
    print(str(player.hit(shoe.draw())) + "\n")
    print(str(player) + "\n")


