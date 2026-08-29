from abc import ABC, abstractmethod
from typing import Dict, Any

class MarineDataAdapter(ABC):
    """
    Abstract Base Class for all ORCA Data Adapters.
    
    The LangGraph orchestrator relies on this unified interface so it doesn't 
    have to care whether data is coming from a live API, a PyTorch model, 
    or a mocked Hugging Face dataset.
    """

    @abstractmethod
    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Fetch data for a specific location and time.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            timestamp (str, optional): ISO 8601 timestamp. Defaults to current time if None.
            
        Returns:
            Dict[str, Any]: A standardized JSON dictionary containing the requested variables.
        """
        pass
