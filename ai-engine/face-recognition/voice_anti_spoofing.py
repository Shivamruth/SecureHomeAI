import os
import argparse

import numpy as np
import onnxruntime as ort
import sounddevice as sd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "aasist", "aasist.onnx")

SAMPLE_RATE = 16000
MIN_DURATION_SECONDS = 3.0
EXPECTED_SAMPLES = 64600

MIN_RMS = 0.002
MAX_PEAK = 0.98
MAX_CLIPPED_RATIO = 0.01

DEFAULT_DEVICE = 1
DEFAULT_RECORD_SECONDS = 5

_session = None


def assess_audio_quality(audio, sample_rate=SAMPLE_RATE):
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)

    signals = []

    if sample_rate != SAMPLE_RATE:
        signals.append("Expected 16000 Hz audio")

    if audio.size == 0:
        return {
            "passed": False,
            "signals": ["Empty audio recording"],
            "duration": 0.0,
            "rms": 0.0,
            "peak": 0.0
        }

    if not np.all(np.isfinite(audio)):
        return {
            "passed": False,
            "signals": ["Audio contains invalid values"],
            "duration": 0.0,
            "rms": 0.0,
            "peak": 0.0
        }

    duration = len(audio) / float(sample_rate)
    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak = float(np.max(np.abs(audio)))
    clipped_ratio = float(np.mean(np.abs(audio) >= 0.999))

    if duration < MIN_DURATION_SECONDS:
        signals.append("Recording is too short")

    if rms < MIN_RMS:
        signals.append("Audio level is too low")

    if peak > MAX_PEAK:
        signals.append("Audio may be distorted")

    if clipped_ratio > MAX_CLIPPED_RATIO:
        signals.append("Excessive audio clipping detected")

    return {
        "passed": len(signals) == 0,
        "signals": signals if signals else ["Audio quality acceptable"],
        "duration": round(duration, 2),
        "rms": round(rms, 6),
        "peak": round(peak, 6)
    }


def prepare_model_audio(audio):
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)

    if audio.size == 0:
        raise ValueError("Cannot process empty audio")

    if not np.all(np.isfinite(audio)):
        raise ValueError("Audio contains invalid values")

    if len(audio) >= EXPECTED_SAMPLES:
        audio = audio[:EXPECTED_SAMPLES]
    else:
        repeats = (EXPECTED_SAMPLES // len(audio)) + 1
        audio = np.tile(audio, repeats)[:EXPECTED_SAMPLES]

    return np.ascontiguousarray(
        audio.reshape(1, EXPECTED_SAMPLES),
        dtype=np.float32
    )


def load_antispoof_model():
    global _session

    if _session is not None:
        return _session

    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"AASIST model not found: {MODEL_PATH}"
        )

    print("Loading AASIST anti-spoofing model...")

    _session = ort.InferenceSession(
        MODEL_PATH,
        providers=["CPUExecutionProvider"]
    )

    inputs = _session.get_inputs()

    if len(inputs) != 1:
        raise RuntimeError("Unexpected AASIST input configuration")

    print("AASIST MODEL READY")

    return _session


def detect_spoof(audio, sample_rate=SAMPLE_RATE):
    quality = assess_audio_quality(audio, sample_rate)

    if not quality["passed"]:
        return {
            "passed": False,
            "is_spoof": None,
            "decision": "REJECTED_AUDIO_QUALITY",
            "reason": "; ".join(quality["signals"]),
            "quality": quality,
            "model": "AASIST"
        }

    if sample_rate != SAMPLE_RATE:
        return {
            "passed": False,
            "is_spoof": None,
            "decision": "INVALID_SAMPLE_RATE",
            "reason": "AASIST requires 16000 Hz audio",
            "quality": quality,
            "model": "AASIST"
        }

    model_audio = prepare_model_audio(audio)
    session = load_antispoof_model()

    input_name = session.get_inputs()[0].name

    outputs = session.run(
        None,
        {input_name: model_audio}
    )

    logits = np.asarray(outputs[0], dtype=np.float32)

    if logits.shape != (1, 2):
        raise RuntimeError(
            f"Unexpected AASIST output shape: {logits.shape}"
        )

    if not np.all(np.isfinite(logits)):
        raise RuntimeError("AASIST returned invalid scores")

    # AASIST class 0 = spoof.
    # AASIST class 1 = bona fide.
    shifted = logits[0] - np.max(logits[0])
    scores = np.exp(shifted)
    scores = scores / np.sum(scores)

    spoof_score = float(scores[0])
    bonafide_score = float(scores[1])

    is_spoof = bool(np.argmax(logits[0]) == 0)

    result = {
        "passed": not is_spoof,
        "is_spoof": is_spoof,
        "decision": "SPOOF" if is_spoof else "BONAFIDE",
        "spoof_score": round(spoof_score, 5),
        "bonafide_score": round(bonafide_score, 5),
        "spoof_logit": round(float(logits[0][0]), 5),
        "bonafide_logit": round(float(logits[0][1]), 5),
        "quality": quality,
        "model": "AASIST",
        "status": "EXPERIMENTAL_UNCALIBRATED"
    }

    return result


def record_and_detect(seconds=DEFAULT_RECORD_SECONDS,
                      device=DEFAULT_DEVICE):

    if seconds < MIN_DURATION_SECONDS:
        raise ValueError("Recording must be at least 3 seconds")

    print(f"\nRecording for {seconds} seconds...")
    print("Speak normally into your microphone.")

    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=device
    )

    sd.wait()

    result = detect_spoof(
        np.asarray(audio, dtype=np.float32).reshape(-1)
    )

    print("\n===== AASIST ANTI-SPOOF RESULT =====")
    print("Decision:", result["decision"])

    if result.get("spoof_score") is not None:
        print("Spoof score:", result["spoof_score"])
        print("Bona fide score:", result["bonafide_score"])

    print("Status:", result.get("status", "CHECK_FAILED"))

    return result


def main():
    parser = argparse.ArgumentParser(
        description="SecureHomeAI AASIST Voice Anti-Spoofing"
    )

    parser.add_argument(
        "--test-mic",
        action="store_true",
        help="Record microphone audio and test it"
    )

    parser.add_argument(
        "--seconds",
        type=int,
        default=DEFAULT_RECORD_SECONDS
    )

    parser.add_argument(
        "--device",
        type=int,
        default=DEFAULT_DEVICE
    )

    args = parser.parse_args()

    if args.test_mic:
        record_and_detect(args.seconds, args.device)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
