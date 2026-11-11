"""Local video editing with FFmpeg, including subtitles and a brand closing."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / 'tools/ffmpeg-runtime'
SUBTITLE_FFMPEG = Path.home() / '.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg'
BRAND_BODY_MAX_SECONDS = 20
BRAND_OUTRO_SECONDS = 4
SUBTITLE_STYLE = (
    'PlayResX=720,PlayResY=1280,FontName=Arial,FontSize=42,Bold=-1,'
    'PrimaryColour=&H00FFFFFF,OutlineColour=&H500C1018,'
    'BorderStyle=3,Outline=8,Shadow=0,Alignment=2,MarginL=86,MarginR=86,MarginV=220'
)


def probe(path, show_packets=False):
    args = [str(BIN / 'ffprobe'), '-v', 'error', '-show_streams', '-show_format', '-of', 'json']
    if show_packets:
        args += ['-show_packets']
    result = subprocess.run(args + [str(path)],
                            check=True, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)


def render(clips, output, duration=None, width=720, height=1280):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output already exists; create a new version')
    if not clips or (duration is not None and duration <= 0):
        raise ValueError('At least one input and a positive trim duration are required')
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise ValueError('Even positive output dimensions are required')
    clips = [Path(p).resolve(strict=True) for p in clips]
    if any(not any(s['codec_type'] == 'video' for s in probe(p)['streams']) for p in clips):
        raise ValueError('Every input must contain video')
    output.parent.mkdir(parents=True, exist_ok=True)
    args = [str(BIN / 'ffmpeg'), '-nostdin', '-hide_banner', '-loglevel', 'error', '-n']
    for clip in clips:
        args += ['-i', str(clip)]
    filters = [f'[{i}:v:0]scale={width}:{height}:force_original_aspect_ratio=decrease,'
               f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,'
               f'format=yuv420p,setpts=PTS-STARTPTS[v{i}]' for i in range(len(clips))]
    filters.append(''.join(f'[v{i}]' for i in range(len(clips))) +
                   f'concat=n={len(clips)}:v=1:a=0[out]')
    args += ['-filter_complex', ';'.join(filters), '-map', '[out]', '-an']
    if duration is not None:
        args += ['-t', str(duration)]
    args += ['-c:v', 'h264_videotoolbox', '-b:v', '4M', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    # Render to a temporary sibling and commit only when decoding/probing succeeds.
    with tempfile.TemporaryDirectory(prefix='.render-', dir=output.parent) as work:
        temporary = Path(work) / 'render.mp4'
        subprocess.run(args + [str(temporary)], check=True, capture_output=True, timeout=240)
        info = probe(temporary)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        if (video['width'], video['height']) != (width, height) or float(info['format']['duration']) <= 0:
            raise ValueError('Rendered media failed validation')
        # Hard link is atomic and refuses overwriting an existing final version.
        os.link(temporary, output)
    return {'path': str(output), 'duration_seconds': float(info['format']['duration']),
            'width': width, 'height': height, 'audio_removed': True}


def _clip_duration(info):
    video = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
    raw = (video or {}).get('duration') or info.get('format', {}).get('duration') or 0
    return float(raw)


def assemble_subtitled_video(
    clips,
    output,
    outro=None,
    music_path=None,
    vocal_vol=1.0,
    music_vol=0.15,
    subtitles='auto',
    margin_v=None,
    width=1080,
    height=1920,
    upscale='auto',
    upscale_model=None,
    texture_preserve=None,
    subtitle_style='editorial_tiktok',
):
    """Assemble generative clips with optional Real-ESRGAN AI upscaling (auto for <720p),
    unified ISK kinetic yellow subtitles (#FFE600, MarginV=300), optional background music,
    and optional brand outro.
    """
    from app import subtitles as sub_mod
    from app import upscaler as up_mod

    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output already exists; create a new version')
    if isinstance(clips, (str, Path)):
        clips = [clips]
    clips = [Path(c).resolve(strict=True) for c in clips]
    if not clips:
        raise ValueError('At least one clip is required')
    outro = Path(outro).resolve(strict=True) if outro else None
    music_path = Path(music_path).resolve(strict=True) if music_path else None
    margin_v = sub_mod.UNIFIED_SUBTITLE_STYLE['margin_v'] if margin_v is None else int(margin_v)
    upscale_model = upscale_model or up_mod.DEFAULT_MODEL
    texture_preserve = up_mod.DEFAULT_TEXTURE_PRESERVE if texture_preserve is None else float(texture_preserve)

    ffmpeg_bin = str(SUBTITLE_FFMPEG) if SUBTITLE_FFMPEG.is_file() else str(BIN / 'ffmpeg')
    upscale_reports = []

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.upscale-stage-', dir=output.parent) as up_stage:
        if upscale in ('auto', 'always'):
            staged_clips = []
            for idx, c in enumerate(clips):
                c_info = probe(c)
                v_s = next((s for s in c_info['streams'] if s['codec_type'] == 'video'), None)
                if v_s and (upscale == 'always' or up_mod.is_low_res(int(v_s['width']), int(v_s['height']))):
                    up_path = Path(up_stage) / f'{output.stem}_upscaled_{idx}.mp4'
                    rep = up_mod.upscale_video(
                        c, up_path, target_width=width, target_height=height,
                        model=upscale_model, texture_preserve=texture_preserve, ffmpeg_bin=ffmpeg_bin,
                    )
                    upscale_reports.append(rep)
                    staged_clips.append(up_path)
                else:
                    staged_clips.append(c)
            clips = staged_clips

        # Burn kinetic yellow subtitles AFTER upscaling onto 1080x1920 frames and BEFORE BGM mixing
        if subtitles:
            processed_clips = []
            multi = len(clips) > 1
            for idx, c in enumerate(clips):
                persistent_sub = output.parent / f'{output.stem}_subtitled_clip_{idx}.mp4'
                ass_name = f'{output.stem}_subtitles_{idx}.ass' if multi else f'{output.stem}_subtitles.ass'
                ass_file = output.parent / ass_name
                if subtitles == 'auto' or not Path(subtitles).exists():
                    if subtitle_style == 'editorial_tiktok':
                        events = sub_mod.auto_transcribe_editorial(c)
                        sub_mod.generate_editorial_ass_script(events, ass_file)
                    else:
                        events = sub_mod.auto_transcribe_and_group(c)
                        sub_mod.generate_ass_script(events, ass_file, margin_v=margin_v)
                else:
                    shutil.copyfile(Path(subtitles), ass_file)
                sub_mod.burn_subtitles_to_video(
                    c, ass_file, persistent_sub, ffmpeg_bin=ffmpeg_bin, width=width, height=height
                )
                processed_clips.append(persistent_sub)
            clips = processed_clips

        inputs = []
        filters = []
        body_count = len(clips)
        body_dur = 0.0

        all_inputs = [*clips, outro] if outro else list(clips)
        for i, p in enumerate(all_inputs):
            inputs += ['-i', str(p)]
            filters.append(
                f'[{i}:v:0]scale={width}:{height}:force_original_aspect_ratio=decrease,'
                f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]'
            )
            info = probe(p)
            if i < body_count:
                body_dur += _clip_duration(info)
            has_audio = any(s['codec_type'] == 'audio' for s in info['streams'])
            if has_audio:
                filters.append(f'[{i}:a:0]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]')
            else:
                filters.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={max(_clip_duration(info), 0.1):.3f}[a{i}]')

        n = len(all_inputs)
        v_concat = ''.join(f'[v{i}]' for i in range(n))
        filters.append(f'{v_concat}concat=n={n}:v=1:a=0[video]')

        if music_path:
            music_idx = n
            inputs += ['-stream_loop', '-1', '-i', str(music_path)]
            body_a_concat = ''.join(f'[a{i}]' for i in range(body_count))
            filters.append(f'{body_a_concat}concat=n={body_count}:v=0:a=1[body_vocal_raw]')
            fade_in = min(0.5, max(0.05, body_dur / 4.0)) if body_dur > 0 else 0.1
            fade_out = min(1.5, max(0.05, body_dur / 3.0)) if body_dur > 0 else 0.1
            fade_start = max(0.0, body_dur - fade_out)
            filters.append(f'[body_vocal_raw]volume={vocal_vol}[vocal]')
            filters.append(
                f'[{music_idx}:a:0]aformat=sample_rates=48000:channel_layouts=stereo,'
                f'atrim=duration={max(body_dur, 0.1):.3f},asetpts=PTS-STARTPTS,'
                f'volume={music_vol},afade=t=in:st=0:d={fade_in:.3f},'
                f'afade=t=out:st={fade_start:.3f}:d={fade_out:.3f}[bgm]'
            )
            filters.append('[vocal][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[body_a]')
            if outro:
                filters.append(f'[body_a][a{body_count}]concat=n=2:v=0:a=1[audio]')
            else:
                filters.append('[body_a]anull[audio]')
        else:
            a_concat = ''.join(f'[a{i}]' for i in range(n))
            filters.append(f'{a_concat}concat=n={n}:v=0:a=1[audio]')

        args = [ffmpeg_bin, '-nostdin', '-hide_banner', '-loglevel', 'error',
                *inputs, '-filter_complex', ';'.join(filters),
                '-map', '[video]', '-map', '[audio]',
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
                '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']

        with tempfile.TemporaryDirectory(prefix='.render-subtitled-', dir=output.parent) as work:
            temporary = Path(work) / 'render.mp4'
            subprocess.run(args + [str(temporary)], cwd=work, check=True, capture_output=True, timeout=300)
            os.link(temporary, output)

    info = probe(output)
    dur = float(info['format']['duration'])
    font_size_used = (
        sub_mod.UNIFIED_SUBTITLE_STYLE['bottom_style']['font_size']
        if subtitle_style == 'editorial_tiktok'
        else sub_mod.UNIFIED_SUBTITLE_STYLE['legacy_preset']['font_size']
    )
    return {
        'path': str(output),
        'duration_seconds': dur,
        'width': width,
        'height': height,
        'subtitle_style': subtitle_style,
        'subtitle_margin_v': margin_v,
        'subtitle_font_size': font_size_used,
        'upscaled_clips': len(upscale_reports),
        'upscale_details': upscale_reports,
    }


def assemble_isk_video(clips, outro, output, subtitles='auto', width=1080, height=1920):
    """Cleanly assemble AI generative clips, burn kinetic yellow subtitles, and append the product-specific ISK brand outro.
    Enforces kinetic yellow hardsub (#FFE600, MarginV=300) and brand outro.
    """
    return assemble_subtitled_video(
        clips,
        output,
        outro=outro,
        subtitles=subtitles,
        width=width,
        height=height,
    )


def assemble_character_video(
    character_id,
    clips,
    output,
    root=ROOT,
    subtitles='auto',
    outro=None,
    music_path=None,
    width=1080,
    height=1920,
    upscale='auto',
    upscale_model=None,
    texture_preserve=None,
    subtitle_style='editorial_tiktok',
):
    """Assemble final TikTok 9:16 video for ISK, Dinda, or Bang Ray with auto AI upscaling + unified ISK subtitles."""
    cid = str(character_id).strip().lower()
    if cid not in ('isk', 'dinda', 'bang_ray', 'pak_vincent'):
        raise ValueError(f'Unsupported character_id: {character_id}')

    root = Path(root)
    resolved_outro = None if outro is False else outro
    if cid == 'isk' and outro is None:
        resolved_outro = root / 'characters/isk/assets/brand/outro_keris_isk.mp4'

    resolved_music = None if music_path is False else music_path
    if cid == 'dinda' and music_path is None:
        default_bgm = root / 'characters/dinda/content/sore_palembang_lofi_acoustic.wav'
        resolved_music = default_bgm if default_bgm.is_file() else None

    result = assemble_subtitled_video(
        clips,
        output,
        outro=resolved_outro,
        music_path=resolved_music,
        subtitles=subtitles,
        width=width,
        height=height,
        upscale=upscale,
        upscale_model=upscale_model,
        texture_preserve=texture_preserve,
        subtitle_style=subtitle_style,
    )
    result['character_id'] = cid
    return result


def render_branded(video, subtitles, outro, output, duration=None):
    """Burn in timed text over the body and append exactly three seconds of branding."""
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output already exists; create a new version')
    if not SUBTITLE_FFMPEG.is_file():
        raise ValueError('The local FFmpeg build with subtitle support is unavailable')
    video, subtitles, outro = (Path(p).resolve(strict=True) for p in (video, subtitles, outro))
    if subtitles.suffix.lower() != '.srt':
        raise ValueError('Supply timed subtitles in a nonempty SRT file')
    captions = probe(subtitles, show_packets=True)
    if not any(s.get('codec_name') == 'subrip' for s in captions['streams']) or not captions.get('packets'):
        raise ValueError('Supply timed subtitles in a nonempty SRT file')

    args = [str(SUBTITLE_FFMPEG), '-nostdin', '-hide_banner', '-loglevel', 'error',
            '-i', str(video), '-i', str(outro)]
    filters = []
    for index, path in enumerate((video, outro)):
        info = probe(path)
        source = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
        if source is None:
            raise ValueError(f'Input must contain video: {path.name}')
        if index == 0:
            source_duration = float(source.get('duration') or info['format']['duration'])
            body_frames = round((source_duration if duration is None else duration) * 30)
            if not 1 <= body_frames <= round(source_duration * 30):
                raise ValueError('Body duration must be positive and fit within the source video')
            if body_frames > BRAND_BODY_MAX_SECONDS * 30:
                raise ValueError(f'Branded video body must be at most {BRAND_BODY_MAX_SECONDS} seconds')
            seconds = body_frames / 30
            for cue in captions['packets']:
                start = float(cue['pts_time'])
                end = start + float(cue['duration_time'])
                if not 0 <= start < end <= seconds + 0.000001:
                    raise ValueError('Every subtitle cue must fit within the main video')
            extra = f",subtitles=captions.srt:force_style='{SUBTITLE_STYLE}'"
        else:
            seconds = BRAND_OUTRO_SECONDS
            extra = ''
        # Extend a short closing with its last frame, and align both streams
        # so even a short voiceover cannot truncate the closing.
        filters.append(
            f'[{index}:v:0]scale=720:1280:force_original_aspect_ratio=decrease,'
            f'pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,fps=30,'
            f'tpad=stop_mode=clone:stop_duration={seconds:.9f},trim=duration={seconds:.9f},'
            f'setpts=PTS-STARTPTS{extra}[v{index}]'
        )
        has_audio = any(s['codec_type'] == 'audio' for s in info['streams'])
        audio = f'[{index}:a:0]aformat=sample_rates=48000:channel_layouts=stereo,apad'
        if not has_audio:
            audio = 'anullsrc=r=48000:cl=stereo'
        filters.append(f'{audio},atrim=duration={seconds:.9f},asetpts=PTS-STARTPTS[a{index}]')

    filters.append('[v0][a0][v1][a1]concat=n=2:v=1:a=1[video][audio]')
    args += ['-filter_complex', ';'.join(filters), '-map', '[video]', '-map', '[audio]',
             '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-c:a', 'aac',
             '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.render-brand-', dir=output.parent) as work:
        temporary = Path(work) / 'render.mp4'
        shutil.copyfile(subtitles, Path(work) / 'captions.srt')
        subprocess.run(args + [str(temporary)], cwd=work, check=True, capture_output=True, timeout=240)
        exported = next(s for s in probe(temporary)['streams'] if s['codec_type'] == 'video')
        expected_frames = body_frames + BRAND_OUTRO_SECONDS * 30
        if (exported['width'], exported['height']) != (720, 1280) or int(exported['nb_frames']) != expected_frames:
            raise ValueError('Branded export failed frame count or dimensions check')
        os.link(temporary, output)
    return {'path': str(output), 'duration_seconds': expected_frames / 30,
            'width': 720, 'height': 1280, 'outro_seconds': BRAND_OUTRO_SECONDS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--duration', type=float)
    parser.add_argument('--character', choices=['isk', 'dinda', 'bang_ray', 'pak_vincent'],
                        help='Assemble character video with unified ISK kinetic yellow subtitles')
    parser.add_argument('--music', type=Path, help='Optional background music track')
    parser.add_argument('--no-music', action='store_true', help='Disable default character background music')
    parser.add_argument('--ass', type=Path, help='Optional pre-generated ASS file for unified character mode')
    parser.add_argument('--upscale', choices=['auto', 'off', 'always'], default='auto',
                        help='AI upscale pre-pass for sub-720p clips (default: auto)')
    parser.add_argument('--upscale-model', default='upscayl-lite-4x',
                        help='Model upscaler (default Varian 3: upscayl-lite-4x; opsi lain: ffmpeg-natural, realesr-animevideov3, high-fidelity-4x)')
    parser.add_argument('--texture-preserve', type=float,
                        help='Bobot campuran tekstur asli anti-plastik 0.0-1.0 (default: 0.45)')
    parser.add_argument('--subtitle-style', choices=['isk_yellow', 'editorial_tiktok'], default='editorial_tiktok',
                        help='Gaya subtitle default: editorial_tiktok (2-tier) atau isk_yellow')
    parser.add_argument('--subtitles', type=Path, help='Timed SRT for a branded export')
    parser.add_argument('--outro', type=Path, help='Approved brand video for closing')
    args = parser.parse_args()
    if args.character:
        music_arg = False if args.no_music else args.music
        sub_arg = args.ass if args.ass else 'auto'
        result = assemble_character_video(
            args.character,
            args.input,
            args.output,
            subtitles=sub_arg,
            outro=args.outro,
            music_path=music_arg,
            upscale=args.upscale,
            upscale_model=args.upscale_model,
            texture_preserve=args.texture_preserve,
            subtitle_style=args.subtitle_style,
        )
    elif args.subtitles or args.outro:
        if not args.subtitles or not args.outro or len(args.input) != 1:
            parser.error('Branded export requires one input, --subtitles, and --outro')
        result = render_branded(args.input[0], args.subtitles, args.outro, args.output, args.duration)
    else:
        result = render(args.input, args.output, args.duration)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
