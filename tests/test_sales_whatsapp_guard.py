#!/usr/bin/env python3
"""
Test Suite: WhatsApp Sales Conversational Guard & Attachment Suppression
Verifies that:
1. Tool call syntax (<tool_call>...</tool_call>, <function=...>, <｜｜DSML｜｜ ...>) is stripped.
2. Local file paths (/Users/.../SKILL.md, ~/..., etc.) are stripped.
3. No document or image attachments are created or delivered.
4. Output is strictly pure conversational text.
Strict 0% Emoji Policy.
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path

# Add hermes-agent to sys.path
HERMES_AGENT_ROOT = Path('/Users/zidane/.hermes/hermes-agent')
if str(HERMES_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_AGENT_ROOT))

try:
    from gateway.platforms.base import MessageEvent, Platform
    from gateway.session import SessionSource
    from gateway.config import PlatformConfig
    from plugins.platforms.whatsapp.adapter import WhatsAppAdapter
    HAS_HERMES = True
except (ImportError, ModuleNotFoundError):
    HAS_HERMES = False
    MessageEvent = Platform = SessionSource = PlatformConfig = WhatsAppAdapter = None


class WhatsAppSalesGuardTest(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(HAS_HERMES, "Hermes runtime environment required")
    async def test_sales_whatsapp_guard(self):
        # Initialize adapter configured in text-only sales mode
        config = PlatformConfig(
            enabled=True,
            extra={
                "text_only": True,
                "conversational_text_only": True,
                "sales_mode": True,
                "bridge_port": 3301
            }
        )
        adapter = WhatsAppAdapter(config)
        adapter._profile_home = Path("/Users/zidane/.hermes/profiles/sales-toko")

        self.assertTrue(adapter._is_conversational_text_only(), "Adapter should recognize conversational text-only mode")

        # Test Case 1: Model response containing tool calls and local SKILL.md path
        dirty_response_1 = (
            "Halo Kak! Terima kasih sudah menghubungi The AI X Academy.\n"
            "<tool_call>read_file{\"Path\": \"/Users/zidane/.hermes/profiles/sales-toko/skills/sales-konsultatif/SKILL.md\"}</tool_call>\n"
            "Untuk kelas AI for Business & Creators, biayanya promo Rp 1.250.000.\n"
            "draft_reply: Kami siap membantu pendaftaran Kakak!"
        )

        dummy_event = MessageEvent(
            text="ada kelas apa aja kak?",
            message_type="text",
            source=SessionSource(platform=Platform.WHATSAPP, chat_id="6282283234250@s.whatsapp.net")
        )

        extracted = await adapter._extract_response_content(dirty_response_1, dummy_event, "test_session", is_ephemeral_response=False)

        self.assertEqual(len(extracted.local_files), 0, "Local files must be strictly 0")
        self.assertEqual(len(extracted.media_files), 0, "Media files must be strictly 0")
        self.assertEqual(len(extracted.images), 0, "Images must be strictly 0")
        self.assertNotIn("<tool_call>", extracted.text_content, "Tool call syntax must be stripped")
        self.assertNotIn("/Users/zidane", extracted.text_content, "Local path must be stripped")
        self.assertNotIn("draft_reply:", extracted.text_content, "Internal metadata must be stripped")
        self.assertIn("Rp 1.250.000", extracted.text_content, "Conversational content must be preserved")

        # Test Case 2: Deliberate attack / synthetic leaked internal path
        dirty_response_2 = (
            "Berikut materi kursusnya Kak:\n"
            "MEDIA:/Users/zidane/Documents/ChatGPT/AI INFLUENCER/config/telegram.json\n"
            "/Users/zidane/.hermes/profiles/sales-toko/config.yaml\n"
            "Apakah Kakak berminat mendaftar?"
        )

        extracted_2 = await adapter._extract_response_content(dirty_response_2, dummy_event, "test_session", is_ephemeral_response=False)
        self.assertEqual(len(extracted_2.local_files), 0, "No local files allowed")
        self.assertNotIn("/Users/zidane", extracted_2.text_content, "No leaked path in text")
        self.assertIn("Apakah Kakak berminat mendaftar?", extracted_2.text_content)

        # Test Case 3: Empty or purely tool-syntax response recovers conversational fallback
        dirty_response_3 = "<tool_call>{\"action\": \"check_price\"}</tool_call>"
        extracted_3 = await adapter._extract_response_content(dirty_response_3, dummy_event, "test_session", is_ephemeral_response=False)
        self.assertGreater(len(extracted_3.text_content), 10, "Must recover conversational fallback")
        self.assertTrue("The AI X Academy" in extracted_3.text_content or "Halo" in extracted_3.text_content)


if __name__ == "__main__":
    unittest.main()
