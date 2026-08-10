from pathlib import Path
from huggingface_hub import snapshot_download


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

MODELS = {
    "parakeet": "nvidia/parakeet-tdt-0.6b-v3",
    "audio_emotion": "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
    "text_emotion": "j-hartmann/emotion-english-distilroberta-base",
}


def download_model(name: str, repo_id: str):
    destination = MODEL_DIR / name
    destination.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 70)
    print(f"Downloading: {name}")
    print(f"Repository: {repo_id}")
    print(f"Destination: {destination}")
    print("=" * 70)

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(destination),
    )

    print(f"✓ {name} downloaded successfully.")


def main():
    print("\nPitSense AI Model Setup")
    print("=" * 70)
    print(f"Models will be stored in: {MODEL_DIR}")
    print("=" * 70)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    for name, repo_id in MODELS.items():
        try:
            download_model(name, repo_id)
        except Exception as exc:
            print(f"\n✗ Failed to download {name}")
            print(f"  Error: {exc}")
            print("\nYou can run this script again later.")
            raise

    print("\n")
    print("=" * 70)
    print("ALL PIT SENSE MODELS DOWNLOADED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Models:")
    for name in MODELS:
        print(f"  ✓ {name}")
    print()


if __name__ == "__main__":
    main()