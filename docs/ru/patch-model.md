# Patch model

PatchKit состоит из трёх слоёв:
- patch files: один логический diff на одну доработку
- manifests: привязка patch set к поддерживаемому upstream ref
- profiles: именованные наборы patch'ей, например `minimal` или `personal`

Patch должен быть маленьким, reviewable и пригодным для пере-проверки на новом upstream.
