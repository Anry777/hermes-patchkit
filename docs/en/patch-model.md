# Patch model

PatchKit uses three layers:
- patch files: one logical customization per diff
- manifests: map patches to a supported upstream ref
- profiles: named patch selections such as `minimal` or `personal`

A patch should be small, reviewable, and easy to revalidate against a new upstream version.
