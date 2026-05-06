import streamlit as st
from Milestone_3_agent import graph, SystemMessage, HumanMessage, system_prompt
from datetime import datetime


# Title map for source display
title_map = {
    # USPTO/Trademark Documents
    "TM-Registration-Toolkit.pdf": "USPTO Trademark Registration Toolkit",
    "TM-Prefiling-Checklist-flyer.pdf": "USPTO Pre-filing Checklist",
    "tmlaw.pdf": "Trademark Manual of Examining Procedure",
    
    # Amazon Brand Registry & Protection
    "brand registry guide.pdf": "Amazon Brand Registry Application Guide",
    "2024 Brand Protection Report Trustworthy Shopping at Amazon.pdf": "Amazon Brand Protection Report 2024",
    
    # Amazon Business Reports
    "small business report.pdf": "Amazon Small Business Empowerment Report 2025",
    "State of Amazon Seller Operations_2026.pdf": "State of Amazon Seller Operations 2026",
    
    # E-commerce Resources
    "COMPARATIVE STUDY OF E-COMMERCE PLATFORMS.pdf": "Comparative Study of E-Commerce Platforms",
    "The Ultimate Guide to Amazon Keyword Research.pdf": "The Ultimate Guide to Amazon Keyword Research",
    "2025 Q4 US Benchmark Report.pdf": "Q4 2025 Retail Media Benchmark Report",
    "Amazon FBA vs FBM; a strategic approach to determine which method.pdf": "Amazon FBA vs FBM: A Strategic Approach to Determine Which Method"
}

# CSS styling
st.markdown("""
<style>
    /* Main title styling */
    .main h1 {
        color: #146eb4;
        font-size: 3rem;
        font-weight: bold;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #232f3e;
        color: #f2f2f2;
    }

    /* Sidebar text */
    [data-testid="stSidebar"] * {
        color: #f2f2f2;
    }

    /* App background */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #f2f2f2;
        border-radius: 10px;
        padding: 15px;
        color: #000000;
    }
    
    /* ALL buttons */
    .stButton > button,
    button[kind="secondary"],
    button[kind="primary"] {
        background-color: #ff9900 !important;
        color: #000000 !important;
        border-radius: 20px;
        padding: 10px 20px;
        border: none;
    }

    /* Hover state */
    .stButton > button:hover,
    button[kind="secondary"]:hover,
    button[kind="primary"]:hover {
        background-color: #e68a00 !important;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="E-commerce Research Advisor",
    layout="wide")

st.title("E-commerce Research Advisor")
st.markdown("*Evidence-backed marketplace strategy insights*")

# Sidebar
with st.sidebar:
    # Clear chat at the TOP
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.header("Example Questions")
    st.caption("Click any question to start creating your perfect ecommerce business strategy!")
    
    examples = [
        "What are the benefits of FBA vs FBM?",
        "Compare Amazon and Etsy for handmade products",
        "What are the steps for Amazon Brand Registry?",
        "What are current Amazon storage fees?",
        "How should I optimize product listings for SEO?"
    ]
    
    for example in examples:
        if st.button(example, key=example):
            st.session_state.current_query = example
    
    st.divider()
    
    # Export chat button
    if "messages" in st.session_state and st.session_state.messages:
        chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button(
            label="Export Chat",
            data=chat_text,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # Export sources button
        import re
        all_sources = set()
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                sources = re.findall(r'([A-Za-z0-9_\s\-\.]+\.pdf)', message["content"])
                all_sources.update(sources)
        
        if all_sources:
           # Apply title map for export
            sources_list = [title_map.get(s, s) for s in sorted(all_sources)]
            sources_text = "SOURCES USED IN THIS CONVERSATION:\n\n" + "\n".join(f"- {s}" for s in sources_list)
            st.download_button(
                label="Export Sources",
                data=sources_text,
                file_name=f"sources_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
    st.divider()
    
    # Recent queries
    if "messages" in st.session_state and st.session_state.messages:
        st.header("Recent Queries")
        recent = [m["content"][:50] for m in st.session_state.messages if m["role"] == "user"][-5:]
        for q in recent:
            st.caption(f"• {q}...")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Two column layout
col1, col2 = st.columns([2, 1])

with col1:
    tab1, tab2 = st.tabs(["Chat", "Sources"])
    
    with tab1:
        # Container for scrollable chat history
        chat_container = st.container(height=500)
        
        with chat_container:
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "tools" in message:
                        st.caption(f"Used: {', '.join(message['tools'])}")
    
    with tab2:
        st.subheader("All Sources Referenced")
        
        if st.session_state.messages:
            import re
            all_pdf_sources = {}
            all_web_sources = {}
            
            for idx, message in enumerate(st.session_state.messages):
                if message["role"] == "assistant":
                    content = message["content"]
                    
                    # Extract PDFs
                    pdf_sources = re.findall(r'([A-Za-z0-9_\s\-\.]+\.pdf)', content)
                    for source in pdf_sources:
                        if source not in all_pdf_sources:
                            all_pdf_sources[source] = []
                        if idx > 0:
                            query_msg = st.session_state.messages[idx-1]
                            all_pdf_sources[source].append(query_msg["content"][:50])
                    
                    url_pattern = r'(?:Sources?:|URL:)\s*([^\n]+)'
                    source_lines = re.findall(url_pattern, content, re.IGNORECASE)
                    
                    all_url_sources = []
                    for line in source_lines:
                        # Split by commas and clean up
                        domains = [d.strip() for d in line.split(',')]
                        for domain in domains:
                            # Add https:// if not present
                            if not domain.startswith('http'):
                                domain = f"https://{domain}"
                            all_url_sources.append(domain)
                    
                    for source in all_url_sources:
                        if source not in all_web_sources:
                            all_web_sources[source] = []
                        if idx > 0:
                            query_msg = st.session_state.messages[idx-1]
                            all_web_sources[source].append(query_msg["content"][:50])
            
            # Display PDFs
            if all_pdf_sources:
                st.subheader("Document Sources")
                for source, queries in all_pdf_sources.items():
                    display_title = title_map.get(source, source)
                    with st.expander(f"{display_title}"):
                        st.write("**Used in queries:**")
                        for q in queries:
                            st.caption(f"• {q}...")
            
            # Display Web Sources
            if all_web_sources:
                st.subheader("Web Sources")
                for source, queries in all_web_sources.items():
                    with st.expander(f"{source[:60]}..."):
                        st.write("**Used in queries:**")
                        for q in queries:
                            st.caption(f"• {q}...")
            
            if not all_pdf_sources and not all_web_sources:
                st.info("No sources cited yet.")
        else:
            st.info("Ask a question to manage your ecommerce business!")
    
    # CHAT INPUT VISIBLE AT BOTTOM
    if "current_query" in st.session_state:
        query = st.session_state.current_query
        del st.session_state.current_query
    else:
        query = st.chat_input("Ask a question...")
    
    # Process query
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Prepare messages
        messages = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"{query}\n\nIMPORTANT: End your response with:\nSources: filename1.pdf, filename2.pdf, url1.com, url2.com")
            ]
        }
        
        # Run agent
        with st.spinner("Researching..."):
            try:
                state = graph.invoke(
                    messages,
                    {"recursion_limit": 50, "max_execution_time": 60}
                )
                answer = state["messages"][-1].content
        
        # Extract sources from tool results directly
                pdf_sources_found = []
                web_sources_found = []
                for msg in state["messages"]:
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        # Extract PDFs from tool results
                        pdfs = re.findall(r'([A-Za-z0-9_\s\-\.]+\.pdf)', msg.content)
                        pdf_sources_found.extend(pdfs)
                        # Extract URLs from tool results
                        urls = re.findall(r'(?:URL:\s*)?(https?://[^\s\n]+)', msg.content)
                        web_sources_found.extend(urls)
        
                # Append sources to answer if found
                if pdf_sources_found or web_sources_found:
                    answer += "\n\nSources: " + ", ".join(set(pdf_sources_found)) + (", " if pdf_sources_found and web_sources_found else "") + ", ".join(set(web_sources_found))
              
                # Detect tools used
                tools_used = []
                for msg in state["messages"]:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tools_used.append(tool_call['name'])
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.stop()
        
        # Store message with tools info
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer,
            "tools": list(set(tools_used))
        })
        st.rerun()

with col2:
    st.subheader("Quick Stats")
    
    if st.session_state.messages:
        total_queries = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.metric("Total Queries", total_queries)
        
        corpus_count = sum(1 for m in st.session_state.messages if m.get("tools") and "search_corpus" in m["tools"])
        web_count = sum(1 for m in st.session_state.messages if m.get("tools") and "search_web" in m["tools"])
        
        st.metric("Corpus Searches", corpus_count)
        st.metric("Web Searches", web_count)
    
    st.divider()
    
    st.subheader("About")
    st.info("""
    **Sources Include:**
    - USPTO Trademark Docs
    - Amazon Seller Reports
    - E-commerce Platform Studies
    - Current Web Data
    """)

