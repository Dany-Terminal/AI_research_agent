from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------------------
# MEMORY STORE
# ---------------------------
memory = {
    "summary": "",
    "recent": []  # list of {"user":..., "assistant":...}
}

MAX_RECENT = 4


# ---------------------------
# ADD INTERACTION
# ---------------------------
def add_interaction(user, assistant):
    memory["recent"].append({
        "user": user,
        "assistant": assistant
    })

    if len(memory["recent"]) > MAX_RECENT:
        summarize_memory()


# ---------------------------
# SUMMARIZE MEMORY
# ---------------------------
def summarize_memory():
    global memory

    old_data = ""

    # include previous summary
    if memory["summary"]:
        old_data += f"Previous Summary:\n{memory['summary']}\n\n"

    # include recent chats
    for convo in memory["recent"]:
        old_data += f"User: {convo['user']}\n"
        old_data += f"Assistant: {convo['assistant']}\n\n"

    prompt = f"""
Summarize the following conversation context.

Keep:
- important facts
- entities
- topic continuity
- comparisons if any

Be concise.

{old_data}
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    memory["summary"] = res.choices[0].message.content.strip()

    # clear recent after summarizing
    memory["recent"] = []


# ---------------------------
# GET CONTEXT
# ---------------------------
def get_context():
    context = ""

    if memory["summary"]:
        context += f"Summary:\n{memory['summary']}\n\n"

    if memory["recent"]:
        context += "Recent Conversation:\n"
        for convo in memory["recent"]:
            context += f"User: {convo['user']}\n"
            context += f"Assistant: {convo['assistant']}\n\n"

    return context.strip()


# ---------------------------
# CLEAR MEMORY
# ---------------------------
def clear_memory():
    memory["summary"] = ""
    memory["recent"] = []
