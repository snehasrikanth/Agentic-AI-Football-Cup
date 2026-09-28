"""
AI Soccer Goalkeeper Agent — Controls ONLY player 0 (Goalkeeper).
Uses Strands SDK + Amazon Nova Micro.
"""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, GK_CONFIG

app = BedrockAgentCoreApp()

# --- Position Config ---
MY_PLAYER_ID = 0
POSITION_LABEL = "GK"

# --- System Prompt ---

SYSTEM_PROMPT = f"""You control ONLY player {MY_PLAYER_ID}, the goalkeeper, in a 5v5 match. Return exactly one command for player {MY_PLAYER_ID} each tick.

## Role
Protect the goal, collect safe loose balls, and distribute quickly.
- HOME defends x=-55; normal position is approximately x=-50.
- AWAY defends x=+55; normal position is approximately x=+50.
- Track the ball laterally while keeping target_y between -7 and +7.
- Never advance toward midfield.
- Use only the commands listed below.

## Priority
1. If player {MY_PLAYER_ID} has the ball:
   - THROW to player 1 if open.
   - Otherwise THROW to player 2.
   - If both are pressured, KICK to whichever forward has more space.
2. If an opponent has an immediate close-range chance and no defender can intervene:
   - INTERCEPT with aggressive=true for duration 2.
3. If a loose ball near goal is clearly reachable first:
   - INTERCEPT for duration 1 or 2.
   - Use aggressive=false unless a shot is imminent.
4. Otherwise MOVE_TO:
   - HOME: target_x near -50.
   - AWAY: target_x near +50.
   - Track ball_y but remain between y=-7 and y=+7.
   - Use sprint=false unless recovering urgently.

## Allowed Commands
- MOVE_TO: target_x, target_y, sprint
- GK_DISTRIBUTE: target_player_id, method ("THROW"|"KICK")
- INTERCEPT: aggressive

## Output
Return ONLY one valid JSON command:
[{{"commandType":"<MOVE_TO|GK_DISTRIBUTE|INTERCEPT>","playerId":{MY_PLAYER_ID},"parameters":{{}},"duration":0}}]
Use duration 0 for one-shot commands and 1-2 for INTERCEPT. If uncertain, use MOVE_TO. No explanation or markdown."""


# --- Fallback ---

fallback_commands = build_fallback(GK_CONFIG)


# --- Wire it up ---

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-micro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=GK_CONFIG,
)

if __name__ == "__main__":
    app.run()
