import os
from google import genai
from dotenv import load_dotenv

# Load your local .env file
load_dotenv()

credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")
test_model = os.getenv("EMBEDDING_MODEL")

print(f"🔑 Credentials Path: {credentials_path}")
print(f"🌍 Routing to: Project '{project_id}' in '{location}'")

if not credentials_path or not os.path.exists(credentials_path):
    print("❌ ERROR: The JSON credentials file was not found at the specified path.")
    exit(1)

# vertexai=True forces the SDK to use the enterprise endpoints and your JSON key
client = genai.Client(
    vertexai=True, 
    project=project_id, 
    location=location
)

print("\n" + "="*50)
print(f" TESTING DIRECT EMBEDDING CALL ({test_model})")
print("="*50)

try:
    print(f"Attempting to embed a sentence...")
    response = client.models.embed_content(
        model=test_model,
        contents="This is a raw API test.",
        config={"task_type": "RETRIEVAL_DOCUMENT"}
    )
    vector = response.embeddings[0].values
    
    print(f"\n🎉 SUCCESS! The API call worked.")
    print(f"📊 Vector generated with {len(vector)} dimensions.")
    print(f"First 3 coordinates: {vector[:3]}")
    
except Exception as e:
    print(f"\n❌ FAILED to embed using '{test_model}'.")
    print(f"Error: {e}")