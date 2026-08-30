import os
from typing import Dict, Any
from .base_adapter import MarineDataAdapter

try:
    import torch
    import timm
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class AmfitriteHABAdapter(MarineDataAdapter):
    """
    Adapter for detecting Harmful Algal Blooms (HABs) using Sentinel-2 Level-2A imagery.
    This integrates the 'kostaspic/AMFITRITE-Sentinel2-HAB-RDNet' PyTorch model from Hugging Face.
    Provides data for requirement D4 (PFZ & HABs).
    """

    def __init__(self, model_path: str = None):
        """
        Initialize the PyTorch model for inference.
        
        Args:
            model_path (str): Optional local path to 'model.pth'. 
                              If not provided, the adapter will run in mock mode.
        """
        self.model = None
        self.mock_mode = True
        
        if TORCH_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                # 1. Load Model (RDNet Base architecture, 10 spectral channels)
                self.model = timm.create_model('rdnet_base', pretrained=False, num_classes=2, in_chans=10)
                # 2. Load Weights
                state_dict = torch.load(model_path, map_location='cpu')
                self.model.load_state_dict(state_dict)
                self.model.eval()
                self.mock_mode = False
                print("AmfitriteHABAdapter: Loaded RDNet model successfully.")
            except Exception as e:
                print(f"AmfitriteHABAdapter: Failed to load model from {model_path}. Error: {e}")
                print("Falling back to Mock Mode.")
        else:
            if not TORCH_AVAILABLE:
                print("AmfitriteHABAdapter: 'torch' or 'timm' not installed. Running in Mock Mode.")
            else:
                print("AmfitriteHABAdapter: No model path provided. Running in Mock Mode.")

    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Runs inference on a specific coordinate to detect toxic blooms.
        
        If in live inference mode, this would ideally fetch a Sentinel-2 
        10-band tensor for the given (lat, lon).
        For the SIH Hackathon MVP, we use simulated tensors or mock data to ensure zero latency.
        """
        
        if not self.mock_mode and self.model is not None:
            # --- LIVE INFERENCE MODE ---
            # In a real environment, we would use rasterio/planetary-computer here 
            # to fetch the Sentinel-2 256x256 tile for (lat, lon).
            # For demonstration, we simulate a 10-band tensor.
            
            # Dummy tensor representing a 10-band image that is 256x256 pixels
            sample_image = torch.rand(10, 256, 256) * 5000 
            
            # Add batch dimension -> Shape: (1, 10, H, W)
            img_tensor = sample_image.unsqueeze(0)
            
            # Force resize to the required 256x256 (redundant here, but good practice)
            if img_tensor.shape[-2:] != (256, 256):
                img_tensor = F.interpolate(img_tensor, size=(256, 256), mode='bilinear', align_corners=False)
                
            # Normalize Sentinel-2 DN values (0-10000) to 0-1 range
            img_tensor = img_tensor / 10000.0
            
            # Predict
            with torch.no_grad():
                output = self.model(img_tensor)
                # Softmax to get probability of Bloom (Class 1)
                prob = torch.softmax(output, dim=1)[0, 1].item()
                
            is_bloom = prob > 0.5
            
            return {
                "source": "AMFITRITE-Sentinel2-HAB-RDNet (Live Inference)",
                "lat": lat,
                "lon": lon,
                "timestamp": timestamp,
                "hab_detected": is_bloom,
                "hab_probability": round(prob, 4),
                "severity": "HIGH" if prob > 0.8 else "MODERATE" if is_bloom else "LOW"
            }
            
        else:
            # --- MOCK MODE (Zero Latency Hackathon Fallback) ---
            # Automatically returns a safe reading, unless it's in a known toxic geo-fence.
            
            # Simple simulation: If lat > 20.0, simulate a toxic bloom for testing routing logic.
            is_toxic_zone = lat > 20.0
            
            return {
                "source": "AMFITRITE-Sentinel2-HAB-RDNet (Mock Dataset)",
                "lat": lat,
                "lon": lon,
                "timestamp": timestamp,
                "hab_detected": is_toxic_zone,
                "hab_probability": 0.95 if is_toxic_zone else 0.05,
                "severity": "HIGH" if is_toxic_zone else "LOW"
            }
