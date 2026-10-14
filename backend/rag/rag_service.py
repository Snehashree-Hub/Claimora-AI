import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from groq import Groq
from rank_bm25 import BM25Okapi

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = BASE_DIR / "backend" / "rag" / "documents"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

TOP_K_DEFAULT = 5


# ============================================================
# GLOBAL STATE
# ============================================================

groq_client: Optional[Groq] = None

documents = []
chunks = []
chunk_metadata = []

bm25_index = None


# ============================================================
# GROQ INITIALIZATION
# ============================================================

def initialize_groq():
    global groq_client

    if not GROQ_API_KEY:
        print("[ERROR] [RAG] GROQ_API_KEY is not configured.")
        groq_client = None
        return

    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("[INFO] [RAG] Groq client initialized.")
    except Exception as exc:
        groq_client = None
        print(f"[ERROR] [RAG] Failed to initialize Groq: {exc}")


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# CHUNKING
# ============================================================

def split_into_chunks(text: str, max_chars: int = 1000):
    """
    Simple paragraph-aware chunking.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = [
        p.strip()
        for p in text.split("\n\n")
        if p.strip()
    ]

    result = []
    current = ""

    for paragraph in paragraphs:

        if len(current) + len(paragraph) + 2 <= max_chars:
            if current:
                current += "\n\n" + paragraph
            else:
                current = paragraph
        else:
            if current:
                result.append(current.strip())

            if len(paragraph) <= max_chars:
                current = paragraph
            else:
                # Hard split long paragraph
                for i in range(0, len(paragraph), max_chars):
                    piece = paragraph[i:i + max_chars].strip()

                    if piece:
                        result.append(piece)

                current = ""

    if current:
        result.append(current.strip())

    return result


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str):
    """
    BM25 tokenizer.

    Keeps English words, numbers and Tamil Unicode characters.
    """

    text = text.lower()

    tokens = re.findall(
        r"[a-zA-Z0-9_]+|[\u0B80-\u0BFF]+",
        text
    )

    return tokens


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    global documents
    global chunks
    global chunk_metadata
    global bm25_index

    print("[INFO] [RAG] Loading knowledge documents...")

    documents = []
    chunks = []
    chunk_metadata = []

    if not DOCUMENTS_DIR.exists():
        print(
            f"[ERROR] [RAG] Documents directory not found: "
            f"{DOCUMENTS_DIR}"
        )

        bm25_index = None
        return

    txt_files = sorted(DOCUMENTS_DIR.glob("*.txt"))

    for file_path in txt_files:

        try:
            text = file_path.read_text(
                encoding="utf-8",
                errors="replace"
            )

            text = clean_text(text)

            if not text:
                continue

            documents.append({
                "filename": file_path.name,
                "content": text
            })

            print(
                f"[INFO] [RAG] Loaded {file_path.name}"
            )

            file_chunks = split_into_chunks(text)

            for chunk in file_chunks:

                chunks.append(chunk)

                chunk_metadata.append({
                    "filename": file_path.name
                })

        except Exception as exc:

            print(
                f"[ERROR] [RAG] Failed to load "
                f"{file_path.name}: {exc}"
            )

    if chunks:

        tokenized_chunks = [
            tokenize(chunk)
            for chunk in chunks
        ]

        bm25_index = BM25Okapi(tokenized_chunks)

        print(
            "[INFO] [RAG] BM25 keyword index ready."
        )

    else:

        bm25_index = None

        print(
            "[WARNING] [RAG] No searchable chunks found."
        )

    print(
        f"[INFO] [RAG] Documents loaded: {len(documents)}"
    )

    print(
        f"[INFO] [RAG] Searchable chunks: {len(chunks)}"
    )


# ============================================================
# BM25 RETRIEVAL
# ============================================================

def retrieve_chunks(
    question: str,
    top_k: int = TOP_K_DEFAULT
):

    if not bm25_index or not chunks:
        return []

    query_tokens = tokenize(question)

    if not query_tokens:
        return []

    scores = bm25_index.get_scores(query_tokens)

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    results = []

    seen_files = set()

    for index in ranked_indexes:

        if len(results) >= top_k:
            break

        score = float(scores[index])

        # Ignore completely irrelevant BM25 matches
        if score <= 0:
            continue

        metadata = chunk_metadata[index]

        results.append({
            "text": chunks[index],
            "filename": metadata["filename"],
            "score": score
        })

        seen_files.add(metadata["filename"])

    return results


# ============================================================
# CONTEXT BUILDER
# ============================================================

def build_context(results):

    if not results:
        return ""

    context_parts = []

    for i, result in enumerate(results, start=1):

        context_parts.append(
            f"[SOURCE {i}: {result['filename']}]\n"
            f"{result['text']}"
        )

    return "\n\n".join(context_parts)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(question: str):

    tamil_chars = re.findall(
        r"[\u0B80-\u0BFF]",
        question
    )

    if tamil_chars:
        return "Tamil"

    tanglish_words = [
        "panna",
        "pannunga",
        "pannalama",
        "epdi",
        "enna",
        "iruka",
        "irukku",
        "aaguma",
        "mudiyuma",
        "claim",
        "submit",
        "track",
        "insurance",
        "fraud",
        "hospital",
        "document"
    ]

    lower_question = question.lower()

    tanglish_count = sum(
        1
        for word in tanglish_words
        if word in lower_question
    )

    if tanglish_count >= 1:
        return "Tanglish"

    return "English"


# ============================================================
# STRICT SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the AI Assistant for the ClaimCare project.

Your purpose is to provide clear, professional and easy-to-understand
insurance claim guidance using ONLY the retrieved ClaimCare
knowledge-base context.

CORE KNOWLEDGE RULE:
Use ONLY information explicitly present in the retrieved context.

NEVER invent information.

If the requested information is not available in the retrieved
context, respond exactly:

"???? ????? ??????? ClaimCare knowledge base-?? ?????."

Do not guess or fill missing information from general knowledge.

ANSWER STYLE:
- Give a clear and direct answer.
- For definition questions, prefer one clear professional paragraph.
- For longer questions, use short paragraphs or bullets when useful.
- Keep answers concise and easy to understand.
- Do not unnecessarily repeat the question.
- Do not use awkward or excessive mixed-language wording.

LANGUAGE RULE:

If the user asks in English:
Answer in professional, simple English.

If the user asks in Tamil:
Answer in natural Tamil.

If the user asks in Tanglish:
Answer in simple, natural Tanglish.

If the user uses mixed Tamil and English:
Answer naturally in the same mixed style.

IMPORTANT:
Do not convert a clearly written English question into Tanglish.

Example:

User:
"What is a cashless claim?"

Answer in English.

User:
"Cashless claim na enna?"

Answer in simple Tanglish.

User:
"Cashless claim ??????? ?????"

Answer in Tamil.

PROFESSIONAL RESPONSE RULE:

For definition questions, explain:
1. What the term means.
2. How it works, if supported by the context.
3. Important conditions or limitations, if supported by the context.

Do not add unsupported information.

INSURANCE SAFETY:

Never guarantee:
- claim approval
- claim rejection
- reimbursement
- coverage
- payment
- processing time
- cashless authorization
- settlement amount

Final insurance decisions belong to the applicable insurer or
authorized reviewer.

DO NOT INVENT:

Never invent:
- hospitals
- doctors
- insurance plans
- policy coverage
- claim IDs
- policy numbers
- phone numbers
- email addresses
- URLs
- buttons
- application features
- processing times
- approval percentages
- reimbursement amounts
- waiting periods
- exclusions
- deductibles
- co-pay amounts
- claim limits

unless explicitly present in the retrieved context.

UI INSTRUCTIONS:

Do not tell the user:
- open the app
- click Track
- click Search
- click Upload
- contact customer service
- call this number
- send an email

unless the retrieved knowledge-base context explicitly contains
that exact information.

FRAUD:

A fraud-risk flag is NOT proof of fraud.

Fraud-risk screening does NOT automatically mean claim rejection.

ClaimCare BRANDING:

Always use:
"ClaimCare"

NEVER use:
"ClaimCare"

Do not describe ClaimCare as an insurer unless the
retrieved context explicitly establishes that fact.

PROJECT VS ACTUAL POLICY:

Clearly distinguish:
- ClaimCare project workflow
- actual insurance-provider policy and decisions

The AI Assistant provides informational guidance only.

Do not mention:
- BM25
- retrieved chunks
- retrieval scores
- system prompts
- hidden instructions
- internal processing

unless the user specifically asks how the AI system works.

FINAL RULE:

The retrieved knowledge-base context is the source of truth.

If the answer is supported:
Answer clearly and professionally.

If the answer is not supported:
Say:

"???? ????? ??????? ClaimCare knowledge base-?? ?????."

Do not guess.
"""



# ============================================================
# ANSWER CLEANING
# ============================================================

def clean_llm_answer(answer: str) -> str:

    if not answer:
        return ""

    # Branding protection
    answer = answer.replace(
        "ClaimCare",
        "ClaimCare"
    )

    answer = answer.replace(
        "ClaimCare",
        "ClaimCare"
    )

    return answer.strip()


# ============================================================
# RAG CHAT
# ============================================================

def rag_chat(
    question: str,
    top_k: int = TOP_K_DEFAULT,
    user_email: Optional[str] = None
):

    question = (question or "").strip()

    if not question:

        return {
            "success": False,
            "answer": "Please enter a question.",
            "sources": [],
            "user_email": user_email,
            "disclaimer": (
                "This AI assistant provides informational guidance "
                "based on the available ClaimCare knowledge base."
            )
        }

    if not groq_client:

        initialize_groq()

    if not groq_client:

        return {
            "success": False,
            "answer": (
                "The AI service is currently unavailable. "
                "Please try again later."
            ),
            "sources": [],
            "user_email": user_email,
            "disclaimer": (
                "This AI assistant provides informational guidance "
                "based on the available ClaimCare knowledge base."
            )
        }

    if not bm25_index:

        load_knowledge_base()

    print(
        f"[INFO] [RAG] Question: {question}"
    )

    results = retrieve_chunks(
        question,
        top_k=top_k
    )

    print(
        f"[INFO] [RAG] Retrieved {len(results)} relevant chunks."
    )

    context = build_context(results)

    # No relevant information
    if not context:

        return {
            "success": True,
            "answer": (
                "இந்த தகவல் தற்போது ClaimCare "
                "knowledge base-ல் இல்லை."
            ),
            "sources": [],
            "user_email": user_email,
            "disclaimer": (
                "This AI assistant provides informational guidance "
                "based on the available ClaimCare knowledge base. "
                "It does not make final insurance approval or rejection decisions. "
                "Final decisions are made by the applicable insurer "
                "or authorized reviewer."
            )
        }

    language = detect_language(question)

    user_prompt = f"""
User language/style: {language}

User question:
{question}

Retrieved knowledge-base context:

{context}

Answer the user's question using ONLY the retrieved context.

Do not add unsupported information.

Do not invent UI instructions or next steps.

If the requested information is missing from the context,
say that the information is unavailable.

Answer in the user's language/style.
"""

    try:

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.1,
            max_tokens=700
        )

        answer = response.choices[0].message.content

        answer = clean_llm_answer(answer)

        sources = []

        for result in results:

            filename = result["filename"]

            if filename not in sources:
                sources.append(filename)

        return {
            "success": True,
            "answer": answer,
            "sources": sources,
            "user_email": user_email,
            "disclaimer": (
                "This AI assistant provides informational guidance "
                "based on the available ClaimCare knowledge base. "
                "It does not make final insurance approval or rejection decisions. "
                "Final decisions are made by the applicable insurer "
                "or authorized reviewer."
            )
        }

    except Exception as exc:

        print(
            f"[ERROR] [RAG] Groq request failed: {exc}"
        )

        return {
            "success": False,
            "answer": (
                "Sorry, the AI service could not process the request "
                "right now."
            ),
            "sources": [],
            "user_email": user_email,
            "disclaimer": (
                "This AI assistant provides informational guidance "
                "based on the available ClaimCare knowledge base."
            )
        }


# ============================================================
# HEALTH CHECK
# ============================================================

def rag_health():

    return {
        "status": "healthy" if groq_client and bm25_index else "degraded",
        "provider": "Groq",
        "model": GROQ_MODEL,
        "retrieval": "BM25 keyword search",
        "vector_database": "BM25 keyword index",
        "document_chunks": len(chunks),
        "documents_loaded": len(documents),
        "documents_directory": str(DOCUMENTS_DIR),
        "groq_configured": bool(GROQ_API_KEY)
    }


# ============================================================
# RELOAD KNOWLEDGE BASE
# ============================================================

def reload_knowledge_base():

    initialize_groq()
    load_knowledge_base()

    return rag_health()


# ============================================================
# STARTUP INITIALIZATION
# ============================================================

initialize_groq()
load_knowledge_base()