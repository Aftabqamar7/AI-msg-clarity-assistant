"""
app.py — Streamlit UI for the AI Message Clarity Assistant

Flow:
  1. User pastes/types a message
  2. Click "Analyze Clarity"
  3. See: clarity score, confusing parts, improved rewrite, and what changed
"""

import streamlit as st

from workflow import analyze_message

st.set_page_config(
    page_title="AI Message Clarity Assistant",
    page_icon="🔎",
    layout="centered",
)

st.title("🔎 AI Message Clarity Assistant")
st.caption(
    "Paste a message you're about to send. Claude will flag confusing parts, "
    "rewrite it more clearly, and explain the changes."
)

# --- API key handling -------------------------------------------------
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        st.subheader("Settings")
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Not stored anywhere. Only used for this session. "
            "For deployment, set GROQ_API_KEY in Streamlit secrets instead.",
        )
        st.markdown(
            "[Get a free API key](https://console.groq.com/keys)"
        )

# --- Input --------------------------------------------------------------
message = st.text_area(
    "Your message",
    height=180,
    placeholder="e.g. Hey can you send that thing over before the meeting, "
    "also loop in the other team if it makes sense idk your call",
)

col1, col2 = st.columns([1, 3])
with col1:
    analyze_clicked = st.button("Analyze Clarity", type="primary", use_container_width=True)
with col2:
    if not api_key:
        st.info("Enter your Anthropic API key in the sidebar to get started.", icon="🔑")

# --- Run analysis ---------------------------------------------------------
if analyze_clicked:
    if not message.strip():
        st.warning("Please enter a message first.")
    elif not api_key:
        st.error("A Groq API key is required. Add it in the sidebar.")
    else:
        with st.spinner("Analyzing clarity..."):
            result = analyze_message(message, api_key=api_key)

        if result.raw_error:
            st.error(f"Something went wrong: {result.raw_error}")
        else:
            st.divider()

            # Clarity score
            score = result.clarity_score
            score_color = "🟢" if score >= 8 else "🟡" if score >= 5 else "🔴"
            st.subheader(f"{score_color} Clarity Score: {score}/10")
            st.write(result.summary)

            # Confusing parts
            st.subheader("⚠️ Confusing Parts")
            if result.confusing_parts:
                for part in result.confusing_parts:
                    with st.container(border=True):
                        st.markdown(f"**Excerpt:** _{part.excerpt}_")
                        st.markdown(f"**Issue:** {part.issue}")
            else:
                st.success("No major confusing parts found!")

            # Improved message
            st.subheader("✅ Improved Version")
            st.text_area(
                "Rewritten message",
                value=result.improved_message,
                height=180,
                label_visibility="collapsed",
            )
            st.button(
                "📋 Copy hint: select the text box above and Ctrl/Cmd+A, Ctrl/Cmd+C",
                disabled=True,
                use_container_width=True,
            )

            # Explanation of changes
            st.subheader("📝 What Changed & Why")
            if result.changes_explained:
                for change in result.changes_explained:
                    st.markdown(f"- **{change.change}** — {change.reason}")
            else:
                st.write("No changes were necessary.")

st.divider()
st.caption(
    "Built for a hackathon MVP • Streamlit + Groq (openai/gpt-oss-120b) • "
    "Set `GROQ_API_KEY` in Streamlit secrets for deployment."
)
