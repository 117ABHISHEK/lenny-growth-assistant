import re
import uuid

GROUNDED_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an AI trained exclusively on Lenny's Podcast transcripts about product management and growth.

RULES:
1. Answer ONLY using the provided transcript context below. Do not use outside knowledge.
2. Every claim must cite its source using this exact format: [Episode: Guest Name, timestamp_ref]
3. If the provided context does not contain enough information to answer the question, respond exactly with: "I do not have sufficient information in Lenny's podcast archive to answer this."
4. Be concise and direct. Do not pad your answer with generic advice not grounded in the transcripts.
{artifact_instruction}

TRANSCRIPT CONTEXT:
{context}
"""

ARTIFACT_INSTRUCTION = """
If the user explicitly asks you to create a document, summary, or shareable write-up, wrap it in an artifact tag like this:
<artifact type="markdown" title="Short Title Here">
... full markdown content here ...
</artifact>

CRITICAL: Content inside the artifact tag must follow the exact same grounding rules as your normal answers — use ONLY the transcripts provided in TRANSCRIPT CONTEXT above, and cite ONLY guests and episodes that actually appear in that context. NEVER invent guest names, episodes, or timestamps that are not in the provided context. If the context doesn't support a full document, write a shorter one using only what's actually there.

Use type="html" instead of "markdown" only if the user specifically asks for an HTML/CSS snippet. Only emit an artifact tag when explicitly asked to create a document.
"""

ARTIFACT_PATTERN = re.compile(
    r'<artifact type="(markdown|html)" title="([^"]*)">(.*?)</artifact>',
    re.DOTALL,
)

KNOWN_GUESTS = {
    "ada chen rekhi", "adam fishman", "alex hardimen", "alisa cohn", "ami vora",
    "amjad masad", "andrew wilkinson", "andy johns", "andy raskin", "annie duke",
    "annie pearl", "anton osika", "anuj rathi", "aparna chennapragada",
    "april dunford", "archie abrams", "arielle jackson", "asha sharma",
    "austin hay", "bangaly kaba", "barbra gago", "ben horowitz", "ben williams",
    "bill carr", "bob baxley", "bob moesta", "boz",
}

def build_context_block(chunks: list[dict]) -> str:
    if not chunks:
        return "(no relevant transcript chunks found)"
    return "\n\n".join(
        f"--- {c['episode']} (Guest: {c['guest']}, {c['timestamp']}) ---\n{c['text']}"
        for c in chunks
    )

def extract_artifacts(full_text: str) -> list[dict]:
    """Find any <artifact> tags in the model's full response and extract them."""
    artifacts = []
    for match in ARTIFACT_PATTERN.finditer(full_text):
        artifact_type, title, content = match.groups()
        artifacts.append({
            "id": str(uuid.uuid4()),
            "artifact_type": artifact_type,
            "title": title.strip() or "Untitled",
            "content": content.strip(),
        })
    return artifacts

def strip_artifact_tags(full_text: str) -> str:
    """Remove artifact blocks from the chat text so they aren't duplicated in the message bubble."""
    return ARTIFACT_PATTERN.sub("[Artifact generated — see viewer]", full_text).strip()

def flag_unverified_citations(text: str) -> list[str]:
    """Return guest names cited in [Episode: Guest, ...] format that aren't in the known corpus."""
    cited = re.findall(r'\[Episode:\s*([^,\]]+)', text)
    unverified = [name.strip() for name in cited if name.strip().lower() not in KNOWN_GUESTS]
    return unverified