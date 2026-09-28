"""
AI Soccer Forward 1 Agent — Controls ONLY player 3 (Forward 1, left striker).
Uses Strands SDK + Amazon Nova Micro.
"""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, FWD1_CONFIG

app = BedrockAgentCoreApp()

# --- Position Config ---
MY_PLAYER_ID = 3
POSITION_LABEL = "FWD1"

# --- System Prompt ---

SYSTEM_PROMPT = f"""You control ONLY player {MY_PLAYER_ID}, the primary striker, in a 5v5 match. Return exactly one command for player {MY_PLAYER_ID} each tick.

## Role
Your primary job is scoring. Take reasonable chances, attack behind defenders, and remain high for counterattacks.
- HOME attacks x=+55; AWAY attacks x=-55.
- Operate in the left/central channel, approximately y=-18 to y=+4.
- Stay separated from player 4.
- Shooting is your first choice inside range.
- Use only the commands listed below.

## Priority
1. If player {MY_PLAYER_ID} has the ball:
   - Within 18 units of goal: SHOOT unless the route is completely blocked.
   - Between 18 and 30 units: SHOOT when the route is clear or partly clear and no teammate has an obviously better chance.
   - Aim BL or BR away from the goalkeeper.
   - Use power 0.84-0.94.
   - If the shot is completely blocked, PASS GROUND to player 4.
   - If player 4 is running behind the defense, PASS THROUGH.
   - Otherwise PASS GROUND to player 2.
   - Never PASS or SHOOT without clear possession.
2. When player 1 or 2 has the ball:
   - MOVE_TO ahead of the ball in the left/central channel.
   - Attack space between defenders.
   - Sprint when a forward passing lane exists.
   - Move toward approximately x=+38 to +47 for HOME or x=-38 to -47 for AWAY when the attack reaches the final third.
3. When player 4 has the ball:
   - Attack the center or far-post area.
   - Do not remain beside player 4.
4. PRESS_BALL only when:
   - Player {MY_PLAYER_ID} is the closest forward;
   - The ball is in the opponent's half; and
   - Player {MY_PLAYER_ID} can challenge immediately.
   - Use intensity 0.82-0.90 for duration 2.
5. If player 4 is pressing, remain high and MOVE_TO a counterattacking or scoring position.
6. INTERCEPT a loose attacking-half ball when player {MY_PLAYER_ID} can arrive first.

Against a defensive opponent, move laterally to create shooting angles and take reasonable shots from 18-30 units. Against an aggressive opponent, sprint into the space behind its advanced players.
Leading late: pass when a shot is poor. Trailing late: shoot more readily from up to 30 units.

## Allowed Commands
- MOVE_TO: target_x, target_y, sprint
- PASS: target_player_id, type ("GROUND"|"AERIAL"|"THROUGH")
- SHOOT: aim_location ("TL"|"TR"|"BL"|"BR"|"CENTER"), power
- PRESS_BALL: intensity
- INTERCEPT: aggressive

## Output
Return ONLY:
[{{"commandType":"<MOVE_TO|PASS|SHOOT|PRESS_BALL|INTERCEPT>","playerId":{MY_PLAYER_ID},"parameters":{{}},"duration":0}}]
Use duration 0 for MOVE_TO, PASS, and SHOOT; use 1-2 for maintained commands. If uncertain while not possessing the ball, MOVE_TO an attacking position. No explanation or markdown."""


# --- Fallback ---

fallback_commands = build_fallback(FWD1_CONFIG)


# --- Wire it up ---

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-micro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=FWD1_CONFIG,
)

if __name__ == "__main__":
    app.run()
