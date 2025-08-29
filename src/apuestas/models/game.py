from functools import cmp_to_key

from apuestas.models.card import Card, Deck
from apuestas.models.player import Player


__all__ = ["PLAYER1", "PLAYER2", "Apuestas"]

PLAYER1, PLAYER2 = "red", "yellow"


def get_round_compare_function(muestra_suit: str, current_suit: str):
    """Given the current 'muestra' suit and current suit, it returns a function that compares two players card plays
    and returns the one that wins"""
    def card_comparison(first_player: Player, second_player: Player):
        valuable_suits = (muestra_suit, current_suit)
        first_card = first_player.current_card
        second_card = second_player.current_card
        if first_card.suit == second_card.suit:
            return first_card.number - second_card.number
        if first_card.suit not in valuable_suits and second_card.suit not in valuable_suits:
            # Both cards have no value for this round. The result does not matter
            # So we return 1. 
            return 1
        # At least one of them has a suit of the muestra or the current one.
        if first_card.suit == muestra_suit:
            # First one has the muestra suit. The second one, at best has the current suit
            # So the first one wins
            return 1
        if second_card.suit == muestra_suit:
            # Second one has the muestra suit. The first one, at best has the current suit
            # So the second one wins
            return -1
        if first_card.suit == current_suit:
            # First one has the current suit. The second one has a card with no value
            # So the first one wins
            return 1
        # Second one has the current suit. The first one has a card with no value
        # So the second one wins
        return -1
    return card_comparison



class Game:
    """
    A Connect Four game.

    Play moves with :meth:`play`.

    Get past moves with :attr:`moves`.

    Check for a victory with :attr:`winner`.

    """

    def __init__(self, max_cards: int = 2):
        self.players: dict[str, Player] = {}
        self.max_cards = max_cards
        self.current_amount_cards = 1
        self.current_muestra: Card = None
        self.current_suit = None
        self.winner = None
        self.current_player_order = []  # list of players names
        self.current_player_index = 0
        self.first_turn_player_index = 0
        self.first_round_player_index = 0
        self.deck = Deck()
        self.current_state = "bet"

    def add_player(self, player_name):
        new_player = Player(player_name)
        self.players[new_player.name] = new_player
        self.current_player_order.append(new_player.name)

    def bet(self, player_name: str, bet: int):
        if player_name != self.current_player_order[self.current_player_index]:
            raise ValueError("It isn't your turn.")

        if bet < 0 or bet > self.current_amount_cards:
            raise ValueError(f"The bet should be a number between 0 and {self.current_amount_cards}.")
        
        next_index = self._get_next_player_index(self.current_player_index)
        if next_index == self.first_round_player_index:
            # it is the last player. The sum of all the bets should not be equal to the amount of cards
            bets = sum([player.current_bet for player in self.players.values()])
            bets += bet
            if bets == self.current_amount_cards:
                raise ValueError(f"You can not bet {bet}. The sum can not be equal to the amount of cards.")

        self.players[player_name].bet(bet)

    def finish_bet_tour(self):
        self.current_player_index = self.first_round_player_index
        self.current_state = "play"

    def play(self, player_name, card_number, card_suit) -> Card:
        """
        Play a card.

        Returns the card played.

        Raises :exc:`ValueError` if the move is illegal.

        """
        if player_name != self.current_player_order[self.current_player_index]:
            raise ValueError("It isn't your turn.")

        card = Card(card_number, card_suit)
        player: Player = self.players[player_name]

        if player.has_card(card) is False:
            raise ValueError("The player does not have this card.")

        if self.current_suit is None:
            # it is the first player. He can choose any card to play
            self.current_suit = card.suit
        elif card.suit != self.current_suit:
            # it is not the first player. We need to check it is a valid play
            # TODO: check if the player has a card of the correct suit
            if player.has_card_with_suit(self.current_suit):
                raise ValueError(f"You have to play your card with the suit '{self.current_suit}'.")

        player.play_card(card)

        return card

    def get_round_winner(self) -> Player:
        comparison_function = get_round_compare_function(self.current_muestra.suit, self.current_suit)
        cmp_key = cmp_to_key(comparison_function)
        # we sort the players depending on their cards.
        # We only want the best one
        return max(self.players.values(), key=cmp_key)

    def _get_next_player_index(self, current_index):
        current_index += 1
        if current_index >= len(self.current_player_order):
            # we are at the end of the list. Next player is the first one
            current_index = 0
        return current_index

    def begin_turn(self):
        self.deck.shuffle()

        hands, muestra = self.deck.get_hands(len(self.current_player_order), self.current_amount_cards)
        self.current_muestra = muestra
        for index, player_name in enumerate(self.current_player_order):
            self.players[player_name].distribute_new_hand(hands[index])
        self.current_state = "bet"

    def end_turn(self):
        """All the turn rounds have finished. We remove the hands and we update the points.
        We change the first player"""
        for player in self.players.values():
            player.end_turn()
        self.first_turn_player_index = self._get_next_player_index(self.first_turn_player_index)
        self.current_player_index = self.first_turn_player_index
        self.first_round_player_index = self.first_turn_player_index
        self.current_amount_cards += 1
    
    def has_game_ended(self):
        return self.current_amount_cards > self.max_cards

    def has_turn_finished(self) -> bool:
        return sum([len(player.current_hand) for player in self.players.values()]) == 0

    def end_round(self) -> Player:
        """Finish a round of cards. The played cards will be removed from the players.
        Returns the winner of the round which was the greater card"""
        winner = self.get_round_winner()
        winner_card = winner.current_card
        for player in self.players.values():
            player.end_round(winner_card)
        self.current_suit = None
        # we change the index to the winner
        self.first_round_player_index = self.current_player_order.index(winner.name)
        self.current_player_index = self.first_round_player_index
        return winner

    def next_player(self) -> Player:
        """Changes the turn to the next player. If the round has finished, it returns None"""
        next_player_index = self._get_next_player_index(self.current_player_index)
        if next_player_index == self.first_round_player_index:
            return None
        self.current_player_index = next_player_index
        player_name = self.current_player_order[next_player_index]
        return self.players[player_name]

    @property
    def current_player(self):
        player_name = self.current_player_order[self.current_player_index]
        return self.players[player_name]
    
    def to_json(self):
        result = {
            "amount_cards": self.current_amount_cards,
            "muestra": self.current_muestra.to_json(),
            "current_suit": self.current_suit,
            "players_info": {player.name: player.to_json(False) for player in self.players.values()},
            "current_player": self.current_player_order[self.current_player_index],
            "current_state": self.current_state 
        }
        return result