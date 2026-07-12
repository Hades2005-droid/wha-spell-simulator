# C=3 Technical Scene Catalyst

The C=3 catalyst defines a deterministic technical scene-plan manifest for local
review. It is metadata only: it does not contact SillyTavern, invoke a model,
read persona content, scrape browsers, or submit media to a renderer.

`buildTechnicalSceneCatalyst` requires:

- setting metadata: location, lighting, and time of day;
- camera metadata: lens, movement, and framing;
- optional wardrobe/silhouette metadata tags;
- a local voice-route reference;
- three to five fade-friendly motion beats; and
- a safety seal confirming fictional adults, consent, and non-explicit content.

Every manifest has `catalyst: 3`, `localOnly: true`, zero external requests,
no remote writes, and `manifest_only` execution. It remains approval-gated.

Use `buildComfyUIMediaReview({ manifest, scenePlan })` to attach a validated
C=3 plan to the existing local media-review manifest. This preserves the media
review's approval and submission controls; it is not a renderer or connector.
