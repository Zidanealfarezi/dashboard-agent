"""Local AI & texture-preserving video upscaler powered by Real-ESRGAN-ncnn-vulkan + FFmpeg."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time

from app import media

ROOT = Path(__file__).resolve().parents[1]
UPSCALER_BIN = ROOT / 'tools/realesrgan-runtime/realesrgan-ncnn-vulkan'
UPSCALER_MODELS = ROOT / 'tools/realesrgan-runtime/models'
DEFAULT_MODEL = 'upscayl-lite-4x'
DEFAULT_TEXTURE_PRESERVE = 0.45
FOUR_X_MODELS = {
    'realesrgan-x4plus',
    'realesrgan-x4plus-anime',
    'upscayl-lite-4x',
    'high-fidelity-4x',
    'ultrasharp-4x',
}
ALLOWED_MODELS = {'ffmpeg-natural', 'realesr-animevideov3'} | FOUR_X_MODELS


def parse_fps(raw_rate: str) -> float:
    """Convert FFmpeg rational frame rate string (e.g. '24000/1001') to float."""
    if not raw_rate or raw_rate == '0/0':
        return 24.0
    if '/' in raw_rate:
        num, den = raw_rate.split('/', 1)
        den_f = float(den)
        return float(num) / den_f if den_f > 0 else 24.0
    val = float(raw_rate)
    return val if val > 0 else 24.0


def choose_scale(in_width: int, in_height: int, target_width: int = 1080, target_height: int = 1920,
                 model: str = DEFAULT_MODEL) -> int:
    """Select an integer ncnn-vulkan scale factor cleanly matching target dimensions."""
    if model in FOUR_X_MODELS:
        return 4
    ratio = max(target_width / max(in_width, 1), target_height / max(in_height, 1))
    needed = math.ceil(ratio - 1e-6)
    return max(2, min(4, needed))


def is_low_res(width: int, height: int) -> bool:
    """Return True when input clip is sub-720p (e.g. Google Flow 360p 360x640)."""
    return min(width, height) < 720


def _upscale_ffmpeg_natural(input_path: Path, output_path: Path, target_width: int, target_height: int,
                            ffmpeg_bin: str) -> None:
    """Pure non-AI Lanczos + Contrast Adaptive Sharpening + micro sensor grain upscale."""
    vf = (
        f'scale={target_width}:{target_height}:flags=lanczos:force_original_aspect_ratio=decrease,'
        f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,setsar=1,'
        f'cas=strength=0.48,unsharp=5:5:0.45:3:3:0.0,noise=c0s=2.5:c0f=t,format=yuv420p'
    )
    with tempfile.TemporaryDirectory(prefix='.upscale-nat-', dir=output_path.parent) as work_dir:
        temporary = Path(work_dir) / 'upscaled.mp4'
        subprocess.run(
            [
                str(ffmpeg_bin), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-i', str(input_path),
                '-vf', vf,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
                '-c:a', 'copy',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                str(temporary),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        os.link(temporary, output_path)


def upscale_video(
    input_video,
    output_video,
    target_width: int = 1080,
    target_height: int = 1920,
    model: str = DEFAULT_MODEL,
    scale: int = None,
    texture_preserve: float = DEFAULT_TEXTURE_PRESERVE,
    threads: str = '2:4:2',
    ffmpeg_bin: str = None,
):
    """Upscale video using Real-ESRGAN ncnn-vulkan (or ffmpeg-natural) with optional anti-plastic texture blend."""
    if model not in ALLOWED_MODELS:
        raise ValueError(f'Model tidak didukung: {model}. Pilih dari: {sorted(ALLOWED_MODELS)}')
    texture_preserve = float(texture_preserve)
    if not 0.0 <= texture_preserve <= 1.0:
        raise ValueError('texture_preserve harus antara 0.0 dan 1.0')

    input_path = Path(input_video).resolve(strict=True)
    output_path = Path(output_video).resolve()
    if output_path.exists():
        raise ValueError('Output already exists; create a new version')

    if ffmpeg_bin is None:
        ffmpeg_bin = str(media.SUBTITLE_FFMPEG) if media.SUBTITLE_FFMPEG.is_file() else str(media.BIN / 'ffmpeg')

    info = media.probe(input_path)
    video_stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
    if video_stream is None:
        raise ValueError('Input must contain a video stream')

    in_w = int(video_stream['width'])
    in_h = int(video_stream['height'])
    fps_raw = video_stream.get('avg_frame_rate') or video_stream.get('r_frame_rate') or '24/1'
    fps = parse_fps(fps_raw)

    t0 = time.monotonic()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if model == 'ffmpeg-natural':
        _upscale_ffmpeg_natural(input_path, output_path, target_width, target_height, str(ffmpeg_bin))
        elapsed = round(time.monotonic() - t0, 2)
        out_info = media.probe(output_path)
        out_video = next(s for s in out_info['streams'] if s['codec_type'] == 'video')
        return {
            'path': str(output_path),
            'source_resolution': [in_w, in_h],
            'output_resolution': [int(out_video['width']), int(out_video['height'])],
            'duration_seconds': float(out_info['format']['duration']),
            'fps': round(fps, 3),
            'model': model,
            'scale': None,
            'texture_preserve': 1.0,
            'frames_processed': int(video_stream.get('nb_frames') or round(float(out_info['format']['duration']) * fps)),
            'elapsed_seconds': elapsed,
        }

    if not UPSCALER_BIN.is_file() or not UPSCALER_MODELS.is_dir():
        raise RuntimeError('Runtime Real-ESRGAN ncnn-vulkan belum tersedia di tools/realesrgan-runtime/')

    chosen_scale = choose_scale(in_w, in_h, target_width, target_height, model) if scale is None else int(scale)

    with tempfile.TemporaryDirectory(prefix='.upscale-', dir=output_path.parent) as work:
        work_dir = Path(work)
        in_dir = work_dir / 'frames_in'
        out_dir = work_dir / 'frames_out'
        in_dir.mkdir()
        out_dir.mkdir()

        # 1. Extract source frames without dropping or duplicating
        subprocess.run(
            [
                str(ffmpeg_bin), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-i', str(input_path),
                '-fps_mode', 'passthrough', '-qscale:v', '2',
                str(in_dir / 'frame_%06d.jpg'),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        in_frames = sorted(in_dir.glob('frame_*.jpg'))
        if not in_frames:
            raise RuntimeError('Gagal mengekstrak frame dari video input')

        # 2. Batch upscale frames via Real-ESRGAN ncnn-vulkan (Vulkan/MoltenVK GPU)
        subprocess.run(
            [
                str(UPSCALER_BIN),
                '-i', str(in_dir),
                '-o', str(out_dir),
                '-m', str(UPSCALER_MODELS),
                '-n', model,
                '-s', str(chosen_scale),
                '-f', 'jpg',
                '-j', threads,
            ],
            check=True,
            capture_output=True,
            timeout=1200,
        )
        out_frames = sorted(out_dir.glob('frame_*.jpg'))
        if len(out_frames) != len(in_frames):
            raise RuntimeError(
                f'Jumlah frame output ({len(out_frames)}) tidak sama dengan input ({len(in_frames)})'
            )

        # 3. Mux upscaled frames, optionally blending Lanczos CAS + micro grain to prevent over-smoothing
        temporary = work_dir / 'upscaled.mp4'
        cmd = [
            str(ffmpeg_bin), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
            '-framerate', f'{fps:.6f}',
            '-i', str(out_dir / 'frame_%06d.jpg'),
            '-i', str(input_path),
        ]
        if texture_preserve > 0.0:
            w_ai = 1.0 - texture_preserve
            fc = (
                f'[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,'
                f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[ai];'
                f'[1:v]scale={target_width}:{target_height}:flags=lanczos:force_original_aspect_ratio=decrease,'
                f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,setsar=1,cas=strength=0.45,format=yuv420p[nat];'
                f"[ai][nat]mix=inputs=2:weights='{w_ai:.2f} {texture_preserve:.2f}':duration=shortest,"
                f'cas=strength=0.20,noise=c0s=2.5:c0f=t,format=yuv420p[v]'
            )
            cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '1:a:0?']
        else:
            vf = (
                f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,'
                f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p'
            )
            cmd += ['-map', '0:v:0', '-map', '1:a:0?', '-vf', vf]

        cmd += [
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-c:a', 'copy',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
            str(temporary),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        os.link(temporary, output_path)

    elapsed = round(time.monotonic() - t0, 2)
    out_info = media.probe(output_path)
    out_video = next(s for s in out_info['streams'] if s['codec_type'] == 'video')
    return {
        'path': str(output_path),
        'source_resolution': [in_w, in_h],
        'output_resolution': [int(out_video['width']), int(out_video['height'])],
        'duration_seconds': float(out_info['format']['duration']),
        'fps': round(fps, 3),
        'model': model,
        'scale': chosen_scale,
        'texture_preserve': texture_preserve,
        'frames_processed': len(out_frames),
        'elapsed_seconds': elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Path ke video sumber (mis. 360p)')
    parser.add_argument('--output', type=Path, required=True, help='Path video output ter-upscale')
    parser.add_argument('--model', default=DEFAULT_MODEL, choices=sorted(ALLOWED_MODELS), help='Model upscaler')
    parser.add_argument('--scale', type=int, help='Faktor skala (2, 3, atau 4)')
    parser.add_argument('--texture-preserve', type=float, default=DEFAULT_TEXTURE_PRESERVE,
                        help='Bobot campuran tekstur asli anti-plastik 0.0-1.0 (default: 0.45)')
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--height', type=int, default=1920)
    args = parser.parse_args()
    result = upscale_video(
        args.input,
        args.output,
        target_width=args.width,
        target_height=args.height,
        model=args.model,
        scale=args.scale,
        texture_preserve=args.texture_preserve,
    )
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
