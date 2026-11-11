#!/usr/bin/env python3
import sys
import os
import av
import numpy as np

def mix_video_with_music(video_path, music_path, output_path, vocal_vol=1.0, music_vol=0.15):
    """
    Combines video dialogue audio with a background music track.
    Vocal volume kept at 100%, background music at 15%.
    Fix: Uses separate container for audio decoding to avoid EOF demux bug.
    """
    print(f"Mixing video: {video_path}")
    print(f"With music: {music_path}")
    print(f"Output: {output_path}")

    sample_rate = 48000

    # 1. Read vocal audio with fresh dedicated container
    in_audio = av.open(video_path)
    resampler = av.AudioResampler(format='s16p', layout='stereo', rate=sample_rate)
    vocal_audio = []
    if in_audio.streams.audio:
        for packet in in_audio.demux(in_audio.streams.audio[0]):
            for frame in packet.decode():
                for rf in resampler.resample(frame):
                    vocal_audio.append(rf.to_ndarray())
    in_audio.close()

    if vocal_audio:
        vocal_data = np.concatenate(vocal_audio, axis=1).astype(np.float32)
    else:
        in_v_temp = av.open(video_path)
        v_dur = float(in_v_temp.duration) / av.time_base if in_v_temp.duration else 8.0
        in_v_temp.close()
        vocal_data = np.zeros((2, int(v_dur * sample_rate)), dtype=np.float32)

    total_samples = vocal_data.shape[1]
    print(f"Vocal samples: {total_samples}, max amplitude: {np.max(np.abs(vocal_data))}")

    # 2. Read music audio
    in_music = av.open(music_path)
    music_resampler = av.AudioResampler(format='s16p', layout='stereo', rate=sample_rate)
    music_audio = []
    if in_music.streams.audio:
        for packet in in_music.demux(in_music.streams.audio[0]):
            for frame in packet.decode():
                for rf in music_resampler.resample(frame):
                    music_audio.append(rf.to_ndarray())
            if sum(m.shape[1] for m in music_audio) >= total_samples:
                break
    in_music.close()

    if music_audio:
        music_data = np.concatenate(music_audio, axis=1).astype(np.float32)
        if music_data.shape[1] < total_samples:
            repeats = int(np.ceil(total_samples / music_data.shape[1]))
            music_data = np.tile(music_data, (1, repeats))[:, :total_samples]
        else:
            music_data = music_data[:, :total_samples]
    else:
        music_data = np.zeros((2, total_samples), dtype=np.float32)

    # Apply fade out to music in the last 1.5 seconds
    fade_len = int(1.5 * sample_rate)
    if total_samples > fade_len:
        music_data[:, -fade_len:] *= np.linspace(1.0, 0.0, fade_len)

    # Mix audio
    mixed_data = (vocal_data * vocal_vol) + (music_data * music_vol)
    mixed_data = np.clip(mixed_data, -32768.0, 32767.0).astype(np.int16)

    # 3. Write video & mixed audio
    in_video = av.open(video_path)
    out = av.open(output_path, mode='w')

    v_stream = in_video.streams.video[0]
    out_v_stream = out.add_stream('libx264', rate=v_stream.average_rate or 24)
    out_v_stream.width = v_stream.width
    out_v_stream.height = v_stream.height
    out_v_stream.pix_fmt = v_stream.pix_fmt or 'yuv420p'

    out_a_stream = out.add_stream('aac', rate=sample_rate)
    out_a_stream.layout = 'stereo'

    # Copy video frames
    for packet in in_video.demux(v_stream):
        for frame in packet.decode():
            for p in out_v_stream.encode(frame):
                out.mux(p)
    for p in out_v_stream.encode():
        out.mux(p)
    in_video.close()

    # Encode mixed audio back to packets
    chunk_size = 1024
    pts = 0
    for i in range(0, total_samples, chunk_size):
        chunk = mixed_data[:, i:i+chunk_size]
        if chunk.shape[1] < chunk_size:
            pad = np.zeros((2, chunk_size - chunk.shape[1]), dtype=np.int16)
            chunk = np.concatenate([chunk, pad], axis=1)
        frame = av.AudioFrame.from_ndarray(chunk, format='s16p', layout='stereo')
        frame.rate = sample_rate
        frame.pts = pts
        pts += chunk_size
        for p in out_a_stream.encode(frame):
            out.mux(p)

    for p in out_a_stream.encode():
        out.mux(p)

    out.close()
    print(f"Successfully mixed video with music -> {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python mix_video_audio.py <video.mp4> <music.mp3> <output.mp4> [vocal_vol] [music_vol]")
        sys.exit(1)
    v_vol = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    m_vol = float(sys.argv[5]) if len(sys.argv) > 5 else 0.15
    mix_video_with_music(sys.argv[1], sys.argv[2], sys.argv[3], v_vol, m_vol)
