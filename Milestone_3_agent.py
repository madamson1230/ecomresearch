import os
from langchain.agents import create_agent
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from qdrant_client import QdrantClient
from tavily import TavilyClient
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = "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"


#APIs
qdrant_url = os.getenv("QDRANT URL", "https://5b37e475-711f-410b-9a99-74f818049901.us-east-1-1.aws.cloud.qdrant.io")
qdrant_key = os.getenv("QDRANT API Key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZTM3MmQ3YzctNTBiZi00MTNjLWIxOGEtM2FhZmQ0MGJiNTNjIn0.0TcVmsjuSaVyCfi9eQX2aZ3khgyITEwpt7egVyowrLw")
openai_key = os.getenv("OpenAI_API Key", "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")
tav_key = os.getenv("Tavily API Key", "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")  # Get from https://tavily.com

qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
embed = OpenAIEmbeddings(model="text-embedding-3-small")
tav_client = TavilyClient(api_key=tav_key) if tav_key else None

@tool
def search_corpus(query: str, top_k: int = 40):
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
    "1) For ANY question, FIRST call search_corpus to find information,\n"
    "2) If search_corpus does not have the answer, OR if asked about current prices/recent news (2024-2025), call search_web,\n"
    "3) Answer in plain paragraphs without numbered lists or bold text,\n"
    "4) When citing sources, use the actual document filenames at the end.\n"
    "5) Important: Always search before answering.\n\n"

    "Answering guidance:\n"
    "For factual or definition-based questions, provide a clear and direct explanation based on the retrieved information.\n\n"

    "For strategic or decision-based questions, do not give only a general explanation. First identify the decision context (such as product type, budget, platform, or scale). Then compare relevant options using key factors like cost, competition, logistics, customer fit, and scalability. Clearly explain trade-offs between options and end with a direct recommendation when appropriate. Keep the answer focused on the decision being made and prioritize actionable guidance over broad background information."
) #I opted to create a system prompt after I really struggled to get the agent to call my corpus. The ssytem prompt will be used in content for messages

chat = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=openai_key
).bind_tools([search_corpus, search_web], tool_choice="required")

# Create the agent
graph = create_agent(
    model=chat,
    tools=[search_corpus, search_web]
)
