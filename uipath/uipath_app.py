import streamlit as st
import json
from datetime import datetime
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path to import from utils and uipath folders
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from uipath.call_uipath_process import call_uipath_process
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure the utils and uipath modules are available")

# Process definitions (keeping these here for reference)
INTENT_TO_PROCESS = {
    "generate product info": "ProductInfoAPI",
    "extract document text": "PDF.to.Text._RPA_",
    "validate invoice": "Invoice.Contract.Validation._Orchestration_",
    "create invoice": "Invoice.Demo.Processing",
    "process uploaded invoice": "Invoice.Upload.Processing"  # New process for uploaded invoices
}

INTENT_KEYWORDS = {
    "generate product info": ["product", "info", "generate", "product info", "payments", "outstanding"],
    "extract document text": ["extract", "document", "text", "extraction", "parse", "read"],
    "validate invoice": ["validate", "invoice", "check", "contract", "validation", "verify"],
    "create invoice": ["create", "invoice", "generate", "process","upload", "uploaded", "file", "process file", "analyze file"],
}

INTENT_INPUT_ARGUMENTS = {
    "extract document text": {
        "in_StorageBucket": "Contracts",
        "in_FileName": "Contract_Services_Agreement.pdf"
    },
    "generate product info": {},
    "validate invoice": {},
    "create invoice": {
        "in_ClientName": "Microsoft",
        "in_InvoiceDate": "08/20/2025",
        "in_InvoiceDueDate": "09/20/2025",
        "in_RateAmount": 1000.00,
        "in_TotalHours": 10,
        "in_LineItemDescription": "Demo invoice for services rendered",
        "In_Services": "Consulting Services",
        "in_InvoiceNumber": "INV-001234589",
        "in_Service": True,
        "in_PO_Number": "PO-INV-00123"
    }
}

def save_uploaded_file(uploaded_file, upload_dir="uploads"):
    """Save uploaded file to a temporary directory and return the file path."""
    try:
        # Create upload directory if it doesn't exist
        upload_path = Path(upload_dir)
        upload_path.mkdir(exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(uploaded_file.name).suffix
        unique_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = upload_path / unique_filename
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return str(file_path)
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def find_best_intent_match(user_input: str):
    """Find the best matching intent based on user input using keyword matching."""
    user_input_lower = user_input.lower().strip()
    
    # First try exact match
    if user_input_lower in INTENT_TO_PROCESS:
        return user_input_lower
    
    # Then try keyword matching
    best_match = None
    best_score = 0
    
    for intent, keywords in INTENT_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in user_input_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = intent
    
    return best_match if best_score > 0 else None

def execute_uipath_process(user_input: str, uploaded_file_path: str = None):
    """Execute UiPath process based on user input"""
    try:
        # Find matching intent
        matched_intent = find_best_intent_match(user_input)
        
        # If there's an uploaded file but no clear intent, assume it's for processing
        if not matched_intent and uploaded_file_path:
            matched_intent = "process uploaded invoice"
        
        if not matched_intent:
            return {
                "status": "error", 
                "message": f"I couldn't understand your request. Please try one of these:\n" + 
                          "\n".join([f"• {intent}" for intent in INTENT_TO_PROCESS.keys()])
            }
        
        # Get process name and inputs
        process_name = INTENT_TO_PROCESS.get(matched_intent)
        inputs = INTENT_INPUT_ARGUMENTS.get(matched_intent, {}).copy()
        
        # Add file path to inputs if provided
        if uploaded_file_path:
            inputs["in_FilePath"] = uploaded_file_path
            inputs["in_FileName"] = Path(uploaded_file_path).name
        
        # Call the actual UiPath process
        result = call_uipath_process(process_name, inputs)
        
        # Add matched intent to result
        if isinstance(result, dict):
            result["matched_intent"] = matched_intent
            result["process_name"] = process_name
            result["inputs"] = inputs
        
        return result
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error executing process: {str(e)}"
        }

def display_file_attachment(uploaded_file):
    """Display file attachment in chat message"""
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # Show file icon based on type
        if uploaded_file.type == "application/pdf":
            st.markdown("📄")
        elif uploaded_file.type.startswith("image/"):
            st.markdown("🖼️")
        else:
            st.markdown("📁")
    
    with col2:
        st.markdown(f"**{uploaded_file.name}**")
        st.caption(f"Size: {uploaded_file.size:,} bytes | Type: {uploaded_file.type}")
        
        # Show image preview for image files
        if uploaded_file.type.startswith("image/"):
            st.image(uploaded_file, width=200)

def process_message_with_file(prompt, uploaded_file):
    """Process a message that includes both text and file"""
    # Save the uploaded file
    file_path = save_uploaded_file(uploaded_file) if uploaded_file else None
    
    # If no prompt but file uploaded, suggest processing the file
    if not prompt.strip() and uploaded_file:
        prompt = "Please process this uploaded invoice file"
    
    # Add user message to chat history with file info
    user_message = {"role": "user", "content": prompt}
    if uploaded_file:
        user_message["file"] = {
            "name": uploaded_file.name,
            "size": uploaded_file.size,
            "type": uploaded_file.type,
            "path": file_path
        }
    
    st.session_state.messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            st.markdown("📎 **Attached file:**")
            display_file_attachment(uploaded_file)
    
    # Process the request
    with st.chat_message("assistant"):
        with st.spinner("Processing your request..."):
            result = execute_uipath_process(prompt, file_path)
            
            # Format response based on result
            if result.get("status") == "error":
                response = f"❌ **Error:** {result.get('message', 'Unknown error occurred')}"
                st.error(response)
                
            elif result.get("status") == "success":
                matched_intent = result.get("matched_intent", "Unknown")
                process_name = result.get("process_name", "Unknown")
                
                response = f"✅ **Success!** I've executed the **{matched_intent}** process.\n\n"
                response += f"**Process:** {process_name}\n\n"
                
                # Add specific result information
                if "message" in result:
                    response += f"**Result:** {result['message']}\n\n"
                
                # Show execution details if available
                if "execution_time" in result:
                    response += f"**Execution Time:** {result['execution_time']}\n\n"
                
                # Show inputs used
                if "inputs" in result and result["inputs"]:
                    response += "**Parameters used:**\n"
                    for key, value in result["inputs"].items():
                        response += f"• {key}: {value}\n"
                
                st.success("Process completed successfully!")
                st.markdown(response)
                
                # Show detailed result in expander
                with st.expander("🔍 View detailed response"):
                    st.json(result)
                    
            else:
                # Handle unexpected response format
                response = f"🔄 **Process executed.** Here's the response:\n\n{str(result)}"
                st.info(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    st.set_page_config(
        page_title="UiPath Assistant",
        page_icon="🤖",
        layout="centered"
    )
    
    # Header
    st.title("🤖 Invoice Process Automation Hub")
    st.markdown("Tell me what automation task you need help with! You can also attach valid files.")
    
    # Initialize chat history and pending action
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Hello! I'm your UiPath automation assistant. I can help you with:\n\n• **Generate product info** - Get product information and check payments\n• **Extract document text** - Extract text from PDF documents\n• **Validate invoice** - Check invoices against contracts\n• **Create invoice** - Generate new invoices\n• **Process uploaded invoice** - Upload and analyze invoice files\n\nYou can attach invoice files directly in the chat below or use the quick actions. What would you like me to help you with today?"
            }
        ]
    
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display file attachment if present
            if "file" in message:
                st.markdown("📎 **Attached file:**")
                file_info = message["file"]
                col1, col2 = st.columns([1, 4])
                with col1:
                    if file_info["type"] == "application/pdf":
                        st.markdown("📄")
                    elif file_info["type"].startswith("image/"):
                        st.markdown("🖼️")
                    else:
                        st.markdown("📁")
                with col2:
                    st.markdown(f"**{file_info['name']}**")
                    st.caption(f"Size: {file_info['size']:,} bytes | Type: {file_info['type']}")
    
    # Process pending action from quick buttons
    if st.session_state.pending_action:
        action_text = st.session_state.pending_action
        st.session_state.pending_action = None  # Clear the pending action
        
        # Process as a regular message without file
        process_message_with_file(action_text, None)
    
    # File upload and chat input section
    st.markdown("---")
    
    # Create two columns for file upload and send button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "📎 Attach invoice file (optional)",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Upload invoice files in PDF or image format",
            label_visibility="collapsed"
        )
    
    with col2:
        # Send file button (only shown when file is uploaded)
        if uploaded_file:
            if st.button("📤 Send File", use_container_width=True, type="primary"):
                process_message_with_file("", uploaded_file)
                st.rerun()
    
    # Show file preview if uploaded
    if uploaded_file:
        st.info("📎 File ready to send. You can add a message below or click 'Send File' to process it directly.")
        display_file_attachment(uploaded_file)
    
    # Chat input
    if prompt := st.chat_input("Type your message here... (file will be attached automatically if uploaded above)"):
        process_message_with_file(prompt, uploaded_file)
        st.rerun()
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("**Quick Actions:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Product Info", use_container_width=True):
            st.session_state.pending_action = "generate product info"
            st.rerun()
    
    with col2:
        if st.button("📄 Extract Text", use_container_width=True):
            st.session_state.pending_action = "extract document text"
            st.rerun()
    
    with col3:
        if st.button("✅ Validate Invoice", use_container_width=True):
            st.session_state.pending_action = "validate invoice"
            st.rerun()
    
    with col4:
        if st.button("📝 Create Invoice", use_container_width=True):
            st.session_state.pending_action = "create invoice"
            st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.messages = [st.session_state.messages[0]]  # Keep only the initial message
        st.rerun()

if __name__ == "__main__":
    main()