"""
test_isk_subtitles_guard.py
Unit tests enforcing the unified video post-production pipeline across ISK, Dinda, and Bang Ray:
1. app/subtitles.py enforces editorial_tiktok as default across isk, dinda, and bang_ray
   (Ray_Top #FFFFFF Helvetica Neue Bold 44 ALL CAPS y=1502 + Ray_Bot #E8FF3B Times New Roman 126 ScaleX=72 lowercase y=1595)
   while keeping legacy ISK_Yellow (#FFE600 / &H0000E6FF, MarginV=300) available as explicit preset.
2. config/project.json, character profiles, and pipeline_spec.json files all mandate the unified
   Varian 3 Hybrid Foto-Realistik upscaler (upscayl-lite-4x, texture_preserve=0.45, auto) + editorial_tiktok subtitles.
3. app/media.assemble_character_video applies identical editorial_tiktok ASS subtitle burning by default for isk, dinda, and bang_ray.
4. scripts/execute_isk_flow_generation.js enforces legacy subtitle guard (--margin-v 300).
"""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestUnifiedSubtitlesGuard(unittest.TestCase):

    def test_ass_template_and_unified_style(self):
        """Verify app/subtitles.py ASS template constants and unified editorial_tiktok + legacy preset."""
        from app.subtitles import (
            ASS_HEADER_TEMPLATE,
            COMPOUND_BRANDS,
            EDITORIAL_ASS_HEADER_TEMPLATE,
            UNIFIED_SUBTITLE_STYLE,
            generate_ass_script,
            generate_editorial_ass_script,
        )

        self.assertEqual(UNIFIED_SUBTITLE_STYLE["default_style"], "editorial_tiktok")
        self.assertEqual(set(UNIFIED_SUBTITLE_STYLE["characters"]), {"isk", "dinda", "bang_ray", "pak_vincent"})

        self.assertIn("PlayResX: 1080", EDITORIAL_ASS_HEADER_TEMPLATE)
        self.assertIn("PlayResY: 1920", EDITORIAL_ASS_HEADER_TEMPLATE)
        self.assertIn("Style: Ray_Top,Helvetica Neue,44,&H00FFFFFF", EDITORIAL_ASS_HEADER_TEMPLATE)
        self.assertIn("Style: Ray_Bot,Times New Roman,126,&H003BFFE8", EDITORIAL_ASS_HEADER_TEMPLATE)

        self.assertIn("&H0000E6FF", ASS_HEADER_TEMPLATE)
        self.assertIn("PlayResX: 1080", ASS_HEADER_TEMPLATE)
        self.assertIn("PlayResY: 1920", ASS_HEADER_TEMPLATE)
        self.assertIn("Paku Cap Keris", COMPOUND_BRANDS)
        self.assertIn("PT Intan Suar Kartika", COMPOUND_BRANDS)

        with tempfile.TemporaryDirectory() as tmp:
            ed_file = Path(tmp) / "editorial.ass"
            generate_editorial_ass_script([(0.0, 1.5, "BIAR KERAMIK", "nggak kopong")], ed_file)
            ed_content = ed_file.read_text(encoding="utf-8")
            self.assertIn("Style: Ray_Top,Helvetica Neue,44,&H00FFFFFF", ed_content)
            self.assertIn("Style: Ray_Bot,Times New Roman,126,&H003BFFE8", ed_content)
            self.assertIn(r"\pos(540,1502)", ed_content)
            self.assertIn(r"\pos(540,1595)", ed_content)

            ass_file = Path(tmp) / "sample_legacy.ass"
            generate_ass_script([(0.0, 1.2, "Halo warga"), (1.2, 2.4, "Banda Aceh")], ass_file)
            content = ass_file.read_text(encoding="utf-8")
            self.assertIn("Style: ISK_Yellow,Arial,68,&H0000E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,10,3,2,60,60,300,1", content)
            self.assertIn(r"{\t(0,70,\fscx106\fscy106)\t(70,140,\fscx100\fscy100)}Halo warga", content)

    def test_phrase_grouping_preserves_brands_without_false_positives(self):
        """Verify 2-3 word grouping works for Dinda/Bang Ray without 'pt' substring false matches."""
        from app.subtitles import group_words_to_phrases

        dinda_words = [
            {"start": 0.0, "end": 0.4, "text": "Cipta"},
            {"start": 0.4, "end": 0.7, "text": "rasa"},
            {"start": 0.7, "end": 1.1, "text": "pempek"},
            {"start": 1.1, "end": 1.5, "text": "bulan"},
            {"start": 1.5, "end": 1.9, "text": "September"},
        ]
        dinda_events = group_words_to_phrases(dinda_words)
        dinda_texts = [t for _, _, t in dinda_events]
        self.assertEqual(dinda_texts, ["Cipta rasa pempek", "bulan September"])

        isk_words = [
            {"start": 0.0, "end": 0.3, "text": "Pakai"},
            {"start": 0.3, "end": 0.6, "text": "paku"},
            {"start": 0.6, "end": 0.9, "text": "cap"},
            {"start": 0.9, "end": 1.2, "text": "keris"},
            {"start": 1.2, "end": 1.5, "text": "dari"},
            {"start": 1.5, "end": 1.7, "text": "PT"},
            {"start": 1.7, "end": 2.0, "text": "Intan"},
            {"start": 2.0, "end": 2.2, "text": "Suar"},
            {"start": 2.2, "end": 2.5, "text": "Kartika."},
        ]
        isk_events = group_words_to_phrases(isk_words)
        self.assertIn("Paku Cap Keris", [t for _, _, t in isk_events])
        self.assertIn("PT Intan Suar Kartika", [t for _, _, t in isk_events])

        bang_ray_words = [
            {"start": 0.0, "end": 0.4, "text": "Pakai"},
            {"start": 0.4, "end": 0.7, "text": "paku"},
            {"start": 0.7, "end": 1.0, "text": "beton"},
            {"start": 1.0, "end": 1.3, "text": "dan"},
            {"start": 1.3, "end": 1.6, "text": "kawat"},
            {"start": 1.6, "end": 1.9, "text": "duri"},
            {"start": 1.9, "end": 2.2, "text": "biasa."},
        ]
        ray_events = group_words_to_phrases(bang_ray_words)
        self.assertNotIn("Kawat Duri Diamond", [t for _, _, t in ray_events])
        self.assertEqual([t for _, _, t in ray_events], ["Pakai paku beton", "dan kawat duri", "biasa."])

    def test_configs_profiles_and_specs_unified_for_all_three_characters(self):
        """Verify global config, profiles, and pipeline specs mandate Varian 3 + editorial_tiktok for isk, dinda, and bang_ray."""
        project = json.loads((PROJECT_ROOT / "config/project.json").read_text(encoding="utf-8"))
        sub_policy = project["video_policy"]["subtitle_policy"]
        self.assertTrue(sub_policy["mandatory"])
        self.assertEqual(set(sub_policy["characters"]), {"isk", "dinda", "bang_ray", "pak_vincent"})
        self.assertEqual(sub_policy["default_style"], "editorial_tiktok")
        self.assertTrue(sub_policy["comma_free"])
        self.assertEqual(sub_policy["top_color"], "#FFFFFF")
        self.assertEqual(sub_policy["bot_color"], "#E8FF3B")

        video_policy = project["video_policy"]
        self.assertEqual(video_policy["flow_input_resolution"], "360p")
        self.assertEqual(video_policy["max_duration_by_character"]["bang_ray"], 30)
        self.assertEqual(video_policy["max_duration_by_character"]["dinda"], 20)
        self.assertEqual(video_policy["max_duration_by_character"]["isk"], 20)
        self.assertEqual(video_policy["max_duration_by_character"]["pak_vincent"], 20)

        up_policy = project["video_policy"]["upscale_policy"]
        self.assertTrue(up_policy["mandatory_for_sub_720p"])
        self.assertEqual(up_policy["raw_input_resolution"], "360p")
        self.assertEqual(up_policy["model"], "upscayl-lite-4x")
        self.assertEqual(up_policy["texture_preserve"], 0.45)
        self.assertEqual(up_policy["mode"], "auto")

        for cid in ("isk", "dinda", "bang_ray"):
            profile = json.loads((PROJECT_ROOT / f"characters/{cid}/profile.json").read_text(encoding="utf-8"))
            self.assertIn("editorial_tiktok", profile.get("subtitle_policy", ""), f"{cid} profile missing editorial_tiktok")
            self.assertIn("upscayl-lite-4x", profile.get("upscale_policy", ""), f"{cid} profile missing upscayl-lite-4x")
            self.assertIn("upscayl-lite-4x", profile.get("production_formula", ""), f"{cid} formula missing upscayl-lite-4x")
            self.assertIn("editorial_tiktok", profile.get("production_formula", ""), f"{cid} formula missing editorial_tiktok")

            spec = json.loads((PROJECT_ROOT / f"characters/{cid}/templates/pipeline_spec.json").read_text(encoding="utf-8"))
            self.assertIn("editorial_tiktok", spec.get("subtitles", ""), f"{cid} pipeline_spec missing editorial_tiktok subtitles")
            self.assertIn("upscayl-lite-4x", spec.get("upscaler", ""), f"{cid} pipeline_spec missing upscayl-lite-4x upscaler")
            self.assertIn("app/subtitles.py", spec.get("subtitles", ""), f"{cid} pipeline_spec must reference app/subtitles.py")

        dinda_spec_text = (PROJECT_ROOT / "characters/dinda/templates/pipeline_spec.json").read_text(encoding="utf-8")
        self.assertNotIn("tanpa burned-in subtitle", dinda_spec_text)

    def test_assemble_character_video_burns_identical_subtitles_for_all_three(self):
        """Verify app/media.assemble_character_video uses unified editorial_tiktok subtitles by default on all 3 characters, and supports legacy isk_yellow."""
        from app import media, subtitles as sub_mod

        if not media.SUBTITLE_FFMPEG.is_file():
            self.skipTest("FFmpeg with libass not available")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_clip = tmp_path / "raw_720p.mp4"
            subprocess.run(
                [
                    str(media.SUBTITLE_FFMPEG), "-y",
                    "-f", "lavfi", "-i", "color=c=blue:s=720x1280:r=24:d=1.2",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=1.2",
                    "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    str(raw_clip),
                ],
                check=True, capture_output=True,
            )

            editorial_events = [(0.1, 0.6, "TES SUBTITLE", "seragam baru"), (0.6, 1.1, "BUAT SEMUA", "tiga akun")]
            with patch.object(sub_mod, "auto_transcribe_editorial", return_value=editorial_events) as mock_editorial:
                for cid in ("dinda", "bang_ray", "isk"):
                    out_file = tmp_path / f"{cid}_final.mp4"
                    outro_arg = False if cid == "isk" else None
                    res = media.assemble_character_video(cid, [raw_clip], out_file, outro=outro_arg)
                    self.assertEqual(res["character_id"], cid)
                    self.assertEqual(res["width"], 1080)
                    self.assertEqual(res["height"], 1920)
                    self.assertTrue(out_file.is_file())
                    ass_text = (tmp_path / f"{cid}_final_subtitles.ass").read_text(encoding="utf-8")
                    self.assertIn("Style: Ray_Top,Helvetica Neue,44,&H00FFFFFF", ass_text)
                    self.assertIn("Style: Ray_Bot,Times New Roman,126,&H003BFFE8", ass_text)

                self.assertEqual(mock_editorial.call_count, 3)

            legacy_out = tmp_path / "bang_ray_legacy.mp4"
            with patch.object(sub_mod, "auto_transcribe_and_group", return_value=[(0.1, 0.9, "Tes legacy")]) as mock_legacy:
                legacy_res = media.assemble_character_video("bang_ray", [raw_clip], legacy_out, subtitle_style="isk_yellow")
            self.assertEqual(mock_legacy.call_count, 1)
            self.assertEqual(legacy_res["subtitle_margin_v"], 300)
            legacy_ass = (tmp_path / "bang_ray_legacy_subtitles.ass").read_text(encoding="utf-8")
            self.assertIn("Style: ISK_Yellow,Arial,68,&H0000E6FF", legacy_ass)

    def test_pipeline_script_has_guard(self):
        """Verify scripts/execute_isk_flow_generation.js enforces subtitle generation with MarginV=300."""
        script_path = PROJECT_ROOT / "scripts" / "execute_isk_flow_generation.js"
        self.assertTrue(script_path.exists(), "execute_isk_flow_generation.js must exist")

        content = script_path.read_text(encoding="utf-8")
        self.assertIn("subtitles_kinetic_yellow.ass", content)
        self.assertIn("app/subtitles.py", content)
        self.assertIn("--margin-v 300", content)
        self.assertIn("PIPELINE VIOLATION", content)

    def test_editorial_tiktok_two_tier_subtitle_generation(self):
        """Verify two-tier editorial TikTok subtitle grouping, ASS rendering, and media assembly."""
        from app import media, subtitles as sub_mod

        words = [
            {"start": 0.0, "end": 0.4, "text": "Dulu"},
            {"start": 0.4, "end": 0.8, "text": "aku"},
            {"start": 0.8, "end": 1.2, "text": "setiap"},
            {"start": 1.2, "end": 1.6, "text": "hari"},
            {"start": 2.1, "end": 2.4, "text": "pakai"},
            {"start": 2.4, "end": 2.8, "text": "roskam"},
            {"start": 2.8, "end": 3.2, "text": "bergigi"},
        ]
        events = sub_mod.group_words_for_editorial(words)
        self.assertEqual(
            events,
            [
                (0.0, 1.6, "DULU AKU", "setiap hari"),
                (2.1, 3.2, "PAKAI", "roskam bergigi"),
            ],
        )

        if not media.SUBTITLE_FFMPEG.is_file():
            self.skipTest("FFmpeg with libass not available")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_clip = tmp_path / "raw_720p.mp4"
            subprocess.run(
                [
                    str(media.SUBTITLE_FFMPEG), "-y",
                    "-f", "lavfi", "-i", "color=c=gray:s=720x1280:r=24:d=1.0",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=1.0",
                    "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    str(raw_clip),
                ],
                check=True, capture_output=True,
            )
            out_file = tmp_path / "bang_ray_editorial.mp4"
            with patch.object(sub_mod, "auto_transcribe_editorial", return_value=[(0.1, 0.9, "BIAR KERAMIK", "nggak kopong")]):
                res = media.assemble_character_video("bang_ray", [raw_clip], out_file, subtitle_style="editorial_tiktok")
            self.assertTrue(out_file.is_file())
            self.assertEqual(res["width"], 1080)
            ass_text = (tmp_path / "bang_ray_editorial_subtitles.ass").read_text(encoding="utf-8")
            self.assertIn("Style: Ray_Top,Helvetica Neue", ass_text)
            self.assertIn("Style: Ray_Bot,Times New Roman", ass_text)
            self.assertIn("BIAR KERAMIK", ass_text)
            self.assertIn("nggak kopong", ass_text)

    def test_subtitles_strip_all_commas_while_preserving_clause_splits(self):
        """Ensure commas split natural speech clauses cleanly without leaving any comma in rendered subtitles."""
        from app import subtitles as sub_mod

        raw = [
            {"start": 0.0, "end": 0.4, "text": "Rakan,"},
            {"start": 0.4, "end": 0.7, "text": "biar"},
            {"start": 0.7, "end": 1.1, "text": "keramik,"},
            {"start": 1.1, "end": 1.5, "text": "nggak"},
            {"start": 1.5, "end": 1.9, "text": "kopong,"},
        ]
        ed_events = sub_mod.group_words_for_editorial(raw)
        self.assertEqual(
            ed_events,
            [
                (0.0, 0.4, "", "rakan"),
                (0.4, 1.1, "BIAR", "keramik"),
                (1.1, 1.9, "NGGAK", "kopong"),
            ],
        )
        for _, _, top_txt, bot_txt in ed_events:
            self.assertNotIn(",", top_txt)
            self.assertNotIn(",", bot_txt)

        legacy_events = sub_mod.group_words_to_phrases(raw)
        self.assertEqual([t for _, _, t in legacy_events], ["Rakan", "biar keramik", "nggak kopong"])

        with tempfile.TemporaryDirectory() as tmp:
            ed_ass = Path(tmp) / "ed_no_comma.ass"
            sub_mod.generate_editorial_ass_script([(0.0, 1.0, "RAKAN, BIAR", "kuat, rapi")], ed_ass)
            ed_dialogues = [l.rsplit("}", 1)[-1] for l in ed_ass.read_text(encoding="utf-8").splitlines() if l.startswith("Dialogue:")]
            self.assertEqual(ed_dialogues, ["RAKAN BIAR", "kuat rapi"])
            self.assertTrue(all("," not in d for d in ed_dialogues), f"Found comma in editorial dialogues: {ed_dialogues}")

            leg_ass = Path(tmp) / "leg_no_comma.ass"
            sub_mod.generate_ass_script([(0.0, 1.0, "Rakan, pakai, ini")], leg_ass)
            leg_dialogues = [l.rsplit("}", 1)[-1] for l in leg_ass.read_text(encoding="utf-8").splitlines() if l.startswith("Dialogue:")]
            self.assertEqual(leg_dialogues, ["Rakan pakai ini"])
            self.assertTrue(all("," not in d for d in leg_dialogues), f"Found comma in legacy dialogues: {leg_dialogues}")


if __name__ == "__main__":
    unittest.main()
