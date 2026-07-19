# Agent Task Completion Contract

> **Role:** stable definition of how a selected agent task closes, fails, and routes to its successor.
> **Current machine source:** `docs/agent/TASK_CATALOG.json`

## Purpose

Onboarding already determines what the agent must read and execute. The completion contract closes the other half of the loop: what must be produced, which current-state fields must change, how failure remains visible, and which successor may be selected.

## Ownership

- `TASK_CATALOG.json` owns task-specific PASS, FAIL, and always-required completion rules.
- `AGENT_TASK.json` is the generated current view and must reproduce the selected catalog contract byte-for-byte as JSON data.
- `STATE.json` owns temporal selection and must keep every action-class field aligned.
- Frozen evidence and machine authority own accepted claims; generated views never do.

## PASS routing

A PASS must produce every declared output role, freeze an independent audit and machine authority, apply every declared state update, prepare the named successor catalog entry, regenerate views, verify the repository, and leave clean `main` ready for bundle export.

The successor cannot be selected merely because its name exists. Before selection, its catalog entry must bind the newly accepted predecessor authority and carry its own completion contract.

## FAIL routing

A FAIL remains a complete result. It must preserve the first meaningful failure, classification, blocked downstream work, and claim boundary. State must record the failure or blocker. The action remains current unless a bounded correction task is explicitly cataloged and declares the action it resumes.

## Invariants

1. `STATE.next_action_class`, `STATE.program.next_action_class`, `STATE.control_work.next_action_class`, and `STATE.control_work.resume_program_action_class` are identical.
2. Stable module revisions and SHA-256 identities in `STATE.json` match their files.
3. Active-plan identities in `STATE.json` match their files.
4. The selected task resolves exactly once in the catalog.
5. The selected task has a completion contract and its successor resolves exactly once.
6. New tracked Markdown/JSON updates the lifecycle registry.
7. Current/generated paths are never newly bound by frozen authority.
