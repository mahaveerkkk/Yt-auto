import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv("/home/veer/Desktop/experiment/config/.env")

print("--- Testing API Credentials Presence ---")
print("CHATGPT_ACCESS_TOKEN:", bool(os.getenv("CHATGPT_ACCESS_TOKEN")))
print("CHATGPT_ACCOUNT_ID:", os.getenv("CHATGPT_ACCOUNT_ID"))
print("BING_COOKIE_U:", bool(os.getenv("BING_COOKIE_U")), (os.getenv("BING_COOKIE_U") or "")[:15] + "...")
print("KIE_API_KEY:", bool(os.getenv("KIE_API_KEY")), (os.getenv("KIE_API_KEY") or "")[:8] + "...")
print("GEMINI_API_KEY:", bool(os.getenv("GEMINI_API_KEY")))
print("HF_TOKEN:", bool(os.getenv("HF_TOKEN")))

os.makedirs("/home/veer/Desktop/experiment/output/test_thumbnails", exist_ok=True)

# 1. Test Clean HF FLUX.1
print("\n--- 1. Testing Clean Hugging Face FLUX.1 ---")
hf_token = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {hf_token}"}
prompt = "The Kola Superdeep Borehole drill rig on snowy arctic surface, cross section showing drill shaft 12000 meters deep into subterranean fiery magma mantle, seismic audio spectrogram waterfall display, digital depth gauge '-12,262m', cinematic documentary photography, 16:9, hyperrealistic"

try:
    hf_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    res = requests.post(hf_url, headers=headers, json={"inputs": prompt}, timeout=45)
    print(f"HF FLUX status: {res.status_code}")
    if res.status_code == 200:
        with open("/home/veer/Desktop/experiment/output/test_thumbnails/flux_clean_kola.jpg", "wb") as f:
            f.write(res.content)
        print("✅ Clean FLUX Image saved: output/test_thumbnails/flux_clean_kola.jpg (Size:", len(res.content), "bytes)")
    else:
        print("HF error:", res.text[:200])
except Exception as e:
    print("HF Exception:", e)

# 2. Test Kie.ai API Key
print("\n--- 2. Testing Kie.ai Key ---")
kie_key = os.getenv("KIE_API_KEY")
try:
    # Test Kie.ai models or user balance
    res = requests.get("https://api.kie.ai/api/v1/chat/models", headers={"Authorization": f"Bearer {kie_key}"}, timeout=15)
    print(f"Kie.ai status: {res.status_code}, response: {res.text[:300]}")
except Exception as e:
    print("Kie.ai Exception:", e)

