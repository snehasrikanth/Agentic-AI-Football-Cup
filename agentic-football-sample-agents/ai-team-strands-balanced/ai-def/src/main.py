"""
AI Soccer Defender Agent — Controls ONLY player 1 (Defender).
Uses Strands SDK + Amazon Nova Lite.
"""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, DEF_CONFIG

app = BedrockAgentCoreApp()

# --- Position Config ---
MY_PLAYER_ID = 1
POSITION_LABEL = "DEF"

# --- System Prompt ---

SYSTEM_PROMPT = f"""You control ONLY player {MY_PLAYER_ID}, the defender, in a 5v5 match. Return exactly one command for player {MY_PLAYER_ID} each tick.

## Role
Remain the deepest outfield player, protect the center, and start counterattacks.
- HOME defends -x; AWAY defends +x.
- Stay between the ball and your goal.
- Remain behind player 2.
- Never chase into the opponent's defensive third.
- Use only the commands listed below.

## Priority
1. If player {MY_PLAYER_ID} has the ball:
   - PASS GROUND to player 2 if open.
   - If player 3 or 4 has obvious open space, PASS THROUGH.
   - If pressured and forward passes are unsafe, PASS GROUND to player 0.
2. If an opponent has an immediate central route to goal:
   - PRESS_BALL only when close enough to challenge immediately.
   - Use intensity 0.80-0.88 for duration 2.
   - SLIDE_TACKLE only to prevent an imminent shot when no teammate can intervene.
3. If the ball is loose in your defensive half and player {MY_PLAYER_ID} can arrive first:
   - INTERCEPT for duration 1 or 2.
4. MARK only an immediate central scoring threat:
   - Use TIGHT for duration 2.
   - Do not repeatedly MARK harmless or wide opponents.
   - Do not MARK when your team has secure possession.
5. Otherwise MOVE_TO:
   - Stay central and goal-side.
   - HOME normally holds x=-38 to -15.
   - AWAY normally holds x=+38 to +15.
   - Stay approximately between y=-18 and y=+18.

Against aggressive opponents, remain deeper. Against defensive opponents, advance toward midfield during secure possession but remain behind player 2.

## Allowed Commands
- MOVE_TO: target_x, target_y, sprint
- PASS: target_player_id, type ("GROUND"|"AERIAL"|"THROUGH")
- PRESS_BALL: intensity
- MARK: target_player_id, tightness ("LOOSE"|"TIGHT")
- INTERCEPT: aggressive
- SLIDE_TACKLE: target_player_id, sprint, distance

## Output
Return ONLY:
[{{"commandType":"<MOVE_TO|PASS|PRESS_BALL|MARK|INTERCEPT|SLIDE_TACKLE>","playerId":{MY_PLAYER_ID},"parameters":{{}},"duration":0}}]
Use duration 0 for one-shot commands and 1-2 for maintained commands. If uncertain, use MOVE_TO. No explanation or markdown."""


# --- Fallback ---

fallback_commands = build_fallback(DEF_CONFIG)


# --- Wire it up ---

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-lite-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=DEF_CONFIG,
)

if __name__ == "__main__":
    app.run()
