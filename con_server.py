import asyncio
import json
import websockets
import uuid
import random
from dto import *

players: dict[str, PlayerData] = {
}
game_state = {
    "stageStarted": False,
    "stageCompleted": False,
    "cops": [],
    "robbers": []
}

GAME_TICK = 1 / 30  # 30 updates/sec
SPEED = 1

async def handler(ws):
    print("New connection", ws)

    player_id = str(uuid.uuid4())
    player_data = PlayerData.create_new_player(player_id, ws)
    players[player_id] = player_data
    await ws.send(json.dumps({
        "type": "init",
        "id": player_id
    }))
    try:
        await wait_for_client_msgs(ws, player_id)
    except websockets.ConnectionClosed:
        print("Connection closed", ws)
    except Exception as e:
        print("Error:", e)
    finally:
        del players[player_id]

async def wait_for_client_msgs(ws, player_id):
    # async for continually receive messages from client
    # it works like an event listener or loop
    async for msg in ws:
        data = json.loads(msg)
        if data["type"] == "move":
            dx, dy = data["dx"], data["dy"]
            players[player_id].x = dx
            players[player_id].y = dy
        elif data["type"] == "stageCompleted":
            players[player_id].completedStage = data["stageCompleted"]
        elif data["type"] == "startGame":
            await start_stage()
        else:
            print("Unknown message type:", data["type"])

async def game_loop():
    while True:
        try:
            state = {
                    pid: p.to_dict()
                    for pid, p in players.items()  
            }
            print("Broadcasting state to players:", state)
            # game_state contains basic types (bool, list), not objects with __dict__
            msg = json.dumps({
                    "type": "state",
                    "players": state,
                    "gameState": game_state
                })
            #print("Message to send:", msg)
            for p in players.values():
                if p.ws is not None:
                    await p.ws.send(msg)
            await asyncio.sleep(GAME_TICK)
        except Exception as e:
            print(f"Error in game loop: {e}")
                
async def start_stage():
    players_items = players.items()
    if len(players_items) < 2:
            print("Not enough players to start the game.")
            return
    if len(players_items) > 5:
        cops_count = 2
    else:
        cops_count = 1
    for k, v in players_items:
        if cops_count > 0:
            v.playerType = PlayerType.COP
            game_state["cops"].append(v.playerId)
            cops_count -= 1
        else:
            v.playerType = PlayerType.ROBBER
            game_state["robbers"].append(v.playerId)
    game_state["stageStarted"] = True
    game_state["stageCompleted"] = False                  

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await game_loop()

asyncio.run(main())
