#!/bin/sh
# Remove environment credentials before Python starts; leave the caller unchanged.
exec env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HUB_DISABLE_IMPLICIT_TOKEN=1 \
    python3 "$(dirname "$0")/transcribe_offline.py" "$@"
