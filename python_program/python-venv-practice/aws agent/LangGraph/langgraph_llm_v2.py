#                     ┌──────────────┐
#                     │     LLM      │
#                     └──────┬───────┘
#                            │
#                         decision
#                       /          \
#                      /            \
#          enough_evidence      need_more_evidence
#                │                    │
#                ▼                    ▼
#               END            gather_evidence
#                                   │
#                                   ▼
#                              state update
#                                   │
#                                   └──────→ LLM

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

def request_more_evidence(state):
    print("More evidence is required.")
    return {
        "answer": "The available evidence is not sufficient for a diagnosis."
    }

# Router function if llm need more evidence then it will call node gather_evidence
def decide_next_step(state):
    if state["decision"] == "enough_evidence":
        return END
    return "gather_evidence"

# define function to gather more evidence
def gather_evidence(state):
    print("Gathering more evidence")
    
    # Adding additional evidence to the existing evidence list
    return {
        "evidence": state["evidence"] + [
            "Task stopped reason: ResourceInitializationError",
            "ECS task could not pull registry authentication"
        ]
    }


graph_builder = StateGraph(State)

graph_builder.add_node("ask_llm", ask_llm)
graph_builder.add_node("gather_evidence", gather_evidence)

graph_builder.add_edge(START, "ask_llm")


graph_builder.add_conditional_edges(
    "ask_llm",
    decide_next_step,
)

# Making loop gather_evidence call to LLM so there is no END
# END will be depends on LLM output
graph_builder.add_edge(
    "gather_evidence",
    "ask_llm"
)

graph = graph_builder.compile()

# passing initial evidence and question to graph
result = graph.invoke({
    "question": "What is wrong with this ECS service?",
    "evidence": [
        "Desired count is 1 but running count is 0"
        #"Task failed to pull ECR registry authentication",
        #"Connection timeout to ECR API"
    ]    
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
#               gather_evidence
#                      │
#                  state updated
#                      │
#                      ▼
#                    LLM #2
#                      │
#                enough_evidence
#                      │
#                      ▼
#                     END
