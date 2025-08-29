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
    
def validate_invoice_data(ClientName: str = "", InvoiceDate: str = "", InvoiceDueDate: str = "", RateAmount: float = 0.00, 
                          TotalHours: int = 0, LineItemDescription: str = "", Services: str = "", InvoiceNumber: str = "", 
                             Service: bool = None, PO_Number: str = "") -> Optional[dict[str, Any]]:
    """
    Validate invoice record by calling Uipath Process via API Call.
    If there are missing data, you will not proceed to any further steps.
    Identify what are the missing or valid data, so users can try correcting or providing it.
    """
    print("VALIDATING INVOICE DATA...")


    try:
        if (ClientName and InvoiceDate and InvoiceDueDate and RateAmount > 0 and TotalHours > 0 and 
            LineItemDescription and Services and InvoiceNumber and Service is not None and PO_Number):
            is_data_valid = True
        else:
            is_data_valid = False  

        return {
            "is_data_valid": is_data_valid
        }
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

TOOLS: List[Callable[..., Any]] = [create_invoice_record,validate_invoice_data]
