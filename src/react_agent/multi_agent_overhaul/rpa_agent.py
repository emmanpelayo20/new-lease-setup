"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime

from react_agent.multi_agent_overhaul.context import Context
from react_agent.multi_agent_overhaul.state import InputState, State
from react_agent.multi_agent_overhaul.tools import RPA_AGENT_TOOLS, update_workflow_status
from react_agent.multi_agent_overhaul.utils import load_chat_model


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

    print("rpa_agent: call_model")

    # Initialize the model with tool binding. Change the model or add more tools here.

    model = load_chat_model(runtime.context.worker_agents_model).bind_tools(RPA_AGENT_TOOLS)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = runtime.context.rpa_agent_system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

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

def post_model_process(state: State):
    
    request_id = state.requestid
    step_id = "10" #step number of lease activation

    print("Updating request Id:" + request_id)
    #Update Workflow status
    response = update_workflow_status(request_id=request_id,step_id=step_id,status="completed")

    print(response)


def rpa_agent():

    # Define a new graph
    builder = StateGraph(State, input_schema=InputState, context_schema=Context)

    # Define the two nodes we will cycle between
    builder.add_node(call_model)
    builder.add_node("tools", ToolNode(RPA_AGENT_TOOLS))
    builder.add_node(post_model_process)

    # Set the entrypoint as `call_model`
    # This means that this node is the first one called
    builder.add_edge("__start__", "call_model")


    def route_model_output(state: State) -> Literal["post_model_process", "tools"]:
        """Determine the next node based on the model's output.

        This function checks if the model's last message contains tool calls.

        Args:
            state (State): The current state of the conversation.

        Returns:
            str: The name of the next node to call ("post_model_process" or "tools").
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(
                f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
            )
        # If there is no tool call, then we finish
        if not last_message.tool_calls:
            return "post_model_process"
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
    builder.add_edge("post_model_process","__end__")

    # Compile the builder into an executable graph
    graph = builder.compile(name="rpa_agent")
    return graph
