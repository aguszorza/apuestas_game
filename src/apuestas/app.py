import asyncio
import json
import secrets

from websockets.asyncio.server import broadcast, serve

from apuestas.models.game import Game
from apuestas.models.card import Card

# TODO: change it so we can have multiple players
PLAYER1, PLAYER2 = "red", "blue"

import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.DEBUG,
)


JOIN = {}

WATCH = {}


async def error(websocket, message):
    """
    Send an error message.

    """
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))


async def replay(websocket, game):
    """
    Send previous moves.

    """
    # Make a copy to avoid an exception if game.moves changes while iteration
    # is in progress. If a move is played while replay is running, moves will
    # be sent out of order but each move will be sent once and eventually the
    # UI will be consistent.
    for player, column, row in game.moves.copy():
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }
        await websocket.send(json.dumps(event))

async def start_turn(game, connected):
    game.begin_turn()
    first_player = game.current_player
    for player_name, connection in connected.items():
        event = {
            "type": "start_turn",
            "first_player": first_player.name,
            "player": game.players[player_name].to_json(),
            "game_info": game.to_json()
        }
        await connection.send(json.dumps(event))

async def waiting_players(websocket, game, game_key, connected, send_message: bool=False):
    async for message in websocket:
        event, error_message = parse_event(message)
        if error_message:
            await error(websocket, error_message)
            continue
        event_type = event["type"]
        if event_type != "start_ack":
            await error(websocket, "Invalid event type. We are in state 'start_ack'")
            continue
        # assert len(connected) == 2
        if event["game_key"] != game_key:
            await error(websocket, "Invalid game_key")
            continue

        if send_message:
            # we start the game and we broadcast the information
            await start_turn(game, connected)
        break

def parse_event(message):
    try:
        return json.loads(message), None
    except Exception as e:
        return None, str(e)


async def play(websocket, game, player, connected):
    """
    Receive and process moves from a player.

    """
    async for message in websocket:
        # Parse a "play" event from the UI.
        event, error_message = parse_event(message)
        if error_message:
            await error(websocket, error_message)
            continue
        event_type = event["type"]

        if event_type == "bet":
            if game.current_state != "bet":
                await error(websocket, "Invalid event type. We are in state 'bet'")
                continue
            player_bet = event["bet"]
            try:
                # Play the move.
                game.bet(player, player_bet)
                next_player = game.next_player()
                if next_player is None:
                    game.finish_bet_tour()
            except ValueError as exc:
                # Send an "error" event if the move was illegal.
                await error(websocket, str(exc))
                continue

            # Send a "bet" event to update the UI.
            event = {
                "type": "bet",
                "player": player,
                "bet": player_bet,
                "game_info": game.to_json(),
            }
            broadcast(connected.values(), json.dumps(event))
        elif event_type == "play":
            if game.current_state != "play":
                await error(websocket, "Invalid event type. We are in state 'play'")
                continue
            card_number = event["number"]
            card_suit = event["suit"]
            try:
                # Play the move.
                game.play(player, card_number, card_suit)
                next_player = game.next_player()
                round_ended = next_player is None
            except ValueError as exc:
                # Send an "error" event if the move was illegal.
                await error(websocket, str(exc))
                continue

            # Send a "play" event to update the UI.
            event = {
                "type": "play",
                "player": player,
                "card": Card(card_number, card_suit).to_json(),
                "game_info": game.to_json(),
                "round_ended": round_ended,
            }
            broadcast(connected.values(), json.dumps(event))

            if next_player is None:
                # Send a "round_ended" event to update the UI.
                round_winner = game.end_round()
                event = {
                    "type": "round_ended",
                    "round_winner": round_winner.name,
                    "game_info": game.to_json(),
                }
                broadcast(connected.values(), json.dumps(event))
            
            if game.has_turn_finished():
                # Send a "turn_ended" event to update the UI.
                game.end_turn()
                if game.has_game_ended():
                    event = {
                        "type": "game_ended",
                        "game_info": game.to_json(),
                    }
                    broadcast(connected.values(), json.dumps(event))
                else:
                    await start_turn(game, connected)
        elif event_type == "game_info":
            event = {
                "type": "game_info",
                "player": game.players[player].to_json(),
                "game_info": game.to_json(),
            }
            await websocket.send(json.dumps(event))


async def start(websocket):
    """
    Handle a connection from the first player: start a new game.

    """
    # Initialize a Connect Four game, the set of WebSocket connections
    # receiving moves from this game, and secret access tokens.
    
    game = Game(max_cards=2)
    game.add_player(PLAYER1)
    connected = {PLAYER1: websocket}
    game_key = secrets.token_urlsafe(12)

    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected, game_key

    watch_key = secrets.token_urlsafe(12)
    WATCH[watch_key] = game, connected

    try:
        # Send the secret access tokens to the browser of the first player,
        # where they'll be used for building "join" and "watch" links.
        event = {
            "type": "init",
            "join": join_key,
            "watch": watch_key,
        }
        await websocket.send(json.dumps(event))
        # Receive and process moves from the first player.
        await waiting_players(websocket, game, game_key, connected, True)

        await play(websocket, game, PLAYER1, connected)
    finally:
        del JOIN[join_key]
        del WATCH[watch_key]


async def join(websocket, join_key):
    """
    Handle a connection from the second player: join an existing game.

    """
    # Find the Connect Four game.
    try:
        game, connected, game_key = JOIN[join_key]
    except KeyError:
        await error(websocket, "Game not found.")
        return

    # Register to receive moves from this game.
    connected[PLAYER2] = websocket
    game.add_player(PLAYER2)
    try:
        if len(connected) == 2:
            event = {
                "type": "start",
                "game_key": game_key,
            }
            broadcast(connected.values(), json.dumps(event))
        # Send the first move, in case the first player already played it.
        # await replay(websocket, game)
        # Receive and process moves from the first player.
        await waiting_players(websocket, game, game_key, connected)

        # Receive and process moves from the second player.
        await play(websocket, game, PLAYER2, connected)
    finally:
        del connected[PLAYER2]
        # TODO: remove it from the game


# async def watch(websocket, watch_key):
#     """
#     Handle a connection from a spectator: watch an existing game.

#     """
#     # Find the Connect Four game.
#     try:
#         game, connected = WATCH[watch_key]
#     except KeyError:
#         await error(websocket, "Game not found.")
#         return

#     # Register to receive moves from this game.
#     connected.add(websocket)
#     try:
#         # Send previous moves, in case the game already started.
#         await replay(websocket, game)
#         # Keep the connection open, but don't receive any messages.
#         await websocket.wait_closed()
#     finally:
#         connected.remove(websocket)


async def handler(websocket):
    """
    Handle a connection and dispatch it according to who is connecting.

    """
    # Receive and parse the "init" event from the UI.
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"

    if "join" in event:
        # Second player joins an existing game.
        await join(websocket, event["join"])
    # elif "watch" in event:
    #     # Spectator watches an existing game.
    #     await watch(websocket, event["watch"])
    else:
        # First player starts a new game.
        await start(websocket)


async def main():
    async with serve(handler, "", 8001) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
