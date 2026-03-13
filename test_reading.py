import requests
import json
import re

# 1. Get Chart Context
print("Step 1: Calling /api/chart...")
url_chart = "http://localhost:8000/api/chart"
payload_chart = {
    "dob": "1955-02-24",
    "tob": "19:15:00",
    "lat": 37.7749,
    "lon": -122.4194,
    "place": "San Francisco"
}
headers = {'Content-Type': 'application/json'}

res_chart = requests.post(url_chart, json=payload_chart, headers=headers)
if res_chart.status_code != 200:
    print(f"Error Chart API: {res_chart.status_code}")
    print(res_chart.text)
    exit()

chart_data = res_chart.json()
chart_ctx = chart_data.get("chart_context", "")
print("Chart context received.")

# 2. Call Chat (This is what the frontend does automatically)
print("\nStep 2: Calling /api/chat...")
url_chat = "http://localhost:8000/api/chat"
payload_chat = {
    "messages": [
        {"role": "user", "content": "Generate my full chart reading exactly in the requested format. Follow the system instructions precisely."}
    ],
    "chart_context": chart_ctx
}

res_chat = requests.post(url_chat, json=payload_chat, headers=headers)
if res_chat.status_code != 200:
    print(f"Error Chat API: {res_chat.status_code}")
    print(res_chat.text)
    exit()

chat_data_res = res_chat.json()
raw_ai = chat_data_res.get("choices", [{}])[0].get("message", {}).get("content", "")

print("\n--- RAW AI RESPONSE ---")
print(raw_ai)

print("\n--- JSON PARSING ATTEMPT (Same as JS) ---")
try:
    clean_json_str = raw_ai.replace("```json", "").replace("```", "").strip()
    # Check if there's any text before the first '{'
    if not clean_json_str.startswith("{"):
        first_brace = clean_json_str.find("{")
        if first_brace != -1:
             clean_json_str = clean_json_str[first_brace:]
             print("Note: Trimmed text before first brace.")
        
    # Check if there's any text after the last '}'
    last_brace = clean_json_str.rfind("}")
    if last_brace != -1:
        clean_json_str = clean_json_str[:last_brace+1]
        print("Note: Trimmed text after last brace.")

    data = json.loads(clean_json_str)
    print("SUCCESS: JSON is valid.")
    print("Keys found:", list(data.keys()))
except Exception as e:
    print(f"FAILURE: {e}")
    print("\nAttempting to find JSON block manually...")
    match = re.search(r'\{.*\}', raw_ai, re.DOTALL)
    if match:
        try:
            json.loads(match.group())
            print("Regex found a valid JSON block.")
        except:
             print("Regex found a block but it's STILL invalid JSON.")
    else:
        print("No JSON block found via Regex.")
