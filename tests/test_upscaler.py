"""Tests for app/upscaler.py and automatic <720p AI upscaling in app/media.py."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app import media, subtitles as sub_mod, upscaler


class UpscalerTests(unittest.TestCase):

    def test_helpers_scale_detection_and_fps(self):
        self.assertEqual(upscaler.DEFAULT_MODEL, 'upscayl-lite-4x')
        self.assertAlmostEqual(upscaler.DEFAULT_TEXTURE_PRESERVE, 0.45, places=2)
        self.assertEqual(upscaler.choose_scale(360, 640, 1080, 1920, 'realesr-animevideov3'), 3)
        self.assertEqual(upscaler.choose_scale(720, 1280, 1080, 1920, 'realesr-animevideov3'), 2)
        self.assertEqual(upscaler.choose_scale(360, 640, 1080, 1920, 'realesrgan-x4plus'), 4)
        self.assertEqual(upscaler.choose_scale(360, 640, 1080, 1920, 'upscayl-lite-4x'), 4)
        self.assertEqual(upscaler.choose_scale(360, 640, 1080, 1920, 'high-fidelity-4x'), 4)
        self.assertTrue(upscaler.is_low_res(360, 640))
        self.assertFalse(upscaler.is_low_res(720, 1280))
        self.assertFalse(upscaler.is_low_res(1080, 1920))
        self.assertAlmostEqual(upscaler.parse_fps('24000/1001'), 23.976, places=2)
        self.assertEqual(upscaler.parse_fps('24/1'), 24.0)

    def test_real_360p_upscale_and_media_auto_integration(self):
        if not upscaler.UPSCALER_BIN.is_file() or not media.SUBTITLE_FFMPEG.is_file():
            self.skipTest('Real-ESRGAN runtime or libass FFmpeg not available')

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            low_clip = tmp_path / 'sample_360p.mp4'
            subprocess.run(
                [
                    str(media.SUBTITLE_FFMPEG), '-y',
                    '-f', 'lavfi', '-i', 'testsrc2=s=360x640:r=24:d=0.5',
                    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo:d=0.5',
                    '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                    str(low_clip),
                ],
                check=True,
                capture_output=True,
            )

            out_final = tmp_path / 'bang_ray_360_upscaled_subtitled.mp4'
            with patch.object(sub_mod, 'auto_transcribe_editorial', return_value=[(0.0, 0.45, 'UJI 360P', 'varian tiga')]):
                res = media.assemble_character_video('bang_ray', [low_clip], out_final, upscale='auto')

            self.assertEqual(res['width'], 1080)
            self.assertEqual(res['height'], 1920)
            self.assertEqual(res['upscaled_clips'], 1)
            self.assertEqual(res['upscale_details'][0]['model'], 'upscayl-lite-4x')
            self.assertEqual(res['upscale_details'][0]['source_resolution'], [360, 640])
            self.assertEqual(res['upscale_details'][0]['output_resolution'], [1080, 1920])
            self.assertEqual(res['upscale_details'][0]['scale'], 4)
            self.assertAlmostEqual(res['upscale_details'][0]['texture_preserve'], 0.45, places=2)
            self.assertEqual(res['upscale_details'][0]['frames_processed'], 12)
            self.assertTrue(out_final.is_file())

    def test_720p_skips_ai_upscaler_in_auto_mode(self):
        if not media.SUBTITLE_FFMPEG.is_file():
            self.skipTest('libass FFmpeg not available')

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hd_clip = tmp_path / 'sample_720p.mp4'
            subprocess.run(
                [
                    str(media.SUBTITLE_FFMPEG), '-y',
                    '-f', 'lavfi', '-i', 'color=c=black:s=720x1280:r=24:d=0.4',
                    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo:d=0.4',
                    '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                    str(hd_clip),
                ],
                check=True,
                capture_output=True,
            )
            out_final = tmp_path / 'skip_upscale.mp4'
            with patch.object(sub_mod, 'auto_transcribe_editorial', return_value=[(0.0, 0.35, 'SUDAH', 'tujuh dua nol')]), \
                 patch.object(upscaler, 'upscale_video') as mock_up:
                res = media.assemble_character_video('bang_ray', [hd_clip], out_final, upscale='auto')

            mock_up.assert_not_called()
            self.assertEqual(res['upscaled_clips'], 0)


    def test_ffmpeg_natural_non_ai_upscale_mode(self):
        if not media.SUBTITLE_FFMPEG.is_file():
            self.skipTest('libass FFmpeg not available')

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            low_clip = tmp_path / 'sample_360p.mp4'
            subprocess.run(
                [
                    str(media.SUBTITLE_FFMPEG), '-y',
                    '-f', 'lavfi', '-i', 'testsrc2=s=360x640:r=24:d=0.4',
                    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo:d=0.4',
                    '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                    str(low_clip),
                ],
                check=True,
                capture_output=True,
            )
            out_final = tmp_path / 'bang_ray_ffmpeg_natural.mp4'
            with patch.object(sub_mod, 'auto_transcribe_editorial', return_value=[(0.0, 0.35, 'TEKSTUR', 'tetap natural')]):
                res = media.assemble_character_video(
                    'bang_ray', [low_clip], out_final, upscale='auto', upscale_model='ffmpeg-natural'
                )
            self.assertEqual(res['upscaled_clips'], 1)
            self.assertEqual(res['upscale_details'][0]['model'], 'ffmpeg-natural')
            self.assertEqual(res['upscale_details'][0]['output_resolution'], [1080, 1920])


if __name__ == '__main__':
    unittest.main()
