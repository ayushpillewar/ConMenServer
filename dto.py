class PlayerType:
    COP: str = "COP"
    ROBBER: str = "ROBBER"


class PlayerData:
    playerId: int
    playerType: PlayerType
    # for when player hits the exit sprite
    completedStage: bool
    username: str
    x: float
    y: float
    ws: any  # WebSocket connection instance

    def create_new_player(player_id, ws):
        playerData = PlayerData()
        playerData.playerId = player_id
        playerData.x = 0.0
        playerData.y = 0.0
        playerData.ws = ws
        playerData.completedStage = False
        playerData.playerType = None
        playerData.username = "Anonymous"

        return playerData
    
    def to_dict(self):
        return {
            "playerId": self.playerId,
            "playerType": self.playerType,
            "completedStage": self.completedStage,
            "username": self.username,
            "x": self.x,
            "y": self.y
        }
    

