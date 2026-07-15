# WSL Dev Environment Doctor Report

Generated: `2026-07-15T21:52:00+00:00`

## Summary

- ✅ Pass: 4
- ⚠️ Warnings: 2
- ❌ Failures: 0
- ℹ️ Informational: 2

## Checks

| Status | Category | Check | Result |
| --- | --- | --- | --- |
| ✅ PASS | Platform | `platform.wsl` | WSL environment detected. |
| ✅ PASS | Toolchain | `toolchain` | Required development tools are available. |
| ⚠️ WARN | Environment | `path` | PATH contains 2 nonexistent entries. |
| ℹ️ INFO | Environment | `environment` | Environment variable names inventoried; values were not read or reported. |
| ✅ PASS | Storage | `disk` | Root filesystem is 11% used. |
| ⚠️ WARN | Containers | `docker` | Docker daemon is unavailable. |
| ℹ️ INFO | Network | `ports` | Found 47 listening TCP port(s). |
| ✅ PASS | GPU | `gpu` | NVIDIA GPU visible: NVIDIA GeForce RTX 5070 Ti. |

## Prioritized remediation

1. **path** — Remove or correct stale PATH entries in your shell configuration.
2. **docker** — Start Docker Desktop and enable WSL integration, or install/start Docker Engine in this distribution.

## Privacy note

This report is read-only. Environment-variable values, shell history, credentials, and configuration files are not collected.
