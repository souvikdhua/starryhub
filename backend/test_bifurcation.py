import requests
import json
import os

BASE_URL = "http://localhost:8000"

def test_initial_reading():
    print("🧪 Testing INITIAL READING (expected JSON)...")
    payload = {
        "messages": [
            {"role": "user", "content": "Generate my full chart reading exactly in the requested format. Follow the system instructions precisely."}
        ],
        "chart_context": "Sun In Sagittarius 9°58' H1\nMoon In Sagittarius 24°45' H1"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        # Check if it's JSON
        json_data = json.loads(content)
        if "today_at_a_glance" in json_data:
            print("✅ SUCCESS: Received valid structured JSON for initial reading.")
            print(f"Sample: {content[:100]}...")
        else:
            print("❌ FAILURE: JSON structure mismatch.")
            print(f"Content: {content}")
    except Exception as e:
        print(f"❌ FAILURE: {e}")

def test_conversational_chat():
    print("\n💬 Testing CONVERSATIONAL CHAT (expected Plain Text)...")
    payload = {
        "messages": [
            {"role": "user", "content": "Generate my full chart reading exactly in the requested format. Follow the system instructions precisely."},
            {"role": "assistant", "content": "{\"today_at_a_glance\": {\"p1\": \"the stars are cold.\", \"p2\": \"...\", \"p3\": \"...\"}}"},
            {"role": "user", "content": "what does my moon in sagittarius mean for my life?"}
        ],
        "chart_context": "Sun In Sagittarius 9°58' H1\nMoon In Sagittarius 24°45' H1"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        # Check if it's NOT just raw JSON (it should be poetic text)
        is_json = False
        try:
            json.loads(content)
            is_json = True
        except:
            pass
        
        if not is_json:
            print("✅ SUCCESS: Received plain text/poetic response for chat.")
            print(f"Snippet: {content[:200]}...")
        else:
            print("❌ FAILURE: Received JSON instead of plain text for chat.")
            print(f"Content: {content}")
    except Exception as e:
        print(f"❌ FAILURE: {e}")

if __name__ == "__main__":
    test_initial_reading()
    test_conversational_chat()
