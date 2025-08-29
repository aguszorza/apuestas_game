import pytest

from apuestas.models.card import Card, Deck


class TestCard:
    @pytest.mark.parametrize("number,suit", [(1, "Basto"), (3, "Oro")])
    def test_init(self, number, suit):
        card = Card(number, suit)
        assert number == card.number
        assert suit == card.suit


class TestDeck:
    def test_init(self):
        deck = Deck()
        amunt_of_suits = 4
        amunt_of_card_per_suit = 12
        assert len(deck.cards) == amunt_of_suits * amunt_of_card_per_suit

    def test_shufle(self):
        first_deck = Deck()
        second_deck = Deck()
        # the decks are created with the same cards in the same order
        assert first_deck.cards == second_deck.cards
        first_deck.shuffle()
        assert first_deck.cards != second_deck.cards
        assert len(first_deck.cards) == len(second_deck.cards)

    @pytest.mark.parametrize("players,cards", [(2, 1), (2, 5), (4, 7)])
    def test_get_hands(self, players, cards):
        deck = Deck()
        hands, muestra = deck.get_hands(players, cards)
        assert len(hands) == players
        for hand in hands:
            assert len(hand) == cards
        # we check the first card of each player was given in the order
        # of the pile deck
        for i in range(players):
            assert hands[i][0] == deck.cards[i]
        assert muestra == deck.cards[players * cards]

