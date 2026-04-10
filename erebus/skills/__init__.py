"""Skills subsystem — autonomous skill creation, storage, execution, and discovery.

Skills are organized in hermes-style nested category directories:

    builtins/
    ├── mcp/
    │   ├── native-mcp/SKILL.md
    │   └── mcporter/SKILL.md
    ├── research/
    │   ├── arxiv/SKILL.md
    │   └── ...
    └── software-development/
        ├── tdd/SKILL.md
        └── ...

The loader module provides recursive skill discovery, and the registry
module maintains an in-memory index of all discovered skills.
"""
