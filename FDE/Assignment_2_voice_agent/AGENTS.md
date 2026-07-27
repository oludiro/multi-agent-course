# Contributor and Workshop Guide

This repository is a workshop implementation of Aurora Hotel's reservation voice agent. Use this guide to understand the operating boundaries before changing the code. `README.md` remains the architectural and setup reference, and `RUNBOOK.md` remains the follow-along command and expected-output reference; do not copy their full walkthroughs into new documentation.

## Repository map and architecture

The core system lives in `pipeline/`:

- `agent.py` is the hotel-agent brain. It defines the system prompt, OpenAI-style tool schemas, mock tool results, and the tool-call loop.
- `providers.py` keeps the provider boundary in one place. It exposes mock, OpenAI, and Groq implementations for chat, transcription, and synthesis.
- `voice_loop.py` runs a cascaded interaction: caller speech -> speech-to-text (STT) -> LLM plus tools -> text-to-speech (TTS) -> spoken reply. It also supports typed turns.
- `smoke_test.py` drives the real `Agent` through the offline mock provider and is the primary regression check.

`mocks/` contains deterministic SIP and IVR demonstrations. They illustrate call control and media flow but never connect to a carrier. `livekit/` is an optional, local WebRTC room/session demo; browser JavaScript and CSS belong in `livekit/web/`. Keep the provider-specific implementation inside `providers.py` so agent policy and tools remain provider-agnostic.

The cascaded pipeline is intentional: each stage is understandable, measurable, and replaceable. `voice_loop.py` records per-stage timing so workshop participants can see where a turn spends time. It is a learning and integration demo, not a production real-time speech stack.

## Hotel-agent boundaries and tools

Aurora is a narrow reservations agent, not a general assistant. It can help with availability, new reservations, room options and tool-returned rates, change or cancellation requests, transfer to the front desk, and ending a call. Redirect weather, news, trivia, coding, medical, legal, financial, and other unrelated questions to hotel reservations.

Availability, rates, confirmation numbers, policies, and guest details are trusted operational data. Never invent them in a response or test fixture. Use `check_availability` before offering a room and `create_booking` only after the caller has selected a room, supplied a name and phone or email, and explicitly confirmed the summarized booking. Transfer to a person for risky, ambiguous, unsupported, or out-of-scope requests, or whenever the caller requests human help. End the call only when the conversation is clearly over.

Voice replies should be short and natural: generally one or two spoken sentences, with no Markdown, bullet lists, or emoji. Preserve these guardrails when changing prompts, tools, mock behavior, or provider adapters. If behavior changes, add or update a `smoke_test.py` assertion that proves the intended reservation path and the relevant `transfer` or `hangup` control result.

## Local development and providers

Python 3.10+ is required. Start every change with the no-cost, offline path from the relevant directory:

```bash
cd pipeline && python3 smoke_test.py
cd pipeline && PROVIDER=mock python3 voice_loop.py --text
```

The smoke test must finish with `RESULT: PASS`. Mock mode uses the real agent and tool loop, but no API key, network access, SDK, or paid service. Typed mode is the preferred first check for both mock and live providers because it removes microphone and audio-device uncertainty.

`PROVIDER=mock` is the default for rehearsals, tests, CI, and service-failure fallback. `PROVIDER=openai` requires `OPENAI_API_KEY`; `PROVIDER=groq` requires `GROQ_API_KEY`. OpenAI and Groq share the same provider adapter interface and accept optional `LLM_MODEL`, `STT_MODEL`, `TTS_MODEL`, and `TTS_VOICE` overrides. Do not alter default model choices or add a provider dependency without documenting the reason and cost implication.

For live work, copy `pipeline/config.example.env` to `pipeline/.env` and set only the selected provider's key. Never commit `.env`, print credentials, put real keys in fixtures, or move secrets into source code. Environment variables may be supplied outside `.env`; the file is a local convenience, not a credential store for the repository.

Use `TTS_BACKEND=system` for a local system voice and lower-cost rehearsal with a live LLM. `TTS_BACKEND=provider` uses cloud TTS and can create service cost and network dependency; reserve it for a polished demo and disclose that choice. Mock mode and the local LiveKit demo are the safe cost-aware defaults. Any contribution that adds a service, configuration variable, credential requirement, or expected spend must say so in its documentation and pull request.

## Voice-loop tuning and fallbacks

Microphone mode captures 16 kHz PCM and uses WebRTC VAD to identify speech. A pause of `ENDPOINT_SILENCE_MS` (600 ms by default) ends the turn; `VAD_AGGRESSIVENESS` controls how aggressively silence is detected on a 0–3 scale. Higher aggressiveness can reduce background noise triggers but can also miss quieter speech. A shorter silence timeout can feel faster but may cut callers off; a longer timeout is more forgiving but adds latency. Keep defaults unless the change has a tested workshop benefit.

Audio libraries are loaded only in microphone mode, so `--text` remains the reliable fallback for missing microphones, unavailable audio dependencies, noisy rooms, and provider diagnosis. The loop reports STT, LLM/tool, and TTS timing with an approximate sub-800 ms workshop target. Treat that as an observation target, not a production latency guarantee.

## LiveKit and SIP scope

LiveKit is optional and comes after typed and local voice mode. From `livekit/`, install its dependencies, start the local server, and use the browser room demo as documented in `README.md` and `livekit/README.md`. It demonstrates the room/session abstraction: callers and agents are participants, audio is a track, and the agent can display a transcript and return audio.

Neither `livekit/` nor `mocks/` is a production telephony deployment. The SIP mock prints representative SIP/RTP flow and maps transfer to a simulated SIP REFER. The LiveKit room demo does not create a phone number or SIP integration. A real deployment also needs a SIP trunk, dispatch/routing rules, an agent worker, audio bridging, production authentication, observability, and operational safeguards. Do not represent the local demo as carrier-connected or production-ready.

## Validation and contribution expectations

Choose the smallest validation that proves the changed behavior, then broaden it when the change crosses a boundary:

| Change area | Required evidence |
| --- | --- |
| Agent, tool, or guardrail behavior | `cd pipeline && python3 smoke_test.py`; cover a normal reservation and relevant transfer or hangup path. |
| Text loop or provider configuration | Run mock typed mode first; use a live typed turn only when credentials are authorized. |
| SIP or IVR demonstration | Run `cd mocks && python3 demo_call.py --transfer` and, when relevant, the normal call or IVR flow. |
| LiveKit browser UI | Start the local demo and manually check the browser at desktop and mobile widths, including keyboard interaction. |
| Documentation or static guide | Check links, whitespace, inline JavaScript syntax, expand/collapse behavior, copy feedback, and reduced-motion behavior. |

There is no repository-wide formatter or linter. Use four-space Python indentation, `snake_case` for functions, variables, and modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Prefer small explicit functions, add type hints when interfaces change, avoid unrelated formatting churn, and do not add dependencies unless the capability requires one.

Use focused, imperative commit subjects that describe behavior. Pull requests should state the user-visible change, validation evidence, and the relevant assignment or issue. Include screenshots for `livekit/web/` changes. Explicitly call out configuration, external services, credentials, cost, and remaining risk. Keep the agent inside its reservations scope and leave detailed commands and expected output in `README.md` and `RUNBOOK.md`.
