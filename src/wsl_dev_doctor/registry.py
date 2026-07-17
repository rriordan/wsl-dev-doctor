from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

UpdateScope = Literal["dedicated", "system", "global_js", "homebrew"]


@dataclass(frozen=True)
class ToolSpec:
    id: str
    command: str
    category: str
    version_args: tuple[str, ...] = ("--version",)
    update_command: tuple[str, ...] | None = None
    update_scope: UpdateScope | None = None


TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "apt",
        "apt",
        "System packages",
        ("--version",),
        ("sudo", "apt-get", "upgrade", "--yes"),
        "system",
    ),
    ToolSpec("snap", "snap", "System packages", ("--version",)),
    ToolSpec("flatpak", "flatpak", "System packages", ("--version",)),
    ToolSpec("brew", "brew", "System packages", ("--version",), ("brew", "update"), "homebrew"),
    ToolSpec("nix", "nix", "System packages", ("--version",)),
    ToolSpec("python3", "python3", "Python", ("--version",)),
    ToolSpec("pip", "pip", "Python", ("--version",)),
    ToolSpec("pipx", "pipx", "Python", ("--version",)),
    ToolSpec("uv", "uv", "Python", ("--version",), ("uv", "self", "update"), "dedicated"),
    ToolSpec("poetry", "poetry", "Python", ("--version",)),
    ToolSpec("conda", "conda", "Python", ("--version",)),
    ToolSpec("micromamba", "micromamba", "Python", ("--version",)),
    ToolSpec("node", "node", "JavaScript", ("--version",)),
    ToolSpec(
        "npm", "npm", "JavaScript", ("--version",), ("npm", "update", "--global"), "global_js"
    ),
    ToolSpec("npx", "npx", "JavaScript", ("--version",)),
    ToolSpec(
        "pnpm", "pnpm", "JavaScript", ("--version",), ("pnpm", "update", "--global"), "global_js"
    ),
    ToolSpec(
        "yarn", "yarn", "JavaScript", ("--version",), ("yarn", "global", "upgrade"), "global_js"
    ),
    ToolSpec("bun", "bun", "JavaScript", ("--version",)),
    ToolSpec("deno", "deno", "JavaScript", ("--version",)),
    ToolSpec("git", "git", "Source control", ("--version",)),
    ToolSpec("gh", "gh", "Source control", ("--version",)),
    ToolSpec("glab", "glab", "Source control", ("--version",)),
    ToolSpec("git-lfs", "git-lfs", "Source control", ("--version",)),
    ToolSpec("claude", "claude", "AI coding", ("--version",), ("claude", "update"), "dedicated"),
    ToolSpec("codex", "codex", "AI coding", ("--version",), ("codex", "update"), "dedicated"),
    ToolSpec("gemini", "gemini", "AI coding", ("--version",)),
    ToolSpec("aider", "aider", "AI coding", ("--version",)),
    ToolSpec("opencode", "opencode", "AI coding", ("--version",)),
    ToolSpec("goose", "goose", "AI coding", ("--version",)),
    ToolSpec("continue", "continue", "AI coding", ("--version",)),
    ToolSpec("antigravity", "antigravity", "AI coding", ("--version",)),
    ToolSpec("ollama", "ollama", "Local LLM", ("--version",)),
    ToolSpec("lmstudio", "lmstudio", "Local LLM", ("--version",)),
    ToolSpec("vllm", "vllm", "Local LLM", ("--version",)),
    ToolSpec("llama-server", "llama-server", "Local LLM", ("--version",)),
    ToolSpec("docker", "docker", "Containers", ("--version",)),
    ToolSpec("docker-compose", "docker-compose", "Containers", ("--version",)),
    ToolSpec("podman", "podman", "Containers", ("--version",)),
    ToolSpec("kubectl", "kubectl", "Platform", ("version", "--client", "--output=json")),
    ToolSpec("helm", "helm", "Platform", ("version", "--short")),
    ToolSpec("terraform", "terraform", "Infrastructure", ("version",)),
    ToolSpec("tofu", "tofu", "Infrastructure", ("version",)),
    ToolSpec("aws", "aws", "Cloud and network", ("--version",)),
    ToolSpec("az", "az", "Cloud and network", ("version",)),
    ToolSpec("gcloud", "gcloud", "Cloud and network", ("--version",)),
    ToolSpec("tailscale", "tailscale", "Cloud and network", ("version",)),
    ToolSpec("ssh", "ssh", "Cloud and network", ("-V",)),
    ToolSpec("make", "make", "Build toolchain", ("--version",)),
    ToolSpec("cmake", "cmake", "Build toolchain", ("--version",)),
    ToolSpec("gcc", "gcc", "Build toolchain", ("--version",)),
    ToolSpec("g++", "g++", "Build toolchain", ("--version",)),
    ToolSpec("clang", "clang", "Build toolchain", ("--version",)),
    ToolSpec("rustc", "rustc", "Build toolchain", ("--version",)),
    ToolSpec("cargo", "cargo", "Build toolchain", ("--version",)),
    ToolSpec("go", "go", "Build toolchain", ("version",)),
    ToolSpec("java", "java", "Build toolchain", ("--version",)),
    ToolSpec("javac", "javac", "Build toolchain", ("--version",)),
    ToolSpec("code", "code", "Editors", ("--version",)),
    ToolSpec("codium", "codium", "Editors", ("--version",)),
    ToolSpec("cursor", "cursor", "Editors", ("--version",)),
)

BUILTIN_PRESETS: dict[str, tuple[str, ...]] = {
    "ai-dev": ("claude", "codex", "gemini", "aider", "opencode", "goose", "continue", "uv"),
    "web-dev": ("node", "npm", "pnpm", "yarn", "bun", "deno"),
    "platform": ("docker", "docker-compose", "kubectl", "helm", "terraform", "tofu"),
    "core-dev": ("git", "gh", "uv", "python3", "make", "cmake"),
    "everything-safe": ("claude", "codex", "uv"),
}


def tool_by_id(tool_id: str) -> ToolSpec | None:
    return next((tool for tool in TOOLS if tool.id == tool_id), None)
