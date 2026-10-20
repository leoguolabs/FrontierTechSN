#!/usr/bin/env python3
"""Create original music/foley and place provider audio on the picture's frame grid."""
import hashlib
import json
from pathlib import Path
import subprocess
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 48000


def write_wav(path, data):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SR)
        out.writeframes((np.clip(data, -.999, .999) * 32767).astype("<i2").tobytes())


def pcm(path):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-ar", str(SR), "-ac", "1",
        "-f", "f32le", "pipe:1",
    ])
    return np.frombuffer(raw, dtype="<f4").copy()


def add(target, sound, time, gain=1, pan=0):
    start = int(round(time * SR))
    offset = max(0, -start)
    start = max(0, start)
    length = min(len(sound) - offset, len(target) - start)
    if length <= 0:
        return
    stereo = np.array([np.sqrt((1-pan)/2), np.sqrt((1+pan)/2)], dtype=np.float32)
    target[start:start+length] += sound[offset:offset+length, None] * gain * stereo


def mallet(frequency, duration=1.4):
    t = np.arange(int(SR * duration), dtype=np.float32) / SR
    # Inharmonic partials and a short attack: a small wooden-bar ensemble.
    result = np.zeros_like(t)
    for multiple, strength, decay in [(1, 1, 3.8), (2.76, .22, 8), (5.4, .08, 17)]:
        result += strength * np.sin(2*np.pi*frequency*multiple*t) * np.exp(-decay*t)
    return result * np.minimum(1, t/.006)


def main():
    subprocess.run(["node", "scripts/captions.mjs"], cwd=ROOT, check=True)
    timeline = json.loads((ROOT / "content/timeline.json").read_text())
    manifest = {row["id"]: row for row in json.loads((ROOT / "media/audio/manifest.json").read_text())}
    count = round(timeline["duration_frames"] / timeline["fps"] * SR)
    speech = np.zeros((count, 2), dtype=np.float32)
    music = np.zeros_like(speech)
    foley = np.zeros_like(speech)
    duck = np.ones(count, dtype=np.float32)
    gains = []
    for shot in timeline["shots"]:
        row = manifest[shot["id"]]
        path = ROOT / row["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["audio_sha256"]:
            raise RuntimeError(f"Provider audio changed: {shot['id']}")
        data = pcm(path)
        active = data[np.abs(data) > .015]
        rms = np.sqrt(np.mean(active**2)) if len(active) else 0
        gain = min(3, .135/max(rms, .001), .85/max(np.max(np.abs(data)), .001))
        edge = min(240, len(data)//2)
        data[:edge] *= np.linspace(0, 1, edge)
        data[-edge:] *= np.linspace(1, 0, edge)
        start = shot["voiceStart"]/timeline["fps"]
        add(speech, data, start, gain*np.sqrt(2))
        gains.append({"id": shot["id"], "gain_db": float(20*np.log10(gain)), "start_frame": shot["voiceStart"]})
        a, b = round(start*SR), min(count, round(start*SR)+len(data))
        duck[max(0,a-4000):min(count,b+8000)] = .32
    # Deterministic, sparse marimba pattern with pizzicato-style bass.
    beat = 60/112
    scale = [261.6256, 329.6276, 391.9954, 493.8833, 440, 391.9954, 329.6276, 293.6648]
    rng = np.random.default_rng(20261021)
    for n, at in enumerate(np.arange(.2, count/SR, beat)):
        if n % 8 in [0, 2, 3, 5, 6]:
            add(music, mallet(scale[(n//2) % len(scale)]), at, .032, (-.32 if n%2 else .32))
        if n % 4 == 0:
            add(music, mallet([65.406, 73.416, 82.407, 65.406][n//16 % 4], 1.8), at, .046)
        if n % 2:
            t = np.arange(2400)/SR
            noise = rng.normal(0, 1, len(t)).astype(np.float32)
            noise = np.convolve(noise, np.ones(5)/5, mode="same")
            add(music, noise*np.exp(-55*t), at, .006, -.25)
    # Smooth music ducking without altering voice timing.
    step = 240
    envelope = duck[::step]
    kernel = np.ones(41)/41
    envelope = np.convolve(np.pad(envelope, (20,20), mode="edge"), kernel, mode="valid")
    duck = np.interp(np.arange(count), np.arange(len(envelope))*step, envelope).astype(np.float32)
    music *= duck[:, None]
    # Material sounds use the exact visual event frame.
    for event in timeline["events"]:
        kind = event["kind"]
        at = event["frame"]/timeline["fps"]
        if kind in {"paper", "ruler", "stamp"}:
            t = np.arange(int(SR*.19))/SR
            noise = rng.normal(0, 1, len(t))
            noise = np.convolve(noise, np.ones(12)/12, mode="same")
            body = np.sin(2*np.pi*(175 if kind=="paper" else 110)*t)*np.exp(-45*t)
            sound = (noise*.45+body)*np.exp(-32*t)
            add(foley, sound.astype(np.float32), at+.06, .022 if kind!="stamp" else .034)
        elif kind in {"line", "marker", "dimension", "circle"}:
            duration = min(.38, event["duration"]/timeline["fps"])
            t = np.arange(int(SR*duration))/SR
            noise = rng.normal(0, 1, len(t))
            noise = noise - np.convolve(noise, np.ones(21)/21, mode="same")
            sound = noise*np.sin(np.pi*np.minimum(t/max(duration,.001),1))**2
            add(foley, sound.astype(np.float32), at, .0018, .12)
    fade = np.ones(count, dtype=np.float32)
    fade[:SR] = np.linspace(0, 1, SR)
    fade[-2*SR:] = np.linspace(1, 0, 2*SR)
    music *= fade[:, None]
    premix = speech + music + foley
    write_wav(ROOT/"media/narration.wav", speech)
    write_wav(ROOT/"media/music.wav", music)
    write_wav(ROOT/"media/foley.wav", foley)
    write_wav(ROOT/"media/premix.wav", premix)
    subprocess.run(["ffmpeg", "-y", "-v", "warning", "-i", str(ROOT/"media/premix.wav"),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", str(SR), "-c:a", "pcm_s24le",
        str(ROOT/"media/master.wav")], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "warning",
        "-i", str(ROOT/"media/picture-v1.mp4"), "-i", str(ROOT/"media/captions-alpha.mov"),
        "-i", str(ROOT/"media/master.wav"),
        "-filter_complex", "[0:v][1:v]overlay=shortest=1:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-map", "2:a:0", "-c:v", "libx264", "-preset", "medium",
        "-crf", "17", "-pix_fmt", "yuv420p", "-r", "24", "-frames:v", str(timeline["duration_frames"]),
        "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-color_range", "tv",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-movflags", "+faststart", str(ROOT/"media/does-ai-help-you-learn.mp4")], check=True)
    (ROOT/"review/audio-mix.json").write_text(json.dumps({
        "sample_rate": SR, "samples": count, "music": "Original procedural mallet/bass/percussion",
        "foley": "Original procedural material sounds", "speech_gains": gains,
        "target_lufs": -16, "target_true_peak": -1.5,
        "perceptual_listening": "Not established by this automated mix",
    }, indent=2)+"\n")
    print("Picture, timed captions, Chatterbox speech, original score and foley encoded.")


if __name__ == "__main__":
    main()
