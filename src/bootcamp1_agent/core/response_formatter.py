"""Complete response formatting, vendored from Bootcamp 1 - provided, complete infrastructure. Do not edit."""
from typing import List, Dict, Any
from src.bootcamp1_agent.core.agent_state import AgentState
from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager

class ResponseFormatter:
    def __init__(self, llm: LLMClient, prompt_mgr: PromptManager):
        self.llm = llm
        self.prompt_mgr = prompt_mgr
    
    def format_grounded_response(self, state: AgentState) -> str:
        """Generate response with citations."""
        prompt = self.prompt_mgr.get_prompt("response_generation_prompt")
        
        # Prepare knowledge context
        knowledge = "\n\n".join([
            f"[{i+1}] {doc['content'][:500]}... (Source: {doc['source']})"
            for i, doc in enumerate(state["retrieved_docs"][:3])
        ])
        
        # Generate response
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user_template"].format(
                query=state["query"],
                knowledge=knowledge if knowledge else "No specific documents retrieved."
            )}
        ]
        
        response = self.llm.generate(messages)
        
        # Add citations
        citations = self.extract_citations(state["retrieved_docs"])
        if citations:
            response += f"\n\n**Sources:** {', '.join(citations)}"
        
        return response
    
    def extract_citations(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Extract citations from documents."""
        return [doc.get("source", "Unknown") for doc in documents[:5]]
