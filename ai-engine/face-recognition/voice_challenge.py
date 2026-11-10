import os
import re
import json
import time
import random

import numpy as np
import sounddevice as sd

from faster_whisper import WhisperModel
from vosk import Model, KaldiRecognizer


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WHISPER_MODEL_SIZE = "base.en"

WHISPER_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "faster-whisper-base.en"
)

VOSK_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "vosk",
    "vosk-model-small-en-us-0.15"
)

SAMPLE_RATE = 16000
RECORD_SECONDS = 8
DEFAULT_DEVICE = 1

MIN_RMS = 0.0015
MAX_CLIPPED_RATIO = 0.01

CPU_THREADS = 6

WORDS = [
    "hello", "water", "happy", "green",
    "morning", "welcome", "garden", "music",
    "today", "people", "yellow", "simple",
    "computer", "security", "number", "window",
    "family", "friend", "beautiful", "open"
]

_whisper_model = None
_vosk_model = None


# ============================================================
# TEXT UTILITIES
# ============================================================

def normalize_text(text):
    return " ".join(
        re.findall(r"[a-z]+", str(text).lower())
    )


def generate_challenge():
    return " ".join(
        random.SystemRandom().sample(WORDS, 3)
    )


# ============================================================
# MODEL LOADING
# ============================================================

def load_whisper_model():
    global _whisper_model

    if _whisper_model is None:

        print("\nLoading Faster-Whisper base.en model...")

        os.makedirs(
            WHISPER_MODEL_PATH,
            exist_ok=True
        )

        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            cpu_threads=CPU_THREADS,
            num_workers=1,
            download_root=WHISPER_MODEL_PATH
        )

        print("FASTER-WHISPER READY")

    return _whisper_model


def load_vosk_model():
    global _vosk_model

    if _vosk_model is None:

        if not os.path.isdir(VOSK_MODEL_PATH):
            raise FileNotFoundError(
                f"Vosk model not found: {VOSK_MODEL_PATH}"
            )

        print("\nLoading Vosk fallback model...")

        _vosk_model = Model(VOSK_MODEL_PATH)

        print("VOSK READY")

    return _vosk_model


# ============================================================
# MICROPHONE RECORDING
# ============================================================

def record_audio(
    seconds=RECORD_SECONDS,
    device=DEFAULT_DEVICE
):

    print(f"\nRecording for {seconds} seconds...")
    print("Speak all THREE displayed words clearly.")
    print("Leave a short pause between words.")
    print("Do not speak before recording starts.")

    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        device=device
    )

    sd.wait()

    return np.asarray(
        audio,
        dtype=np.int16
    ).reshape(-1)


# ============================================================
# AUDIO QUALITY
# ============================================================

def assess_audio_quality(audio):

    audio = np.asarray(
        audio,
        dtype=np.int16
    ).reshape(-1)

    if audio.size == 0:
        return {
            "passed": False,
            "reason": "Empty recording",
            "rms": 0.0,
            "peak": 0.0,
            "clipped_ratio": 0.0
        }

    samples = audio.astype(np.float32) / 32768.0

    if not np.all(np.isfinite(samples)):
        return {
            "passed": False,
            "reason": "Invalid audio values",
            "rms": 0.0,
            "peak": 0.0,
            "clipped_ratio": 0.0
        }

    rms = float(
        np.sqrt(np.mean(samples ** 2))
    )

    peak = float(
        np.max(np.abs(samples))
    )

    clipped_ratio = float(
        np.mean(np.abs(samples) >= 0.999)
    )

    if rms < MIN_RMS:
        reason = "Microphone audio too quiet"

    elif clipped_ratio > MAX_CLIPPED_RATIO:
        reason = "Excessive audio clipping"

    else:
        reason = "Audio quality acceptable"

    return {
        "passed": reason == "Audio quality acceptable",
        "reason": reason,
        "rms": round(rms, 6),
        "peak": round(peak, 6),
        "clipped_ratio": round(clipped_ratio, 6)
    }


# ============================================================
# FASTER-WHISPER WITH VAD
# ============================================================

def transcribe_with_whisper(audio):

    audio = np.asarray(
        audio,
        dtype=np.int16
    ).reshape(-1)

    if audio.size == 0:
        return {
            "text": "",
            "segments": [],
            "average_probability": None,
            "speech_duration": 0.0,
            "engine": "faster-whisper"
        }

    model = load_whisper_model()

    audio_float = (
        audio.astype(np.float32) / 32768.0
    )

    segments, info = model.transcribe(
        audio_float,

        language="en",
        task="transcribe",

        beam_size=3,
        best_of=1,

        temperature=0.0,

        condition_on_previous_text=False,

        # Voice Activity Detection
        vad_filter=True,

        vad_parameters={
            "threshold": 0.55,
            "min_speech_duration_ms": 150,
            "min_silence_duration_ms": 500,
            "speech_pad_ms": 200
        },

        # Reduce silence-related hallucinations
        no_speech_threshold=0.75,
        log_prob_threshold=-0.8,
        compression_ratio_threshold=2.0,
        hallucination_silence_threshold=1.0,

        # Limit unnecessary generated text
        max_new_tokens=12,

        word_timestamps=True
    )

    recognized_segments = []
    word_probabilities = []
    speech_durations = []
    no_speech_values = []

    for segment in segments:

        segment_text = normalize_text(
            segment.text
        )

        if segment_text:
            recognized_segments.append(
                segment_text
            )

        speech_durations.append(
            max(0.0, float(segment.end - segment.start))
        )

        no_speech_values.append(
            float(segment.no_speech_prob)
        )

        if segment.words:

            for word in segment.words:

                word_probabilities.append(
                    float(word.probability)
                )

    transcript = normalize_text(
        " ".join(recognized_segments)
    )

    average_probability = (
        round(
            float(np.mean(word_probabilities)),
            3
        )
        if word_probabilities
        else None
    )

    total_speech_duration = round(
        sum(speech_durations),
        2
    )

    average_no_speech_probability = (
        round(float(np.mean(no_speech_values)), 3)
        if no_speech_values
        else None
    )

    return {
        "text": transcript,
        "segments": recognized_segments,
        "average_probability": average_probability,
        "speech_duration": total_speech_duration,
        "average_no_speech_probability":
            average_no_speech_probability,
        "language": getattr(info, "language", "en"),
        "engine": "faster-whisper"
    }


# ============================================================
# VOSK FALLBACK
# ============================================================

def transcribe_with_vosk(audio):

    audio = np.asarray(
        audio,
        dtype=np.int16
    ).reshape(-1)

    if audio.size == 0:
        return {
            "text": "",
            "segments": [],
            "average_probability": None,
            "engine": "vosk"
        }

    model = load_vosk_model()

    recognizer = KaldiRecognizer(
        model,
        SAMPLE_RATE,
        json.dumps(WORDS + ["[unk]"])
    )

    recognizer.SetWords(True)

    recognizer.AcceptWaveform(
        audio.tobytes()
    )

    result = json.loads(
        recognizer.FinalResult()
    )

    transcript = normalize_text(
        result.get("text", "")
    )

    probabilities = [
        float(word["conf"])
        for word in result.get("result", [])
        if "conf" in word
    ]

    return {
        "text": transcript,
        "segments": [transcript] if transcript else [],
        "average_probability": (
            round(float(np.mean(probabilities)), 3)
            if probabilities
            else None
        ),
        "engine": "vosk"
    }


# ============================================================
# TRANSCRIPTION CONTROLLER
# ============================================================

def transcribe_audio_details(audio):

    try:

        return transcribe_with_whisper(audio)

    except Exception as whisper_error:

        print("\nWHISPER ERROR:")
        print(whisper_error)

        print("\nTrying Vosk fallback...")

        try:

            result = transcribe_with_vosk(audio)

            result["fallback_used"] = True

            return result

        except Exception as vosk_error:

            raise RuntimeError(
                "Both speech recognition engines failed.\n"
                f"Whisper error: {whisper_error}\n"
                f"Vosk error: {vosk_error}"
            ) from vosk_error


# ============================================================
# STRICT CHALLENGE VERIFICATION
# ============================================================

def verify_challenge(challenge, transcript):

    expected = normalize_text(
        challenge
    ).split()

    actual = normalize_text(
        transcript
    ).split()

    verified = (
        len(expected) == 3
        and actual == expected
    )

    matched = sum(
        1
        for expected_word, actual_word
        in zip(expected, actual)
        if expected_word == actual_word
    )

    return {
        "verified": verified,
        "expected": " ".join(expected),
        "recognized": " ".join(actual),
        "matched_words": matched,
        "total_words": 3,
        "match_score": round(matched / 3, 2),
        "reason": (
            "Exact challenge matched"
            if verified
            else "Challenge did not match exactly"
        )
    }


# ============================================================
# MAIN VOICE CHALLENGE
# ============================================================

def run_voice_challenge(device=DEFAULT_DEVICE):

    challenge = generate_challenge()

    print("\n========================================")
    print("       SECUREHOMEAI VOICE CHALLENGE")
    print("========================================")

    print("\nSAY THESE WORDS:")
    print("\n", challenge.upper())

    input("\nPress ENTER when ready...")

    for number in (3, 2, 1):
        print(number)
        time.sleep(1)

    audio = record_audio(
        device=device
    )

    quality = assess_audio_quality(audio)

    print("\n===== AUDIO QUALITY =====")
    print("RMS:", quality["rms"])
    print("Peak:", quality["peak"])
    print("Clipping:", quality["clipped_ratio"])
    print("Status:", quality["reason"])

    if not quality["passed"]:

        return {
            "verified": False,
            "decision": "REJECTED_AUDIO_QUALITY",
            "quality": quality,
            "reason": quality["reason"]
        }

    print("\n===== SPEECH RECOGNITION =====")
    print("Processing with VAD-enabled Faster-Whisper...")

    details = transcribe_audio_details(audio)

    transcript = details["text"]

    print("\n===== TRANSCRIPTION DIAGNOSTICS =====")
    print("Engine:", details["engine"])
    print("Segments:", details["segments"])
    print("Transcript:", transcript)
    print("Speech duration:", details.get("speech_duration"))
    print(
        "Average word probability:",
        details["average_probability"]
    )

    print(
        "Average no-speech probability:",
        details.get("average_no_speech_probability")
    )

    if details.get("fallback_used"):
        print("WARNING: Vosk fallback was used.")

    result = verify_challenge(
        challenge,
        transcript
    )

    result["quality"] = quality
    result["transcription"] = details

    print("\n===== VOICE CHALLENGE RESULT =====")
    print("Expected:", result["expected"])
    print("Recognized:", result["recognized"])

    print(
        "Matched words:",
        result["matched_words"],
        "/",
        result["total_words"]
    )

    print("Match score:", result["match_score"])

    print(
        "\nDECISION:",
        "PASS" if result["verified"] else "FAIL"
    )

    return result


# ============================================================
# COMMAND LINE
# ============================================================

def main():

    import argparse

    parser = argparse.ArgumentParser(
        description="SecureHomeAI Voice Challenge"
    )

    parser.add_argument(
        "--device",
        type=int,
        default=DEFAULT_DEVICE
    )

    args = parser.parse_args()

    try:

        result = run_voice_challenge(
            device=args.device
        )

        print("\n===== FINAL RESULT =====")
        print(json.dumps(result, indent=4))

    except KeyboardInterrupt:

        print("\nVoice challenge cancelled.")

    except Exception as error:

        print("\nVOICE CHALLENGE ERROR:")
        print(error)


if __name__ == "__main__":
    main()