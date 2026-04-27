# Curio Roadmap

## Immediately After Textify V1

1. YouTube and social-video transcripts through Supadata/SuperData.
   - Prefer transcript retrieval over video-frame OCR when the source platform can provide a transcript.
   - Research supported platforms, authentication, pricing, rate limits, transcript language metadata, timestamps, and failure modes.
   - Feed retrieved transcripts into the normal `textify -> translate -> evaluate` pipeline as source-language text.

2. Podcast transcript API research.
   - Compare OpenAI speech-to-text, Deepgram prerecorded audio, AssemblyAI transcription/diarization, and any podcast-platform transcript APIs available at implementation time.
   - Evaluate transcript quality, speaker labels, timestamps, cost, language detection, and long-audio handling.
   - Do not add audio transcription to Textify V1 without a separate design checkpoint.
