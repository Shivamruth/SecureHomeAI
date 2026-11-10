import sounddevice as sd
import numpy as np

DEVICES = [1, 2, 14, 15]

RATE = 16000
SECONDS = 3

for device in DEVICES:

    info = sd.query_devices(device)

    print("\n================================")
    print("DEVICE:", device)
    print("NAME:", info["name"])
    print("================================")

    input("Press ENTER, then speak for 3 seconds...")

    try:
        audio = sd.rec(
            int(RATE * SECONDS),
            samplerate=RATE,
            channels=1,
            dtype="float32",
            device=device
        )

        sd.wait()

        audio = audio.reshape(-1)

        rms = float(np.sqrt(np.mean(audio ** 2)))
        peak = float(np.max(np.abs(audio)))

        print("RMS:", round(rms, 6))
        print("PEAK:", round(peak, 6))

        if rms > 0.0015:
            print("STATUS: AUDIO DETECTED")
        else:
            print("STATUS: VERY QUIET / NO AUDIO")

    except Exception as error:
        print("DEVICE ERROR:", error)

print("\nMICROPHONE TEST COMPLETED")