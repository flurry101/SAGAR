import os
import re
import sys
import time
import json
import urllib.request
from deep_translator import GoogleTranslator

# Try to load .env file manually so we don't need to pip install python-dotenv
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, val = line.strip().split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

LOCALE_MAP = {
    'hi': 'hi', 'kn': 'kn', 'ta': 'ta', 'te': 'te', 'ml': 'ml',
    'mr': 'mr', 'gu': 'gu', 'bn': 'bn', 'or': 'or', 'ur': 'ur',
    'pa': 'pa', 'as': 'as', 'ne': 'ne', 'sd': 'sd', 'sa': 'sa',
}

def translate_batch_gemini(texts, lang_code, lang_name):
    """Batch translates strings using Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"Translate the following UI strings into {lang_name} ({lang_code}) for a marine safety app. Preserve all formatting, technical terms (like PFZ), variables like {{variable}}, and HTML/JSX tags. Reply ONLY with a valid JSON array of strings in the exact same order.\n\n"
    prompt += json.dumps(texts, ensure_ascii=False)
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            translated = json.loads(text_response)
            if len(translated) == len(texts):
                return translated
            else:
                print(f"Gemini returned mismatched array length. Expected {len(texts)}, got {len(translated)}.")
                return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None

def process_po_file(filepath, lang_code):
    if lang_code not in LOCALE_MAP:
        print(f"Skipping {lang_code}, no mapping available.")
        return

    print(f"\nProcessing {filepath} for language: {lang_code}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    blocks = content.split('\n\n')
    
    # 1. Identify which strings need translation
    to_translate_indices = []
    texts_to_translate = []
    
    for i, block in enumerate(blocks):
        if not block.strip() or block.startswith('msgid ""\nmsgstr ""\n"Project-Id-Version:'):
            continue
            
        msgid_match = re.search(r'msgid "(.*?)"', block, flags=re.DOTALL)
        msgstr_match = re.search(r'msgstr "(.*?)"', block, flags=re.DOTALL)
        
        if msgid_match and msgstr_match:
            msgid = msgid_match.group(1).replace('\n"', '')
            msgstr = msgstr_match.group(1).replace('\n"', '')
            
            # Needs translation if empty or same as English
            if (not msgstr.strip() or msgstr.strip() == msgid.strip()) and msgid.strip():
                to_translate_indices.append(i)
                texts_to_translate.append(msgid.replace('\\"', '"'))

    if not texts_to_translate:
        print(f"No missing translations found for {lang_code}.")
        return

    print(f"Found {len(texts_to_translate)} strings to translate.")
    
    # 2. Attempt Gemini Bulk Translation if Key Exists
    translated_texts = []
    gemini_success = False
    
    if GEMINI_API_KEY:
        print("GEMINI_API_KEY found. Attempting bulk translation...")
        batch_size = 50
        gemini_success = True
        
        for i in range(0, len(texts_to_translate), batch_size):
            batch = texts_to_translate[i:i+batch_size]
            print(f"Translating batch {i//batch_size + 1}...")
            
            batch_result = translate_batch_gemini(batch, lang_code, lang_code)
            if batch_result:
                translated_texts.extend(batch_result)
            else:
                print("Gemini bulk translation failed for a batch. Falling back to scraper for remaining...")
                gemini_success = False
                break
                
        if gemini_success and len(translated_texts) == len(texts_to_translate):
            # Apply Gemini translations
            for idx, trans_text in zip(to_translate_indices, translated_texts):
                clean_trans = trans_text.replace('"', '\\"')
                blocks[idx] = re.sub(r'msgstr ""|msgstr ".*?"', f'msgstr "{clean_trans}"', blocks[idx])
            print(f"✅ Successfully batch-translated {len(texts_to_translate)} strings using Gemini.")
        else:
            gemini_success = False

    # 3. Fallback to deep-translator scraper
    if not gemini_success:
        print("Using deep-translator fallback (1-by-1)...")
        translator = GoogleTranslator(source='en', target=LOCALE_MAP[lang_code])
        translated_count = 0
        
        for idx, original_text in zip(to_translate_indices, texts_to_translate):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    translated_text = translator.translate(original_text)
                    time.sleep(1.0)
                    
                    if translated_text:
                        clean_trans = translated_text.replace('"', '\\"')
                        blocks[idx] = re.sub(r'msgstr ""|msgstr ".*?"', f'msgstr "{clean_trans}"', blocks[idx])
                        translated_count += 1
                        print(f"Translated: '{original_text[:30]}...' -> '{translated_text[:30]}...'")
                    break
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3
                        print(f"Rate limited. Retrying in {wait_time}s... ({e})")
                        time.sleep(wait_time)
                        translator = GoogleTranslator(source='en', target=LOCALE_MAP[lang_code])
                    else:
                        print(f"Failed to translate '{original_text}' after retries.")
                        
        print(f"✅ Successfully translated {translated_count} strings using fallback scraper.")

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(blocks))

if __name__ == "__main__":
    locales_dir = os.path.join(os.path.dirname(__file__), 'src', 'locales')
    
    if len(sys.argv) > 1:
        lang = sys.argv[1]
        process_po_file(os.path.join(locales_dir, lang, 'messages.po'), lang)
    else:
        for lang in os.listdir(locales_dir):
            if os.path.isdir(os.path.join(locales_dir, lang)) and lang != 'en':
                process_po_file(os.path.join(locales_dir, lang, 'messages.po'), lang)
