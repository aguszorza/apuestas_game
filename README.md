# Apuestas Game

`Apuestas` is a cards game that consists in betting on how many cards you will win. It is compose by turns that have rounds. In each turn you will receive a certain number of cards which will varied turn to turn. A card called `muestra` (sample) will also be presented. The suit of this card will define the most important suit for the cards that were provisioned. Each player will see their cards and they will bet in order, the amount of cards they think they will win. The last player may have a constraint in his chosen value as he can not choose a number that makes the sum of all bets equal to the amount of cards. This is to assure that at least one player loses its bet. Ex:

We have three players and each one has three cards. The first  one chooses 1, the second one 0, then the last player can not bet 2. He can choose 1 or 0.

Now they can start to play. They will play several rounds (`x` rounds where `x` is the amount of cards in this turn) before the end of the turn. The first player will play the card he wants. The suit of this card will define two things:

- The second most powerfull suit: this suit and the `muestra` suit will be the only suits with value for this cards. The other suits have no value and they will always lose.
- The suit that must be played: other players must play a card of this suit if they have one in their hands. They can only play other suit if they do not have a card of this suit.

The next players will choose which card to play (following the defined constraints) until the last player. Then the person with the strongest card will "win" that round. Then the winner will play another card and the other players will follow. We will continue doing this until they have played all the cards. 

Once they have played all the cards, the turn is over and we will assign the points. We will compare the amount of cards each player had won and what they had bet. If they did not win what they have bet, they will gain the amount of cards they won as points. If they have won exactly what they bet, then they will gain `10 + cards * 5` points. Ex:

|    Bet    | Cards won | Points obtained |
| --------- | --------- | --------------- |
|     0     |     1     |        1        |
|     5     |     4     |        4        |
|     0     |     0     |        10       |
|     1     |     1     |        15       |
|     2     |     2     |        20       |

Now we will start a new turn but we are going to change a few thigs:

- The player that was the first one to bet before, will be the last one now.
- We will change the amount of cards we are going to receive. The game starts with one card, then with two, three until we play with seven. We will play two times with seven, the first one with `muestra` and the second one without. Then we will continue decreasing the number until we arrive to one again.
- As we are distributing new cards, the `muestra` will also change.

The game finishes once we have played all the turns and the player with more points win.

# TODOs

This a simple version of a game, so there are a lot of things to improve or a few things that have not yet been done.

As regards the card game rules:

* Make the amount of players variable
* Make the maximum amount of cards variable ?
* Check there are enough cards for the amount of players and so vary the maximum amount of cards
* The game is ending once we arrive to the maximum amount of cards. Add the logic that we turn back reducing the amount of cards until 1.
* Add the logic that the maximum amount of cards is played two times, the second time without the `muestra`
* Add a variation that when we play with one card we can not see the card
* Fix the cards value. For simplicity, I used the number when comparing cards of the same suit. But it is not exactly like that. Once changed, I have to add this information in the documentation
* The game is using the Spanish cards. Maybe add the possibility to use the Poker cards

As regards the game system/communication:

* I did a really simple solution based on the example of the websockets library [documentation](https://websockets.readthedocs.io/en/stable/intro/tutorial2.html). So there are for sure a lot of things to change. The `waiting solution` is not really good and I am not sure about the proposed solution were we have common data accesed by different async functions. 
* Everything is in memory, no data is saved in another place. So if the server goes down, the games are lost.
* If a player lost its connection, he can not reconnect to the game. We need to add some logic to it. But we may need to add some auth logic so we can know who is doing the reconnection request to check if he has an existing match and rejoin him to the match with the correct player
* There is no time constraints. The players can take all the time they want which means the game can get stuck if a player lost his connection or he just do not plays
* We do not check if the game is `playing`. If some game is stuck the game resources will not be freed. I think the is freed only if the player that created the game loses connection
* If the player that created the game loses/closes its connection, the game will be freed from the joinable games. The other players will still be playing (in a stuck game), but the game is not joinable. So if the player wants to rejoin, it will not be possible.
* There is a Watch