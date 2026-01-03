import asyncio
import json
import websockets
import uuid

players = {}  # player_id -> {x, y, ws}

GAME_TICK = 1 / 30  # 30 updates/sec
SPEED = 5

async def handler(ws):
    player_id = str(uuid.uuid4())
    players[player_id] = {"x": 0, "y": 0, "ws": ws}

    await ws.send(json.dumps({
        "type": "init",
        "id": player_id
    }))

    try:
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "move":
                dx, dy = data["dx"], data["dy"]
                players[player_id]["x"] += dx * SPEED
                players[player_id]["y"] += dy * SPEED
    finally:
        del players[player_id]

async def game_loop():
    while True:
        state = {
            pid: {"x": p["x"], "y": p["y"]}
            for pid, p in players.items()
        }

        msg = json.dumps({
            "type": "state",
            "players": state
        })

        for p in players.values():
            await p["ws"].send(msg)

        await asyncio.sleep(GAME_TICK)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await game_loop()

asyncio.run(main())
