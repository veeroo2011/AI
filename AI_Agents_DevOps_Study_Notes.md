
# AI Agents for DevOps - Structured Study Notes

Source: attached ChatGPT conversation export "Learn AI Agents for DevOps" dated 09/19/2026.

## 1. Roadmap

LLM -> Prompting -> Tools -> Tool Calling -> Agents -> Agent Frameworks -> DevOps Agents -> Production

The conversation's practical goal is a DevOps AI agent that can investigate AWS, GitHub Actions, Kubernetes, Terraform, monitoring and logs.

### Core definitions

| Term | 1-sentence definition |
|---|---|
| AI | Broad field of making computers perform tasks that normally require human intelligence. |
| Generative AI | AI that generates new content such as text, code, JSON, images or audio. |
| LLM | Large Language Model designed to understand and generate human language. |
| Agent | LLM + tools + loop, later extended with state/memory, planning, grounding and guardrails. |
| Tool | Callable function/API that lets the agent obtain real information or perform an operation. |
| State | Structured record of what the agent knows, what it has already done and what remains to investigate. |
| Planner | Logic that selects the next investigation/action from the current state. |
| Grounding | Anchoring model output to real evidence, tool results and validation. |
| Structured output | Machine-readable output constrained to an expected schema such as JSON. |

## 2. Theory branch

### AI -> ML -> Generative AI -> LLM

This is the simplified learning hierarchy used in the conversation:

AI
  -> Machine Learning
  -> Deep Learning
  -> Generative AI
  -> LLM
  -> AI Application
  -> AI Agent

### How an LLM works

Text -> tokens -> token IDs -> model processing -> next-token prediction -> generated response

- Token = a piece of text.
- Token ID = numeric identifier for a token.
- Context window = maximum tokenized context the model can use for the current request.
- Tool results also consume context.

### Prompts and messages

- System message = behavior/instructions.
- User message = request/input.
- Assistant message = model output.
- Tool call/result = structured exchange with an external function.

### Temperature

Temperature controls variation in next-token choice.
For DevOps troubleshooting, the conversation recommends lower temperature for more focused, factual-style behavior. Temperature alone does not make an agent safe.

### Hallucinations and grounding

Hallucination = plausible but incorrect information.

Grounding in the course means supplying real context/evidence, using tools, validating important outputs, and avoiding invented infrastructure state.

## 3. Context and memory

### Short-term / in-context memory

Conversation history + new user message -> LLM -> new response

The conversation stresses that the application provides the relevant prior context; the model should not be treated as magically remembering arbitrary previous API calls.

Connection:
Short-term memory <-> conversation history <-> context window <-> in-context learning

### Long-term memory

Planned later in the roadmap. It was not fully implemented in the exported conversation.

### previous_response_id

The conversation distinguishes:
- previous_response_id: continues the response context chain.
- explicit instructions: remain the application's behavioral contract and should not be assumed to be automatically re-injected on every follow-up call.

## 4. Tool Use / Function Calling

### Definition

Tool calling lets the model request that the application execute a function with specific arguments.

### Manual tool-calling loop

1. User request.
2. Call the model.
3. Inspect `response.output`.
4. Detect `item.type == "function_call"`.
5. Read `item.name`, `item.arguments`, `item.call_id`.
6. Execute the mapped Python function.
7. Send a `function_call_output` tied to the same `call_id`.
8. Call the model again.
9. Repeat until the model returns a final answer.

### Key syntax

```python
for item in response.output:
    if item.type == "function_call":
        print("LLM wants to call a tool")
        print("Tool:", item.name)
        print("Arguments:", item.arguments)
        print("Call ID:", item.call_id)
```

### call_id

`call_id` links the returned tool result to the exact tool request.

LLM -- call_id=ABC --> Tool
Tool -- call_id=ABC --> LLM

### function_call_output

This structured result tells the model which tool call the returned data belongs to.

### Arguments

Example function:

```python
def get_server_status(server_name):
    ...
```

Possible model-generated arguments:

```json
{"server_name": "web-01"}
```

### Tool selection

The model uses the available tool definitions/schema, including tool name, description and arguments, to select an appropriate tool.

Good tool descriptions therefore matter for routing.

## 5. Agent loop

The core agent loop from the conversation:

```text
User
  -> LLM
  -> Need more information?
       -> YES -> Tool -> Result -> LLM
       -> NO  -> Answer
```

Why multiple model calls happen:
Each new tool result can change the next decision.

Example:
User -> ECS service unhealthy
  -> get service status
  -> get tasks
  -> get task details
  -> get CloudWatch logs
  -> diagnose

## 6. State and Planning

The agent state in the conversation evolved to include:

- cluster
- service
- services
- service_status
- tasks
- stopped_tasks
- task_details
- service events
- cloudtrail_event
- cloudwatch_logs
- evidence_analysis
- failure_classification
- investigation_complete
- investigation_reason
- missing_evidence
- next_action

Planner interface:

```python
def determine_next_action(state):
    ...
```

### Planner pattern

```text
Current state
    |
    v
determine_next_action()
    |
    +--> collect evidence
    +--> recheck
    +--> analyze evidence
    +--> determine missing evidence
    +--> diagnose
    +--> complete
```

### Infinite-loop lesson

If the planner returns the same action but the action does not update the state used by the planner, the loop can repeat forever.

Rule:
Every action must cause a meaningful state update or move to a terminal state.

Examples:
- get tasks -> update `state["tasks"]`
- recheck service -> refresh `state["service_status"]`
- get logs -> update `state["cloudwatch_logs"]`
- classify failure -> update `state["failure_classification"]`
- determine missing evidence -> update `state["missing_evidence"]`

## 7. ECS troubleshooting architecture

Evidence chain built and tested in the conversation:

1. ECS service status
2. ECS tasks
3. stopped-task details
4. service events
5. CloudTrail lookup
6. CloudWatch log configuration
7. exact log stream
8. recent/time-window log events
9. deterministic evidence analysis
10. failure classification
11. incident decision engine
12. LLM diagnosis

### ECS functions/tools

Examples developed in the conversation:
- `get_ecs_service_status()`
- `get_ecs_tasks()`
- `get_stopped_ecs_tasks()`
- `get_ecs_task_details()`
- service-event retrieval
- CloudTrail lookup
- `get_ecs_task_log_configuration()`
- `find_ecs_log_stream()`
- recent/time-window log retrieval
- combined `get_ecs_task_logs()`
- deterministic evidence analysis
- failure classification
- incident decision logic

### ECS lifecycle rule learned

For the specific workflow, `desired_count == running_count` was used as a capacity/recovery check.

Important refinement:
- desired count 0 can be intentional.
- user-initiated stop is not automatically an application failure.
- task startup failure is different from a running application later being stopped.

## 8. CloudWatch / evidence correlation

Task ARN
  -> task definition/log configuration
  -> log group + stream prefix
  -> exact log stream
  -> log events
  -> evidence analysis

The conversation intentionally tested the CloudWatch functions independently before integration. This revealed practical issues such as incorrect log-stream naming assumptions and tasks that had not yet produced a usable log stream.

### Evidence separation

Raw evidence
  -> deterministic analysis
  -> conflict detection / confidence
  -> LLM interpretation

This is a central design principle in the source chat.

## 9. Failure classification and incident decision engine

Fields introduced include:
- `failure_stage`
- `failure_type`

Examples tested:
- `task_startup / ECR_CONNECTIVITY`
- `task_startup / ECR_AUTHORIZATION`
- `task_termination / USER_INITIATED_STOP`

### Conflict detection

The workflow can separate:
1. What ECS reports.
2. Whether the other evidence agrees.

Example:
ECS says user-initiated stop while the container has a non-zero exit code.

Result can preserve:
`failure_type = USER_INITIATED_STOP`
and add:
`evidence_conflict = true`

Chain:
Classification -> evidence validation -> conflict detection -> confidence adjustment -> diagnosis

### Missing evidence

The conversation refined the loop to:

```python
if not investigation_status["complete"]:
    return "determine_missing_evidence"
```

This replaces an overly generic "investigate_more" step with a targeted search for the evidence needed next.

## 10. OpenAI Agents SDK

The conversation makes this memorable distinction:

| Concept | Memorize |
|---|---|
| Agent | Definition / configuration |
| Model | Reasoning |
| Runner | Execution / orchestration |

### Agent

```python
from agents import Agent, Runner, function_tool

agent = Agent(
    name="ECS Troubleshooting Agent",
    model="gpt-5.4-mini",
    instructions="""
    You are an AWS ECS troubleshooting agent.
    Do not invent AWS resource information.
    Use tools when necessary.
    """,
    tools=[get_ecs_service_status, get_ecs_tasks],
)
```

Agent defines what it is, how it behaves, which model it uses and which tools it has.

### Model

```python
model="gpt-5.4-mini"
```

The model is the reasoning engine.

### Runner

```python
result = Runner.run_sync(
    agent,
    "What is the status of my ECS service?"
)
```

Runner starts and manages the agent execution lifecycle, including the model/tool/result cycle.

### SDK execution

```text
User
  -> Runner
  -> Agent
  -> Model
  -> Tool
  -> Tool result
  -> Model
  -> Final answer
```

## 11. @function_tool and tool schema

Definition:
`@function_tool` exposes a Python function as a callable tool for the Agents SDK.

```python
@function_tool
def get_environment():
    return {
        "environment": "dev",
        "region": "eu-west-1"
    }
```

The tool schema communicates:
- what can be called
- what the tool does
- what arguments it needs

In the custom Phase 4 agent, you built tool schemas manually. In the Agents SDK, the decorated function supplies the tool interface/schema for the runtime.

## 12. Multiple and dependent tools

### Multiple tools

The model selects a relevant tool using the tool definitions and the user's request.

### Dependent tools

Example tested in the conversation:

```text
User request
   ->
get_ecs_tasks()
   ->
select first task
   ->
get_ecs_task_details()
   ->
final answer
```

The second tool depends on information returned by the first tool.

### Tool-call tracing

Tracing shows the model/tool boundary and helps inspect:
- selected tool
- generated arguments
- tool execution
- tool result
- next model step
- final result

## 13. Framework / ecosystem roadmap

The source roadmap proposes:

- OpenAI Agents SDK
- Anthropic
- LangChain
- LangGraph
- MCP
- possibly CrewAI / other frameworks where useful

### MCP

Planned architecture:

```text
AI Agent
   |
   v
  MCP
   +--> AWS
   +--> GitHub
   +--> Kubernetes
   +--> Terraform
   +--> Databases
   +--> Monitoring
```

MCP was presented as a planned protocol layer and the conversation planned to build an MCP server rather than only study the theory.

## 14. Planned advanced topics

The original roadmap places these after MCP:

- Memory
- RAG
- Multi-agent systems
- Guardrails / security
- Production architecture

These were roadmap items, not all completed implementations in the exported conversation.

## 15. Cross-links

- Short-term memory <-> conversation history <-> context window.
- Tool calling <-> grounding.
- Tools <-> planning.
- State <-> planning.
- Evidence analysis <-> grounding.
- ECS task lifecycle <-> CloudWatch log availability.
- Agent <-> Runner.
- Manual loop <-> framework orchestration.

## 16. Final single-glance map

```text
                    AI AGENTS LEARNING ROADMAP
                              |
       +----------------------+----------------------+
       |                      |                      |
    THEORY                 AGENT CORE             PRACTICAL
       |                      |                      |
 AI / GenAI / LLM       Model / Agent            Python / boto3
 Tokens / Context       Tools / Functions        AWS APIs
 Prompts / Messages     State / Memory           ECS
 Parameters             Planning / Loop          CloudWatch
 Grounding              Evidence                 CloudTrail
 Structured JSON        Diagnosis                GitHub / K8s
       |                      |                      |
       +----------------------+----------------------+
                              |
                      MANUAL TOOL LOOP
      User -> LLM -> function_call -> Python Tool
               ^                         |
               |                         v
               +---- function_call_output

                      AGENTS SDK LOOP
      User -> Runner -> Agent -> Model -> Tool
            -> Result -> Model -> Answer

                       LATER / PLANNED
        MCP -> Memory -> RAG -> Multi-agent
              -> Guardrails -> Production
```

## 17. Memorize these

Agent = Definition
Model = Reasoning
Runner = Execution

Manual tool loop:
Model -> function_call -> Python tool -> function_call_output -> Model

DevOps investigation loop:
Incident -> Evidence -> State -> Planner -> Tool -> Analyze -> Diagnose

Correctness rule:
Never let the LLM invent infrastructure state when a tool can retrieve the real state.

## 18. Completed progression from the chat

1. Single-turn OpenAI API call
2. Better context experiments
3. Multi-turn conversation history
4. Structured JSON output
5. First function call
6. Tool arguments
7. call_id
8. function_call_output
9. Complete manual tool loop
10. Real AWS / boto3 integration
11. ECS service discovery
12. Multiple/dependent tools
13. Agent state
14. Deterministic planner
15. ECS task investigation
16. CloudTrail evidence
17. CloudWatch log discovery
18. Evidence correlation
19. Failure classification
20. Incident decision engine
21. Investigation loop
22. Missing-evidence branch
23. OpenAI Agents SDK
24. Agent / Model / Runner
25. @function_tool
26. Multiple tools
27. Dependent tool calls
28. Tool-call tracing
