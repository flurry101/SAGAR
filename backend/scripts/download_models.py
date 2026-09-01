#!/usr/bin/env python3
import os
import argparse
import logging
import gc

# Disable symlink warnings and fallback safely on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("Please install huggingface_hub: pip install huggingface_hub")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The strict 5 models required for the offline fallback architecture
MODELS = {
    "indic-conformer": "ai4bharat/indic-conformer-600m-multilingual",
    "indictrans2-en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
    "indictrans2-indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
    "indicf5": "ai4bharat/IndicF5",
    "qwen-7b": "Qwen/Qwen2.5-7B-Instruct"
}

def force_vram_clear():
    """Forces aggressive garbage collection and CUDA cache clearing."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass

def main():
    parser = argparse.ArgumentParser(description="Download ORCA offline fallback models locally.")
    parser.add_argument("--token", type=str, default=os.environ.get("HF_TOKEN"), 
                        help="Hugging Face access token for gated AI4Bharat models.")
    args = parser.parse_args()

    if not args.token:
        logger.warning("No Hugging Face token provided! AI4Bharat models are gated and require authentication.")
        logger.warning("Please pass --token YOUR_TOKEN or set HF_TOKEN environment variable.")

    logger.info("Starting model download for ORCA Offline Voice Architecture...")
    logger.info("Internet ON: Fetching models to local HuggingFace cache.")
    
    base_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(base_dir, exist_ok=True)
    
    failed_downloads = []
    
    # STEP 1: DOWNLOAD ALL 5 MODELS
    for key, model_id in MODELS.items():
        logger.info(f"Downloading {key}...")
        try:
            local_path = os.path.join(base_dir, key)
            downloaded_path = snapshot_download(
                repo_id=model_id, 
                local_dir=local_path,
                local_dir_use_symlinks=False,
                token=args.token,
                resume_download=True
            )
            logger.info(f"✓ {key} downloaded")
        except Exception as e:
            logger.error(f"Failed to download {model_id}: {e}")
            failed_downloads.append(model_id)

    if failed_downloads:
        logger.error(f"❌ OFFLINE READY = false (Downloads failed: {failed_downloads})")
        logger.error("Please ensure your token is valid and you have accepted the model terms on Hugging Face.")
        exit(1)

    print("\nTesting sequential loading...\n")
    
    # STEP 2 & 3: VERIFY AND LOAD EACH MODEL SEQUENTIALLY
    try:
        from transformers import (
            AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
            AutoModelForSpeechSeq2Seq, AutoProcessor,
            AutoModelForSeq2SeqLM, AutoModelForTextToWaveform
        )
        import torch
        
        use_cuda = torch.cuda.is_available()
        device_str = "cuda" if use_cuda else "cpu"
        
        # 1. IndicConformer
        logger.info(f"Testing IndicConformer load on {device_str}...")
        force_vram_clear()
        conformer_path = os.path.join(base_dir, "indic-conformer")
        proc1 = AutoProcessor.from_pretrained(conformer_path, local_files_only=True)
        mod1 = AutoModelForSpeechSeq2Seq.from_pretrained(conformer_path, local_files_only=True)
        if use_cuda: mod1 = mod1.to("cuda")
        del mod1, proc1
        logger.info("✓ IndicConformer load successful")
        
        # 2. IndicTrans2 EN-Indic
        logger.info(f"Testing IndicTrans2 EN-Indic load on {device_str}...")
        force_vram_clear()
        t2_en_in_path = os.path.join(base_dir, "indictrans2-en-indic")
        tok2 = AutoTokenizer.from_pretrained(t2_en_in_path, local_files_only=True)
        mod2 = AutoModelForSeq2SeqLM.from_pretrained(t2_en_in_path, local_files_only=True)
        if use_cuda: mod2 = mod2.to("cuda")
        del mod2, tok2
        logger.info("✓ IndicTrans2 EN→Indic load successful")
        
        # 3. IndicTrans2 Indic-EN
        logger.info(f"Testing IndicTrans2 Indic-EN load on {device_str}...")
        force_vram_clear()
        t2_in_en_path = os.path.join(base_dir, "indictrans2-indic-en")
        tok3 = AutoTokenizer.from_pretrained(t2_in_en_path, local_files_only=True)
        mod3 = AutoModelForSeq2SeqLM.from_pretrained(t2_in_en_path, local_files_only=True)
        if use_cuda: mod3 = mod3.to("cuda")
        del mod3, tok3
        logger.info("✓ IndicTrans2 Indic→EN load successful")
        
        # 4. IndicF5
        logger.info(f"Testing IndicF5 load on {device_str}...")
        force_vram_clear()
        f5_path = os.path.join(base_dir, "indicf5")
        tok4 = AutoTokenizer.from_pretrained(f5_path, local_files_only=True)
        mod4 = AutoModelForTextToWaveform.from_pretrained(f5_path, local_files_only=True)
        if use_cuda: mod4 = mod4.to("cuda")
        del mod4, tok4
        logger.info("✓ IndicF5 load successful")
        
        # 5. Qwen 7B 4-bit
        logger.info(f"Testing Qwen 7B 4-bit load on {device_str}...")
        force_vram_clear()
        qwen_path = os.path.join(base_dir, "qwen-7b")
        tok5 = AutoTokenizer.from_pretrained(qwen_path, local_files_only=True)
        if use_cuda:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
            mod5 = AutoModelForCausalLM.from_pretrained(
                qwen_path,
                quantization_config=bnb_config,
                device_map="auto",
                local_files_only=True
            )
        else:
            mod5 = AutoModelForCausalLM.from_pretrained(qwen_path, local_files_only=True)
        del mod5, tok5
        logger.info("✓ Qwen 7B 4-bit load successful")
        
        force_vram_clear()
            
    except Exception as e:
        logger.error(f"❌ OFFLINE READY = false. Verification failed during offline load test: {e}")
        exit(1)

    print("\n================================")
    print("✅ OFFLINE READY = true")
    print("================================\n")
    logger.info("You can now safely turn your Wi-Fi off. ORCA is fully autonomous!")

if __name__ == "__main__":
    main()
