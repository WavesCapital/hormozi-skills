
# Architecture

This release uses a public-core model.

Public core:
- skill instructions
- routing manifests
- source policy
- public-safe examples and metadata

Private/user-supplied overlay:
- proprietary or copyrighted source materials
- extracted raw markdown from those materials
- any source-dependent eval fixtures

The router skill decides which `hormozi-*` skill applies. Child skills perform the domain work. Public releases intentionally avoid bundling original source materials.
