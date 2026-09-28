# Agentic AI Football Cup

A multi-agent AI football simulation where five role-based players coordinate in real time to defend, create chances, and score goals.

This project adapts the AWS Agentic Football Cup sample into deployable, position-specific agents built with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) and Amazon Bedrock AgentCore.

## What is included

- Five specialist agents: goalkeeper, defender, midfielder, and two forwards
- A balanced `1-1-1-2` tactical formation
- LLM-driven decisions with position-specific system prompts
- Rule-based fallbacks when an LLM response is unavailable or invalid
- Tolerant JSON parsing for reliable in-game commands
- Local tests and scripts to deploy the full team to Amazon Bedrock AgentCore
- Alternative tactical implementations: balanced, aggressive, defensive, memory-enabled, and gateway-based teams

## How it works

Every two seconds, each agent receives a snapshot of the match state: ball and player positions, possession, score, stamina, current actions, and coach instructions. The agent returns a valid command for its assigned player.

```text
Match Server → Agent Loop → Five AI Players
                              ├── Goalkeeper
                              ├── Defender
                              ├── Midfielder
                              ├── Forward 1
                              └── Forward 2
```

The shared library handles agent construction, match-state parsing, command validation, error recovery, and safe fallback behavior.

## Project structure

```text
agentic-football-sample-agents/
├── BUILD_AND_DEPLOY.md              # Complete workshop and deployment guide
├── lib/                             # Shared agent framework and tests
├── ai-team-strands-balanced/        # Balanced 1-1-1-2 team
├── ai-team-strands-extremely-aggressive/
├── ai-team-strands-extremely-defensive/
├── ai-team-strands-memory/          # Team with memory capabilities
└── ai-team-strands-gateway/         # Team with tactical gateway tools
```

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 20+ and npm
- AWS CLI configured with credentials
- AWS account with Amazon Bedrock model access
- [AgentCore CLI](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-getting-started.html), AWS CDK, and [uv](https://docs.astral.sh/uv/)

### Test locally

```bash
cd agentic-football-sample-agents/ai-team-strands-balanced
python3 ai-gk/test_local.py
```

To test an agent with a real model response, use:

```bash
python3 ai-gk/test_local.py --llm
```

### Deploy the balanced team

```bash
cd agentic-football-sample-agents/ai-team-strands-balanced
AWS_DEFAULT_REGION=us-east-1 python deploy_all.py
```

For complete setup instructions, the command contract, architecture details, and both no-code and code-based deployment paths, see [Build and Deploy an AWS Agentic Football Team](agentic-football-sample-agents/BUILD_AND_DEPLOY.md).

## Player roles

| Player | Role | Default model |
| --- | --- | --- |
| 0 | Goalkeeper | Nova Micro |
| 1 | Defender | Nova Lite |
| 2 | Midfielder | Nova Pro |
| 3 | Forward 1 | Nova Micro |
| 4 | Forward 2 | Nova Lite |

## Contributing

Experiment with tactical prompts, model choices, fallback configurations, and team formations. Run the local tests before deploying changes to AgentCore.
