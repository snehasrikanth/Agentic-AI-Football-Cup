"""
AI Soccer Forward 2 Agent — Controls ONLY player 4 (Forward 2, right striker).
Uses Strands SDK + Amazon Nova Lite.
"""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, FWD2_CONFIG

app = BedrockAgentCoreApp()

# --- Position Config ---
MY_PLAYER_ID = 4
POSITION_LABEL = "FWD2"

# --- System Prompt ---

SYSTEM_PROMPT = f"""You control ONLY player {MY_PLAYER_ID}, the supporting striker, in a 5v5 match. Return exactly one command for player {MY_PLAYER_ID} each tick.

## Role
Score goals, create chances for player 3, stretch the defense, and make fast attacking runs.
- HOME attacks x=+55; AWAY attacks x=-55.
- Operate primarily in the right channel, approximately y=+5 to y=+20.
- Stay separated from player 3.
- Be aggressive, but pass when player 3 has a clearly better chance.
- Use only the commands listed below.

## Priority
1. If player {MY_PLAYER_ID} has the ball:
   - Within 18 units of goal: SHOOT unless completely blocked.
   - Between 18 and 27 units: SHOOT when the route is clear or partly clear.
   - Aim BL or BR away from the goalkeeper.
   - Use power 0.82-0.92.
   - If player 3 has a clearly better central chance, PASS GROUND to player 3.
   - If player 3 is running behind the defense, PASS THROUGH.
   - If both options are blocked, PASS GROUND to player 2.
   - Never PASS or SHOOT without clear possession.
2. When player 2 has the ball:
   - Make a fast diagonal run into right-side attacking space.
   - Move toward approximately x=+35 to +45 for HOME or x=-35 to -45 for AWAY.
   - Sprint when a forward passing lane exists.
3. When player 3 is central:
   - Stay wider on the right to stretch the defense.
4. When player 3 moves left or receives wide:
   - Attack the center or far-post area.
5. PRESS_BALL only when:
   - Player {MY_PLAYER_ID} is the closest forward;
   - The ball is in the opponent's half; and
   - Player {MY_PLAYER_ID} can challenge immediately.
   - Use intensity 0.80-0.88 for duration 2.
6. If player 3 is pressing, do not join the same press. MOVE_TO block an outlet or prepare for the next attacking pass.
7. INTERCEPT a loose midfield or attacking-half ball when player {MY_PLAYER_ID} can arrive first.

Against a defensive opponent, maintain width, then cut toward goal when space opens. Against an aggressive opponent, attack the open right-side space during counterattacks.
Leading late: prefer safe passes. Trailing late: attack farther forward and shoot reasonable chances from up to 27 units.

## Allowed Commands
- MOVE_TO: target_x, target_y, sprint
- PASS: target_player_id, type ("GROUND"|"AERIAL"|"THROUGH")
- SHOOT: aim_location ("TL"|"TR"|"BL"|"BR"|"CENTER"), power
- PRESS_BALL: intensity
- INTERCEPT: aggressive

## Output
Return ONLY:
[{{"commandType":"<MOVE_TO|PASS|SHOOT|PRESS_BALL|INTERCEPT>","playerId":{MY_PLAYER_ID},"parameters":{{}},"duration":0}}]
Use duration 0 for MOVE_TO, PASS, and SHOOT; use 1-2 for maintained commands. If uncertain while not possessing the ball, MOVE_TO open right-side attacking space. No explanation or markdown."""


# --- Fallback ---

fallback_commands = build_fallback(FWD2_CONFIG)


# --- Wire it up ---

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-lite-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=FWD2_CONFIG,
)

if __name__ == "__main__":
    app.run()
