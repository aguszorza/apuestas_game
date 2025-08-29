from unittest.mock import patch
import pytest

from apuestas.models.card import Card
from apuestas.models.player import Player
from apuestas.models.game import Game


class TestGame:
    def setup_method(self):
        self.max_cards = 2
        self.game = Game(self.max_cards)
        self.game.add_player("red")
        self.game.add_player("blue")
        self.game.add_player("green")

    @pytest.mark.parametrize("max_cards", [(2), (4)])
    def test_init(self, max_cards):
        game = Game(max_cards)
        assert game.max_cards == max_cards
        assert game.current_amount_cards == 1
        assert game.players == {}
        assert game.current_muestra is None
        assert game.current_suit is None
        assert game.winner is None
        assert game.current_player_order  == []
        assert game.current_player_index  == 0
        assert game.first_turn_player_index  == 0

    def test_add_player(self):
        first_player = "red"
        other_player = "blue"
        game = Game(3)
        
        assert game.players == {}
        game.add_player(first_player)
        game.add_player(other_player)
        assert first_player in game.players
        game.players[first_player].name == first_player
        game.players[other_player].name == other_player
        assert game.current_player_order == [first_player, other_player]
    
    def test_begin_turn(self):
        players_number = len(self.game.current_player_order)
        cards_per_player = self.game.current_amount_cards
        assert self.game.current_muestra is None

        self.game.begin_turn()
        
        assert self.game.current_muestra is not None
        assert self.game.current_muestra == self.game.deck.cards[cards_per_player * players_number]
        for player in self.game.players.values():
            assert len(player.current_hand) == cards_per_player
    
    @pytest.mark.parametrize("turn_index, round_index, player_index, expected_index", [(0, 0, 2, 1), (1, 2, 1, 2), (2, 1, 0, 0)])
    def test_end_turn(self, turn_index, round_index, player_index, expected_index):
        self.game.first_turn_player_index = turn_index
        self.game.first_round_player_index = round_index
        self.game.current_player_index = player_index
        amount_of_cards = self.game.current_amount_cards

        self.game.end_turn()

        assert self.game.first_turn_player_index == expected_index
        assert self.game.first_round_player_index == expected_index
        assert self.game.current_player_index == expected_index
        assert self.game.current_amount_cards == amount_of_cards + 1

    @pytest.mark.parametrize("round_index, player_index, expected_player_index", [(0, 0, 1), (0, 1, 2), (1, 1, 2), (1, 2, 0), (2, 2, 0), (2, 0, 1)])
    def test_next_player_when_unfinish(self, round_index, player_index, expected_player_index):
        self.game.first_round_player_index = round_index
        self.game.current_player_index = player_index
        
        player = self.game.next_player()

        assert player is not None
        assert self.game.first_round_player_index == round_index
        assert self.game.current_player_index == expected_player_index
        assert player.name == self.game.current_player_order[expected_player_index]
    
    @pytest.mark.parametrize("round_index, player_index", [(0, 2), (1, 0), (2, 1)])
    def test_next_player_when_finished(self, round_index, player_index):
        self.game.first_round_player_index = round_index
        self.game.current_player_index = player_index

        player = self.game.next_player()

        assert player is None

    def test_end_round(self):
        self.game.current_muestra = Card(1, "Basto")
        cards = [Card(1, "Espada"), Card(3, "Basto"), Card(1, "Copa")]
        for index, player_name in enumerate(self.game.current_player_order):
            self.game.players[player_name].distribute_new_hand([cards[index]])
            self.game.players[player_name].play_card(cards[index])
        expacted_winner_index = 1
        expected_winner_name = self.game.current_player_order[expacted_winner_index]


        winner = self.game.end_round()

        assert winner == self.game.players[expected_winner_name]
        assert self.game.current_suit is None
        assert self.game.current_player_index == expacted_winner_index
        assert self.game.first_round_player_index == expacted_winner_index

    def test_has_turn_finished(self):
        assert self.game.has_turn_finished() is True

        self.game.begin_turn()
        
        assert self.game.has_turn_finished() is False
    
    def test_play_raises_if_not_player_turn(self):
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[2]
        card = list(self.game.players[player_name].current_hand)[0]
        
        with pytest.raises(ValueError) as e:
            self.game.play(player_name, card.number, card.suit)

        assert "It isn't your turn." in str(e.value)
    
    def test_play_raises_if_player_does_not_have_card(self):
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        current_player_name = self.game.current_player_order[0]
        other_player_name = self.game.current_player_order[2]
        card = list(self.game.players[other_player_name].current_hand)[0]
        
        with pytest.raises(ValueError) as e:
            self.game.play(current_player_name, card.number, card.suit)

        assert "The player does not have this card." in str(e.value)
    
    def test_play_raises_if_player_plays_other_suit_when_he_has_it(self):
        self.game.current_amount_cards = 2
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]
        self.game.players[player_name].distribute_new_hand([Card(1, "Basto"), Card(1, "Oro")])
        self.game.current_suit = "Basto"
        
        with pytest.raises(ValueError) as e:
            self.game.play(player_name, 1, "Oro")

        assert "You have to play your card with the suit 'Basto'." in str(e.value)
    
    def test_play_as_first_player(self):
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]
        card = list(self.game.players[player_name].current_hand)[0]

        assert self.game.players[player_name].current_card is None
        
        played_card = self.game.play(player_name, card.number, card.suit)

        assert played_card == card
        assert self.game.players[player_name].current_card == card
    
    def test_play_as_second_player(self):
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        first_player_name = self.game.current_player_order[0]
        second_player_name = self.game.current_player_order[1]
        self.game.players[first_player_name].distribute_new_hand([Card(1, "Basto"), Card(1, "Oro")])
        self.game.players[second_player_name].distribute_new_hand([Card(1, "Espada"), Card(1, "Copa")])

        assert self.game.current_suit is None
        
        played_card = self.game.play(first_player_name, 1, "Basto")
        assert played_card == Card(1, "Basto")
        assert self.game.players[first_player_name].current_card == played_card
        assert self.game.current_suit == played_card.suit

        player_2 = self.game.next_player()
        assert player_2.name == second_player_name

        played_card = self.game.play(second_player_name, 1, "Espada")
        assert played_card == Card(1, "Espada")
        assert self.game.players[second_player_name].current_card == played_card

    def test_bet_raises_if_not_player_turn(self):
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[2]
        
        with pytest.raises(ValueError) as e:
            self.game.bet(player_name, 1)

        assert "It isn't your turn." in str(e.value)

    def test_bet_raises_if_value_incorrect(self):
        self.game.current_amount_cards = 2
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]

        expected_error_message = "The bet should be a number between 0 and 2."        

        with pytest.raises(ValueError) as e:
            self.game.bet(player_name, -1)

        assert expected_error_message in str(e.value)
    
        with pytest.raises(ValueError) as e:
            self.game.bet(player_name, 10)

        assert expected_error_message in str(e.value)

    def test_bet_nominal(self):
        self.game.current_amount_cards = 2
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]

        self.game.bet(player_name, 2)

        assert self.game.players[player_name].current_bet == 2

    def test_bet_last_player_nominal(self):
        self.game.current_amount_cards = 2
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]
        self.game.bet(player_name, 2)
        
        player_2 = self.game.next_player()
        self.game.bet(player_2.name, 1)

        last_player = self.game.next_player()
        self.game.bet(last_player.name, 0)

        assert self.game.players[player_name].current_bet == 2
        assert self.game.players[player_2.name].current_bet == 1
        assert self.game.players[last_player.name].current_bet == 0

    def test_bet_last_player_raises_if_sum_equal_to_cards(self):
        self.game.current_amount_cards = 2
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]
        self.game.bet(player_name, 0)
        
        player_2 = self.game.next_player()
        self.game.bet(player_2.name, 1)

        last_player = self.game.next_player()
        with pytest.raises(ValueError) as e:
            self.game.bet(last_player.name, 1)

        assert "You can not bet 1. The sum can not be equal to the amount of cards." in str(e.value)
        assert self.game.players[player_name].current_bet == 0
        assert self.game.players[player_2.name].current_bet == 1

    def test_finish_bet_tour(self):
        self.game.current_amount_cards = 2
        self.game.begin_turn()

        assert self.game.current_player_index == 0

        player_name = self.game.current_player_order[0]
        self.game.bet(player_name, 2)
        
        player_2 = self.game.next_player()
        assert self.game.current_player_index == 1
        self.game.bet(player_2.name, 1)

        last_player = self.game.next_player()
        assert self.game.current_player_index == 2
        self.game.bet(last_player.name, 0)

        player = self.game.next_player()
        assert player is None
        assert self.game.current_player_index == 2

        self.game.finish_bet_tour()
        assert self.game.current_player_index == 0
    
    def test_has_game_ended(self):
        assert self.game.max_cards == 2
        assert self.game.current_amount_cards == 1
        assert self.game.first_turn_player_index == 0
        assert self.game.has_game_ended() is False

        self.game.end_turn()
        assert self.game.current_amount_cards == 2
        assert self.game.first_turn_player_index == 1
        assert self.game.has_game_ended() is False

        self.game.end_turn()
        assert self.game.current_amount_cards == 3
        assert self.game.first_turn_player_index == 2
        assert self.game.has_game_ended() is True


class TestSimulateGame:
    """Simulate the game but with some workflows. But, to make it easier to test,
    the cards will not be shuffled, and hte max cards will be 2. 
    """
    def test_full_game(self):
        # prepare game
        max_cards = 2
        game = Game(max_cards)
        game.add_player("red")
        game.add_player("blue")
        game.add_player("green")
        red_player = game.players["red"]
        blue_player = game.players["blue"]
        green_player = game.players["green"]

        assert len(red_player.current_hand) == 0
        assert len(blue_player.current_hand) == 0
        assert len(green_player.current_hand) == 0

        # start game
        # First turn
        with patch("apuestas.models.card.random"):
            game.begin_turn()
        
        assert len(red_player.current_hand) == 1
        assert len(blue_player.current_hand) == 1
        assert len(green_player.current_hand) == 1
        assert Card(1, "Oro") in red_player.current_hand
        assert Card(2, "Oro") in blue_player.current_hand
        assert Card(3, "Oro") in green_player.current_hand
        assert Card(4, "Oro") == game.current_muestra

        # players bet
        game.bet(red_player.name, 1)
        player = game.next_player()
        assert player.name == blue_player.name
        game.bet(blue_player.name, 1)
        player = game.next_player()
        assert player.name == green_player.name
        game.bet(green_player.name, 1)
        player = game.next_player()
        assert player is None

        # First Bet finished
        game.finish_bet_tour()
        assert game.first_turn_player_index == 0
        assert game.first_round_player_index == 0
        assert game.current_player_index == 0
        assert red_player.current_bet == 1
        assert blue_player.current_bet == 1
        assert green_player.current_bet == 1

        # Players play their cards
        game.play(red_player.name, 1, "Oro")
        player = game.next_player()
        assert player.name == blue_player.name
        game.play(blue_player.name, 2, "Oro")
        player = game.next_player()
        assert player.name == green_player.name
        game.play(green_player.name, 3, "Oro")
        player = game.next_player()
        assert player is None
        
        assert Card(1, "Oro") == red_player.current_card
        assert Card(2, "Oro") == blue_player.current_card
        assert Card(3, "Oro") == green_player.current_card

        # First Round finished
        round_winner = game.end_round()
        assert round_winner.name == green_player.name
        assert red_player.current_winning_cards == 0
        assert blue_player.current_winning_cards == 0
        assert green_player.current_winning_cards == 1

        # The first turn has also finished
        assert game.has_turn_finished() is True
        assert red_player.points == 0
        assert blue_player.points == 0
        assert green_player.points == 0
        assert game.first_turn_player_index == 0
        assert game.first_round_player_index == 2  # Was the player that won
        assert game.current_player_index == 2  # Was the player that won

        game.end_turn()
        assert red_player.points == 0
        assert blue_player.points == 0
        assert green_player.points == 15
        assert game.first_turn_player_index == 1
        assert game.first_round_player_index == 1
        assert game.current_player_index == 1
        assert game.has_game_ended() is False

        # Start Second turn
        with patch("apuestas.models.card.random"):
            game.begin_turn()

        assert len(red_player.current_hand) == 2
        assert len(blue_player.current_hand) == 2
        assert len(green_player.current_hand) == 2
        assert Card(1, "Oro") in red_player.current_hand
        assert Card(2, "Oro") in blue_player.current_hand
        assert Card(3, "Oro") in green_player.current_hand
        assert Card(4, "Oro") in red_player.current_hand
        assert Card(5, "Oro") in blue_player.current_hand
        assert Card(6, "Oro") in green_player.current_hand
        assert Card(7, "Oro") == game.current_muestra

        # players bet. Now it starts the blue player
        game.bet(blue_player.name, 1)
        player = game.next_player()
        assert player.name == green_player.name
        game.bet(green_player.name, 2)
        player = game.next_player()
        assert player.name == red_player.name
        game.bet(red_player.name, 0)
        player = game.next_player()
        assert player is None

        # Second Bet finished
        game.finish_bet_tour()
        assert game.first_turn_player_index == 1
        assert game.first_round_player_index == 1
        assert game.current_player_index == 1
        assert red_player.current_bet == 0
        assert blue_player.current_bet == 1
        assert green_player.current_bet == 2

        # Players play their cards in the first round of second turn
        game.play(blue_player.name, 2, "Oro")
        player = game.next_player()
        assert player.name == green_player.name
        game.play(green_player.name, 6, "Oro")
        player = game.next_player()
        assert player.name == red_player.name
        game.play(red_player.name, 4, "Oro")
        player = game.next_player()
        assert player is None
        
        assert Card(4, "Oro") == red_player.current_card
        assert Card(2, "Oro") == blue_player.current_card
        assert Card(6, "Oro") == green_player.current_card

        # Round finished
        round_winner = game.end_round()
        assert round_winner.name == green_player.name
        assert red_player.current_winning_cards == 0
        assert blue_player.current_winning_cards == 0
        assert green_player.current_winning_cards == 1
        assert game.first_turn_player_index == 1
        assert game.first_round_player_index == 2  # Was the player that won
        assert game.current_player_index == 2
        assert game.has_turn_finished() is False

        # Players play their cards in the second round of second turn
        game.play(green_player.name, 3, "Oro")
        player = game.next_player()
        assert player.name == red_player.name
        game.play(red_player.name, 1, "Oro")
        player = game.next_player()
        assert player.name == blue_player.name
        game.play(blue_player.name, 5, "Oro")
        player = game.next_player()
        assert player is None
        
        assert Card(1, "Oro") == red_player.current_card
        assert Card(5, "Oro") == blue_player.current_card
        assert Card(3, "Oro") == green_player.current_card

        # Round finished
        round_winner = game.end_round()
        assert round_winner.name == blue_player.name
        assert red_player.current_winning_cards == 0
        assert blue_player.current_winning_cards == 1
        assert green_player.current_winning_cards == 1
        assert game.first_turn_player_index == 1
        assert game.first_round_player_index == 1  # Was the player that won
        assert game.current_player_index == 1

        # The second turn has also finished
        assert game.has_turn_finished() is True
        assert red_player.points == 0
        assert blue_player.points == 0
        assert green_player.points == 15

        game.end_turn()
        assert red_player.points == 10
        assert blue_player.points == 15
        assert green_player.points == 16
        assert game.first_turn_player_index == 2
        assert game.first_round_player_index == 2
        assert game.current_player_index == 2

        # We have arrived to the maximum cards and the game has finished
        assert game.has_game_ended() is True