"""This module provides example tools for web scraping and search functionality.

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from datetime import datetime, timezone
from typing import Any, Callable, List, Optional, cast
from typing_extensions import Annotated
from dataclasses import asdict

from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command, Send
from langgraph.runtime import get_runtime
from langgraph.graph import MessagesState

from react_agent.multi_agent_overhaul.state import State, InputState

from uipath.call_uipath_process import run_uipath_process_sync

import os
import requests

#handoff tool for supervisor
def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Transfer to {agent_name}"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[State, InjectedState], 
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(  
            goto=agent_name,  
            update={"messages": state.messages + [tool_message]},  
            graph=Command.PARENT,  
        )
    return handoff_tool

# Handoffs
assign_to_extraction_agent = create_handoff_tool(
    agent_name="extraction_agent",
    description="Assign task to extraction agent.",
)

assign_to_rpa_agent = create_handoff_tool(
    agent_name="rpa_agent",
    description="Assign task to rpa agent.",
)

def search_knowledge_base(
    query: str
) -> str:
    """
    Get document contents on user query coming from vector database.
    """

    print("SEARCHING KNOWLEDGE BASE...")

    api_endpoint = os.getenv("DOC_API_ENDPOINT_SEARCH")

    try:
        payload = {
            "query": query,
            "max_results": 3,
            "min_similarity_threshold": 0.5,
            "source_filter": "",
            "enable_query_enhancement": False,
            "enable_context": True,
            "full_content": False
        }
 
        headers = {
            "Content-Type": "application/json",
        }
 
        response = requests.post(api_endpoint, json=payload, headers=headers)
 
        if response.status_code == 200:
            result = response.json()  # Fixed: Added parentheses
            return result  
               
        else:
            # Get error details from response if available
            try:
                error_detail = response.json().get('detail', response.text)
            except:
                error_detail = response.text
            return f"Failed to retrieve document. API returned status code: {response.status_code}. Details: {error_detail}"
 
    except requests.exceptions.RequestException as e:
        return f"Network error retrieving document from vector database: {str(e)}"
    except Exception as e:
        return f"Error retrieving document from vector database: {str(e)}"

def create_authority_to_trade_form(PropertyName: str, TenantLegalEntity: str, ShopNumber: str, SAPProjectNumber: str, 
                          HandoverDate: str, FitoutDuration: str, OpenForTradeDate: str, RentStartDate: str, 
                          SignedLeaseReceived: str) -> Optional[dict[str, Any]]:
    """
    Create authority to trade form by calling Uipath Process.
    """

    print("CREATING AUTHORITY TO TRADE FORM...")

    input_data = {
        "in_PropertyName": PropertyName,
        "in_TenantLegalEntity": TenantLegalEntity,
        "in_ShopNumber": ShopNumber,
        "in_SAPProjectNumber": SAPProjectNumber,
        "in_HandoverDaters": HandoverDate,
        "in_FitoutDuration": FitoutDuration,
        "in_OpenForTradeDate": OpenForTradeDate,
        "in_RentStartDate": RentStartDate,
        "in_SignedLeaseReceived": SignedLeaseReceived
        }

    try:
        result = run_uipath_process_sync("Create.Authority.to.Trade.Form", input_data)
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def update_workflow_status(request_id: str, step_id: str, status: str = "completed") -> str:

    print("UPDATING WORKFLOW STATUS...")

    api_endpoint = f"http://localhost:3002/api/lease-requests/{request_id}/workflow-steps/{step_id}"

    try:
        update_data = {
            "status": status,
            "completedAt": datetime.now(timezone.utc).isoformat(),
        }
 
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
 
        response = requests.patch(api_endpoint, json=update_data, headers=headers)

        if response.status_code == 200:
            result = response.json()  # Fixed: Added parentheses
            return result
          
        else:
            # Get error details from response if available
            try:
                error_detail = response.json().get('detail', response.text)
            except:
                error_detail = response.text
            return f"Failed to retrieve document. API returned status code: {response.status_code}. Details: {error_detail}"
 
    except requests.exceptions.RequestException as e:
        return f"Network error retrieving document from vector database: {str(e)}"
    except Exception as e:
        return f"Error retrieving document from vector database: {str(e)}"

SUPERVISOR_AGENT_TOOLS: List[Callable[..., Any]] = [assign_to_extraction_agent,assign_to_rpa_agent]

LEASE_PROCESSOR_AGENT_TOOLS: List[Callable[..., Any]] = [search_knowledge_base, create_authority_to_trade_form]
    
EXTRACTION_AGENT_TOOLS: List[Callable[..., Any]] = [search_knowledge_base]

RPA_AGENT_TOOLS: List[Callable[..., Any]] = [create_authority_to_trade_form]
