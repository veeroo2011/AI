#                    ┌──────────────┐
#                    │     LLM      │
#                    └──────┬───────┘
#                           │
#                    enough evidence?
#                     /           \
#                   yes            no
#                    │              │
#                    ▼              ▼
#                   END     inspect_ecs_service
#                                  │
#                                  ▼
#                         get_ecs_service_status()
#                                  │
#                                  ▼
#                              AWS result
#                                  │
#                                  ▼
#                                State
#                                  │
#                                  └──────→ LLM

from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from openai import OpenAI


client = OpenAI()

# Define state type
class State(TypedDict):
    question: str
    evidence: list[str]
    answer: str
    decision: str

# Define LLM as a node
def ask_llm(state):
    response = client.responses.create(
        model="gpt-5.4-mini",
        input=f"""
        You are an ECS troubleshooting assistant.

        "Question": {state["question"]}
        "evidence": {state["evidence"]}

        Based on the evidence, decide whether there is enough evidence
        to provide a diagnosis.

        Return your response in exactly this format:

        DECISION: enough_evidence
        ANSWER: <your diagnosis>

        or:

        DECISION: need_more_evidence
        ANSWER: <what additional evidence is needed>
        """
    )
    output = response.output_text

    print("LLM response:")
    print(output)

    if "DECISION: enough_evidence" in output:
        decision = "enough_evidence"
    else:
        decision = "need_more_evidence"

    return {
        "decision": decision,
        "answer": output
    }

# Router function if llm need more evidence then it will call node gather_evidence
def decide_next_step(state):
    if state["decision"] == "enough_evidence":
        return END
    return "inspect_ecs_service"

# define normal python function instead of node
def get_ecs_service_status():
    print("Calling ecs service tools")
    return{
        "desired_count": 1,
        "running_count": 0,
        "pending_count": 0
    }


# define function to gather more evidence
def inspect_ecs_service(state):

    print("Gathering more evidence")

    service_status = get_ecs_service_status()

    # Adding additional evidence to the existing evidence list
    return {
        "evidence": state["evidence"] + [
            f"Desire count: {service_status["desired_count"]}",
            f"Running count: {service_status["running_count"]}",
            f"Pending count: {service_status["pending_count"]}"
        ]
    }


graph_builder = StateGraph(State)

graph_builder.add_node("ask_llm", ask_llm)
graph_builder.add_node("inspect_ecs_service", inspect_ecs_service)

graph_builder.add_edge(START, "ask_llm")


graph_builder.add_conditional_edges(
    "ask_llm",
    decide_next_step,
)

# Making loop gather_evidence call to LLM so there is no END
# END will be depends on LLM output
graph_builder.add_edge(
    "inspect_ecs_service",
    "ask_llm"
)

graph = graph_builder.compile()

# passing initial evidence and question to graph
result = graph.invoke({
    "question": "What is wrong with this ECS service?",
    "evidence": []
        #"Desired count is 1 but running count is 0"
        #"Task failed to pull ECR registry authentication",
        #"Connection timeout to ECR API"
    #]    
})

print("Question:", result["question"])
print("Answer:", result["answer"])


# Complete execution

#                    START
#                      │
#                      ▼
#                    LLM #1
#                      │
#               need_more_evidence
#                      │
#                      ▼
#               inspect_ecs_service
#                      │
#                ecs_service_status()
#                      |
#                      ▼
#                   AWS result
#                      |
#                      ▼
#                  state updated
#                      │
#                      ▼
#                    LLM #2
#                      │
#                enough_evidence
#                      │
#                      ▼
#                     END
