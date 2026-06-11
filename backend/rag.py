import os
import json
import math
from typing import Dict, Any, List, Tuple, Generator
from backend.config import OPENAI_API_KEY, GEMINI_API_KEY

# Fallback mechanism if chromadb is not installed/compilable on Windows
CHROMA_AVAILABLE = False
try:
    import chromadb
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    CHROMA_AVAILABLE = True
except ImportError:
    print("[RAG INFO] chromadb not available or failed to import. Using robust pure-Python Vector DB.")

# Simple Pure-Python Cosine-Similarity Vector Store to ensure 100% build compatibility on Windows.
class PurePythonVectorStore:
    def __init__(self, api_key: str, gemini_key: str = ""):
        self.api_key = api_key
        self.gemini_key = gemini_key
        if api_key and "your_openai" not in api_key:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        self.storage = []  # list of dicts: {"vector": [...], "text": "...", "metadata": {...}}

    def _get_embedding(self, text: str) -> List[float]:
        # Try Gemini embedding REST API if Gemini key is available
        if self.gemini_key and "your_gemini" not in self.gemini_key:
            import urllib.request
            try:
                # Use gemini-embedding-001 or gemini-embedding-2 (which are supported and available)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={self.gemini_key}"
                payload = {
                    "model": "models/gemini-embedding-2",
                    "content": {"parts": [{"text": text}]}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    return res_data["embedding"]["values"]
            except Exception as e:
                print(f"[Gemini Embedding Error] {e}. Falling back...")

        # Fallback to OpenAI if client is loaded
        if hasattr(self, 'client'):
            try:
                response = self.client.embeddings.create(
                    input=[text],
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"[Embedding Error] Could not generate embedding: {e}")
                
        # Mock embedding fallback (3072 dims for Gemini embedding, or 1536 for OpenAI)
        dims = 3072 if (self.gemini_key and "your_gemini" not in self.gemini_key) else 1536
        return [0.0] * dims

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        for text, meta in zip(texts, metadatas):
            vector = self._get_embedding(text)
            self.storage.append({
                "vector": vector,
                "text": text,
                "metadata": meta
            })

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Any, float]]:
        query_vector = self._get_embedding(query)
        
        results = []
        for item in self.storage:
            v1 = query_vector
            v2 = item["vector"]
            
            # Compute Cosine Similarity: dot(v1, v2) / (norm(v1) * norm(v2))
            dot_product = sum(a * b for a, b in zip(v1, v2))
            norm_v1 = math.sqrt(sum(a * a for a in v1))
            norm_v2 = math.sqrt(sum(b * b for b in v2))
            
            if norm_v1 == 0 or norm_v2 == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm_v1 * norm_v2)
                
            results.append((item, similarity))
            
        # Sort descending by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Format like LangChain documents
        class MockDocument:
            def __init__(self, page_content: str, metadata: Dict[str, Any]):
                self.page_content = page_content
                self.metadata = metadata
                
        formatted_results = []
        for item, score in results[:k]:
            doc = MockDocument(item["text"], item["metadata"])
            formatted_results.append((doc, score))
            
        return formatted_results

class RAGEngine:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.gemini_key = GEMINI_API_KEY
        self.vector_db = None
        self.raw_video_data = {}  # Store video details for global context (key: "A" or "B")
        
        # Check if any key is configured
        if not self.api_key and not self.gemini_key:
            print("[RAG WARNING] No API key (OpenAI or Gemini) is configured. RAG will use simulation.")

    def reset_database(self):
        """Cleans and re-initializes the session vector database."""
        if CHROMA_AVAILABLE and self.api_key:
            try:
                # We use ephemeral Chroma for thread/session separation
                self.vector_db = None
            except Exception:
                pass
        self.vector_db = PurePythonVectorStore(self.api_key, self.gemini_key)
        self.raw_video_data = {}

    def index_video_transcripts(self, video_a_data: Dict[str, Any] = None, video_b_data: Dict[str, Any] = None):
        """Splits, embeds, and indexes transcripts for provided videos."""
        self.reset_database()
        
        # Retain raw stats for global metadata operations (engagement, follower count, etc.)
        if video_a_data:
            self.raw_video_data["A"] = video_a_data
        if video_b_data:
            self.raw_video_data["B"] = video_b_data
        
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=40,
            separators=["\n", ".", " - ", " "]
        )
        
        chunks = []
        metadatas = []
        
        # Process Video A
        chunks_a = []
        if video_a_data:
            transcript_a = video_a_data.get("transcript", "")
            chunks_a = text_splitter.split_text(transcript_a)
            for chunk in chunks_a:
                chunks.append(chunk)
                metadatas.append({
                    "video_id": "A",
                    "platform": video_a_data.get("platform", "YouTube"),
                    "creator": video_a_data.get("creator", "Creator A"),
                    "title": video_a_data.get("title", "Video A"),
                    "views": video_a_data.get("views", 0),
                    "likes": video_a_data.get("likes", 0),
                    "comments": video_a_data.get("comments", 0),
                    "engagement_rate": video_a_data.get("engagement_rate", 0.0),
                    "follower_count": video_a_data.get("follower_count", 0),
                    "url": video_a_data.get("url", "")
                })
            
        # Process Video B
        chunks_b = []
        if video_b_data:
            transcript_b = video_b_data.get("transcript", "")
            chunks_b = text_splitter.split_text(transcript_b)
            for chunk in chunks_b:
                chunks.append(chunk)
                metadatas.append({
                    "video_id": "B",
                    "platform": video_b_data.get("platform", "Instagram Reels"),
                    "creator": video_b_data.get("creator", "Creator B"),
                    "title": video_b_data.get("title", "Video B"),
                    "views": video_b_data.get("views", 0),
                    "likes": video_b_data.get("likes", 0),
                    "comments": video_b_data.get("comments", 0),
                    "engagement_rate": video_b_data.get("engagement_rate", 0.0),
                    "follower_count": video_b_data.get("follower_count", 0),
                    "url": video_b_data.get("url", "")
                })
            
        # Add to Vector DB
        if self.vector_db:
            self.vector_db.add_texts(chunks, metadatas)
        else:
            self.vector_db = PurePythonVectorStore(self.api_key, self.gemini_key)
            self.vector_db.add_texts(chunks, metadatas)
            
        print(f"[RAG SUCCESS] Chunked and indexed transcripts. Total Chunks: {len(chunks)} (Video A: {len(chunks_a)}, Video B: {len(chunks_b)})")

    def _retrieve_relevant_chunks(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top K relevant chunks from our local vector database with metadata."""
        if not self.vector_db:
            return []
            
        results = self.vector_db.similarity_search_with_score(query, k=k)
        retrieved = []
        for doc, score in results:
            retrieved.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })
        return retrieved

    def get_streaming_response(self, user_query: str, chat_history: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Streams the LLM response using OpenAI GPT-4o-mini or Gemini 1.5 Flash.
        Maintains conversational history, retrieves context chunks, and appends citations dynamically.
        """
        has_gemini = self.gemini_key and "your_gemini" not in self.gemini_key
        has_openai = self.api_key and "your_openai" not in self.api_key
        
        # 1. Fallback Mode if neither key is configured
        if not has_gemini and not has_openai:
            yield "data: " + json.dumps({"token": "[SYSTEM NOTICE: You are running in SIMULATION mode because no API key (OpenAI/Gemini) is configured in .env. Please supply an OpenAI or Gemini API key in .env for full live dynamic responses.]\n\n"}) + "\n\n"
            # Return static rich response based on question matching
            simulated_response = self._get_simulated_response(user_query)
            for char in simulated_response:
                yield "data: " + json.dumps({"token": char}) + "\n\n"
            yield "data: [DONE]\n\n"
            return
            
        # 2. Retrieve Relevant Context
        context_chunks = self._retrieve_relevant_chunks(user_query, k=5)
        
        # Structure the context block for the LLM
        context_str = ""
        citations_list = []
        for idx, chunk in enumerate(context_chunks):
            meta = chunk["metadata"]
            vid_id = meta["video_id"]
            title = meta["title"]
            creator = meta["creator"]
            platform = meta["platform"]
            
            context_str += f"--- CONTEXT CHUNK {idx+1} [Video {vid_id} | {platform} | Title: {title} | Creator: {creator}] ---\n"
            context_str += f"{chunk['text']}\n\n"
            
            # Format clean citation item
            citations_list.append({
                "video_id": vid_id,
                "platform": platform,
                "creator": creator,
                "text": chunk["text"],
                "url": meta["url"]
            })
            
        # Gather global stats to answer statistical queries directly
        video_a_meta = self.raw_video_data.get("A", {})
        video_b_meta = self.raw_video_data.get("B", {})
        
        global_stats_str = "Global Statistics:\n"
        if video_a_meta:
            global_stats_str += (
                f"VIDEO A:\n"
                f"- Platform: {video_a_meta.get('platform')}\n"
                f"- URL: {video_a_meta.get('url')}\n"
                f"- Title: {video_a_meta.get('title')}\n"
                f"- Creator: {video_a_meta.get('creator')} (Followers: {video_a_meta.get('follower_count')})\n"
                f"- Views: {video_a_meta.get('views')}\n"
                f"- Likes: {video_a_meta.get('likes')}\n"
                f"- Comments: {video_a_meta.get('comments')}\n"
                f"- Engagement Rate: {video_a_meta.get('engagement_rate')}%\n\n"
            )
        if video_b_meta:
            global_stats_str += (
                f"VIDEO B:\n"
                f"- Platform: {video_b_meta.get('platform')}\n"
                f"- URL: {video_b_meta.get('url')}\n"
                f"- Title: {video_b_meta.get('title')}\n"
                f"- Creator: {video_b_meta.get('creator')} (Followers: {video_b_meta.get('follower_count')})\n"
                f"- Views: {video_b_meta.get('views')}\n"
                f"- Likes: {video_b_meta.get('likes')}\n"
                f"- Comments: {video_b_meta.get('comments')}\n"
                f"- Engagement Rate: {video_b_meta.get('engagement_rate')}%\n"
            )
        
        # 3. Construct System Prompt
        if video_a_meta and video_b_meta:
            system_prompt = (
                "You are an expert Social Media & Viral Growth Analyst. Your job is to help creators compare two videos "
                "(Video A and Video B) and provide extremely precise, data-driven, and actionable advice to improve their metrics.\n\n"
                "You have access to the exact transcripts, hooks, and views/likes/comments metadata. "
                "Always cite whether your information comes from Video A or Video B, referencing creator profiles and engagement numbers.\n\n"
                "Here is the retrieved context from transcripts:\n"
                f"{context_str}\n"
                "Here are the absolute global metadata metrics for both videos:\n"
                f"{global_stats_str}\n"
                "INSTRUCTIONS:\n"
                "1. Answer the user's questions in a clear, engaging, professional tone using Markdown format.\n"
                "2. When comparing engagement rates, views, or creators, use the specific numbers provided above.\n"
                "3. If asked about the 'first 5 seconds hook', look closely at the timestamp indicators in the transcripts (e.g., 0:00 - 0:05).\n"
                "4. Be critical but constructive. Offer specific recommendations for improvements.\n"
                "5. ALWAYS refer to the videos as 'Video A' and 'Video B' clearly.\n"
                "6. Make sure to present your findings cleanly."
            )
        else:
            vid_label = "Video A" if video_a_meta else "Video B"
            system_prompt = (
                f"You are an expert Social Media & Viral Growth Analyst. Your job is to help creators analyze a single video "
                f"({vid_label}) and provide extremely precise, data-driven, and actionable advice to improve their metrics.\n\n"
                f"You have access to the exact transcripts, hooks, and views/likes/comments metadata. "
                f"Always cite that your information comes from the video, referencing creator profiles and engagement numbers.\n\n"
                f"Here is the retrieved context from transcripts:\n"
                f"{context_str}\n"
                f"Here are the absolute global metadata metrics for the video:\n"
                f"{global_stats_str}\n"
                f"INSTRUCTIONS:\n"
                f"1. Answer the user's questions in a clear, engaging, professional tone using Markdown format.\n"
                f"2. When referring to engagement rates or views, use the specific numbers provided above.\n"
                f"3. Be critical but constructive. Offer specific recommendations for improvements.\n"
                f"4. Make sure to present your findings cleanly."
            )
        
        # 4. Stream using Gemini API if configured (Free Dynamic Live RAG)
        if has_gemini:
            import urllib.request
            
            history_prompt = ""
            for msg in chat_history[-6:]:
                role_label = "Assistant" if msg["role"] == "assistant" else "User"
                history_prompt += f"{role_label}: {msg['content']}\n\n"
            history_prompt += f"User: {user_query}"
            
            prompt_content = f"{system_prompt}\n\nConversational Context:\n{history_prompt}"
            
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt_content}]}],
                "generationConfig": {
                    "temperature": 0.7
                }
            }
            
            try:
                # Use gemini-2.5-flash which is available and has active quota
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent?key={self.gemini_key}"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                
                # Send citations first
                yield "data: " + json.dumps({"citations": citations_list}) + "\n\n"
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    buffer = ""
                    brace_count = 0
                    start_idx = -1
                    
                    while True:
                        chunk = response.read(1024)
                        if not chunk:
                            break
                        buffer += chunk.decode("utf-8")
                        
                        i = 0
                        while i < len(buffer):
                            if buffer[i] == '{':
                                if brace_count == 0:
                                    start_idx = i
                                brace_count += 1
                            elif buffer[i] == '}':
                                brace_count -= 1
                                if brace_count == 0 and start_idx != -1:
                                    json_str = buffer[start_idx:i+1]
                                    try:
                                        obj = json.loads(json_str)
                                        text_chunk = obj["candidates"][0]["content"]["parts"][0]["text"]
                                        yield "data: " + json.dumps({"token": text_chunk}) + "\n\n"
                                    except Exception:
                                        pass
                                    buffer = buffer[i+1:]
                                    i = -1
                            i += 1
                yield "data: [DONE]\n\n"
                return
            except Exception as e:
                print(f"[Gemini Error] {e}. Falling back to simulation...")
                yield "data: " + json.dumps({"token": f"\n\n[Gemini API Error: {e}]. Falling back to simulation...\n\n"}) + "\n\n"
                simulated_response = self._get_simulated_response(user_query)
                for char in simulated_response:
                    yield "data: " + json.dumps({"token": char}) + "\n\n"
                yield "data: [DONE]\n\n"
                return

        # 5. Stream using OpenAI API if OpenAI is configured
        if has_openai:
            import openai
            
            messages = [{"role": "system", "content": system_prompt}]
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_query})
            
            client = openai.OpenAI(api_key=self.api_key)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )
                
                yield "data: " + json.dumps({"citations": citations_list}) + "\n\n"
                
                for chunk in response:
                    token = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
                    if token:
                        yield "data: " + json.dumps({"token": token}) + "\n\n"
                        
                yield "data: [DONE]\n\n"
            except Exception as e:
                print(f"[LLM Error] API call failed: {e}")
                yield "data: " + json.dumps({"token": f"\n\n[OpenAI API Error occurred: {e}].\nFalling back to simulated diagnostic response...\n\n"}) + "\n\n"
                simulated_response = self._get_simulated_response(user_query)
                for char in simulated_response:
                    yield "data: " + json.dumps({"token": char}) + "\n\n"
                yield "data: [DONE]\n\n"

    def _get_simulated_response(self, query: str) -> str:
        """Returns detailed, high-fidelity mock responses for offline/simulation testing."""
        q = query.lower()
        video_a = self.raw_video_data.get("A", {})
        video_b = self.raw_video_data.get("B", {})
        
        rate_a = video_a.get("engagement_rate", 9.62)
        rate_b = video_b.get("engagement_rate", 4.65)
        
        creator_a = video_a.get("creator", "TechCraft Studio")
        creator_b = video_b.get("creator", "code_with_alex")
        fol_b = video_b.get("follower_count", 125000)
        
        if "engagement rate" in q or "engagement" in q and "rate" in q:
            return (
                f"### Engagement Rate Comparison\n\n"
                f"*   **Video A (YouTube):** **{rate_a}%**\n"
                f"    *   *Calculation:* ({video_a.get('likes')} likes + {video_a.get('comments')} comments) / {video_a.get('views')} views × 100\n"
                f"*   **Video B (Instagram Reels):** **{rate_b}%**\n"
                f"    *   *Calculation:* ({video_b.get('likes')} likes + {video_b.get('comments')} comments) / {video_b.get('views')} views × 100\n\n"
                f"**Analysis:** Video A has a significantly higher engagement rate. Even though YouTube videos are longer, "
                f"Video A successfully drove high interactive actions (likes and comments relative to view count) compared to Video B."
            )
            
        elif "why did video a" in q or "more engagement" in q or "compare" in q and "engagement" in q:
            return (
                f"### Why Video A got More Engagement than Video B\n\n"
                f"Based on my analysis of the transcripts and metrics, **Video A ({rate_a}% engagement)** outperformed **Video B ({rate_b}% engagement)** due to three key pillars:\n\n"
                f"1.  **High-Urgency Hook in Video A:**\n"
                f"    *   *Video A's hook:* `\"This single prompt is about to replace 90% of junior developers...\"` (0:00 - 0:05). This leverages direct *curiosity gap* and *industry FOMO* immediately.\n"
                f"    *   *Video B's hook:* `\"Um, hey guys... so, I wanted to show you three extensions...\"` (0:00 - 0:05). It uses conversational fillers (`\"um\"`, `\"so\"`) and slow pacing, failing to grab attention.\n\n"
                f"2.  **Structured Value Delivery:**\n"
                f"    *   Video A utilizes data citations (e.g., `\"GitHub Copilot... 55% faster\"`) and walks through a code failure (forgetting a mutex lock in Go). This creates a high retention rate.\n"
                f"    *   Video B simply lists standard extensions (Prettier, GitLens) that most developers already know, failing to provide novel value.\n\n"
                f"3.  **Active Engagement Loop:**\n"
                f"    *   Video A triggers a highly specific comment prompt: discussing production costing and AI replacement, leading to massive debate (2,400 comments). Video B has a soft, passive CTA (410 comments)."
            )
            
        elif "hook" in q or "first 5 seconds" in q or "5 second" in q:
            return (
                f"### 5-Second Hook Comparison\n\n"
                f"Analyzing the opening transcripts for both videos reveals a stark difference in script design:\n\n"
                f"*   **Video A (YouTube):**\n"
                f"    *   *Script:* `\"This single prompt is about to replace 90% of junior developers, or at least that's what the headlines want you to think.\"`\n"
                f"    *   *Type:* **Provocative & Curiosity-Driven**. It creates an instant emotional trigger (fear of replacement) and promises a logical deconstruction.\n\n"
                f"*   **Video B (Instagram Reels):**\n"
                f"    *   *Script:* `\"Um, hey guys... so, I wanted to show you three extensions in VS Code that I use almost every day.\"`\n"
                f"    *   *Type:* **Passive & Generic**. The use of fillers (`\"Um\"`, `\"so\"`) and a standard introduction wastes the critical first 3 seconds when viewers decide to scroll away.\n\n"
                f"**Recommendation:** Video B should eliminate the introduction and start directly with the action: `\"Stop formatting your code manually. You need this...\"`."
            )
            
        elif "creator" in q or "who is the creator" in q or "follower count" in q:
            return (
                f"### Creator & Audience Profile\n\n"
                f"*   **Video A's Creator:** **{creator_a}** on YouTube.\n"
                f"    *   *Follower Count:* **850,000 subscribers**\n"
                f"*   **Video B's Creator:** **{creator_b}** on Instagram Reels.\n"
                f"    *   *Follower Count:* **{fol_b:,} followers**\n\n"
                f"While {creator_a} has a much larger absolute subscriber base, {creator_b} has a highly dedicated micro-creator audience on Instagram, meaning Video B has massive potential if optimized for viral hooks."
            )
            
        elif "suggest improvements" in q or "improvement" in q or "suggest" in q:
            return (
                f"### Actionable Improvements for Video B based on Video A\n\n"
                f"Here are 3 concrete improvements to boost Video B's performance, modeled directly after what worked for Video A:\n\n"
                f"1.  **Optimize the Opening Hook (The First 3 Seconds):**\n"
                f"    *   *Action:* Delete passive intros like `\"Hey guys, so today...\"`. Instead, open with a polarizing statement or a visual demonstration.\n"
                f"    *   *Revised Script Hook:* `\"If you aren't using these 3 VS Code extensions, you are actively writing code slower. Let's fix that.\"`\n\n"
                f"2.  **Increase Novelty & Depth:**\n"
                f"    *   Instead of presenting basic extensions like *Prettier* (which 95% of devs already use), present hidden gems or specific setup features. For example, explain how Peacock prevents database deployment mistakes by color-coding dev vs production folders (similar to how Video A highlighted a Go mutex race condition).\n\n"
                f"3.  **Deploy an Interactive Comment Prompt (Call to Action):**\n"
                f"    *   Create a debate or resource-distribution loop: `\"Comment EXTENSIONS below and my automated bot will DM you my full setting.json file!\"` or `\"Which extension is overrated? Let's argue in the comments!\"`."
            )
            
        else:
            return (
                f"Hello! I am ready to analyze your video metrics. Here is what we have loaded:\n\n"
                f"- **Video A (YouTube):** *{video_a.get('title', 'AI Software Engineering')}* by {creator_a} ({rate_a}% engagement).\n"
                f"- **Video B (Instagram Reel):** *{video_b.get('title', 'VS Code Extensions')}* by {creator_b} ({rate_b}% engagement).\n\n"
                f"Feel free to ask me to compare their hooks, analyze why A beat B, suggest improvements, or provide their follower metrics!"
            )
