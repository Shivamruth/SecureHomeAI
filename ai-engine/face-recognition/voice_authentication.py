import os
import json
import argparse
import tempfile

import numpy as np
import sounddevice as sd
import torch

from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.utils.fetching import LocalStrategy

from voice_anti_spoofing import assess_audio_quality


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models",
    "spkrec-ecapa-voxceleb"
)

PROFILE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "voice_profiles.json"
)

MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"

SAMPLE_RATE = 16000
DEFAULT_DEVICE = 1
DEFAULT_RECORD_SECONDS = 5
DEFAULT_ENROLLMENT_SAMPLES = 3

# Provisional threshold. Calibrate using genuine and impostor recordings.
DEFAULT_THRESHOLD = 0.25

_model = None


def load_model():
    global _model

    if _model is not None:
        return _model

    print("Loading ECAPA-TDNN speaker model...")

    _model = SpeakerRecognition.from_hparams(
        source=MODEL_SOURCE,
        savedir=MODEL_DIR,
        run_opts={"device": "cpu"},
        local_strategy=LocalStrategy.COPY
    )

    print("ECAPA-TDNN READY")

    return _model


def load_profiles(path=PROFILE_PATH):
    if not os.path.exists(path):
        return {
            "version": 1,
            "profiles": {}
        }

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid profile database")

        profiles = data.get("profiles")

        if not isinstance(profiles, dict):
            raise ValueError("Invalid profiles structure")

        return data

    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Cannot safely load voice profiles: {error}"
        )


def save_profiles(data, path=PROFILE_PATH):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    fd, temporary_path = tempfile.mkstemp(
        prefix="voice_profiles_",
        suffix=".tmp",
        dir=directory
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        os.replace(temporary_path, path)

    except Exception:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise


def record_audio(seconds=DEFAULT_RECORD_SECONDS, device=DEFAULT_DEVICE):
    if seconds < 3:
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

    return np.asarray(audio, dtype=np.float32).reshape(-1)


def normalize_embedding(embedding):
    embedding = np.asarray(
        embedding,
        dtype=np.float32
    ).reshape(-1)

    if embedding.size == 0:
        raise ValueError("Empty speaker embedding")

    if not np.all(np.isfinite(embedding)):
        raise ValueError("Invalid speaker embedding")

    norm = float(np.linalg.norm(embedding))

    if norm < 1e-10:
        raise ValueError("Zero speaker embedding")

    return embedding / norm


def extract_embedding(audio):
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)

    quality = assess_audio_quality(audio, SAMPLE_RATE)

    if not quality["passed"]:
        raise ValueError(
            "Audio quality check failed: "
            + "; ".join(quality["signals"])
        )

    model = load_model()

    waveform = torch.from_numpy(audio).float().unsqueeze(0)

    with torch.no_grad():
        embedding = model.encode_batch(waveform)

    embedding = embedding.detach().cpu().numpy()

    return normalize_embedding(embedding)


def cosine_similarity(embedding_a, embedding_b):
    a = normalize_embedding(embedding_a)
    b = normalize_embedding(embedding_b)

    if a.shape != b.shape:
        raise ValueError("Embedding dimensions do not match")

    return float(np.dot(a, b))


def enroll_user(
    user_name,
    samples=DEFAULT_ENROLLMENT_SAMPLES,
    seconds=DEFAULT_RECORD_SECONDS,
    device=DEFAULT_DEVICE,
    force=False
):
    user_name = user_name.strip()

    if not user_name:
        raise ValueError("User name cannot be empty")

    if samples < 2:
        raise ValueError("Enrollment requires at least 2 samples")

    database = load_profiles()
    profiles = database["profiles"]

    if user_name in profiles and not force:
        raise ValueError(
            f"Voice profile already exists for {user_name}. "
            "Use --force to replace it."
        )

    embeddings = []

    print("\n===== VOICE ENROLLMENT =====")
    print("User:", user_name)
    print("Samples required:", samples)

    for index in range(samples):
        print(f"\nSample {index + 1}/{samples}")

        audio = record_audio(seconds, device)

        quality = assess_audio_quality(audio)

        print("Audio quality:", quality)

        if not quality["passed"]:
            raise RuntimeError(
                "Enrollment stopped. Please repeat enrollment "
                "in a quieter environment."
            )

        embedding = extract_embedding(audio)
        embeddings.append(embedding)

        print("Voice sample accepted.")

        del audio

    average_embedding = np.mean(
        np.stack(embeddings),
        axis=0
    )

    average_embedding = normalize_embedding(average_embedding)

    profiles[user_name] = {
        "user": user_name,
        "model": MODEL_SOURCE,
        "sample_rate": SAMPLE_RATE,
        "embedding": average_embedding.tolist(),
        "threshold": DEFAULT_THRESHOLD,
        "enrollment_samples": samples,
        "spoof_detection": "NOT_IMPLEMENTED"
    }

    save_profiles(database)

    print("\nVOICE ENROLLMENT SUCCESSFUL")
    print("User:", user_name)
    print("Profile saved:", PROFILE_PATH)

    return {
        "success": True,
        "user": user_name,
        "samples": samples
    }


def verify_user(
    user_name,
    seconds=DEFAULT_RECORD_SECONDS,
    device=DEFAULT_DEVICE
):
    user_name = user_name.strip()

    database = load_profiles()
    profile = database["profiles"].get(user_name)

    if profile is None:
        return {
            "verified": False,
            "user": user_name,
            "reason": "Voice profile not found",
            "spoof_detection": "NOT_CHECKED"
        }

    print("\n===== VOICE VERIFICATION =====")
    print("User:", user_name)

    audio = record_audio(seconds, device)

    quality = assess_audio_quality(audio)

    if not quality["passed"]:
        return {
            "verified": False,
            "user": user_name,
            "reason": "Audio quality check failed",
            "quality": quality,
            "spoof_detection": "NOT_CHECKED"
        }

    test_embedding = extract_embedding(audio)

    stored_embedding = np.asarray(
        profile["embedding"],
        dtype=np.float32
    )

    similarity = cosine_similarity(
        test_embedding,
        stored_embedding
    )

    threshold = float(
        profile.get("threshold", DEFAULT_THRESHOLD)
    )

    verified = similarity >= threshold

    result = {
        "verified": verified,
        "user": user_name,
        "similarity": round(similarity, 4),
        "threshold": threshold,
        "reason": (
            "Speaker matched"
            if verified
            else "Speaker did not match"
        ),
        "quality": quality,
        "spoof_detection": "NOT_CHECKED"
    }

    print("\nVOICE VERIFICATION RESULT")
    print("Similarity:", result["similarity"])
    print("Threshold:", threshold)
    print("Verified:", verified)
    print("Spoof detection: NOT CHECKED")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="SecureHomeAI Voice Authentication"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    enroll_parser = subparsers.add_parser("enroll")
    enroll_parser.add_argument("--user", required=True)
    enroll_parser.add_argument("--samples", type=int, default=3)
    enroll_parser.add_argument("--seconds", type=int, default=5)
    enroll_parser.add_argument("--device", type=int, default=DEFAULT_DEVICE)
    enroll_parser.add_argument("--force", action="store_true")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--user", required=True)
    verify_parser.add_argument("--seconds", type=int, default=5)
    verify_parser.add_argument("--device", type=int, default=DEFAULT_DEVICE)

    args = parser.parse_args()

    if args.command == "enroll":
        enroll_user(
            user_name=args.user,
            samples=args.samples,
            seconds=args.seconds,
            device=args.device,
            force=args.force
        )

    elif args.command == "verify":
        result = verify_user(
            user_name=args.user,
            seconds=args.seconds,
            device=args.device
        )

        print("\nFINAL RESULT:", result)


if __name__ == "__main__":
    main()
