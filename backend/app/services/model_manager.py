import logging
import gc
from typing import Any, Dict, Callable

logger = logging.getLogger(__name__)

# Try to import torch for CUDA management, but don't fail if not present
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. CUDA management disabled.")

class ModelManager:
    """
    Centralized Model Manager to handle lazy-loading, device placement, and 
    aggressive VRAM cleanup for limited VRAM environments (e.g., RTX 3050 4GB).
    """
    
    def __init__(self):
        self._loaded_models: Dict[str, Any] = {}
        self._model_devices: Dict[str, str] = {}
        
    def _get_cuda_status(self) -> Dict[str, Any]:
        """Returns the current VRAM status."""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return {"available": False, "memory_allocated_mb": 0, "memory_reserved_mb": 0}
        
        return {
            "available": True,
            "device_name": torch.cuda.get_device_name(0),
            "memory_allocated_mb": torch.cuda.memory_allocated(0) / (1024 ** 2),
            "memory_reserved_mb": torch.cuda.memory_reserved(0) / (1024 ** 2),
        }
        
    def get_device(self, preferred_device: str = "cuda") -> str:
        """Determines the safest device to use."""
        if preferred_device == "cuda" and TORCH_AVAILABLE and torch.cuda.is_available():
            return "cuda"
        return "cpu"
        
    def purge_vram(self, aggressive: bool = True):
        """Cleans up CUDA cache to prevent OOM."""
        if not TORCH_AVAILABLE:
            return
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            if aggressive:
                gc.collect()
            logger.info(f"VRAM purged. Status: {self._get_cuda_status()}")
            
    def load_model(self, model_key: str, loader_func: Callable[[str], Any], preferred_device: str = "cuda") -> Any:
        """
        Lazily loads a model if it isn't already loaded.
        Requires a loader_func that accepts a device string ('cuda' or 'cpu').
        """
        if model_key in self._loaded_models:
            logger.debug(f"Model {model_key} already loaded.")
            return self._loaded_models[model_key]
            
        logger.info(f"Loading model {model_key}...")
        device = self.get_device(preferred_device)
        
        try:
            model = loader_func(device)
            self._loaded_models[model_key] = model
            self._model_devices[model_key] = device
            logger.info(f"Successfully loaded {model_key} on {device}")
            
            # Log VRAM status if using CUDA
            if device == "cuda":
                logger.info(f"CUDA Status after loading {model_key}: {self._get_cuda_status()}")
                
            return model
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower() or "oom" in str(e).lower():
                logger.error(f"CUDA OOM while loading {model_key}. Purging VRAM.")
                self.purge_vram()
                raise RuntimeError(f"CUDA OOM while loading {model_key}: {e}")
            else:
                logger.error(f"Failed to load model {model_key}: {e}")
                raise
                
    def unload_model(self, model_key: str):
        """Explicitly unloads a model to free VRAM."""
        if model_key in self._loaded_models:
            logger.info(f"Unloading model {model_key}...")
            del self._loaded_models[model_key]
            del self._model_devices[model_key]
            
            # Run garbage collection and VRAM purge
            gc.collect()
            self.purge_vram()
        else:
            logger.debug(f"Model {model_key} is not loaded. Cannot unload.")
            
    def unload_all(self):
        """Unloads all models to completely clear VRAM."""
        models = list(self._loaded_models.keys())
        for m in models:
            self.unload_model(m)
            
    def get_loaded_models(self) -> Dict[str, str]:
        """Returns a dict of currently loaded models and their devices."""
        return self._model_devices.copy()

# Singleton instance
model_manager = ModelManager()
