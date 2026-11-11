"""
Motion Graphic Subtitle Generator (Standar Terpadu ISK, Dinda, dan Bang Ray)
Implements:
1. Electric Vibrant Yellow (#FFE600 / &H0000E6FF), Arial Bold 68, thick black outline (10)
2. Lower-third TikTok safe zone (MarginV=300 on 1080x1920)
3. Natural phrase grouping (2-3 words) with subtle pop animation
4. Compound Brand Names on 1 single line when spoken:
   - "Paku Cap Keris"
   - "PT Intan Suar Kartika"
   - "Kawat Licin Diamond"
   - "Kawat Duri Diamond"
   - "Kereta Sorong Five Star"
5. Automated Faster-Whisper audio alignment & subtitle burning via FFmpeg
"""

import argparse
from pathlib import Path
import re
import subprocess
from typing import List, Tuple, Optional

UNIFIED_SUBTITLE_STYLE = {
    "engine": "faster_whisper_small_id",
    "format": "ass",
    "default_style": "editorial_tiktok",
    "style_name": "editorial_tiktok",
    "top_style": {
        "name": "Ray_Top",
        "font_name": "Helvetica Neue",
        "font_size": 44,
        "bold": True,
        "case": "UPPERCASE",
        "primary_hex": "#FFFFFF",
        "y": 1502,
    },
    "bottom_style": {
        "name": "Ray_Bot",
        "font_name": "Times New Roman",
        "font_size": 126,
        "scale_x": 72,
        "scale_y": 108,
        "case": "lowercase",
        "primary_hex": "#E8FF3B",
        "primary_ass_colour": "&H003BFFE8",
        "y": 1595,
    },
    "legacy_preset": {
        "style_name": "ISK_Yellow",
        "font_name": "Arial",
        "font_size": 68,
        "primary_hex": "#FFE600",
        "primary_ass_colour": "&H0000E6FF",
        "margin_v": 300,
    },
    "font_name": "Times New Roman",
    "font_size": 126,
    "bold": False,
    "primary_hex": "#E8FF3B",
    "primary_ass_colour": "&H003BFFE8",
    "outline_width": 1.4,
    "shadow_depth": 4,
    "margin_v": 300,
    "play_res": [1080, 1920],
    "phrase_words": [2, 4],
    "comma_free": True,
    "characters": ["isk", "dinda", "bang_ray", "pak_vincent"],
}

COMPOUND_BRANDS = [
    "PT Intan Suar Kartika",
    "Paku Cap Keris",
    "Kawat Licin Diamond",
    "Kawat Duri Diamond",
    "Kereta Sorong Five Star",
    "Kereta Pasir Five Star"
]

ASS_HEADER_TEMPLATE = r"""[Script Info]
Title: ISK Dynamic Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ISK_Yellow,Arial,{font_size},&H0000E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,10,3,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

EDITORIAL_ASS_HEADER_TEMPLATE = r"""[Script Info]
Title: Editorial Two-Tier Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Ray_Top,Helvetica Neue,44,&H00FFFFFF,&H000000FF,&H80000000,&H95000000,-1,0,0,0,94,100,-1,0,1,1.6,3,2,60,60,300,1
Style: Ray_Bot,Times New Roman,126,&H003BFFE8,&H000000FF,&H90000000,&H98000000,0,0,0,0,72,108,-5,0,1,1.4,4,2,60,60,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

SUBTITLE_STYLES = {'isk_yellow', 'editorial_tiktok'}


def _norm_tok(text: str) -> str:
    return re.sub(r'[^\w]', '', text.lower())


def _strip_commas(text: str) -> str:
    """Remove commas from subtitle display text while preserving natural spacing."""
    return re.sub(r'\s{2,}', ' ', str(text or '').replace(',', '')).strip()


def format_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"


def generate_ass_script(
    dialogue_events: List[Tuple[float, float, str]],
    output_path: Path,
    margin_v: int = UNIFIED_SUBTITLE_STYLE["legacy_preset"]["margin_v"],
    font_size: int = UNIFIED_SUBTITLE_STYLE["legacy_preset"]["font_size"],
):
    """
    dialogue_events: list of (start_seconds, end_seconds, text)
    """
    header = ASS_HEADER_TEMPLATE.format(margin_v=margin_v, font_size=font_size).strip()
    lines = [header]
    for start_s, end_s, text in dialogue_events:
        clean_text = _strip_commas(text)
        if not clean_text:
            continue
        t_start = format_timestamp(start_s)
        t_end = format_timestamp(end_s)
        # Apply subtle pop transform (\t(0, 70, \fscx106\fscy106)\t(70, 140, \fscx100\fscy100))
        styled_text = r"{\t(0,70,\fscx106\fscy106)\t(70,140,\fscx100\fscy100)}" + clean_text
        lines.append(f"Dialogue: 0,{t_start},{t_end},ISK_Yellow,,0,0,0,,{styled_text}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def group_words_to_phrases(raw_words: List[dict]) -> List[Tuple[float, float, str]]:
    """
    Group word-level timestamps into natural phrases (2-3 words) while keeping
    known ISK compound brand names intact on one line without affecting unrelated dialogue.
    """
    if not raw_words:
        return []

    tokens = []
    n = len(raw_words)
    i = 0
    while i < n:
        w = raw_words[i]
        c = _norm_tok(w['text'])
        next_c = _norm_tok(raw_words[i + 1]['text']) if i + 1 < n else ''

        # 1. Paku Cap Keris grouping
        if c == 'paku' and next_c in {'cepkris', 'keris', 'cap'}:
            end_time = raw_words[i + 1]['end']
            consumed = 2
            if i + 2 < n and _norm_tok(raw_words[i + 2]['text']) in {'keris', 'kris'}:
                end_time = raw_words[i + 2]['end']
                consumed = 3
            tokens.append({'start': w['start'], 'end': end_time, 'text': 'Paku Cap Keris', 'is_brand': True})
            i += consumed
            continue

        # 2. PT Intan Suar Kartika grouping (strict token boundaries avoid matching e.g. "cipta"/"september")
        if 'intansuar' in c or (
            (c == 'pt' and next_c in {'intan', 'intansuar', 'suar'})
            or (c == 'intan' and next_c in {'suar', 'kartika'})
        ):
            start_time = w['start']
            end_time = w['end']
            j = i
            while j < n and _norm_tok(raw_words[j]['text']) in {'pt', 'intan', 'intansuar', 'suar', 'kartika'}:
                end_time = raw_words[j]['end']
                j += 1
            tokens.append({'start': start_time, 'end': end_time, 'text': 'PT Intan Suar Kartika', 'is_brand': True})
            i = j
            continue

        # 2b. Kawat Duri / Licin Diamond grouping
        if c == 'kawat' and next_c in {'duri', 'licin', 'diamond', 'dimon'}:
            start_time = w['start']
            end_time = w['end']
            j = i + 1
            words_in_group = [w['text']]
            norm_group = [c]
            while j < n and _norm_tok(raw_words[j]['text']) in {'duri', 'licin', 'diamond', 'dimon'}:
                end_time = raw_words[j]['end']
                words_in_group.append(raw_words[j]['text'])
                norm_group.append(_norm_tok(raw_words[j]['text']))
                j += 1
            if 'diamond' in norm_group or 'dimon' in norm_group:
                if 'duri' in norm_group:
                    label = 'Kawat Duri Diamond'
                elif 'licin' in norm_group:
                    label = 'Kawat Licin Diamond'
                else:
                    label = ' '.join(words_in_group).title()
                tokens.append({'start': start_time, 'end': end_time, 'text': label, 'is_brand': True})
                i = j
                continue

        # 2c. Kereta Sorong Five Star grouping
        if c in {'kereta', 'gerobak', 'sorong'} and next_c in {'sorong', 'pasir', 'five', 'star', 'fivestar'}:
            start_time = w['start']
            end_time = w['end']
            j = i + 1
            norm_group = [c]
            while j < n and _norm_tok(raw_words[j]['text']) in {'sorong', 'pasir', 'five', 'star', 'fivestar'}:
                end_time = raw_words[j]['end']
                norm_group.append(_norm_tok(raw_words[j]['text']))
                j += 1
            if any(k in norm_group for k in ('five', 'star', 'fivestar')):
                tokens.append({'start': start_time, 'end': end_time, 'text': 'Kereta Sorong Five Star', 'is_brand': True})
                i = j
                continue

        raw_text = str(w['text']).strip()
        has_pause = raw_text.endswith(('.', '!', '?', ','))
        clean_w = _strip_commas(raw_text)
        if not clean_w:
            if tokens and has_pause:
                tokens[-1]['has_pause'] = True
            i += 1
            continue
        tokens.append({'start': w['start'], 'end': w['end'], 'text': clean_w, 'has_pause': has_pause, 'is_brand': False})
        i += 1

    # Second pass: group non-brand tokens into natural phrases of 2-3 words
    events = []
    curr = []
    for tok in tokens:
        if tok.get('is_brand'):
            if curr:
                phrase_text = _strip_commas(' '.join(x['text'] for x in curr))
                events.append((curr[0]['start'], curr[-1]['end'], phrase_text))
                curr = []
            events.append((tok['start'], tok['end'], _strip_commas(tok['text'])))
            continue

        if not curr:
            curr.append(tok)
            continue

        gap = tok['start'] - curr[-1]['end']
        has_punct = bool(curr[-1].get('has_pause')) or curr[-1]['text'].endswith(('.', '!', '?', ','))
        if len(curr) >= 3 or gap > 0.35 or has_punct:
            phrase_text = _strip_commas(' '.join(x['text'] for x in curr))
            events.append((curr[0]['start'], curr[-1]['end'], phrase_text))
            curr = [tok]
        else:
            curr.append(tok)

    if curr:
        phrase_text = _strip_commas(' '.join(x['text'] for x in curr))
        events.append((curr[0]['start'], curr[-1]['end'], phrase_text))

    return events


def group_words_for_editorial(raw_words: List[dict]) -> List[Tuple[float, float, str, str]]:
    """
    Group word timestamps into natural 2-4 word editorial phrases and split into
    (top_caps_white_sans, bottom_lowercase_yellow_lime_serif), free of commas.
    """
    if not raw_words:
        return []

    normalized = []
    for w in raw_words:
        raw_t = str(w.get('text', '')).strip()
        if not raw_t:
            continue
        has_pause = raw_t.endswith(('.', '!', '?', ','))
        clean_t = _strip_commas(raw_t)
        if not clean_t:
            if normalized and has_pause:
                normalized[-1]['has_pause'] = True
            continue
        normalized.append({'start': w['start'], 'end': w['end'], 'text': clean_t, 'has_pause': has_pause})
    if not normalized:
        return []

    chunks = []
    curr = []
    for w in normalized:
        if not curr:
            curr.append(w)
            continue
        gap = w['start'] - curr[-1]['end']
        prev_punct = bool(curr[-1].get('has_pause'))
        if len(curr) >= 4 or gap > 0.35 or prev_punct:
            chunks.append(curr)
            curr = [w]
        else:
            curr.append(w)
    if curr:
        chunks.append(curr)

    events = []
    for grp in chunks:
        words = [x['text'].strip() for x in grp if x['text'].strip()]
        if not words:
            continue
        start_s, end_s = grp[0]['start'], grp[-1]['end']
        if len(words) == 1:
            top_txt = ''
            bot_txt = _strip_commas(words[0]).lower()
        elif len(words) == 2:
            top_txt = _strip_commas(words[0]).upper()
            bot_txt = _strip_commas(words[1]).lower()
        else:
            mid = len(words) // 2
            top_txt = _strip_commas(' '.join(words[:mid])).upper()
            bot_txt = _strip_commas(' '.join(words[mid:])).lower()
        events.append((start_s, end_s, top_txt, bot_txt))
    return events


def generate_editorial_ass_script(
    editorial_events: List[Tuple[float, float, str, str]],
    output_path: Path,
    y_top: int = 1502,
    y_bot: int = 1595,
):
    """Write two-tier editorial TikTok ASS script (ALL-CAPS white sans over large lime-yellow serif)."""
    lines = [EDITORIAL_ASS_HEADER_TEMPLATE.strip()]
    for start_s, end_s, top_txt, bot_txt in editorial_events:
        clean_top = _strip_commas(top_txt)
        clean_bot = _strip_commas(bot_txt)
        t_start = format_timestamp(start_s)
        t_end = format_timestamp(end_s)
        if clean_top:
            top_tag = rf"{{\pos(540,{y_top})\blur1.1\t(0,70,\fscx98\fscy104)\t(70,140,\fscx94\fscy100)}}"
            lines.append(f"Dialogue: 1,{t_start},{t_end},Ray_Top,,0,0,0,,{top_tag}{clean_top}")
        if clean_bot:
            bot_tag = rf"{{\pos(540,{y_bot})\blur1.4\t(0,70,\fscx76\fscy113)\t(70,140,\fscx72\fscy108)}}"
            lines.append(f"Dialogue: 0,{t_start},{t_end},Ray_Bot,,0,0,0,,{bot_tag}{clean_bot}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def transcribe_raw_words(video_path: Path) -> List[dict]:
    """Extract word-level Indonesian timestamps once using faster-whisper small."""
    from faster_whisper import WhisperModel

    model = WhisperModel('small', device='cpu', compute_type='int8')
    segments, _ = model.transcribe(str(video_path), word_timestamps=True, language='id')

    raw_words = []
    for s in segments:
        for w in s.words:
            clean = w.word.strip()
            if clean:
                raw_words.append({'start': w.start, 'end': w.end, 'text': clean})
    return raw_words


def auto_transcribe_and_group(video_path: Path) -> List[Tuple[float, float, str]]:
    """
    Extract exact word-level timestamps using faster-whisper and group into natural phrases (2-3 words)
    while preserving compound brand names on their own single line.
    """
    return group_words_to_phrases(transcribe_raw_words(video_path))


def auto_transcribe_editorial(video_path: Path) -> List[Tuple[float, float, str, str]]:
    """Transcribe raw dialogue words and format into two-tier editorial cues."""
    return group_words_for_editorial(transcribe_raw_words(video_path))


def burn_subtitles_to_video(
    video_path: Path,
    ass_path: Path,
    output_path: Path,
    ffmpeg_bin: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
):
    """
    Burn ASS subtitles directly into video container using FFmpeg libass filter.
    """
    if ffmpeg_bin is None:
        hermes_ffmpeg = Path.home() / '.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg'
        ffmpeg_bin = str(hermes_ffmpeg) if hermes_ffmpeg.exists() else 'ffmpeg'

    output_path = Path(output_path).resolve()
    ass_path = Path(ass_path).resolve()
    video_path = Path(video_path).resolve()
    if output_path.exists():
        output_path.unlink()

    vf_parts = []
    if width and height:
        vf_parts.append(
            f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p'
        )
    vf_parts.append(f'ass={ass_path.name}')

    cmd = [
        str(ffmpeg_bin), '-y',
        '-i', str(video_path),
        '-vf', ','.join(vf_parts),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'copy',
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True, cwd=str(ass_path.parent))
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Path ke video sumber')
    parser.add_argument('--output', type=Path, required=True, help='Path output video dengan subtitle')
    parser.add_argument('--ass', type=Path, help='Path file ASS (opsional, jika kosong di-generate otomatis)')
    parser.add_argument(
        '--margin-v',
        type=int,
        default=UNIFIED_SUBTITLE_STYLE['margin_v'],
        help='Margin vertikal dari bawah (default: 300 standar ISK TikTok safe zone)',
    )
    parser.add_argument('--style', choices=sorted(SUBTITLE_STYLES), default='editorial_tiktok',
                        help='Gaya subtitle: editorial_tiktok (default 2-tier) atau isk_yellow')
    parser.add_argument('--width', type=int, default=1080, help='Lebar kanvas output (default: 1080)')
    parser.add_argument('--height', type=int, default=1920, help='Tinggi kanvas output (default: 1920)')
    args = parser.parse_args()

    ass_file = args.ass
    if not ass_file or not ass_file.exists():
        if not ass_file:
            ass_file = args.output.parent / f"{args.output.stem}_subtitles.ass"
        print(f"[Subtitles] Melakukan auto-transcribe dari {args.input}...")
        if args.style == 'editorial_tiktok':
            events = auto_transcribe_editorial(args.input)
            generate_editorial_ass_script(events, ass_file)
        else:
            events = auto_transcribe_and_group(args.input)
            generate_ass_script(events, ass_file, margin_v=args.margin_v)
        print(f"[Subtitles] File ASS dibuat: {ass_file}")

    print(f"[Subtitles] Membakar subtitle ({args.style}, MarginV={args.margin_v}) ke {args.output}...")
    burn_subtitles_to_video(args.input, ass_file, args.output, width=args.width, height=args.height)
    print(f"[Subtitles] Selesai! Output tersimpan: {args.output}")


if __name__ == '__main__':
    main()
