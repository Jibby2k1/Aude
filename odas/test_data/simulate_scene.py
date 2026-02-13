"""
Simulate a 2-speaker scene with a 4-mic square array (ReSpeaker layout)
and export as raw audio for ODAS testing.

Uses REAL SPEECH from CMU ARCTIC dataset (male + female speakers).

Realistic setup:
- Array on a table at 1.0m height
- Speakers standing, mouths at ~1.7m height
- This means speakers are ABOVE the array, falling within ODAS's
  upper-hemisphere spatial filter (which is the default config)
"""

import numpy as np
import pyroomacoustics as pra
import soundfile as sf
import os
import urllib.request

# ============================================================
# STEP 1: Download real speech if needed
# ============================================================
speech_dir = "/odas/test_data"
fs = 16000
duration = 8.0  # seconds

# Try multiple sources for speech audio
speech_files = [
    {
        "path": os.path.join(speech_dir, "speech1.wav"),
        "urls": [
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav",
            "http://festvox.org/cmu_arctic/cmu_arctic/cmu_us_bdl_arctic/wav/arctic_a0001.wav",
        ],
        "label": "Speaker 1",
    },
    {
        "path": os.path.join(speech_dir, "speech2.wav"),
        "urls": [
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0030_8k.wav",
            "http://festvox.org/cmu_arctic/cmu_arctic/cmu_us_slt_arctic/wav/arctic_a0001.wav",
        ],
        "label": "Speaker 2",
    },
]

def download_and_concat(urls, out_path, target_fs, target_duration):
    """Download speech clips, concatenate, resample to target_fs."""
    all_audio = []
    target_samples = int(target_duration * target_fs)

    for url in urls:
        tmp_path = out_path + ".tmp.wav"
        print(f"  Downloading {url}...")
        try:
            urllib.request.urlretrieve(url, tmp_path)
            audio, file_fs = sf.read(tmp_path)
            if audio.ndim > 1:
                audio = audio[:, 0]  # mono
            # Resample if needed
            if file_fs != target_fs:
                ratio = target_fs / file_fs
                n_out = int(len(audio) * ratio)
                indices = np.arange(n_out) / ratio
                audio = np.interp(indices, np.arange(len(audio)), audio)
            all_audio.append(audio)
            if sum(len(a) for a in all_audio) >= target_samples:
                break
        except Exception as e:
            print(f"  Warning: Could not download {url}: {e}")
            continue
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    if len(all_audio) == 0:
        print("  Download failed, generating speech-like broadband signal...")
        # Use filtered noise with speech-like amplitude envelope
        # This has the broadband content ODAS needs for localization
        np.random.seed(hash(out_path) % 2**31)  # different seed per speaker
        signal = np.random.randn(target_samples)

        # Bandpass to speech range (~100-4000 Hz) using simple FIR
        from scipy.signal import firwin, lfilter
        nyq = target_fs / 2
        taps = firwin(101, [100/nyq, 4000/nyq], pass_zero=False)
        signal = lfilter(taps, 1.0, signal)

        # Speech-like amplitude envelope: bursts with pauses
        envelope = np.zeros(target_samples)
        t = 0
        while t < target_samples:
            # Speech burst (200-800ms)
            burst_len = int(np.random.uniform(0.2, 0.8) * target_fs)
            burst_end = min(t + burst_len, target_samples)
            # Smooth onset/offset
            burst = np.ones(burst_end - t)
            ramp = min(int(0.02 * target_fs), len(burst) // 4)
            if ramp > 0:
                burst[:ramp] = np.linspace(0, 1, ramp)
                burst[-ramp:] = np.linspace(1, 0, ramp)
            envelope[t:burst_end] = burst
            t = burst_end
            # Pause (100-500ms)
            pause_len = int(np.random.uniform(0.1, 0.5) * target_fs)
            t += pause_len

        signal *= envelope * 0.5
        return signal

    # Concatenate and trim/pad to target duration
    combined = np.concatenate(all_audio)
    if len(combined) >= target_samples:
        combined = combined[:target_samples]
    else:
        # Loop to fill
        repeats = int(np.ceil(target_samples / len(combined)))
        combined = np.tile(combined, repeats)[:target_samples]

    # Save for reuse
    sf.write(out_path, combined, target_fs)
    return combined


signals_loaded = []
for info in speech_files:
    if os.path.exists(info["path"]):
        print(f"Loading cached: {info['label']}")
        audio, loaded_fs = sf.read(info["path"])
        if loaded_fs != fs:
            ratio = fs / loaded_fs
            n_out = int(len(audio) * ratio)
            audio = np.interp(np.arange(n_out) / ratio, np.arange(len(audio)), audio)
        target_samples = int(duration * fs)
        if len(audio) < target_samples:
            audio = np.tile(audio, int(np.ceil(target_samples / len(audio))))[:target_samples]
        else:
            audio = audio[:target_samples]
        signals_loaded.append(audio)
    else:
        print(f"Downloading: {info['label']}")
        audio = download_and_concat(info["urls"], info["path"], fs, duration)
        signals_loaded.append(audio)

signal1 = signals_loaded[0]
signal2 = signals_loaded[1]

print(f"\nSignal 1: {len(signal1)} samples ({len(signal1)/fs:.1f}s)")
print(f"Signal 2: {len(signal2)} samples ({len(signal2)/fs:.1f}s)")

# ============================================================
# STEP 2: Define the room
# ============================================================
room_dims = [8, 6, 3]  # meters [length, width, height]
rt60 = 0.4  # reverberation time in seconds

e_absorption, max_order = pra.inverse_sabine(rt60, room_dims)

room = pra.ShoeBox(
    room_dims,
    fs=fs,
    materials=pra.Material(e_absorption),
    max_order=max_order,
)

print(f"\nRoom: {room_dims[0]}m x {room_dims[1]}m x {room_dims[2]}m")
print(f"RT60: {rt60}s, max reflection order: {max_order}")

# ============================================================
# STEP 3: Place the microphone array (on a table at 1.0m)
# ============================================================
array_center = np.array([4.0, 3.0, 1.0])

mic_offsets = np.array([
    [-0.0405,  0.0000, 0.0000],  # Mic 1: left
    [ 0.0000,  0.0405, 0.0000],  # Mic 2: front
    [ 0.0405,  0.0000, 0.0000],  # Mic 3: right
    [ 0.0000, -0.0405, 0.0000],  # Mic 4: back
])

mic_positions = (array_center + mic_offsets).T
room.add_microphone_array(mic_positions)

print(f"Array center: {array_center} (table height)")
print(f"Number of mics: {mic_positions.shape[1]}")

# ============================================================
# STEP 4: Place speakers (standing, mouth height ~1.7m)
# ============================================================
speaker1_pos = [5.5, 4.5, 1.7]
speaker2_pos = [2.5, 1.5, 1.7]

room.add_source(speaker1_pos, signal=signal1)
room.add_source(speaker2_pos, signal=signal2)

print(f"\nSpeaker 1 position: {speaker1_pos}")
print(f"Speaker 2 position: {speaker2_pos}")

# Compute ground truth directions
print("\n" + "="*60)
print("GROUND TRUTH")
print("="*60)
for i, pos in enumerate([speaker1_pos, speaker2_pos]):
    diff = np.array(pos) - array_center
    azimuth = np.degrees(np.arctan2(diff[1], diff[0]))
    elevation = np.degrees(np.arctan2(diff[2], np.sqrt(diff[0]**2 + diff[1]**2)))
    distance = np.linalg.norm(diff)
    unit = diff / distance
    print(f"Speaker {i+1}:")
    print(f"  Position: {pos}")
    print(f"  Azimuth: {azimuth:.1f}°, Elevation: {elevation:.1f}°")
    print(f"  Distance: {distance:.2f}m")
    print(f"  Unit vector: ({unit[0]:.3f}, {unit[1]:.3f}, {unit[2]:.3f})")
    print(f"  (This is what ODAS should output as x, y, z)")

# ============================================================
# STEP 5: Simulate
# ============================================================
room.simulate()
print(f"\nSimulation complete. Output shape: {room.mic_array.signals.shape}")

# ============================================================
# STEP 6: Export as raw file for ODAS
# ============================================================
signals = room.mic_array.signals

# Normalize
max_val = np.max(np.abs(signals))
signals = signals / max_val * 0.9

# Convert to 32-bit signed integers, interleave
signals_int32 = (signals * (2**31 - 1)).astype(np.int32)
interleaved = signals_int32.T.flatten()

output_path = "/odas/test_data/test_scene.raw"
with open(output_path, 'wb') as f:
    f.write(interleaved.tobytes())

print(f"\nOutput saved to: {output_path}")
print(f"Format: {signals_int32.shape[1]} samples, 4 channels, 32-bit signed int, 16kHz")
print(f"File size: {os.path.getsize(output_path)} bytes")

wav_path = "/odas/test_data/test_scene.wav"
sf.write(wav_path, signals.T, fs)
print(f"WAV saved to: {wav_path}")
