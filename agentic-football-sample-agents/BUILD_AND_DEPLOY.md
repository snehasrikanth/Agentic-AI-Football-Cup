# Build and Deploy an AWS Agentic Football Team

This guide explains how to design, test, deploy, register, and improve a five-agent football team for the AWS Agentic Football Cup.

You can use either of two paths:

- **AgentCore Harness:** configure prompts and models entirely in the AWS Console. This is the fastest route and requires no code.
- **Strands + AgentCore Runtime:** edit the sample Python agents, test them locally, and deploy them as AgentCore runtimes. This provides deterministic response parsing, rule-based fallbacks, and more control.

Do not mix ARN types between paths. Harness agents use **Harness ARNs**; code-based agents use **Runtime ARNs**.

## 1. Understand the Match Architecture

The workshop manages the match server, physics, orchestration, and Player Portal. You provide five independently deployed agents:

```text
Workshop infrastructure                 Your AWS account

Player Portal
     |
Match Server <-> Agent Loop <---------> AgentCore
                                          |- Player 0: Goalkeeper
                                          |- Player 1: Defender
                                          |- Player 2: Midfielder
                                          |- Player 3: Forward 1
                                          `- Player 4: Forward 2
```

Approximately every two seconds, the Agent Loop sends each agent a game-state snapshot. Each agent has at most five seconds to return one valid football command for its player.

The game state includes:

- Ball position, velocity, and possession
- Positions and movement of both teams
- Score, clock, and play mode
- Player stamina and current actions
- `teamId`, which determines attacking direction
- `myPlayers`, identifying the player controlled by this invocation
- `teamChat`, containing live coach instructions

The field is approximately `x=-55..+55` and `y=-35..+35`:

- HOME defends `-x` and attacks `+x`
- AWAY defends `+x` and attacks `-x`

## 2. Design the Team Before Deploying

Start with a clear tactical identity. The sample balanced team uses a `1-1-1-2` shape:

- Player 0: goalkeeper
- Player 1: deepest defender
- Player 2: central playmaker
- Player 3: primary striker
- Player 4: supporting striker

For each player, define:

1. **Identity:** the exact player ID and role.
2. **Zone:** where the player should normally operate.
3. **Decision hierarchy:** what to do in possession, out of possession, and when the ball is loose.
4. **Coordination rules:** when to defer to teammates and how to avoid duplicating their actions.
5. **Constraints:** actions or areas the player must avoid.
6. **Output contract:** exactly one JSON command for the correct player.
7. **Safe default:** normally `MOVE_TO` when the correct action is uncertain.

Good prompts are concise and operational. Prefer:

```text
If player 3 has possession within 18 units of goal, SHOOT unless the route is completely blocked.
```

Avoid:

```text
Be creative and play like a world-class striker.
```

### Coordination rules that matter

- Only the closest suitable player should press.
- If one forward presses, the other should remain available for a counterattack.
- The defender should remain behind the midfielder.
- The two forwards should use different channels.
- Players should pass or shoot only when possession is explicit.
- Maintained commands should use short durations so agents can reconsider quickly.

## 3. Command Contract

Every response must be a JSON array containing commands for the invoked player. The recommended design returns exactly one command:

```json
[{"commandType":"MOVE_TO","playerId":2,"parameters":{"target_x":8.0,"target_y":-3.0,"sprint":false},"duration":0}]
```

Common commands:

- `MOVE_TO`: `target_x`, `target_y`, `sprint`
- `PASS`: `target_player_id`, `type`
- `SHOOT`: `aim_location`, `power`
- `GK_DISTRIBUTE`: `target_player_id`, `method`
- `PRESS_BALL`: `intensity`
- `MARK`: `target_player_id`, `tightness`
- `INTERCEPT`: `aggressive`
- `FOLLOW_PLAYER`: `target_player_id`, `target_team`, `distance`
- `SLIDE_TACKLE`: `target_player_id`, `sprint`, `distance`
- `SET_STANCE`: `stance`

Use `duration: 0` for one-shot commands such as `MOVE_TO`, `PASS`, `SHOOT`, and `GK_DISTRIBUTE`. Use a positive duration for maintained commands such as `PRESS_BALL`, `MARK`, `INTERCEPT`, and `FOLLOW_PLAYER`.

Keep maintained durations short—typically one or two ticks—unless a longer commitment is deliberate.

## 4. Path A: Build with AgentCore Harness

Choose Harness when you want to focus on prompt engineering and tactics without writing or packaging code.

### Create the goalkeeper

1. Sign in to the AWS Console in `us-east-1`.
2. Open **Amazon Bedrock → AgentCore → Harness**.
3. Open the dropdown beside **Quick create harness**.
4. Select **Advanced create harness**.
5. Configure:
   - Name: `ai_gk_agent`
   - Model: a model available in the workshop account
   - Instructions: only the goalkeeper system prompt
   - Permissions: **Use another role**
   - Service role: the pre-provisioned role beginning with `team-SolutionAccessRole-`
6. Leave unrelated settings at their defaults.
7. Create the harness and wait for status **Ready**.

Do not select **Create default role** in the workshop account; participants generally cannot create IAM roles.

### Create the remaining players

Repeat the same process with:

- `ai_def_agent`: defender prompt for player 1
- `ai_mid_agent`: midfielder prompt for player 2
- `ai_fwd1_agent`: primary-striker prompt for player 3
- `ai_fwd2_agent`: supporting-striker prompt for player 4

Paste only one player's prompt into each harness. Never combine all five prompts in one harness.

### Choose a Harness model

Model selection is a latency-versus-reliability decision:

- A model that misses the five-second deadline cannot help, regardless of reasoning quality.
- A very small model may respond quickly but produce malformed JSON or misunderstand possession.
- Larger models generally follow strict output formats more reliably.

Start with a capable, responsive model such as Claude Sonnet 4.6 or Nova Pro when available in the workshop account. Run the fitness test repeatedly. Keep the model if it consistently returns valid commands within the deadline; switch to a faster option if timeouts recur.

For the goalkeeper, output reliability is more important than elaborate reasoning. For the midfielder, tactical reasoning is more valuable because passing and positioning decisions are more complex.

### Update a Harness agent

Open the harness, edit **Instructions** or change the model, and save. Changes apply to subsequent invocations without a code redeployment.

### Record the correct ARNs

Open each harness and copy its **Harness ARN**. Do not copy the Runtime ARN shown elsewhere in the console.

## 5. Path B: Build with Strands and AgentCore Runtime

Choose the code path when you want deterministic parsing, rule-based fallbacks, local tests, CloudWatch logs, and access to advanced AgentCore features.

### Clone the sample repository

```bash
git clone --filter=blob:none --sparse https://github.com/aws-samples/sample-ai-possibilities
cd sample-ai-possibilities
git sparse-checkout set agentic-football-sample-agents
cd agentic-football-sample-agents
```

The balanced team is located at:

```text
ai-team-strands-balanced/
├── ai-gk/               # Player 0
├── ai-def/              # Player 1
├── ai-mid/              # Player 2
├── ai-fwd1/             # Player 3
├── ai-fwd2/             # Player 4
├── deploy-all.sh
├── deploy-all-windows.ps1
└── deploy_all.py
```

Shared behavior lives in `lib/`:

- `agent_base.py`: model creation and invocation handling
- `state.py`: converts raw game state into model context
- `parsing.py`: extracts and validates model commands
- `fallback.py`: position-specific rule-based actions
- `json_tolerant.py`: recovers selected malformed JSON responses
- `test_helpers.py`: mock state for local testing

### Install prerequisites on macOS or Linux

Use Python 3.10 for compatibility with the deployment runtime.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env" 2>/dev/null || source "$HOME/.cargo/env" 2>/dev/null || true

python3 -m venv .venv
source .venv/bin/activate

pip install strands-agents bedrock-agentcore-starter-toolkit
pip install -r ai-team-strands-balanced/ai-gk/requirements.txt
```

You also need:

- AWS CLI
- `rsync`
- Valid workshop AWS credentials
- Access to the selected Bedrock models

### Configure temporary workshop credentials

Copy the credentials from **Workshop Studio → Get AWS CLI credentials**:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="us-east-1"
```

Verify them before testing or deploying:

```bash
aws sts get-caller-identity
```

If this fails, refresh the temporary credentials. Do not debug deployment until identity verification succeeds.

### Customize an agent

Each player's primary configuration is in:

```text
ai-team-strands-balanced/<agent>/src/main.py
```

The important values are:

```python
MY_PLAYER_ID = 0
POSITION_LABEL = "GK"

SYSTEM_PROMPT = """..."""

fallback_commands = build_fallback(GK_CONFIG)

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-micro-v1:0")
```

When changing an agent:

- Keep `MY_PLAYER_ID` aligned with its portal position.
- Keep the prompt's player ID consistent.
- List only commands that the role should use.
- Ensure command parameters match the game schema.
- Choose a fallback configuration appropriate for the role.
- Select a Bedrock model available in the workshop account and region.

### Understand the three safety layers

The code path prevents a single bad model response from freezing a player:

1. The LLM returns a command and the parser validates it.
2. If parsing fails, position-specific rule logic generates a fallback.
3. If both layers fail, the agent returns one safe last-resort command.

This is a major reliability advantage over prompt-only formatting.

## 6. Test Before Deployment

From `agentic-football-sample-agents/ai-team-strands-balanced`:

```bash
python3 ai-gk/test_local.py
python3 ai-def/test_local.py
python3 ai-mid/test_local.py
python3 ai-fwd1/test_local.py
python3 ai-fwd2/test_local.py
```

These offline tests validate state summarization, parsing, player IDs, and fallbacks without calling AWS.

Test a real model response after configuring credentials:

```bash
python3 ai-gk/test_local.py --llm
```

Repeat the LLM test several times because model output is non-deterministic. Confirm:

- The response arrives within five seconds.
- It is valid JSON.
- It contains exactly one command.
- `playerId` is correct.
- The command is legal for the selected role.
- Possession-only actions are not attempted without possession.

## 7. Deploy Code-Based Agents

From the balanced-team directory:

```bash
cd ai-team-strands-balanced
chmod +x deploy-all.sh
AWS_DEFAULT_REGION=us-east-1 ./deploy-all.sh
```

Deploy only one changed agent:

```bash
AWS_DEFAULT_REGION=us-east-1 ./deploy-all.sh ai-gk
```

On Windows PowerShell:

```powershell
$env:AWS_DEFAULT_REGION = "us-east-1"
.\deploy-all-windows.ps1
```

The deployment script:

1. Verifies the AgentCore CLI, AWS CLI, credentials, and required local tools.
2. Creates a temporary `_build/<agent>` staging directory.
3. Copies the agent source, shared library, and dependencies.
4. Generates `.bedrock_agentcore.yaml` with the account and region.
5. Runs `agentcore deploy`.
6. Creates or updates the AgentCore Runtime.
7. Removes the temporary build directory.

The configuration enables AgentCore observability and uses a Python 3.10 Linux ARM64 runtime.

After deployment:

1. Open **Amazon Bedrock → AgentCore → Runtime**.
2. Confirm all five agents show **Ready**.
3. Open each runtime.
4. Copy its **Runtime ARN**.

## 8. Register the Team in the Player Portal

1. Open [https://agentic-football.aws.dev](https://agentic-football.aws.dev).
2. Sign in with the event team code.
3. Open **My Team**.
4. Select a logo, formation, player names, and coach identity.
5. Register the five ARNs in the matching positions:
   - Player 0 ARN → goalkeeper
   - Player 1 ARN → defender
   - Player 2 ARN → midfielder
   - Player 3 ARN → forward 1
   - Player 4 ARN → forward 2
6. Run **Test your agents**.

Use Harness ARNs for Harness agents and Runtime ARNs for code-based agents.

Complete at least one practice match before official tournament matches begin.

## 9. Practice and Improve

Benchmark against all three reference styles:

- Balanced opponent: measures overall shape and decision quality.
- Extremely aggressive opponent: tests deep defending and counterattacking.
- Extremely defensive opponent: tests width, patience, movement, and shot creation.

Do not judge a strategy from one match. LLM decisions are non-deterministic. Run several matches against the same opponent and compare:

- Goals scored and conceded
- Valid-command rate
- Response latency
- Fallback frequency
- Shot quality and shot count
- Possession losses
- Duplicate pressing or marking
- Stamina usage

Use the iteration loop:

```text
Observe -> form one hypothesis -> change one variable -> deploy -> replay -> measure
```

Changing one prompt or model at a time makes results easier to interpret.

## 10. Observe and Troubleshoot

### CloudWatch and AgentCore

For Runtime agents:

1. Open **AgentCore → Runtime**.
2. Select an agent.
3. Follow its **Logs** link to CloudWatch.
4. Search for parse failures, exceptions, access errors, and timeouts.

Useful log patterns:

- `LLM parse failed, using fallback`: invalid or unusable model output
- `recovered malformed JSON`: tolerant parsing rescued the command
- `AccessDeniedException`: missing model, Memory, Gateway, or execution-role permission
- `Timeout`: model or tool chain exceeded the decision budget
- `agent error`: unhandled invocation failure

### Common deployment failures

**`aws sts get-caller-identity` fails**

Refresh Workshop Studio credentials and export all four AWS environment variables again.

**`agentcore` is not found**

Activate the virtual environment and install:

```bash
pip install bedrock-agentcore-starter-toolkit
```

**`uv` is not found**

Re-run the installer and source the environment file shown by the installer.

**Model access is denied**

Confirm the model is enabled and available in `us-east-1`, then verify the execution role can invoke it.

**Harness fitness tests fail intermittently**

Run the test again. If failures repeat, simplify the prompt, restrict the allowed command set, add concrete JSON examples, or select a more reliable model.

**The player moves but ignores the intended tactics**

Check whether fallbacks are activating. A functioning fallback can hide repeated malformed LLM output.

**The wrong player acts**

Verify `MY_PLAYER_ID`, the prompt identity, portal position, and registered ARN all agree.

## 11. Live Coaching

Coach messages are delivered in `gameState.teamChat`. Code-based agents must include that field in the model context if they are expected to react to it.

Make messages specific:

```text
Player 3: stay high and attack behind their advanced defender.
```

Avoid vague or conflicting instructions:

```text
Play better and be aggressive but also stay defensive.
```

Treat coaching as a tactical override, not a replacement for a well-defined base prompt.

## 12. Advanced AgentCore Options

After the baseline team works reliably, consider:

- **Memory:** recalls earlier decisions and opponent patterns within a match.
- **Gateway:** exposes tactical calculators as MCP tools.
- **Observability:** traces model calls, tools, memory access, latency, and errors.
- **Evaluate:** uses built-in or custom evaluators to assess decision quality.

Advanced features add latency and operational complexity. Establish a reliable baseline first, then add one feature at a time and measure whether it improves match results.

## Final Deployment Checklist

- [ ] All five player IDs and roles are correct.
- [ ] Every prompt has a clear priority order and safe default.
- [ ] Output is exactly one JSON command per invocation.
- [ ] Offline tests pass for all five agents.
- [ ] Repeated LLM or Harness tests stay within five seconds.
- [ ] All five AgentCore resources show **Ready**.
- [ ] Correct ARN type is registered for every player.
- [ ] Portal connectivity tests pass.
- [ ] At least one practice match is complete.
- [ ] Logs and latency have been reviewed.
- [ ] Strategy has been tested against more than one opponent style.

Build for reliability first, coordination second, and tactical sophistication third. A simple team that returns valid, timely, coordinated commands will usually outperform a clever team that times out or contradicts itself.
