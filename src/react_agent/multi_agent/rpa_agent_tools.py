"""This module provides example tools for web scraping and search functionality.

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, Optional, cast

from langgraph.runtime import get_runtime

from react_agent.context import Context

from uipath.call_uipath_process import call_uipath_process

import os

def create_invoice_record(ClientName: str, InvoiceDate: str, InvoiceDueDate: str, RateAmount: float, 
                          TotalHours: int, LineItemDescription: str, Services: str, InvoiceNumber: str, 
                             Service: bool, PO_Number: str) -> Optional[dict[str, Any]]:
    """
    Create invoice record by calling Uipath Process via API Call.
    Do not attempt to create the invoice record if is_data_valid is true.
    """

    print("CREATING INVOICE DATA...")

    input_data = {
        "in_ClientName": ClientName,
        "in_InvoiceDate": InvoiceDate,
        "in_InvoiceDueDate": InvoiceDueDate,
        "in_RateAmount": RateAmount,
        "in_TotalHours": TotalHours,
        "in_LineItemDescription": LineItemDescription,
        "In_Services": Services,
        "in_InvoiceNumber": InvoiceNumber,
        "in_Service": Service,
        "in_PO_Number": PO_Number
        }

    try:
        result = call_uipath_process("Invoice.Demo.Processing", input_data)
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def get_product_list(inputs: str) -> Optional[dict[str, Any]]:
    """
    Get list of products by calling Uipath Process via API Call.
    """
    try:
        result = call_uipath_process("ProductInfoAPI")
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

TOOLS: List[Callable[..., Any]] = [create_invoice_record,get_product_list]
