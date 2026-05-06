import os
from langgraph.prebuilt import create_react_agent
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from qdrant_client import QdrantClient
from tavily import TavilyClient
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()


#APIs
qdrant_url = os.getenv("QDRANT_URL")
qdrant_key = os.getenv("QDRANT_API_Key")
openai_key = os.getenv("OPENAI_API_KEY")
tav_key = os.getenv("TAVILY_API_KEY") 

qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
embed = OpenAIEmbeddings(model="text-embedding-3-small")
tav_client = TavilyClient(api_key=tav_key) if tav_key else None

@tool
def search_corpus(query: str, top_k: int = 10):
    """Search e-commerce research documents for established practices, policies, and strategies."""
    
    # Map filenames to document titles
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
    
    try:
        # embedding for the query
        query_vector = embed.embed_query(query)
        
        # Search Qdrant
        output = qdrant_client.query_points(
            collection_name="ecommerce_research",
            query=query_vector,
            limit=top_k
        ).points #lots of errors had to debug using chat to figure out to add the word points

        
        if not output:
            return "No applicable information found in database."
        
        # Format results with sources
        output_format = []
        for result in output:
            text = result.payload.get("text", "")
            filename = result.payload.get("source", "Unknown Source")
            
            # Keep filename as-is so Streamlit regex can extract .pdf
            output_format.append(
                f"[Source: {filename}]\n {text}\n"
            )
        
        return "\n \n".join(output_format)
    
    except Exception as e:
        return f"Error searching research corpus: {str(e)}"


@tool
def search_web(query: str, max_results: int = 5):
    """Search the web for current industry data and pricing."""
    try:
        response = tav_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results
        )
        
        if not response.get("results"):
            return "No web results."
        
        output_format = []
        for result in response["results"]:  # Removed idx since not using it
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "No content available")
            
            output_format.append(
                f"[Web Source: {title}]\n"  # Removed number
                f"URL: {url}\n"
                f"Content: {content}\n"
            )
        
        return "\n \n".join(output_format)  # Fixed variable name (was formatted_results)
    
    except Exception as e:
        return f"Error performing web search: {str(e)}"

system_prompt = (
    "You are a research assistant.\n"
    "Rules:\n"
    "You are a research assistant.\n"
    "1) ALWAYS call search_corpus first.\n"
    "2) Call search_web only if you need current 2024-2026 data.\n"
    "3) Answer in plain paragraphs.\n"
    "4) CRITICAL: At the very end of your answer, add a new line that says 'Sources: ' and then list EVERY filename.pdf you saw in [Source: filename.pdf] tags from the tool results.\n"
    "5) Stop after answering - don't call tools repeatedly."
    
    "For factual questions, provide a clear explanation based on retrieved information.\n"
    "For strategic questions, identify the decision context, compare options using key factors, explain trade-offs, and provide a recommendation."
) #I opted to create a system prompt after I really struggled to get the agent to call my corpus. The ssytem prompt will be used in content for messages

chat = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=openai_key,
    timeout=60
).bind_tools([search_corpus, search_web])

# Create the agent
graph = create_react_agent(
    model=chat,
    tools=[search_corpus, search_web]
)
