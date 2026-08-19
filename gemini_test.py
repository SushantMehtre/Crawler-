import os
import sys
from google import genai

def test_gemini_key():
    # Prompt user for API key if not in environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter your Gemini API key to test: ").strip()
        
    if not api_key:
        print("No API key provided. Exiting.")
        return
        
    print("\n--- Diagnostic Start ---")
    print(f"Initializing Gemini Client...")
    try:
        client = genai.Client(api_key=api_key)
        
        print("Attempting to list available models...")
        models = client.models.list()
        text_models = [m.name for m in models if 'generateContent' in m.supported_actions]
        print(f"Successfully retrieved models! Found {len(text_models)} text models:")
        for name in text_models[:15]:  # print first 15 models
            print(f"  - {name}")
        if len(text_models) > 15:
            print(f"  - ... and {len(text_models) - 15} more.")
        
        # Test generation with the first available model instead of hardcoded 'gemini-1.5-flash'
        target_model = text_models[0] if text_models else "gemini-1.5-flash"
        print(f"\nTesting text generation with model '{target_model}'...")
        response = client.models.generate_content(
            model=target_model,
            contents="Say: Connection Successful!"
        )
        print(f"API Response: {response.text.strip()}")
        print("🎉 SUCCESS! Your API Key is active and working perfectly.")
        
    except Exception as e:
        print("\n❌ DIAGNOSTIC FAILED!")
        print(f"Error Details: {str(e)}")
        print("\nPossible causes:")
        print("1. Your API key might be invalid or copied incorrectly.")
        print("2. Google may have blocked/suspended free-tier usage for your account (common on new accounts without phone verification).")
        print("3. Your region might not support the free tier Google Gemini API.")
        
    print("--- Diagnostic End ---\n")

if __name__ == "__main__":
    test_gemini_key()
