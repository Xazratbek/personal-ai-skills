---
name: pragmatic-clean-code
description: Use when Codex is writing, editing, refactoring, or reviewing application code and must keep it readable, maintainable, simple, and architecture-aware. Trigger for requests that mention clean code, readable code, SOLID, DRY, KISS, YAGNI, PEP8, architecture, refactoring, AI-generated code quality, maintainability, service/view/component boundaries, or making code easier for humans to understand.
---

# Pragmatic Clean Code

## Mission

Write code that a capable developer can understand, change, and test later without asking why obvious decisions were hidden. Treat SOLID, DRY, KISS, YAGNI, PEP8/style guides, patterns, and architecture as decision tools, not universal laws. Prefer the simplest design that fits the current codebase and the known change.

Optimize for the next reader first: the main path should be discoverable from names, file placement, and function shape. Working code is not complete if the important business decision is buried in a large view, generic helper, unexplained abstraction, or long function that requires re-reading.

## Non-Negotiable Workflow

1. Read the surrounding code before editing. Identify the existing architecture, naming style, module boundaries, validation patterns, error handling, tests, and formatting tools.
2. State the intended shape for non-trivial changes before editing: where logic belongs, which existing pattern will be followed, and which principle is driving the decision.
3. Keep the behavioral change narrow. Do not refactor unrelated code, rename broadly, or introduce a new architecture unless the task requires it.
4. Separate responsibilities at the smallest useful boundary. Keep UI/views/controllers thin; move domain decisions, validation, permissions, status transitions, data access, and side effects to the existing appropriate layer.
5. Keep each non-trivial function shaped around one level of abstraction. If a function mixes validation, querying, decision-making, mutation, and response formatting, split it before finalizing.
6. Use tests, linting, type checks, or focused manual checks that match the risk of the change. If verification cannot run, say exactly why.
7. Do a final self-review for readability, unnecessary abstraction, duplication, naming, error paths, and consistency with local patterns before responding. Fix issues found by the review instead of only reporting them.

## Principle Selection

Apply principles according to context:

- KISS: Default to the simplest readable implementation. Remove cleverness, hidden control flow, and generic machinery unless they clearly reduce real complexity.
- YAGNI: Do not add extension points, interfaces, configuration, generic helpers, factories, or framework layers for hypothetical future needs.
- DRY: Remove duplication only when repeated code has the same reason to change and the new name makes the domain clearer. Keep small duplication when abstraction would hide intent, couple unrelated concepts, or require vague names.
- SOLID: Use mainly where there are stable domain/service boundaries, classes, plugins, multiple implementations, or meaningful dependency seams. Do not force SOLID ceremony into small scripts, simple views, or one-off transformations.
- Style guides such as PEP8: Follow project tooling and language conventions, including line length and wrapping. Remember that formatting is not enough: names, boundaries, and explicit behavior matter more than superficial style compliance.
- Design patterns: Use established local patterns first. Introduce a named pattern only when it solves a present problem more clearly than direct code.

## Readability Rules

Prefer:

- Domain-specific names such as `reserve_stock_for_order` over vague names such as `process_data`.
- Short functions with one clear reason to change.
- Function names that describe the domain action and return value. Prefer `reserve_stock_for_order` over `reserve_order_stock` when the object being changed is stock reservation behavior, and prefer returning the updated domain object over forcing callers to re-fetch it.
- Explicit data flow over hidden mutation.
- Plain conditionals over over-generalized polymorphism when only one or two cases exist.
- Small, named helpers when they clarify business intent.
- Comments that explain why a non-obvious decision exists, not what the next line does.

Avoid:

- Large components, views, or services that mix rendering, fetching, validation, permissions, persistence, and business rules.
- Premature base classes, interfaces, factories, registries, hooks, or utilities.
- Generic names like `handle`, `manager`, `utils`, `data`, `item`, or `process` when a domain name is available.
- Refactors that only make code look abstract without reducing cognitive load.
- Passing lint while leaving behavior difficult to reason about.
- Re-fetching data only because a function did not return the useful updated object.
- Long single-line framework declarations when wrapping would make the code easier to scan.

## Function Shape Rules

Use these as guardrails, not hard math:

- Keep orchestration functions readable in one screen when practical. If a function grows past roughly 40-60 lines or has more than three nested decision levels, look for named helpers.
- Extract helpers around domain concepts, not programming mechanics. Prefer `_ensure_stock_is_available` over `_check_data`.
- Keep query-building, precondition checks, and mutation steps visibly separated in business workflows.
- Do not create a helper for a single line unless the helper name reveals a business rule.
- Avoid returning unused values. If a service returns data, the caller should use it; otherwise return only the updated domain object or nothing.

## Architecture Boundaries

When the project has layers, keep them meaningful:

- Views/controllers/components: orchestration, request/response handling, rendering, and user interaction.
- Domain/services/use cases: business rules, workflows, status changes, permission decisions, and cross-entity coordination.
- Repositories/API clients/data access: persistence, external calls, query details, serialization boundaries.
- Validators/schemas/forms: input shape, type coercion, field-level validation, and user-facing validation errors.

If the existing project does not use these exact names, follow its closest equivalent instead of inventing a parallel structure.

## AI Coding Discipline

Before writing code, check whether the request needs clarification. Ask only when a wrong assumption would create risky behavior. Otherwise make a conservative assumption and state it.

During implementation:

- Prefer changing existing code in place over adding parallel systems.
- Keep public APIs backward compatible unless the user requested a breaking change.
- Preserve user changes and unrelated dirty work.
- Use structured parsers and framework APIs instead of fragile string manipulation when available.
- Keep dependencies unchanged unless a dependency is clearly justified and approved when needed.
- Prefer readable framework usage over compressed one-liners. Wrap long querysets, serializer updates, decorators, and response construction when they carry multiple ideas.
- If a workflow has business rules, test both the success path and the important failure paths. Tests should name the behavior, not the implementation detail.

After implementation, report:

- What changed.
- Why the chosen structure is readable and proportional.
- What verification ran or could not run.
- Any remaining risk or follow-up that matters.

## Final Quality Gate

Before the final response, inspect the changed code as if reviewing another agent's work. Fix the code before finalizing if any of these are true:

- A view/controller/action contains business rules that belong in a service/domain layer.
- A service function mixes precondition validation, query locking, availability checks, mutation, and response shaping without clear named sections or helpers.
- A caller re-fetches data that the called function could return clearly.
- A function name is vague or describes implementation instead of domain behavior.
- A line is technically valid but harder to scan because it compresses multiple framework calls or assignments.
- Tests pass but do not cover the main failure mode introduced by the change.
- The implementation adds an abstraction whose name is generic or whose only purpose is to look architectural.

## Review Checklist

Use this checklist before final output:

- Can a developer understand the main path in one pass?
- Are names specific to the domain and behavior?
- Is business logic outside UI/view/controller code where the project supports that?
- Did DRY avoid only true same-reason duplication?
- Did KISS/YAGNI prevent unnecessary abstraction?
- Is SOLID used only where it improves substitutability, testability, or boundaries?
- Are error and edge cases visible?
- Are tests or checks proportional to the change?
- Did the final code become more understandable than the first working draft?
