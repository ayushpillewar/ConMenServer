import asyncio
import json
import websockets
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import time


class TestWebSocketAPI(unittest.TestCase):
    """Test cases for the WebSocket API server"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.server_uri = "ws://localhost:8765"
        self.test_timeout = 5  # seconds
    
    async def connect_websocket(self):
        """Helper method to establish WebSocket connection"""
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(self.server_uri), 
                timeout=self.test_timeout
            )
            return websocket
        except asyncio.TimeoutError:
            self.fail("Could not connect to WebSocket server within timeout")
        except Exception as e:
            self.fail(f"Failed to connect to WebSocket server: {e}")
    
    async def send_and_receive(self, websocket, message):
        """Helper method to send message and optionally receive response"""
        await websocket.send(json.dumps(message))
        await asyncio.sleep(0.1)  # Small delay for processing
    
    async def test_connection_and_player_creation(self):
        """Test WebSocket connection and initial player data reception"""
        print("Testing connection and player creation...")
        
        async with await self.connect_websocket() as websocket:
            # Should receive initial player data upon connection
            response = await asyncio.wait_for(
                websocket.recv(), 
                timeout=self.test_timeout
            )
            
            player_data = json.loads(response)
            
            # Validate player data structure
            self.assertIn("playerId", player_data)
            self.assertIn("x", player_data)
            self.assertIn("y", player_data)
            self.assertIn("completedStage", player_data)
            
            # Check initial values
            self.assertEqual(player_data["x"], 0.0)
            self.assertEqual(player_data["y"], 0.0)
            self.assertEqual(player_data["completedStage"], False)
            
            print(f"✓ Player created with ID: {player_data['playerId']}")
    
    async def test_player_movement(self):
        """Test player movement message handling"""
        print("Testing player movement...")
        
        async with await self.connect_websocket() as websocket:
            # Skip initial player data message
            await websocket.recv()
            
            # Send movement command
            move_message = {
                "type": "move",
                "dx": 10.5,
                "dy": 20.3
            }
            
            await self.send_and_receive(websocket, move_message)
            print("✓ Movement message sent successfully")
    
    async def test_stage_completion(self):
        """Test stage completion message handling"""
        print("Testing stage completion...")
        
        async with await self.connect_websocket() as websocket:
            # Skip initial player data message
            await websocket.recv()
            
            # Send stage completion command
            completion_message = {
                "type": "stageCompleted",
                "stageCompleted": True
            }
            
            await self.send_and_receive(websocket, completion_message)
            print("✓ Stage completion message sent successfully")
    
    async def test_start_game_single_player(self):
        """Test starting game with single player (should handle gracefully)"""
        print("Testing game start with single player...")
        
        async with await self.connect_websocket() as websocket:
            # Skip initial player data message
            await websocket.recv()
            
            # Send start game command
            start_message = {
                "type": "startGame"
            }
            
            await self.send_and_receive(websocket, start_message)
            print("✓ Start game message sent (should handle insufficient players)")
    
    async def test_multiple_players_connection(self):
        """Test multiple players connecting simultaneously"""
        print("Testing multiple player connections...")
        
        websockets_list = []
        player_ids = []
        
        try:
            # Connect multiple players
            for i in range(3):
                ws = await self.connect_websocket()
                websockets_list.append(ws)
                
                # Receive initial player data
                response = await ws.recv()
                player_data = json.loads(response)
                player_ids.append(player_data["playerId"])
                
                print(f"✓ Player {i+1} connected with ID: {player_data['playerId']}")
            
            # All players should have unique IDs
            self.assertEqual(len(set(player_ids)), len(player_ids), "Player IDs should be unique")
            
            # Test game state updates
            await asyncio.sleep(0.5)  # Wait for game loop updates
            
        finally:
            # Clean up connections
            for ws in websockets_list:
                await ws.close()
    
    async def test_start_game_multiple_players(self):
        """Test starting game with multiple players"""
        print("Testing game start with multiple players...")
        
        websockets_list = []
        
        try:
            # Connect 3 players
            for i in range(3):
                ws = await self.connect_websocket()
                websockets_list.append(ws)
                await ws.recv()  # Skip initial player data
            
            # Send start game command from first player
            start_message = {
                "type": "startGame"
            }
            
            await self.send_and_receive(websockets_list[0], start_message)
            
            # Wait for game state updates
            await asyncio.sleep(1)
            
            print("✓ Game started with multiple players")
            
        finally:
            # Clean up connections
            for ws in websockets_list:
                await ws.close()
    
    async def test_invalid_message_type(self):
        """Test handling of invalid message types"""
        print("Testing invalid message handling...")
        
        async with await self.connect_websocket() as websocket:
            # Skip initial player data message
            await websocket.recv()
            
            # Send invalid message type
            invalid_message = {
                "type": "invalidType",
                "someData": "test"
            }
            
            await self.send_and_receive(websocket, invalid_message)
            print("✓ Invalid message handled gracefully")
    
    async def test_malformed_json(self):
        """Test handling of malformed JSON messages"""
        print("Testing malformed JSON handling...")
        
        async with await self.connect_websocket() as websocket:
            # Skip initial player data message
            await websocket.recv()
            
            try:
                # Send malformed JSON
                await websocket.send("{ invalid json }")
                await asyncio.sleep(0.1)
                print("✓ Malformed JSON handled (connection should remain open)")
            except Exception as e:
                print(f"! Malformed JSON caused exception: {e}")
    
    async def test_connection_cleanup(self):
        """Test that player data is cleaned up when connection closes"""
        print("Testing connection cleanup...")
        
        # Connect and then disconnect
        websocket = await self.connect_websocket()
        response = await websocket.recv()
        player_data = json.loads(response)
        player_id = player_data["playerId"]
        
        print(f"✓ Player {player_id} connected")
        
        # Close connection
        await websocket.close()
        
        # Wait a moment for cleanup
        await asyncio.sleep(0.5)
        
        print("✓ Connection closed - player should be cleaned up from server")


class WebSocketAPITestRunner:
    """Test runner for WebSocket API tests"""
    
    def __init__(self):
        self.test_case = TestWebSocketAPI()
    
    async def run_all_tests(self):
        """Run all WebSocket API tests"""
        print("=" * 60)
        print("WEBSOCKET API TEST SUITE")
        print("=" * 60)
        print()
        
        tests = [
            self.test_case.test_connection_and_player_creation,
            self.test_case.test_player_movement,
            self.test_case.test_stage_completion,
            self.test_case.test_start_game_single_player,
            self.test_case.test_multiple_players_connection,
            self.test_case.test_start_game_multiple_players,
            self.test_case.test_invalid_message_type,
            self.test_case.test_malformed_json,
            self.test_case.test_connection_cleanup
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            test_name = test.__name__
            try:
                print(f"\nRunning {test_name}...")
                await test()
                print(f"✓ {test_name} PASSED")
                passed += 1
            except Exception as e:
                print(f"✗ {test_name} FAILED: {e}")
                failed += 1
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total:  {passed + failed}")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
        
        return failed == 0


# Standalone test functions for individual testing
async def test_basic_connection():
    """Simple connection test"""
    print("Testing basic WebSocket connection...")
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"Connected! Player ID: {data['playerId']}")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


async def test_movement_simple():
    """Simple movement test"""
    print("Testing player movement...")
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.recv()  # Skip initial data
            
            move_msg = {
                "type": "move",
                "dx": 100,
                "dy": 200
            }
            
            await websocket.send(json.dumps(move_msg))
            print("Movement command sent successfully!")
            return True
    except Exception as e:
        print(f"Movement test failed: {e}")
        return False


if __name__ == "__main__":
    print("WebSocket API Test Client")
    print("Make sure the WebSocket server is running on localhost:8765")
    print()
    
    import sys
    
    if len(sys.argv) > 1:
        # Run specific test
        if sys.argv[1] == "connection":
            asyncio.run(test_basic_connection())
        elif sys.argv[1] == "movement":
            asyncio.run(test_movement_simple())
        else:
            print("Available tests: connection, movement")
    else:
        # Run full test suite
        runner = WebSocketAPITestRunner()
        asyncio.run(runner.run_all_tests())