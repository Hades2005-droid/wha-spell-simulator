# ComfyUI ElevenLabs Garden bridge

The repository bridge treats "Elvenio" as the local ComfyUI ElevenLabs
integration unless a different local service is explicitly identified. It
indexes the native ComfyUI API-node implementation and an optional local
workflow into a Shadow Garden manifest:

```sh
python3 tools/elevenlabs_garden_bridge.py status
python3 tools/elevenlabs_garden_bridge.py write
```

Set `COMFYUI_ROOT` and `COMFYUI_GARDEN_WORKFLOW` to use paths other than the
defaults. The bridge emits node names, endpoint paths, workflow node counts,
file sizes, and SHA-256 metadata. It never emits workflow prompt content,
credential values, audio payloads, or API responses.

The default mode is manifest-only. It does not submit ComfyUI prompts, call
ElevenLabs, upload files, automate a browser, or write to a remote service.
`--probe` only checks whether the configured local ComfyUI port is open. Any
live audio operation remains explicitly approval-gated.
