from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from react_agent.multi_agent.rpa_agent import rpa_agent
from react_agent.multi_agent.extraction_agent import extraction_agent

from langgraph.runtime import Runtime
from react_agent.context import Context
from react_agent.state import InputState, State
from react_agent.utils import load_chat_model

#Initialize Worker agents
rpa_agent = rpa_agent()
extraction_agent = extraction_agent()

runtime = Runtime(context=Context)

#Initialize Supervisor Agent and assign worker agents
supervisor_agent = create_supervisor(
    agents=[rpa_agent, extraction_agent],
    model=load_chat_model(runtime.context.supervisor_model),
    prompt=(
        runtime.context.supervisor_system_prompt
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
    input_schema=InputState, 
    context_schema=Context,
    handoff_tool_prefix="assign_to_"

).compile(name="Supervisor_Agent")