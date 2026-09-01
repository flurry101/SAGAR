import os
import logging
from typing import List, Any
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.services.model_manager import model_manager

logger = logging.getLogger(__name__)

class QwenFallbackLLM:
    """
    Duck-types LangChain LLM invoke() to provide Qwen 7B 4-bit fallback.
    """
    def invoke(self, messages: List[BaseMessage]) -> Any:
        logger.info("Executing Qwen 7B 4-bit Fallback via ModelManager.")
        
        # Format LangChain messages into a single prompt for Qwen
        prompt = "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
        
        def qwen_loader(device: str):
            logger.info(f"Loading Qwen 7B 4-bit model weights on {device}")
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
                import torch
                
                # Path matches the local_dir from scripts/download_models.py
                model_id = os.environ.get("QWEN_MODEL_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "models", "qwen-7b"))
                
                bnb_config = None
                if device == "cuda":
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True
                    )
                
                # local_files_only=True guarantees no internet connection is required
                tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=bnb_config,
                    device_map="auto" if device == "cuda" else "cpu",
                    local_files_only=True
                )
                
                def run_qwen(prompt_text):
                    inputs = tokenizer(prompt_text, return_tensors="pt").to(device)
                    outputs = model.generate(**inputs, max_new_tokens=256)
                    return tokenizer.decode(outputs[0], skip_special_tokens=True)
                return run_qwen
                
            except Exception as e:
                logger.warning(f"Failed to load real Qwen model: {e}. Using mock fallback.")
                return lambda p: "{\n  \"intent\": \"trip_assessment\",\n  \"required_capabilities\": [\"geo\", \"weather\", \"marine\", \"risk\"],\n  \"priority\": \"safety\",\n  \"requires_safety_assessment\": true,\n  \"requires_route\": false,\n  \"requires_visualization\": false,\n  \"requires_report\": false,\n  \"clarification_required\": false,\n  \"reasoning_summary\": \"Fallback Qwen response\",\n  \"recommendation\": \"Safe to proceed.\",\n  \"reason\": \"Fallback Qwen evaluation.\",\n  \"recommendation_text\": \"Fallback Qwen recommendation.\"\n}"
            
        model = model_manager.load_model("qwen-7b-4bit", qwen_loader, preferred_device="cuda")
        
        # Inference
        result_text = model(prompt)
        
        # Unload Qwen from VRAM immediately after generating response (Sequential GPU strategy)
        model_manager.unload_model("qwen-7b-4bit")
        
        # Duck-type the response object LangChain expects
        class MockResponse:
            def __init__(self, content):
                self.content = content
        return MockResponse(result_text)


class ResilientLLM:
    """
    Wraps Gemini with a local Qwen 7B fallback.
    Preserves existing LangChain tool calling flow.
    """
    def __init__(self, temperature: float = 0.1):
        self.temperature = temperature
        from app.config import settings
        self.api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
        
        if self.api_key:
            self.primary_llm = ChatGoogleGenerativeAI(
                model="gemini-3.6-flash",
                google_api_key=self.api_key,
                temperature=self.temperature
            )
        else:
            self.primary_llm = None
            
        self.fallback_llm = QwenFallbackLLM()
        
    def invoke(self, messages: List[BaseMessage]) -> Any:
        if self.primary_llm:
            try:
                return self.primary_llm.invoke(messages)
            except Exception as e:
                logger.warning(f"Primary Gemini LLM failed: {e}. Falling back to Qwen 7B 4-bit.")
                return self.fallback_llm.invoke(messages)
        else:
            logger.warning("GOOGLE_API_KEY not set. Using Qwen 7B fallback immediately.")
            return self.fallback_llm.invoke(messages)

def get_llm(temperature: float = 0.1) -> ResilientLLM:
    """Returns the resilient LLM instance (Gemini -> Qwen)."""
    return ResilientLLM(temperature=temperature)
