from react_agent.multi_agent_overhaul.rpa_agent import rpa_agent
from react_agent.multi_agent_overhaul.extraction_agent import extraction_agent

from react_agent.multi_agent_overhaul.tools import SUPERVISOR_AGENT_TOOLS
from react_agent.multi_agent_overhaul.state import InputState, State
from react_agent.multi_agent_overhaul.context import Context
from react_agent.multi_agent_overhaul.utils import load_chat_model

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

from langfuse.langchain import CallbackHandler

runtime = Runtime(context=Context)

async def call_model(
    state: State, runtime: Runtime[Context]
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """

    print("supervisor_agent: call_model")

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(runtime.context.supervisor_model).bind_tools(SUPERVISOR_AGENT_TOOLS)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = runtime.context.supervisor_system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}

def supervisor_agent():
# Define a new graph
    builder = StateGraph(State, input_schema=InputState, context_schema=Context)

    # Define the two nodes we will cycle between
    builder.add_node(call_model)
    builder.add_node("tools", ToolNode(SUPERVISOR_AGENT_TOOLS))

    # Set the entrypoint as `call_model`
    # This means that this node is the first one called
    builder.add_edge("__start__", "call_model")

    def route_model_output(state: State) -> Literal["__end__", "tools"]:
        """Determine the next node based on the model's output.

        This function checks if the model's last message contains tool calls.

        Args:
            state (State): The current state of the conversation.

        Returns:
            str: The name of the next node to call ("__end__" or "tools").
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(
                f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
            )
        # If there is no tool call, then we finish
        if not last_message.tool_calls:
            return "__end__"
        # Otherwise we execute the requested actions
        return "tools"

    # Add a conditional edge to determine the next step after `call_model`
    builder.add_conditional_edges(
        "call_model",
        # After call_model finishes running, the next node(s) are scheduled
        # based on the output from route_model_output
        route_model_output,
    )

    # Add a normal edge from `tools` to `call_model`
    # This creates a cycle: after using tools, we always return to the model
    builder.add_edge("tools", "call_model")

    # Compile the builder into an executable graph
    graph = builder.compile(name="supervisor_agent")
    return graph

#Initialize agents
supervisor_agent = supervisor_agent()
rpa_agent = rpa_agent()
extraction_agent = extraction_agent()

langfuse_handler = CallbackHandler()

builder = StateGraph(State, input_schema=InputState, context_schema=Context)

# NOTE: `destinations` is only needed for visualization and doesn't affect runtime behavior
builder.add_node(supervisor_agent, destinations=("extraction_agent", "rpa_agent", END))
builder.add_node(extraction_agent)
builder.add_node(rpa_agent)
builder.add_edge(START, "supervisor_agent")
# always return back to the supervisor
builder.add_edge("extraction_agent", "supervisor_agent")
builder.add_edge("rpa_agent", "supervisor_agent")
graph = builder.compile()#.with_config({"callbacks": [langfuse_handler]})
