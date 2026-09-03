import os
import sys
import json
import urllib.request

API_KEY = "AQ.Ab8RN6LrGcDT4L9RziAwFcyShBMQTvuxaOf9uTObJoTao_UbAA"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def translate_texts(texts, target_lang):
    prompt = f"Translate the following UI strings into {target_lang}. Preserve all formatting, variables like {{variable}}, and HTML/JSX tags. Reply ONLY with a JSON array of strings in the exact same order.\n\n"
    prompt += json.dumps(texts, ensure_ascii=False)
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    req = urllib.request.Request(URL, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(text)
    except Exception as e:
        print(f"Error translating: {e}")
        return texts

import re

def process_po(filepath, lang_name):
    print(f"Processing {filepath} for {lang_name}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find all msgid/msgstr blocks
    blocks = content.split('\n\n')
    
    to_translate = []
    block_indices = []
    
    for i, block in enumerate(blocks):
        if not block.strip() or block.startswith('msgid ""\nmsgstr ""\n"Project-Id-Version:'):
            continue
            
        msgid_match = re.search(r'msgid "(.+?)"', block, flags=re.DOTALL)
        msgstr_match = re.search(r'msgstr "(.*?)"', block, flags=re.DOTALL)
        
        if msgid_match and msgstr_match:
            msgid = msgid_match.group(1).replace('\n"', '')
            msgstr = msgstr_match.group(1).replace('\n"', '')
            
            if not msgstr.strip():
                to_translate.append(msgid)
                block_indices.append(i)
                
    if not to_translate:
        print("Nothing to translate.")
        return
        
    print(f"Found {len(to_translate)} strings to translate.")
    
    # Batch translation (50 strings at a time)
    batch_size = 50
    translated = []
    
    for i in range(0, len(to_translate), batch_size):
        batch = to_translate[i:i+batch_size]
        print(f"Translating batch {i//batch_size + 1}/{len(to_translate)//batch_size + 1}...")
        trans_batch = translate_texts(batch, lang_name)
        
        if len(trans_batch) != len(batch):
            print(f"WARNING: Batch size mismatch! Expected {len(batch)}, got {len(trans_batch)}. Falling back to English.")
            trans_batch = batch
            
        translated.extend(trans_batch)
        
    # Reconstruct blocks
    for idx, msgid, trans in zip(block_indices, to_translate, translated):
        block = blocks[idx]
        # properly escape quotes and newlines if needed, simple approach for now
        trans_clean = trans.replace('"', '\\"')
        new_block = re.sub(r'msgstr ""', f'msgstr "{trans_clean}"', block)
        blocks[idx] = new_block
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(blocks))
    print(f"Done {lang_name}.")

process_po('src/locales/kn/messages.po', 'Kannada')
# process_po('src/locales/hi/messages.po', 'Hindi')
# process_po('src/locales/ta/messages.po', 'Tamil')
# process_po('src/locales/te/messages.po', 'Telugu')
# process_po('src/locales/ml/messages.po', 'Malayalam')

