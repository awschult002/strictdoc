# StrictDoc upstream style profile

This profile covers how to prepare changes in `awschult002/strictdoc` so they can go upstream to
`strictdoc-project/strictdoc` with little review friction. It is built from the repo docs, the config, `git log`, and
maintainer comments from 2022 to Oct 2026. Raw quotes are in `../evidence.md`.

**Maintainers:** Stanislav Pankevich (@stanislaw) has 3451 commits since 2023, 518 of the 803 PR review comments, and 892 of the
1554 issue comments. Maryna Balioura (@mettta, frontend/UI) has 1471 commits, 99 review comments, and 67 issue comments. Everyone else is far behind:
haxtibal has 79 commits and thseiler has 53. Capacity is also reduced: "approximately 25-50% of its usual capacity until the end of 2026"
(issue #3174, https://github.com/strictdoc-project/strictdoc/issues/3174).

## Hard rules (must)

1. **Run `invoke check` and get it green.** It runs lint_commit, ruff format, ruff check, mypy, and the unit, unit_server, and
   integration tests. Sources: `tasks.py` (`check`, `lint`) and `docs/strictdoc_10_contributing.sdoc` ("the very task that is run by the GitHub CI"). Comment: "you need to run through the `invoke check` tasks to get it to a green state" (https://github.com/strictdoc-project/strictdoc/pull/2071#issuecomment-2621130010).
2. **Use Conventional Commit titles with an allowed type.** The allowed types are chore, ci, docs, feat, fix, perf, refactor, release, and test. Pattern: `type(scope): description`.
   The check is enforced by `developer/git/commit_validator.py` (last 10 non-merge commits) and documented in SDG §"Git commit message". In #2631 the maintainer
   "edited your commit title slightly to make it pass the Conventional Commits checker" (https://github.com/strictdoc-project/strictdoc/pull/2631#issuecomment-3705981838).
3. **Always use a scope, and make it a folder or feature path.** Examples: `fix(backend/excel): …`, `fix(helpers/path_filter): …`.
   SDG: "most StrictDoc commits do have a scope". You can see the pattern in `git log upstream/main`.
4. **Rebase. Never merge main into your branch.** SDG: "Merging `main` into development branches shall be avoided". Comment: "Please use the
   `git fetch origin && git rebase origin/main` workflow instead of `git merge origin/main`" (https://github.com/strictdoc-project/strictdoc/pull/2767#issuecomment-4343048611).
5. **Send one commit per PR, or several self-contained commits that each pass the checks.** Source: SDG §"Commit and pull request workflow". Comments: "rebase/squash this branch
   to just one commit" (https://github.com/strictdoc-project/strictdoc/pull/3212#issuecomment-5677138412) and "Please also squash it to one commit" (https://github.com/strictdoc-project/strictdoc/pull/2742#pullrequestreview-4216866898).
6. **Split large work into independent PRs.** SDG: "split the work into several independent PRs to simplify the work of the reviewer."
   Comment: "We can expedite and do it now but with a separate PR please." (https://github.com/strictdoc-project/strictdoc/pull/2672#issuecomment-3860547367).
7. **Include tests with every behavior change.** SDG §Testing: "For every new feature, write at least one new integration or end-to-end
   test." Contributing: "A contribution without any tests is unlikely to be accepted". Only `refactor` and `chore` changes are exempt.
8. **Keep tests self-contained, with no network or third-party runtimes.** "StrictDoc's integration tests are normally self-contained. They do not install or
   execute third-party documentation frameworks" (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008139391).
9. **Keep fixtures to a minimum.** "let's reduce it to the bare minimum we need to exercise this new feature" (https://github.com/strictdoc-project/strictdoc/pull/2805#discussion_r3233215822).
10. **Use strict typing on all new code.** `tasks.py` `lint_mypy` runs `--strict --disallow-untyped-defs --warn-unused-ignores` and more.
    Comments: "Please include the type annotations for the fields too: `self.view_id: str = view_id`" (https://github.com/strictdoc-project/strictdoc/pull/1600#discussion_r1456425515) and "Is it possible that you remove this mypy ignore" (https://github.com/strictdoc-project/strictdoc/pull/2143#discussion_r2042823476).
11. **Keep lines to 80 characters, in code and docs.** `ruff.toml` `line-length = 80`. SDG §"Line length" and §"Documentation" ("Every line of documentation shall be no longer than 80 characters").
12. **Update the release notes for non-trivial user-facing changes.** Write them under the existing single "Unreleased" section and start with "This release contains the following enhancements:".
    Ignore CHANGELOG.md. Source: SDG §"How to update release notes". Comment: "I have added the release notes" (https://github.com/strictdoc-project/strictdoc/pull/2631#issuecomment-3705981838).
13. **Apply the project's writing skills to text written with AI.** Run `developer/skills/humanizer` and `crystal` on commit messages, PR descriptions, docs, and comments.
    Sources: `AGENTS.md` ("apply `developer/skills/humanizer/SKILL.md`") and https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008305526 ("just tell it to use the **crystal** … skill").

## Strong preferences (should)

14. **Write explicit None checks**, for example `if foo is not None` and `if foo is not None and len(foo) > 0`, not `if foo`. Source: SDG §"Explicit If-checks".
15. **Use full names.** Write `document`, not `doc`. Don't shadow builtins: "It is better not to use `id` … `view_id` would do just fine" (https://github.com/strictdoc-project/strictdoc/pull/1600#discussion_r1456423647).
    Add a trailing underscore to loop and lambda variables, as in `for node_ in nodes`. Sources: SDG §"Full descriptive names" and §"Short-lived/temporary variables". Ruff rule `A` is enabled in `ruff.toml`.
16. **Order code newspaper style.** Put public functions first and prefix private ones with `_`. Source: SDG §"Order and naming of functions".
17. **Open files with `file_open_read_utf8` / `file_open_read_bytes`, not a bare `open()`.** Source: SDG §"Opening files".
18. **Follow the naming conventions and reuse existing mechanisms.** Name output classes "Writers (`_writer.py`), not Exporters" (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008094657). Reuse
    `PathFilter` instead of new matching logic (https://github.com/strictdoc-project/strictdoc/pull/2805#discussion_r3233232806). "We don't require `__init__.py` files" (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008082942).
19. **Keep docs to sentence-case titles, sub-SECTIONs instead of RST underlines, and `.. note::`.** Sources: https://github.com/strictdoc-project/strictdoc/pull/2742#discussion_r2994253582 ("StrictDoc uses
    sentence-style capitalization for titles") and https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008397138.
20. **Run tests through Invoke**, with `invoke test-integration --focus X` and `invoke test-end2end --headless`. Don't write throwaway smoke tests. Sources: `AGENTS.md` §Testing and https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3445867700.

## AI-specific expectations

- AI use is fine. The maintainer uses Codex and Claude himself: "I have been using Codex until now" (https://github.com/strictdoc-project/strictdoc/pull/2766#discussion_r3293012653) and "AI authors MIDs quite well"
  (https://github.com/strictdoc-project/strictdoc/pull/3105#discussion_r3789907879). Unedited AI output gets rejected:
  - "I cannot merge this PR as is because it has too many AI patterns in it." (https://github.com/strictdoc-project/strictdoc/pull/3211#issuecomment-6255341679)
  - "Much of the text has been polished into overly abstract and general language." (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008305526)
  - "please write with less abstraction by AI." (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008362996)
  - "TOML is a legacy format but AI still added it without any practical reason." (https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3446462455)
  - "this file is a transient file from ChatGPT, not from us." (https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3445840049)
- Remove agent artifacts, unused config, and transient files. Keep prose concrete.

## Things they pushed back on

- Merging main into the PR branch (https://github.com/strictdoc-project/strictdoc/pull/2767#issuecomment-4343048611).
- External runtimes in the integration tests, such as Antora/NPM (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008139391).
- Bloated fixtures (https://github.com/strictdoc-project/strictdoc/pull/2805#discussion_r3233215822).
- New mypy ignores in new files (https://github.com/strictdoc-project/strictdoc/pull/2143#discussion_r2042823476).
- Unmanaged file handles (https://github.com/strictdoc-project/strictdoc/pull/2143#discussion_r2042832051).
- Domain-specific prefixes added to general code (https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008109351).
- New config placed in the wrong layer (https://github.com/strictdoc-project/strictdoc/pull/1600#discussion_r1456421609).
- Work that belongs in a different repo, such as templates moved to strictdoc-templates (https://github.com/strictdoc-project/strictdoc/pull/1140#issuecomment-1528726623).
- Large PRs that the maintainer ends up reworking or re-integrating in his own PR (#2143→#2159, #2587, #3049→#3071, #3211).

## Pre-submit checklist

- [ ] The branch is rebased on `upstream/main` with no merge commits, and it is one commit or a few self-contained ones.
- [ ] Every commit title passes `invoke lint-commit` and has a path-like scope.
- [ ] The PR covers one topic. Unrelated fixes go in separate PRs.
- [ ] `invoke check` is green, and `invoke test-end2end --headless` is green if you touched the UI or server.
- [ ] Each behavior change has a minimal integration, unit, or end2end test, with no network.
- [ ] mypy strict passes with no new `type: ignore` or `noqa`, and there are no new per-file-ignores in `ruff.toml`.
- [ ] The code uses explicit None checks, full names, and `file_open_read_utf8`.
- [ ] Release notes are updated under the existing "Unreleased" section. Docs are within 80 columns and use sentence-case titles.
- [ ] All text has been through humanizer/crystal, and there are no AI artifacts or filler files.
