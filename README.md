# LangGraph ReAct Agent Template

Github Repo: https://github.com/langchain-ai/react-agent

The core logic, defined in `src/react_agent/graph.py`, demonstrates a flexible ReAct agent that iteratively reasons about user queries and executes actions, showcasing the power of this approach for complex problem-solving tasks.

## What it does

The ReAct agent:

1. Takes a user **query** as input
2. Reasons about the query and decides on an action
3. Executes the chosen action using available tools
4. Observes the result of the action
5. Repeats steps 2-4 until it can provide a final answer

By default, it's set up with a basic set of tools, but can be easily extended with custom tools to suit various use cases.

## Getting Started

1. Create virtual env.

2. Create .env file

3. To install dependencies from pyproject.toml
  "pip install -e ."

4. To run langgraph project
  "langgraph dev --allow-blocking"

Note:
If you run into a "ModuleNotFoundError" or "ImportError", even after installing the local package (pip install -e .), 
it is likely the case that you need to install the CLI into your local virtual environment 
to make the CLI "aware" of the local package. 
You can do this by running python 
-m pip install "langgraph-cli[inmem]" 
and re-activating your virtual environment before running langgraph dev.

Note:
Langgraph will start on the graph declared in the langgraph.json

5. Check on langgraph API documentation on http://localhost:2024/docs

6. Change langgraph.json based on need:
For single agent with tools:
"agent": "./src/react_agent/graph.py:graph"

For multi agent with supervisor:
"agent": "./src/react_agent/multi_agent/supervisor_agent.py:graph"
