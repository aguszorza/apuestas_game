from apuestas.models.card import Card


class Player:
    def __init__(self, player_name):
        self.name = player_name
        self.points = 0
        self._initialize_turn()

    def _initialize_turn(self):
        self.current_hand = set()
        self.current_winning_cards = 0
        self.current_card: Card = None
        self.current_bet = 0

    def distribute_new_hand(self, cards):
        self.current_hand = set(cards)

    def calculate_round_points(self) -> int:
        if self.current_winning_cards != self.current_bet:
            return self.current_winning_cards
        return 10 + self.current_winning_cards * 5

    def end_turn(self):
        """We calculate and update the points. We reinitialize the turn"""
        points = self.calculate_round_points()
        self.points += points
        self._initialize_turn()
    
    def end_round(self, winning_card: Card):
        if winning_card == self.current_card:
            self.current_winning_cards += 1
        self.current_hand.remove(self.current_card)
        self.current_card = None

    def bet(self, new_bet: int):
        self.current_bet = new_bet

    def has_card(self, card):
        return card in self.current_hand
    
    def has_card_with_suit(self, suit):
        return any([card.suit == suit for card in self.current_hand])

    def play_card(self, card):
        self.current_card = card
    
    def to_json(self, show_all:bool=True):
        result = {
            "name": self.name,
            "points": self.points,
            "played_card": self.current_card.to_json() if self.current_card else None,
            "turn_bet": self.current_bet,
            "turn_wins": self.current_winning_cards
        }
        if show_all:
            result["hand"] = [card.to_json() for card in self.current_hand]
        return result
