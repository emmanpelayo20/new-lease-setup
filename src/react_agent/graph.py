"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
import os
import requests
import json
from typing import Dict, List, Literal, cast
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, filter_messages
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime

from langfuse.langchain import CallbackHandler

from react_agent.context import Context
from react_agent.state import InputState, State, remove_messages_in_state, get_file_binary_list
from react_agent.tools import TOOLS
from react_agent.utils import load_chat_model

load_dotenv()

# Define the function that pre-process attached pdf documents
def pre_process_documents(state: State):
    
    def process_document_with_api(base64_content: str, filename: str, content_type: str) -> str:
     """
    Process a document by converting it to base64 and sending to your API.
   
    This tool acts as the bridge between your LangGraph application and your
    document processing API that stores content in the vector database.
    """
     
     api_endpoint = os.getenv("DOC_API_ENDPOINT_UPLOAD")
 
     try:
          payload = {
               "filename" : filename,
               "file_data": base64_content,
               "content_type": content_type
          }
 
          headers = {
               "Content-Type": "application/json",
          }
 
          response = requests.post(api_endpoint, json=payload, headers=headers)
 
          if response.status_code == 200:
               result = response.json
               return f"Document processed sucessfully: '{filename}'"
          else:
               return f"Failed to process document: '{filename}'. API returned status code:{response.status_code}"
   
     except Exception as e:
          return f"Error processing document ' {filename}' : {str(e)}"
     
    try: 
        #return attached files binary data, filename, mime type
        binary_files = get_file_binary_list(state, "type", "file")

        #if has binary files, pre process it
        if(len(binary_files) > 0):
            for binary in binary_files:
                process_document_with_api(binary[0], binary[1], binary[2])
    except:
        print("An error occured while trying to pre-process documents.")

# Define the function that calls the model
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

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(runtime.context.model).bind_tools(TOOLS)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = runtime.context.system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    #remove type = file to be passed to llm call
    updated_state_messages = remove_messages_in_state(state.messages, "type", "file")

    response = cast(
         AIMessage,
         await model.ainvoke(
             [{"role": "system", "content": system_message}, *updated_state_messages]
         ),
     )

    #Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    updated_state_messages = []

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}

# Define a new graph

builder = StateGraph(State, input_schema=InputState, context_schema=Context)

# Define the two nodes we will cycle between
builder.add_node(pre_process_documents)
builder.add_node(call_model)
builder.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "pre_process_documents") 
builder.add_edge("pre_process_documents", "call_model")


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

langfuse_handler = CallbackHandler()

# Compile the builder into an executable graph
graph = builder.compile(name="ReAct Agent").with_config({"callbacks": [langfuse_handler]})