import os
import time
import json
import wave
import shutil
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydub import AudioSegment

# ============================================================
# Setup
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "Missing GEMINI_API_KEY. Create a .env file and add:\n"
        "GEMINI_API_KEY=your_real_key_here"
    )

client = genai.Client(api_key=API_KEY)

OUTPUT_DIR = Path("audio-output")
OUTPUT_DIR.mkdir(exist_ok=True)

LOG_FILE = Path("audio-cost-log.jsonl")

SUPPORTED_STT_FORMATS = {".mp3", ".wav"}
TTS_MODEL = "gemini-3.1-flash-tts-preview"
STT_MODEL = "gemini-3-flash-preview"

VOICE_1 = "Kore"
VOICE_2 = "Puck"

MUSEUM_TEXT = (
    "Welcome to the museum audio guide. This exhibit presents a bronze helmet "
    "from the late classical period. Archaeologists believe it belonged to a "
    "high-ranking soldier and was used both for protection and ceremonial display. "
    "Notice the detailed cheek guards and the worn edges, which suggest long-term use. "
    "This object helps historians understand how craftsmanship, warfare, and status "
    "were connected in ancient societies."
)


# ============================================================
# Utility helpers
# ============================================================

def require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is not installed or not in PATH. "
            "Install ffmpeg so pydub can convert WAV to MP3."
        )


def write_wav_file(filename: str, pcm_data: bytes, channels: int = 1,
                   rate: int = 24000, sample_width: int = 2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def wav_to_mp3(wav_path: Path, mp3_path: Path):
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3")


def get_audio_duration_seconds(audio_path: str) -> float:
    audio = AudioSegment.from_file(audio_path)
    return round(len(audio) / 1000, 1)


def short_preview(text: str, limit: int = 70) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def estimate_cost_free_tier(call_type: str) -> float:
    # Gemini free tier for this homework
    return 0.0


def log_api_call(call_type: str, model: str, duration_seconds: float,
                 input_size: str, cost_estimate: float, metadata: dict | None = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "call_type": call_type,
        "model": model,
        "duration_seconds": round(duration_seconds, 2),
        "input_size": input_size,
        "cost_estimate_usd": round(cost_estimate, 6),
        "metadata": metadata or {},
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def normalize_words(text: str) -> list[str]:
    cleaned = (
        text.lower()
        .replace(".", "")
        .replace(",", "")
        .replace(":", "")
        .replace(";", "")
        .replace("!", "")
        .replace("?", "")
        .replace("-", " ")
        .replace("\n", " ")
    )
    return [w for w in cleaned.split() if w.strip()]


def compare_texts(original: str, transcribed: str) -> dict:
    original_words = normalize_words(original)
    transcribed_words = normalize_words(transcribed)

    original_set = set(original_words)
    transcribed_set = set(transcribed_words)

    overlap = original_set & transcribed_set
    word_overlap_accuracy = (
        (len(overlap) / len(original_set)) * 100 if original_set else 0.0
    )

    sequence_score = SequenceMatcher(
        None,
        " ".join(original_words),
        " ".join(transcribed_words)
    ).ratio() * 100

    missing = sorted(original_set - transcribed_set)[:10]
    extra = sorted(transcribed_set - original_set)[:10]

    return {
        "word_overlap_accuracy": round(word_overlap_accuracy, 1),
        "sequence_similarity": round(sequence_score, 1),
        "original_word_count": len(original_words),
        "transcribed_word_count": len(transcribed_words),
        "missing_words": missing,
        "extra_words": extra,
    }


# ============================================================
# TTS
# ============================================================

def text_to_speech_gemini(text: str, voice: str, output_filename: str, retries: int = 2) -> dict:
    require_ffmpeg()

    mp3_path = OUTPUT_DIR / output_filename
    wav_path = OUTPUT_DIR / output_filename.replace(".mp3", ".wav")

    last_error = None

    for attempt in range(1, retries + 1):
        start = time.time()
        try:
            response = client.models.generate_content(
                model=TTS_MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    ),
                ),
            )

            audio_bytes = response.candidates[0].content.parts[0].inline_data.data
            write_wav_file(str(wav_path), audio_bytes)
            wav_to_mp3(wav_path, mp3_path)

            elapsed = round(time.time() - start, 2)
            file_size = mp3_path.stat().st_size
            cost = estimate_cost_free_tier("tts")

            log_api_call(
                call_type="tts",
                model=TTS_MODEL,
                duration_seconds=elapsed,
                input_size=f"{len(text)} chars",
                cost_estimate=cost,
                metadata={
                    "voice": voice,
                    "wav_file": wav_path.name,
                    "mp3_file": mp3_path.name,
                    "file_size_bytes": file_size,
                    "attempt": attempt,
                },
            )

            return {
                "success": True,
                "voice": voice,
                "wav_path": str(wav_path),
                "mp3_path": str(mp3_path),
                "generation_time_seconds": elapsed,
                "file_size_bytes": file_size,
                "text_length_chars": len(text),
                "cost_estimate_usd": cost,
            }

        except Exception as e:
            last_error = str(e)
            elapsed = round(time.time() - start, 2)

            log_api_call(
                call_type="tts",
                model=TTS_MODEL,
                duration_seconds=elapsed,
                input_size=f"{len(text)} chars",
                cost_estimate=0.0,
                metadata={"voice": voice, "error": last_error, "attempt": attempt},
            )

            if attempt == retries:
                return {
                    "success": False,
                    "voice": voice,
                    "error": last_error,
                    "generation_time_seconds": elapsed,
                }

            time.sleep(1)

    return {"success": False, "voice": voice, "error": last_error}


# ============================================================
# STT
# ============================================================

def speech_to_text_gemini(audio_file_path: str, retries: int = 2) -> dict:
    path = Path(audio_file_path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {audio_file_path}"}

    if path.suffix.lower() not in SUPPORTED_STT_FORMATS:
        return {
            "success": False,
            "error": f"Unsupported format: {path.suffix}. Supported: .mp3, .wav"
        }

    last_error = None

    for attempt in range(1, retries + 1):
        start = time.time()
        try:
            uploaded = client.files.upload(file=str(path))

            response = client.models.generate_content(
                model=STT_MODEL,
                contents=[
                    "Generate a clean transcript of the speech only. "
                    "Do not summarize. Do not explain. Return only the transcript.",
                    uploaded,
                ],
            )

            elapsed = round(time.time() - start, 2)
            file_size_kb = round(path.stat().st_size / 1024, 1)
            duration_seconds = get_audio_duration_seconds(str(path))
            cost = estimate_cost_free_tier("stt")

            transcript_text = (response.text or "").strip()

            log_api_call(
                call_type="stt",
                model=STT_MODEL,
                duration_seconds=elapsed,
                input_size=f"{file_size_kb:.1f} KB",
                cost_estimate=cost,
                metadata={
                    "audio_file": path.name,
                    "audio_format": path.suffix.lower(),
                    "audio_duration_seconds": duration_seconds,
                    "attempt": attempt,
                },
            )

            return {
                "success": True,
                "text": transcript_text,
                "transcription_time_seconds": elapsed,
                "duration_seconds": duration_seconds,
                "file_name": path.name,
                "file_size_kb": file_size_kb,
                "cost_estimate_usd": cost,
            }

        except Exception as e:
            last_error = str(e)
            elapsed = round(time.time() - start, 2)

            log_api_call(
                call_type="stt",
                model=STT_MODEL,
                duration_seconds=elapsed,
                input_size=f"{path.stat().st_size / 1024:.1f} KB",
                cost_estimate=0.0,
                metadata={"audio_file": path.name, "error": last_error, "attempt": attempt},
            )

            if attempt == retries:
                return {
                    "success": False,
                    "error": last_error,
                    "transcription_time_seconds": elapsed,
                }

            time.sleep(1)

    return {"success": False, "error": last_error}


# ============================================================
# Summary
# ============================================================

def print_summary(tts_results: list[dict], stt_result: dict):
    successful_tts = [r for r in tts_results if r.get("success")]
    successful_stt = [stt_result] if stt_result.get("success") else []

    total_tts_cost = sum(r.get("cost_estimate_usd", 0.0) for r in successful_tts)
    total_stt_cost = sum(r.get("cost_estimate_usd", 0.0) for r in successful_stt)
    total_pipeline_cost = total_tts_cost + total_stt_cost

    avg_tts_latency = (
        sum(r.get("generation_time_seconds", 0.0) for r in successful_tts) / len(successful_tts)
        if successful_tts else 0.0
    )
    avg_stt_latency = (
        sum(r.get("transcription_time_seconds", 0.0) for r in successful_stt) / len(successful_stt)
        if successful_stt else 0.0
    )

    print("\n=== Cost and Latency Summary ===")
    print(f"  TTS calls:  {len(successful_tts)} | Total cost: ${total_tts_cost:.4f} | Avg latency: {avg_tts_latency:.2f}s")
    print(f"  STT calls:  {len(successful_stt)} | Total cost: ${total_stt_cost:.4f} | Avg latency: {avg_stt_latency:.2f}s")
    print(f"  Pipeline total: ${total_pipeline_cost:.4f}")


# ============================================================
# Main
# ============================================================

def main():
    print("=== HW2 Audio Pipeline ===")

    tts_1 = text_to_speech_gemini(
        text=MUSEUM_TEXT,
        voice=VOICE_1,
        output_filename=f"voice_{VOICE_1.lower()}_sample.mp3"
    )
    if not tts_1["success"]:
        print(f"\n[1/4] Generating speech with voice: {VOICE_1}")
        print(f"  Error: {tts_1['error']}")
        return

    print(f"\n[1/4] Generating speech with voice: {VOICE_1}")
    print(f'  Text: "{short_preview(MUSEUM_TEXT)}"')
    print(f"  Generated in {tts_1['generation_time_seconds']:.2f}s")
    print(f"  File: {tts_1['mp3_path']} ({tts_1['file_size_bytes'] / 1024:.1f} KB)")
    print(f"  Cost: ${tts_1['cost_estimate_usd']:.4f}")

    tts_2 = text_to_speech_gemini(
        text=MUSEUM_TEXT,
        voice=VOICE_2,
        output_filename=f"voice_{VOICE_2.lower()}_sample.mp3"
    )
    if not tts_2["success"]:
        print(f"\n[2/4] Generating speech with voice: {VOICE_2}")
        print(f"  Error: {tts_2['error']}")
        return

    print(f"\n[2/4] Generating speech with voice: {VOICE_2}")
    print(f'  Text: "{short_preview(MUSEUM_TEXT)}"')
    print(f"  Generated in {tts_2['generation_time_seconds']:.2f}s")
    print(f"  File: {tts_2['mp3_path']} ({tts_2['file_size_bytes'] / 1024:.1f} KB)")
    print(f"  Cost: ${tts_2['cost_estimate_usd']:.4f}")

    stt = speech_to_text_gemini(tts_1["mp3_path"])
    if not stt["success"]:
        print(f"\n[3/4] Transcribing {tts_1['mp3_path']}")
        print(f"  Error: {stt['error']}")
        return

    print(f"\n[3/4] Transcribing {tts_1['mp3_path']}")
    print(f'  Transcript: "{short_preview(stt["text"])}"')
    print(f"  Transcribed in {stt['transcription_time_seconds']:.2f}s")
    print(f"  Audio duration: {stt['duration_seconds']:.1f}s")
    print(f"  Cost: ${stt['cost_estimate_usd']:.4f}")

    comparison = compare_texts(MUSEUM_TEXT, stt["text"])

    print(f"\n[4/4] Comparing original vs transcribed text")
    print(f'  Original:    "{short_preview(MUSEUM_TEXT)}"')
    print(f'  Transcribed: "{short_preview(stt["text"])}"')
    print(f"  Word overlap accuracy: {comparison['word_overlap_accuracy']:.1f}%")

    print_summary([tts_1, tts_2], stt)

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()