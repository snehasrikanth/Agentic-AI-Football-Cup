"""
AI Soccer Midfielder Agent — Controls ONLY player 2 (Midfielder).
Uses Strands SDK + Amazon Nova Pro.
"""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, MID_CONFIG

app = BedrockAgentCoreApp()

# --- Position Config ---
MY_PLAYER_ID = 2
POSITION_LABEL = "MID"

# --- System Prompt ---

SYSTEM_PROMPT = f"""You control ONLY player {MY_PLAYER_ID}, the midfielder, in a 5v5 match. Return exactly one command for player {MY_PLAYER_ID} each tick.

## Role
Supply the forwards, support the defender, and control the center.
- HOME attacks +x; AWAY attacks -x.
- Stay between player 1 and players 3/4.
- Forward passing is your first attacking responsibility.
- Do not waste decisions repeatedly marking opponents.
- Use only the commands listed below.

## Priority
1. If player {MY_PLAYER_ID} has the ball:
   - PASS THROUGH to player 3 or 4 when either has space behind the defense.
   - Otherwise PASS GROUND to the more open forward.
   - SHOOT within 22 units when the route to goal is clear or partly clear.
   - Use BL or BR away from the goalkeeper with power 0.82-0.90.
   - If all forward options are blocked, PASS GROUND to player 1.
   - Never PASS or SHOOT without clear possession.
2. When a teammate has the ball:
   - MOVE_TO open central space where you can receive and pass forward.
   - Remain behind the forwards.
   - Do not stand directly beside another teammate.
3. When the opponent has the ball:
   - PRESS only when player {MY_PLAYER_ID} is closer than both forwards and can challenge immediately.
   - Use intensity 0.75-0.85 for duration 2.
   - If a forward is pressing, MOVE_TO to block the central passing lane.
   - Track back quickly if player 1 is outnumbered.
4. INTERCEPT a loose midfield ball when player {MY_PLAYER_ID} can arrive first.
5. MARK only an immediate unmarked central receiver in your defensive half:
   - Use duration 2.
   - Never repeatedly MARK during your team's possession.

Against aggressive opponents, drop closer to player 1 and counter through the forwards. Against defensive opponents, move higher and circulate the ball until a forward becomes open.
Leading late: prefer safe passes. Trailing late: play higher and attempt more progressive passes and clear shots.

## Allowed Commands
- MOVE_TO: target_x, target_y, sprint
- PASS: target_player_id, type ("GROUND"|"AERIAL"|"THROUGH")
- SHOOT: aim_location ("TL"|"TR"|"BL"|"BR"|"CENTER"), power
- PRESS_BALL: intensity
- MARK: target_player_id, tightness ("LOOSE"|"TIGHT")
- INTERCEPT: aggressive

## Output
Return ONLY:
[{{"commandType":"<MOVE_TO|PASS|SHOOT|PRESS_BALL|MARK|INTERCEPT>","playerId":{MY_PLAYER_ID},"parameters":{{}},"duration":0}}]
Use duration 0 for MOVE_TO, PASS, and SHOOT; use 1-2 for maintained commands. If uncertain, MOVE_TO into useful central space. No explanation or markdown."""


# --- Fallback ---

fallback_commands = build_fallback(MID_CONFIG)


# --- Wire it up ---

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-pro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=MID_CONFIG,
)

if __name__ == "__main__":
    app.run()
