import streamlit as st
import zipfile
import re
import os
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from io import BytesIO
from collections import Counter
import random

# --- Preprocessing ---
def extract_text(lines, include_emojis=False):
    messages = []
    emoji_pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"      # symbols & pictographs
        u"\U0001F680-\U0001F6FF"      # transport
        u"\U0001F1E0-\U0001F1FF"      # flags
        "]", flags=re.UNICODE
    )

    for line in lines:
        if "end-to-end encrypted" in line or '-' not in line:
            continue
        match = re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}\s[APap][Mm]\s-\s.+?:\s(.+)', line)
        if match:
            msg = match.group(1).strip()
            if not include_emojis:
                msg = emoji_pattern.sub('', msg)
            messages.append(msg)
    return messages

# --- Word Frequency Viewer ---
def get_word_freq(messages):
    all_text = ' '.join(messages).lower()
    words = re.findall(r'\b\w+\b', all_text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return Counter(filtered).most_common(20)

# --- Generate Word Cloud Image ---
def create_wordcloud(messages, theme='light', use_freq=False, random_seed=None):
    all_text = ' '.join(messages).lower()
    colors = {
        'light': 'white',
        'dark': '#1c1c1c',
        'pastel': '#fef7f7'
    }
    word_freq = Counter(all_text.split()) if use_freq else None

    wc = WordCloud(
        width=1000,
        height=500,
        background_color=colors.get(theme, 'white'),
        colormap='viridis' if theme == 'dark' else 'plasma',
        stopwords=STOPWORDS,
        random_state=random_seed
    ).generate_from_frequencies(word_freq) if use_freq else WordCloud(
        width=1000,
        height=500,
        background_color=colors.get(theme, 'white'),
        colormap='viridis' if theme == 'dark' else 'plasma',
        stopwords=STOPWORDS,
        random_state=random_seed
    ).generate(all_text)

    return wc

# --- Streamlit App ---
st.set_page_config(page_title="WordStorm ☁️", layout="wide")
st.title("📱 WordStorm — Word Cloud Generator")

st.markdown("Upload your exported WhatsApp `.txt` or `.zip` file and get a visual of your chat's most frequent words.")

uploaded_file = st.file_uploader("Upload .zip or .txt", type=['zip', 'txt'])

theme = st.selectbox("🎨 Choose a Theme", ['light', 'dark', 'pastel'])
include_emojis = st.checkbox("😄 Include Emojis?", value=False)
use_freq = st.checkbox("📊 Frequency Mode (Bigger = More Used)", value=True)
random_seed = st.slider("🔁 Random Seed (Regenerate Layout)", 1, 100, random.randint(1, 100))

if uploaded_file:
    # Handle zip/txt
    if uploaded_file.name.endswith('.zip'):
        with zipfile.ZipFile(uploaded_file) as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            if not txt_files:
                st.error("No .txt file found in ZIP!")
            else:
                with z.open(txt_files[0]) as f:
                    lines = f.read().decode("utf-8").splitlines()
    else:
        lines = uploaded_file.read().decode("utf-8").splitlines()

    if 'lines' in locals():
        msgs = extract_text(lines, include_emojis=include_emojis)

        if not msgs:
            st.warning("!!No valid messages found!!")
        else:
            # Display Word Frequency Table
            with st.expander("Top 20 Words Used"):
                st.table(get_word_freq(msgs))

            # Create word cloud
            wc = create_wordcloud(msgs, theme, use_freq, random_seed)

            st.subheader("Your Word Cloud 🌥️:")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

            # Download
            img_buf = BytesIO()
            wc.to_image().save(img_buf, format='PNG')
            st.download_button(
                label="⬇️ Download Word Cloud as PNG",
                data=img_buf.getvalue(),
                file_name="wordcloud.png",
                mime="image/png"
            )
