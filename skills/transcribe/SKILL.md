---
name: transcribe
description: Transcribes audio and video files into text, using a local Whisper model by default or ElevenLabs Scribe via browser automation when speaker diarization is required, and optionally saves the result as a timestamped Obsidian note. Use when asked to transcribe a recording, produce a 회의록, do 전사 or 받아쓰기 on an audio/video file, separate speakers in a multi-person recording, turn a lecture or interview into searchable text, or shrink a large video down to its audio track before processing it. Not for real-time live captioning. Local Whisper output carries no speaker labels; ElevenLabs Scribe's output does, as anonymous `[Speaker N]` indices that still need content-based identity mapping.
metadata:
  version: 1.2.0
---

# transcribe

Turn an audio or video file into text — preferring a local Whisper model when no speaker separation is needed, or ElevenLabs Scribe when it is — and optionally save the result as a timestamped Obsidian note.
Success is a complete, honestly-labeled transcript — every low-confidence, unclear, or hallucinated segment marked as such rather than passed through as fact.

## Preprocess — extract audio before anything else

Never feed a large video file straight into a transcription engine or an upload step.
Pull the audio track down to a small mono file first; a 15-minute, 2.0GB video reduces to about 5.3MB with no meaningful quality loss for speech:

```bash
ffmpeg -nostdin -v error -i "input.mp4" -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 48k output.mp3
```

`-ac 1` (mono) and `-ar 16000` (16kHz) match the input spec every STT model expects.
Check duration and size before and after:

```bash
ffprobe -v error -show_entries format=duration,size -of default=nw=1 input.mp4
```

## Chunk long files before transcribing

Split anything past a few minutes into fixed-length segments; this both isolates hallucination-loop damage (see below) to one chunk instead of the whole file and keeps any per-file cloud limit in reach:

```bash
ffmpeg -nostdin -v error -i input.mp3 -f segment -segment_time 300 -c copy chunks/chunk_%03d.mp3
```

Each chunk's own timestamps reset to `0:00`.
When assembling the final transcript, add the chunk's offset (`chunk_index × 300s`) to every timestamp — skipping this silently produces a transcript with wrong times.

## Pick the engine — by requirement, not by default

Whether speaker separation is needed flips the priority order:

| Need | Priority | Engine | When |
|---|---|---|---|
| No speaker separation | 1 | `mlx_whisper` (Apple Silicon) | Default. Free, offline, no length cap — verified end-to-end on a 15-minute Korean recording. |
| No speaker separation | 2 | ElevenLabs Scribe via `aside` browser automation | Conditional, not a general fallback: only once the credit math below clears, or on a paid plan. |
| Speaker separation needed | 1 | ElevenLabs Scribe via `aside` browser automation | `mlx_whisper` produces no speaker labels at all. Verified end-to-end on a 15:20 two-speaker Korean recording — see "Diarization" below. |
| Speaker separation needed | 2 | `pyannote.audio` | Only if ElevenLabs is unavailable; named as a pointer, not a tested path in this skill. |
| Neither of the above | 3 | Other cloud STT API (OpenAI Whisper, Deepgram, AssemblyAI, …) | Only once a real API key is confirmed present — see "Verify the key" below. |

### Run `mlx_whisper`

```bash
mlx_whisper --model mlx-community/whisper-large-v3-mlx --language ko \
  --output-format all --word-timestamps True \
  --condition-on-previous-text False --temperature 0 --compression-ratio-threshold 2.0 \
  --output-name "<chunk-name>" --output-dir out \
  --initial-prompt "<short domain terms>" "<chunk-name>.mp3"
```

Confirm the CLI is installed with `which mlx_whisper` — `uv tool install` puts it in an isolated venv, so `python3 -c "import mlx_whisper"` against the system Python reports it missing even when it works fine.
If `which` comes back empty, install it: `uv tool install mlx-whisper`.
A 15-minute file finishes in a few minutes; run it with `run_in_background: true` and poll rather than blocking.
The first run also downloads the model (~3GB).

One call per input file, not a file list: passing several files to one invocation reuses the first file's output name and silently overwrites every prior result with the last chunk's.
Loop over chunks and pass `--output-name` explicitly each time:

```bash
for i in 000 001 002; do
  mlx_whisper --output-name "chunk_$i" --output-dir out "chunks/chunk_$i.mp3"
done
```

Always redirect the `--verbose` console output (on by default) to a log file per chunk — it prints the full timestamped transcript as it runs, so a log survives even if the output file itself gets overwritten by the bug above.

`--condition-on-previous-text False`, `--temperature 0`, and `--compression-ratio-threshold 2.0` guard against a hallucination-repeat loop: the default `condition_on_previous_text=True` can lock onto a phrase and repeat it for the rest of the file.
Keep `--initial-prompt` short — a long prompt has been observed triggering the same loop; if a run degenerates into repetition, retry without it before anything else.

### Quality-gate every `mlx_whisper` run — do not skip this

```bash
for f in out/*.txt; do
  l=$(wc -l < "$f"); u=$(sort -u "$f" | wc -l)
  echo "$f  uniq_ratio=$(( u * 100 / l ))%"
done
```

Below roughly 80% unique lines means a hallucination loop ate the transcript, not real content — a real case dropped from 40% to 88% unique once the anti-loop flags above were applied.
Treat a failing ratio as a failed run: retry with the anti-loop flags, or without `--initial-prompt`, before trusting or saving the output.

## Diarization — verified via ElevenLabs Scribe

Local `mlx_whisper` still produces no speaker labels at all — that has not changed.
ElevenLabs Scribe's output does: each timecode line ends with a `[Speaker N]` tag.
Verified end-to-end on a 15:20, two-speaker Korean meeting recording — full 920s covered, 153 utterances, short backchannel lines (`"네."`, `"음."`) captured, no repeat/hallucination loop:

```
00:00:01,020 --> 00:00:20,780 [Speaker 0]
네. 지금 가장 큰 병목은 매뉴얼 리뷰를 몇백 개 해야 되는 거에 대한 문제가...

00:00:30,040 --> 00:00:30,540 [Speaker 1]
음.
```

`Speaker 0` / `Speaker 1` are anonymous indices, not names — Scribe has no identity input, so mapping an index to a real person is still a human judgment call from content, not something the engine hands you.
Look for a naming utterance first: in the verified run, one speaker addressed the other by name ("범수 씨가 아까 말씀드린 것처럼"), which settled the mapping outright.
Honorific/register asymmetry (존댓말 vs 반말) and role patterns (지시 vs 보고) are weaker supporting evidence — usable together, not alone.
Whatever the mapping rests on, write the reasoning into the note; do not relabel `Speaker N` → a name with no trace of why.
If no naming utterance or other clear evidence exists, leave the anonymous index label in place rather than guessing.

ElevenLabs Scribe's upload dialog has no "speaker labels" or "number of speakers" field, and its `Assign speakers from library` toggle matches against saved speaker profiles — it is still not an automatic-diarization switch, and confusing the two overstates what the toggle does.
Whether that toggle changes or is required for the `[Speaker N]` labels above is untested; treat it only as a saved-profile matcher, separate from whatever produced the verified output.

## ElevenLabs Scribe path — credit math before anything else

Only the web-UI path, driven through `aside`, is verified here — no API key was available, so the API path is undocumented and may behave differently.

The pre-upload estimate runs high — treat it as a ceiling, not a forecast: for the same 15:20 (920s) Korean recording, the upload dialog quoted **~12,785 credits needed** before clicking Upload, but the actual post-transcription charge on a completed run was only **5,063 credits** — about 330 credits/minute actual, versus ~834/minute estimated.
On the ceiling estimate a Free-plan account (10,000 credits/month) looked capped around 12 minutes; the real-cost rate suggests it may cover closer to 30 minutes, but that has not been tested — don't promise a minute ceiling, check the dialog's live numbers instead.

Check the math without spending a click:
- after choosing the file and language in the upload dialog, the modal already shows `<needed> credits / <remaining> credits` next to the Upload button — read it there, and remember it is the high-side estimate above, not the expected charge.
- clicking Upload when the needed amount exceeds the balance only surfaces a "Credit limit reached" gate; it does not charge credits, so a failed attempt costs nothing.
- to check balance on its own: bottom-left profile avatar → Balance popover (Total / Remaining / plan / workspace).

Never upgrade the plan, change the subscription, or enter payment details to clear a credit block — that decision belongs to the user, not the agent.
Report the shortfall (`needed` vs `remaining`) and stop; exit the modal with `Remind Me Later` or `Close`.
This is a validated pattern, not just a rule: an earlier run hit exactly this shortfall, reported it, and stopped; the user then funded the account directly (a Starter-plan purchase, unrelated to and outside this skill), and a follow-up run on the now-funded account transcribed successfully with diarization — the agent never touched payment at any point.
As with any browser-automation path, uploading is not transcribing — confirm the actual result file downloads, with a plausible size, before reporting success.

## Verify the key before reaching for another cloud API

Check for a real credential with a pattern that cannot silently lie about success:

```bash
# wrong — the && depends on head's exit code, not security's
security find-generic-password -s "svc" -w 2>/dev/null | head -c 8 && echo "(found)"
# right
security find-generic-password -s "svc" -w 2>/dev/null || echo "NOT FOUND"
```

A free-tier key commonly cannot process a long file and throws an upgrade prompt instead of a transcript — treat that as a credit/quota shortfall to report, not a working key, and never pay or upgrade to clear it.

## Save the output

Default: leave `.srt` / `.json` / `.txt` in the scratchpad.
When asked for an Obsidian note: include `[MM:SS]` timestamps, `[[wikilink]]` names, and frontmatter matching the target vault's convention.
For a meeting recording, split out a `## 결정 사항` (Decisions) section and quote only what the recording actually contains — write "녹취에서 확인되지 않음" (not found in the recording) rather than filling a gap.
Every engine tested here misreads domain jargon on Korean technical audio — not just local Whisper — so build a project-specific term-correction pass regardless of which engine ran:
- `mlx_whisper`: `repo` → "래퍼", `chore` → "초어", `refactor` → "리펙터", `CCS` → "css", `tangled commit` → "탱글링 커뮤니티", `Gemma` → "제임마".
- ElevenLabs Scribe: `chore` → "초원"/"초워", `Qwen` → "Q-end"/"QN", `Gemma` → "젬마", `tangled commit` → "탱글링 커미션", `imbalance` → "인밸런스", `CCS` → "CSS", `inference` → "influence".

Flag "기술용어 오인식 다수, 검증 필요" near the top of any note built from a technical recording, regardless of engine.

## Requirements

- `ffmpeg` / `ffprobe` on `PATH` for preprocessing and chunking.
- `mlx_whisper` on Apple Silicon, installed via `uv tool install mlx-whisper`; verify with `which mlx_whisper`, not a Python import check.
- `aside` CLI on `PATH` for the ElevenLabs Scribe web-UI path, only once the credit math above clears.
- A cloud STT API key only when the local engine is unavailable, verified with the `||`-based check above.
- `pyannote.audio`, named only as a pointer for real diarization — not exercised by this skill.

## Anti-patterns

- Uploading or processing a full-size video file directly → extract audio with `ffmpeg` first; a multi-GB video becomes a few-MB mono track.
- Checking `mlx_whisper` availability with `python3 -c "import mlx_whisper"` → use `which mlx_whisper`; `uv tool install` isolates it from the system Python.
- Running a local transcription synchronously and blocking on it → launch with `run_in_background: true` and poll.
- Passing multiple input files to one `mlx_whisper` call → it silently overwrites the output with only the last chunk's result; loop one call per file with an explicit `--output-name`.
- Trusting `mlx_whisper` output without the uniqueness quality gate → a hallucination loop can leave a 15-minute file with two minutes of real content and one repeated line; check `uniq_ratio` before saving or quoting anything.
- Reassembling chunked output without correcting timestamps → each chunk resets to `0:00`; add `chunk_index × segment_length` before writing a note.
- Skipping `--initial-prompt` on a domain-heavy recording → list names, jargon, and IDs up front; it measurably improves accuracy. A long prompt has also been observed triggering a hallucination loop — keep it short, drop it and retry if a run degenerates.
- Reaching for `mlx_whisper` when speaker separation is required → it produces no speaker labels at all; use ElevenLabs Scribe instead.
- Relabeling `Speaker N` → a real name with no supporting evidence → find a naming utterance, honorific/role asymmetry, or other content evidence first, and write the reasoning into the note.
- Leaving `Speaker N` unmapped-but-silently-renamed, or guessing when no evidence exists → keep the anonymous index label rather than guessing.
- Treating ElevenLabs' `Assign speakers from library` as automatic diarization → it matches saved speaker profiles, not a diarization toggle; no such toggle exists in the upload dialog, and it is untested whether it affects the `[Speaker N]` output.
- Treating the pre-upload "needed credits" estimate as the expected charge → in the verified run it overstated the real post-transcription cost by roughly 2.5×; treat it as a ceiling, not a forecast.
- Citing a fixed Free-tier minute ceiling as settled fact → the estimate-vs-actual gap means the real ceiling is unverified; check the dialog's live numbers instead of quoting a fixed minute count.
- Chaining `security find-generic-password ... | head -c 8 && echo found` to check for a key → the `&&` tests `head`'s exit code, not whether a password was found; use `|| echo "NOT FOUND"`.
- Treating a free-tier or credit-limited quota rejection as "no key found" → it is a present-but-insufficient credential; report the shortfall rather than silently falling through.
- Upgrading a plan, changing a subscription, or entering payment details to clear a credit block → report `needed` vs `remaining` and stop; exit the modal instead.
- Reporting a browser-automation transcription as done once the upload succeeds → upload success is not transcription success; confirm the result actually downloads, at a plausible size.
- Quoting a "결정 사항" that is not actually in the recording → write "녹취에서 확인되지 않음" instead of filling the gap.
- Passing Korean technical jargon through uncorrected → these engines mishear domain terms consistently; flag the note as needing human review of jargon.

## Verification

- [ ] Audio was extracted from any video source before processing (`ffmpeg -vn -ac 1 -ar 16000`), and long files were chunked with offsets tracked
- [ ] `mlx_whisper` presence was checked with `which`, the run used `run_in_background`, and each chunk got its own `--output-name`
- [ ] The output passed the uniqueness quality gate (roughly ≥80%) or was retried with anti-loop flags / a shorter prompt
- [ ] `--initial-prompt` carried the recording's domain terms without being long enough to risk a repeat loop
- [ ] If speaker separation was needed, ElevenLabs Scribe was used (not `mlx_whisper`, which has no speaker labels); `Speaker N` → identity mapping is evidence-based and the evidence is written into the note
- [ ] If ElevenLabs was considered, the pre-upload "needed credits" number was treated as a ceiling (not a forecast) and checked against the balance before attempting, and no payment or upgrade action was taken on a shortfall
- [ ] Any cloud or browser-automation fallback was gated on a confirmed real key/credit balance and a confirmed downloaded result
- [ ] Domain jargon was checked against the engine-specific misrecognition list (or a new list was built) and flagged in the note, regardless of which engine ran
- [ ] An Obsidian note output uses `[MM:SS]` timestamps, `[[wikilinks]]`, vault-matching frontmatter, quotes only what the recording contains, and flags likely jargon misrecognition
