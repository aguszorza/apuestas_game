import pytest

from apuestas.models.card import Card
from apuestas.models.player import Player


class TestPlayer:
    def test_init(self):
        player_name = "red"
        player = Player(player_name)
        assert player.name == player_name
        assert player.points == 0
        assert player.current_hand == set()
        assert player.current_winning_cards == 0
        assert player.current_bet == 0
        assert player.current_card is None

    @pytest.mark.parametrize("cards, expected_cards", [([Card(1, "Basto"), Card(1, "Oro")], set([Card(1, "Basto"), Card(1, "Oro")])), ([Card(1, "Basto"), Card(1, "Basto")], set([Card(1, "Basto")]))])
    def test_distribute_new_hand(self, cards, expected_cards):
        player = Player("red")
        player.distribute_new_hand(cards)
        assert player.current_hand == expected_cards
    
    @pytest.mark.parametrize("bet, winning_cards, expected_points", [(0, 0, 10), (0, 2, 2), (1, 1, 15), (5, 4, 4), (5, 5, 35)])
    def test_calculate_round_points(self, bet, winning_cards, expected_points):
        player = Player("red")
        player.current_bet = bet
        player.current_winning_cards = winning_cards
        assert player.calculate_round_points() == expected_points
    
    def test_end_turn(self):
        player = Player("red")
        player.current_bet = 2
        player.current_winning_cards = 2
        assert player.points == 0
        player.end_turn()
        assert player.points == 20
        assert player.current_hand == set()
        assert player.current_winning_cards == 0
        assert player.current_bet == 0
        assert player.current_card is None

    @pytest.mark.parametrize("winning_card, expected_difference", [(Card(1, "Basto"), 1), (Card(1, "Espada"), 0)])
    def test_end_round(self, winning_card, expected_difference):
        player = Player("red")
        cards = [Card(1, "Basto"), Card(1, "Oro")]
        played_card = cards[0]
        player.distribute_new_hand(cards)
        player.current_card = played_card
        current_winning_cards = player.current_winning_cards

        player.end_round(winning_card)

        assert player.current_winning_cards - current_winning_cards == expected_difference
        assert player.current_card is None
        assert played_card not in player.current_hand
    
    def test_has_card(self):
        player = Player("red")
        cards = [Card(1, "Basto"), Card(1, "Oro")]
        player.distribute_new_hand(cards)

        assert player.has_card(Card(1, "Basto")) is True
        assert player.has_card(Card(1, "Oro")) is True
        assert player.has_card(Card(1, "Espada")) is False

    def test_has_card_with_suit(self):
        player = Player("red")
        cards = [Card(1, "Basto"), Card(1, "Oro")]
        player.distribute_new_hand(cards)

        assert player.has_card_with_suit("Basto") is True
        assert player.has_card_with_suit("Oro") is True
        assert player.has_card_with_suit("Espada") is False
        assert player.has_card_with_suit("Copa") is False
