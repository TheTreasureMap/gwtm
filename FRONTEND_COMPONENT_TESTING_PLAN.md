# GWTM Frontend Component Testing Plan

Continues `FRONTEND_TESTING_PLAN.md`, which established business-logic testing and
deferred component testing. Conventions in `FRONTEND_TESTING_GUIDELINES.md` still apply.

## Starting position

151 tests cover validators, astronomical calculations and error handling. Everything
that renders is untested:

| Area | Size | Coverage |
| --- | --- | --- |
| `src/lib/components/**/*.svelte` | 57 components | excluded from coverage |
| `src/routes/**` | 18 pages | excluded from coverage |
| `src/lib/stores/auth.ts` | 213 lines | 0% |
| `src/lib/stores/formStore.ts` | 514 lines | 0% |

Total Svelte source: 16,117 lines.

## Why now

No component uses Svelte 5 runes. All 52 components with props use `export let`, `$:`,
`<slot>` and `$$slots`, so the entire UI runs in Svelte 5's legacy compatibility mode.
That mode goes away in Svelte 6, and migrating means rewriting the reactive core of every
component. Tests written now are the safety net for that migration.

The same gap shows up immediately in dependency upgrades: a Svelte 5.33 to 5.57 bump
passes CI without exercising a single component.

## Scope

Testable under vitest and jsdom:

| Category | Count | Notes |
| --- | --- | --- |
| Presentational | ~12 | Props in, DOM out |
| Form components | ~7 | Needs `user-event` |
| Tables | ~4 | Needs fixtures |
| Importing the API client | 20 | Needs module mocking |

Out of scope for jsdom:

- `SkyVisualization` (1155 lines), `OverlayManager` (546), `AladinVisualization`,
  `EventExplorer`, `FootprintVisualization`, `CoverageCalculatorTab`. These wrap Aladin
  Lite and plotly, which need canvas and WebGL. They belong in Playwright, tracked
  separately.
- Route pages. They need `$app/*` and `$env/*` runtime mocks and are deferred until the
  component layer is established.

## Phases

Each phase is independently shippable.

### Phase 0: harness (done)

`@testing-library/svelte` and `@testing-library/user-event` are installed.
`src/lib/setup.ts` mocks `$app/environment`, `$app/navigation` and `$app/stores`, and
calls `cleanup()` after each test. Tests live in `__tests__/` next to the code under test.

Three things the harness needs that are not obvious:

**`resolve.conditions: ['browser']` in `vitest.config.ts`.** Without it Vite resolves
Svelte's server build and every render fails with `lifecycle_function_unavailable`.

**`component.$on` does not exist.** Svelte 5 removed it, including for components written
in legacy syntax, and calling it throws `component_api_changed`. Forwarded events are wired
through `mount`'s `events` option, which `render` passes through:

```ts
render(Button, { props: { disabled: true }, events: { click: onClick } });
```

**`vi.mock` factories are hoisted above imports.** A factory needing a real module must
pull it in itself with `await vi.importActual(...)` rather than referencing a top-level
import.

### Phase A: stores (done)

`formStore.ts` backs every form in the application; `auth.ts` wraps token and localStorage
state. Both are plain TypeScript, so they need no rendering and no component harness.

Done: `formStore` (44 tests), `auth` (26 tests). Store coverage went from 0% to 99.4%,
which took the whole-project figure from 51.92% to 96.05%.

`auth.ts` exports a singleton and calls `init()` at import, so its tests take a fresh copy
per case via `vi.resetModules()` and a dynamic import. `$lib/api` and
`$lib/utils/errorHandling` are mocked at module scope.

`setFieldValue` schedules its form-wide revalidation on a macrotask, so assertions about
overall validity have to await a tick. Per-field errors update synchronously.

### Phase B: presentational components (started)

The ~12 components that take props and render markup: `Button`, `Card`, `StatusBadge`,
`LoadingSpinner`, `ErrorMessage`, `PageHeader`, `BackLink`, `QuickActionCard` and
similar. The purpose is to establish a pattern the team can copy, not to find bugs.

Done: `StatusBadge` (8 tests), `Button` (15 tests, including forwarded-event handling).

Target: 30-40 tests.

### Phase C: form components

`FormField.svelte` (568 lines) is the highest-value component in the codebase: every field
in every submission flow renders through it. Cover validation display, error states,
conditional rendering and real typing via `user-event`. Then `Form`, `CoordinateFields`,
`TimeField`, `FootprintTypeSelector`, `ConditionalSection`.

Target: 50-70 tests.

### Phase D: tables

`PointingsTable`, `AlertResultsTable`, `ExistingInstrumentsTable`,
`ReportingInstrumentsTable`. Fixture data in, rows out, plus sorting, empty states and
pagination.

Target: 25-35 tests.

## Coverage thresholds

Phase A raised the measured figures well clear of the current gates, so
`src/lib/stores/**` can take a threshold of its own now.

Components stay excluded from coverage until Phase B completes, then get their own low
starting thresholds that ratchet up per phase.

Two constraints on when to set them:

Removing the component exclusion drops global coverage far below the current global
threshold of 80, so CI fails before the components are covered.

Vitest 4 changes coverage measurement. Measured on identical code and tests, branch
coverage on `src/lib/validation/**` reads 99.2% under vitest 3 and 87.07% under vitest 4;
`src/lib/utils/**` reads 95.4% and 76.72%. The vitest 3 figures are inflated, because
vitest 4 makes AST-aware remapping the default. Set thresholds after that upgrade lands,
against honest numbers, rather than tuning them twice.
