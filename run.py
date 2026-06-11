import os
import sys
import shutil

def setup_environment():
    """Automatically ensures a local .env exists for the developer to run the project immediately."""
    print("==================================================")
    print("     VIBE_RAG Chatbot Comparative Analyser        ")
    print("==================================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    env_example_path = os.path.join(base_dir, ".env.example")
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            print("[SETUP] Local .env not found. Auto-generating .env from template .env.example...")
            shutil.copyfile(env_example_path, env_path)
            print("[SETUP] Created .env file. Please add your OPENAI_API_KEY inside the .env file for LLM answers.")
        else:
            print("[ERROR] .env.example template not found. Please create a .env file manually.")
    else:
        print("[SETUP] Found existing local .env file.")

def main():
    setup_environment()
    
    # Import config and start uvicorn
    try:
        import uvicorn
    except ImportError:
        print("[ERROR] uvicorn is not installed. Please run:")
        print("        pip install -r requirements.txt   OR   pip install uvicorn fastapi pydantic jinja2 python-dotenv yt-dlp youtube-transcript-api openai langchain langchain-community langchain-openai")
        sys.exit(1)
        
    from backend.config import HOST, PORT
    
    print(f"[LAUNCH] Launching FastAPI full-stack server on http://{HOST}:{PORT}")
    print("[INFO] Hot-reload is active. Open this URL in Chrome to interact with the dashboard.\n")
    
    # Execute uvicorn server programmatically
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)

if __name__ == "__main__":
    main()
