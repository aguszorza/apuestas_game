import random


CARD_NUMBERS = [i for i in range(1, 13)]
CARD_SUITS = ["Oro", "Espada", "Basto", "Copa"]


class Card:
    def __init__(self, number, suit):
        if number not in CARD_NUMBERS or suit not in CARD_SUITS:
            raise ValueError("Invalid card.")

        self.number = number
        self.suit = suit
    
    def __eq__(self, other_card):
        return self.number == other_card.number and self.suit == other_card.suit

    def __hash__(self):
        return hash((self.number, self.suit))
    
    def __repr__(self):
        return f"Card({self.number}, {self.suit})"
    
    def to_json(self):
        return {
            "number": self.number,
            "suit": self.suit,
        }


class Deck:
    def __init__(self):
        self.cards = []
        for suit in CARD_SUITS:
            for number in CARD_NUMBERS:
                self.cards.append(Card(number, suit))
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def get_hands(self, players: int, cards_per_player: int):
        total_cards = players * cards_per_player
        hands = [[] for _ in range(players)]
        for i in range(total_cards):
            hands[i % players].append(self.cards[i])
        muestra = self.cards[total_cards]
        return hands, muestra
