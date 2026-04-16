# Reflection

## 1. Consent

If this pipeline processed real user audio instead of synthetic speech, explicit consent would be required. Before recording or processing audio, the user should be informed clearly about what data is being collected, how it will be used, and whether it will be stored. A consent screen should appear before recording starts, explaining that audio will be sent to an external API (Gemini) for transcription.

The consent should be given actively (for example, by clicking an “I agree” button). It should also be possible to revoke consent later. If a user withdraws consent, their stored audio and transcripts should be deleted immediately.

In my pipeline run, audio files such as `voice_kore_sample.mp3` (29.2 seconds) were generated and processed automatically. If this were real user audio, consent would need to be collected before generating or uploading such files.

---

## 2. Retention

Audio retention depends on the use case.

For a study application, audio could be stored temporarily (for example, a few hours or one day) to allow users to review results, then deleted automatically.

For a customer service tool, audio might be stored longer (for example, several weeks) for quality assurance and training purposes.

For a medical application, retention must follow strict regulations, meaning audio may need to be stored securely for a long time, with strong access control.

In my pipeline, generated files like `voice_kore_sample.mp3` and `voice_puck_sample.mp3` are stored locally in the `audio-output/` folder. For a real system, these files should either be deleted automatically after processing or stored with a clear retention policy.

---

## 3. PII in Audio

Audio contains more sensitive information than text. Even if the words are not identifying, the voice itself can act as a biometric identifier. Accent, tone, and speaking style can reveal information about a person’s background.

Background sounds can also expose private details such as location or environment. Emotional state can be inferred from voice, which is another sensitive aspect.

Additionally, metadata like file names, timestamps, and audio duration (for example, 29.2 seconds in my run) can indirectly identify users or reveal patterns.

Because of this, audio data should be treated as highly sensitive and protected accordingly.

---

## 4. Capstone Considerations

In this project, I used a museum audio guide scenario. The pipeline successfully generated speech (with ~18–19 seconds latency per TTS call) and transcribed it back with 100% word overlap accuracy.

Currently, the pipeline uses generated audio, so there are no privacy risks. However, if user recordings were added later, the system would need consent mechanisms, secure storage, and clear retention policies.

Encryption would be required both in transit and at rest. Access to audio data should be limited, and logs should not expose sensitive information.

Overall, adding audio features increases both the complexity and the responsibility of handling user data properly.