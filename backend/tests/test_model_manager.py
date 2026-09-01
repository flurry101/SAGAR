import pytest
from app.services.model_manager import model_manager

def test_lazy_loading():
    model_manager.unload_all()
    assert len(model_manager.get_loaded_models()) == 0
    
    def dummy_loader(device):
        return "loaded_model"
        
    res = model_manager.load_model("dummy", dummy_loader, "cpu")
    assert res == "loaded_model"
    assert "dummy" in model_manager.get_loaded_models()
    
    model_manager.unload_model("dummy")
    assert "dummy" not in model_manager.get_loaded_models()

def test_oom_purging():
    model_manager.unload_all()
    
    def oom_loader(device):
        raise RuntimeError("CUDA out of memory error")
        
    with pytest.raises(RuntimeError) as exc:
        model_manager.load_model("oom_test", oom_loader, "cuda")
        
    assert "OOM" in str(exc.value)
