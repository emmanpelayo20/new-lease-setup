from langgraph_supervisor import create_supervisor

from react_agent.multi_agent.rpa_agent import rpa_agent
from react_agent.multi_agent.extraction_agent import extraction_agent
from react_agent.multi_agent.lease_processor_agent import lease_processor_agent

from langgraph.runtime import Runtime
from react_agent.multi_agent.context import Context
from react_agent.multi_agent.utils import load_chat_model
from react_agent.multi_agent.state import State, get_file_binary_list

from langchain_core.messages import HumanMessage, RemoveMessage

from typing import Annotated, Sequence, Dict, Any

from langfuse.langchain import CallbackHandler

# def pre_supervisor_node(state: State) -> State:

#     messages = state.messages
#     file_ids = []
    
#     for message in messages:
#         should_keep = True
        
#         if isinstance(message, HumanMessage):
#             content = message.content
            
#             # Check if this is a multimodal message with file content
#             if isinstance(content, list):
#                 for content_item in content:
#                     if isinstance(content_item, dict) and content_item.get("type") == "file":
#                         should_keep = False
#                         break
        
#         if not should_keep:
#             file_ids.append(message.id)

#     print(file_ids)
#     remove_file_messages = [RemoveMessage(id=m) for m in file_ids]
#     print(remove_file_messages)

#     return {
#         "messages": remove_file_messages,
#     }

langfuse_handler = CallbackHandler()

#Initialize Worker agents
rpa_agent = rpa_agent()
extraction_agent = extraction_agent()
#lease_processor_agent = lease_processor_agent()

runtime = Runtime(context=Context)

#Initialize Supervisor Agent and assign worker agents
graph = create_supervisor(
    agents=[rpa_agent, extraction_agent],
    model=load_chat_model(runtime.context.supervisor_model),
    prompt=(
        runtime.context.supervisor_system_prompt
    ),
    #response_format=,
    add_handoff_back_messages=False,
    add_handoff_messages=True,
    output_mode="last_message", 
    context_schema=Context,
    state_schema= State,
    #pre_model_hook = pre_supervisor_node

).compile(name="supervisor_agent").with_config({"callbacks": [langfuse_handler]})