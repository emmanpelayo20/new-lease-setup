To install dependencies from pyproject.toml
pip install -e .

Note:
If you run into a "ModuleNotFoundError" or "ImportError", even after installing the local package (pip install -e .), 
it is likely the case that you need to install the CLI into your local virtual environment 
to make the CLI "aware" of the local package. 
You can do this by running python 
-m pip install "langgraph-cli[inmem]" 
and re-activating your virtual environment before running langgraph dev.

To run langgraph project
langgraph dev or
langgraph dev --allow-blocking

Note:
Langgraph will start on the graph declared in the langgraph.json