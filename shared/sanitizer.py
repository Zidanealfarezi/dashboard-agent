"""
Shared Text Sanitizer - Strict No-Emoji Enforcement
Memastikan seluruh caption dan teks publikasi bebas dari emoji atau emotikon.
"""
import re

EMOJI_PATTERN = re.compile(
    "[\U00010000-\U0010ffff]"
    "|[\u2600-\u27bf]"
    "|[\u2300-\u23ff]"
    "|[\u2b50-\u2b55]"
    "|[\ufe00-\ufe0f]"
    "|[\u200d]"
    "|[\u20e3]",
    flags=re.UNICODE
)

def clean_emojis(text: str) -> str:
    """Menghapus seluruh emoji dan merapikan spasi berlebih."""
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub("", text)
    # Rapikan spasi ganda
    cleaned = re.sub(r"  +", " ", cleaned).strip()
    return cleaned

def has_emojis(text: str) -> bool:
    """Memeriksa apakah teks mengandung emoji."""
    return bool(EMOJI_PATTERN.search(text))
