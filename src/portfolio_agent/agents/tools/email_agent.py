# agents/tools/email_agent.py
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ...utils import llm_chat
import os
import smtplib
from email.message import EmailMessage

EMAIL_FROM = os.getenv("EMAIL_FROM")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def email_agent(state: MessagesState) -> Command[Literal["end"]]:
    """
    Draft an email using the model and optionally send it (if SMTP configured & allow_send flag).
    Expects state.messages[-1] to contain the user's request like 'draft email to recruiter about X'
    """
    user_msg = state.messages[-1]["content"]
    prompt = [
        {"role":"system","content":"You are a formal assistant that drafts professional emails."},
        {"role":"user","content": f"Draft a professional email: {user_msg}"}
    ]
    draft = llm_chat(prompt, max_tokens=400)
    allow_send = getattr(state, "allow_send", False)
    if allow_send and SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_FROM:
        # naive send: extract to/from subject from state or message. For prod, require explicit fields.
        # This is a demo: do not send unless fields exist in state
        to_address = getattr(state, "email_to", None)
        subject = getattr(state, "email_subject", "Message from portfolio assistant")
        if to_address:
            msg = EmailMessage()
            msg["From"] = EMAIL_FROM
            msg["To"] = to_address
            msg["Subject"] = subject
            msg.set_content(draft)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            return Command(goto="end", update={"email_sent": True, "draft": draft})
    return Command(goto="end", update={"email_sent": False, "draft": draft})
