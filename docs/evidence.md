# Evidence: raw maintainer quotes

These are the full comment bodies, capped at 600 characters, from the GitHub API (`pulls/comments` and `issues/comments` since 2022-01-01, plus PR reviews).

- https://github.com/strictdoc-project/strictdoc/pull/1140#issuecomment-1528726623
  > @stanislaw 2023-04-29: Here we go: https://github.com/strictdoc-project/strictdoc-templates  Could I ask you to re-create this PR there?  The best strategy for testing them will be to keep them in that repository, in a folder `templates/`. I could quickly set up a test of integration tests that verify the integrity of the templates by running strictdoc against them.
- https://github.com/strictdoc-project/strictdoc/pull/1600#discussion_r1456421609
  > @stanislaw 2024-01-17: Now that I see it implemented this way, I realize that we should rather move the `DEFAULT_VIEW` to the DocumentConfig as follows. It will make the meaning of this field consistent with the other fields because it is actually an option.  ``` [DOCUMENT] TITLE: Requirements UID: SDOC_REQ OPTIONS:   REQUIREMENT_STYLE: Inline   DEFAULT_VIEW: PRINT_VIEW VIEWS: ... ```  Simply make the `DEFAULT_VIEW` to be the last field of the document config part. Also this makes sense when we get to editing the document options in the UI and the default view will be co-located with the other document 
- https://github.com/strictdoc-project/strictdoc/pull/1600#discussion_r1456423647
  > @stanislaw 2024-01-17: It is better not to use `id` because it is a Python built-in and some quality tools may complain that you overlap with Python's id:  ``` strictdoc-project/strictdoc (html) $ python Python 3.7.15 (default, Dec 29 2022, 19:39:20) [Clang 14.0.0 (clang-1400.0.29.202)] on darwin Type "help", "copyright", "credits" or "license" for more information. >>> id <built-in function id> ```  In this case, `view_id` would do just fine.
- https://github.com/strictdoc-project/strictdoc/pull/1600#discussion_r1456425515
  > @stanislaw 2024-01-17: Please include the type annotations for the fields too:  `self.view_id: str = view_id`  This extra verbosity pays off when the static analyzers can give you helpful hints if you happen to use these types incorrectly somewhere else in the code. The developer guide mentions this.  I will not comment on the similar issues below. Please double-check this for all `self.*` fields in the PR.
- https://github.com/strictdoc-project/strictdoc/pull/2071#issuecomment-2621130010
  > @stanislaw 2025-01-29: Thank for working on this. It looks like you need to run through the `invoke check` tasks to get it to a green state.
- https://github.com/strictdoc-project/strictdoc/pull/2143#discussion_r2042823476
  > @stanislaw 2025-04-14: Is it possible that you remove this mypy ignore. It is a new file, so you probably just need to add just a few types here and there.
- https://github.com/strictdoc-project/strictdoc/pull/2143#discussion_r2042832051
  > @stanislaw 2025-04-14: Since this is not using `with`, we should either use `exit_stack` like does it in `tests/end2end/server.py`, or use explicit close() calls in the close() method.  Otherwise, we will probably be leaking the file descriptors. I don't know how Python handles this but with sockets those would definitely not be closed after the process terminates.
- https://github.com/strictdoc-project/strictdoc/pull/2631#issuecomment-3705981838
  > @stanislaw 2026-01-02: @thseiler thanks a lot for contributing! I have added the release notes and edited your commit title slightly to make it pass the Conventional Commits checker (see #2632). 
- https://github.com/strictdoc-project/strictdoc/pull/2672#issuecomment-3860547367
  > @stanislaw 2026-02-06: I was going to drop 3.9 very soon. We can expedite and do it now but with a separate PR please.
- https://github.com/strictdoc-project/strictdoc/pull/2742#discussion_r2994253582
  > @stanislaw 2026-03-26: ```suggestion TITLE: Asset upload endpoint ```  (StrictDoc uses sentence-style capitalization for titles)
- https://github.com/strictdoc-project/strictdoc/pull/2742#pullrequestreview-4216866898
  > (review body or issue; see link)
- https://github.com/strictdoc-project/strictdoc/pull/2766#discussion_r3293012653
  > @stanislaw 2026-05-23: The PR had a few instances of this. @thseiler I am curious if this is produced by an AI tool. Which tool did you possibly use to create it? I would be curious if we could extend our Dev Guide and let all AI tools avoid creating this pattern in the future.  (I have been using Codex until now and haven't seen this pattern from it)
- https://github.com/strictdoc-project/strictdoc/pull/2767#issuecomment-4343048611
  > @stanislaw 2026-04-29: Hey @xxhoeckyxx, thanks for contributing this. I was away from StrictDoc for some time due to other tasks but now I am back.  I see that you are merging in the latest main branch to your branch and that creates redundant commits in this PR. Please use the `git fetch origin && git rebase origin/main` workflow instead of `git merge origin/main` to make the Git history of this PR to only contain your work and no unrelated commits.
- https://github.com/strictdoc-project/strictdoc/pull/2805#discussion_r3233215822
  > @stanislaw 2026-05-13: Yes, copying is of course fine but let's reduce it to the bare minimum we need to exercise this new feature.  In particular, let's remove this XML file. And also I think it should be enough to only leave this test function in the test file as it is the only one you are actually testing against:  ``` TEST(MyTestSuiteName, TestName) ```  (the background for this is that StrictDoc has lots of test boilerplate and I try to reduce how much boilerplate is needed and used by each test)
- https://github.com/strictdoc-project/strictdoc/pull/2805#discussion_r3233232806
  > @stanislaw 2026-05-13: I am curious if there is an opportunity for reusing the already implemented filtering mechanism. Could we use the same approach that is used for `include_doc_paths` and `include_source_paths`? These filters are based on `PathFilter`.  See around these lines:  ``` path_filter_includes = PathFilter(             include_paths, positive_or_negative=True         ) ```  This way the new `tree_map_test_path_pattern` will simply follow the same configuration interface (an array of lines to whitelist) and use the same filtering mechanism.
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3445840049
  > @stanislaw 2026-06-20: It looks like this file is a transient file from ChatGPT, not from us. Should we keep it here?  I see that our gitignore file already had these files excluded. Maybe this was added a little after.
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3445867700
  > @stanislaw 2026-06-20: I will extract this to a separate PR myself as I wanted to add similar notes to the AGENTS. In particular I want that the agents always use our `invoke test*` helpers instead of trying of figure their own custom methods for running tests.
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3446462455
  > @stanislaw 2026-06-20: This file can be removed. TOML is a legacy format but AI still added it without any practical reason.  `section_behavior = "[[SECTION]]"` is our default behavior can has no effect.
- https://github.com/strictdoc-project/strictdoc/pull/3105#discussion_r3789907879
  > @stanislaw 2026-08-15: AI authors MIDs quite well. It is very useful for creating L2 or L3 requirements with Claude. I would not introduce this rule here.
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008082942
  > @stanislaw 2026-09-14: We don't require `__init__.py` files in this repo. You can safely remove it from the changeset.
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008094657
  > @stanislaw 2026-09-14: We normally call these classes Writers (`_writer.py`), not Exporters. The format readers/parsers are called Readers (when supported by a format).
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008109351
  > @stanislaw 2026-09-14: Is `sd_uid_` something very custom to your project / domain?  If it has general applicability, there has to be a comment explaining what this prefix is about.  If it is something custom, is there a way, we could avoid introducing it here for a general AsciiDoc exporter?
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008139391
  > @stanislaw 2026-09-14: Thank you for adding the Antora integration test. Testing this integration is valuable, but I do not think the Antora build should become part of StrictDoc’s integration test suite.  StrictDoc’s integration tests are normally self-contained. They do not install or execute third-party documentation frameworks, and they do not require network access. Adding NPM and Antora would introduce another runtime, a large dependency tree, network-dependent setup, and failures outside StrictDoc’s control.  Instead of keeping the entire Antora example here, I suggest that you create a very representative se
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008305526
  > @stanislaw 2026-09-14: Two comments:  1) This documentation seems to have been produced by AI. Much of the text has been polished into overly abstract and general language. Below, I will make a few comments to explain what I mean.  2) As a general note, we have merged a set of technical writing skills that can be used to improve AI's technical writing.  Since you use AI, just tell it to use the **crystal** (as in 'crystal clear writing') skill from `developer/skills/crystal` for polishing your final text. Explore the skill itself and see what it does by calling to the lower-level skills.
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008362996
  > @stanislaw 2026-09-14: This sentence is not clear: `retains` in which sense? Does this mean that the output AsciiDoc file name and output path are constructed from the source doc's file name / relative directory?  Either way, please write with less abstraction by AI.
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008397138
  > @stanislaw 2026-09-14: We normally don't use RST's section constructs such as `~~~~~~~~~~~~~~~~~~`. Instead, please create a sub-SECTION and have the following text in its own TEXT node.  This way the section will be accurately reflected in the User Guide's TOC.
- https://github.com/strictdoc-project/strictdoc/pull/3211#issuecomment-6255341679
  > @stanislaw 2026-10-18: Hey @yashi, I did a round of review and realized that I cannot merge this PR as is because it has too many AI patterns in it. I would prefer to avoid leaving a long list of review comments because I don't have enough time to give you instructions precise enough to avoid further rework and review iterations.  Instead, I would prefer to rework this change extensively from the ground up and integrate it myself. For this, I would need a good chunk of uninterrupted time, which I currently don't have. See https://github.com/strictdoc-project/strictdoc/issues/3174.  I encourage you to maintain a 
- https://github.com/strictdoc-project/strictdoc/pull/3212#issuecomment-5677138412
  > @stanislaw 2026-09-15: Please fix the linting issues and rebase/squash this branch to just one commit.

## AI-related maintainer comments (all found)
- https://github.com/strictdoc-project/strictdoc/pull/2672#discussion_r2776158870 (@stanislaw 2026-02-06)
  > It is the most detailed code comment that StrictDoc ever had 👍   It makes me wondering if we should introduce an existing formalism for documenting function parameters? Otherwise the parameters are not easily to distinguish from the rest of the descriptive text.  E.g., `:param name: An identifier that should be globally unique for...`...  ChatGPT says there are three different conventions:   1) Sphinx-style and PEP 257. 2) Google style. 3) NumPy style.  I guess we would pick the first one or just use colons like you did for `attributes:` below? 🤔 
- https://github.com/strictdoc-project/strictdoc/pull/2672#discussion_r2777422689 (@stanislaw 2026-02-07)
  > > attributes: is only one colon away from reST/Sphinx syntax, so I'd vote to do :attributes: to have something that's commonly used. This will also become useful for distinction should we want to mix our source node syntax (key: value) with API documentation (:param: description).  Yes, let's go with reST/Sphinx syntax 👍 In the future, we could ask Codex/Claude to fix all this stuff automatically to be consistent.
- https://github.com/strictdoc-project/strictdoc/pull/2766#discussion_r3293012653 (@stanislaw 2026-05-23)
  > The PR had a few instances of this. @thseiler I am curious if this is produced by an AI tool. Which tool did you possibly use to create it? I would be curious if we could extend our Dev Guide and let all AI tools avoid creating this pattern in the future.  (I have been using Codex until now and haven't seen this pattern from it)
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3445840049 (@stanislaw 2026-06-20)
  > It looks like this file is a transient file from ChatGPT, not from us. Should we keep it here?  I see that our gitignore file already had these files excluded. Maybe this was added a little after.
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3446462455 (@stanislaw 2026-06-20)
  > This file can be removed. TOML is a legacy format but AI still added it without any practical reason.  `section_behavior = "[[SECTION]]"` is our default behavior can has no effect.
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3446463411 (@stanislaw 2026-06-20)
  > This file can be removed. TOML is a legacy format but AI still added it without any practical reason.  `section_behavior = "[[SECTION]]"` is our default behavior can has no effect.
- https://github.com/strictdoc-project/strictdoc/pull/2936#discussion_r3446477305 (@stanislaw 2026-06-20)
  > Does it make sense to make this a general helper? It would make this test shorter and help us to reuse the helper in other places. AI also likes to reuse stuff when he see an opportunity for doing it.
- https://github.com/strictdoc-project/strictdoc/pull/3049#discussion_r3652991658 (@stanislaw 2026-07-26)
  > @martinezlc99, I have tried testing this branch against StrictDoc's own documentation. I set the threshold to a small value as follows:  ```     DEFAULT_CHUNKED_DOCUMENTS_THRESHOLD = 5 ```  When I reload the User Guide document and I start scrolling slowly, I start seeing empty gaps starting from the section:  <img width="635" height="576" alt="Image" src="https://github.com/user-attachments/assets/b4064d6a-8658-4d47-9123-3ed63955fb60" />  I gave it to ChatGPT quickly and it produced the following change that seems to fix it however I didn't spend enough time with your PR to fully un
- https://github.com/strictdoc-project/strictdoc/pull/3105#discussion_r3789907879 (@stanislaw 2026-08-15)
  > AI authors MIDs quite well. It is very useful for creating L2 or L3 requirements with Claude. I would not introduce this rule here.
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008305526 (@stanislaw 2026-09-14)
  > Two comments:  1) This documentation seems to have been produced by AI. Much of the text has been polished into overly abstract and general language. Below, I will make a few comments to explain what I mean.  2) As a general note, we have merged a set of technical writing skills that can be used to improve AI's technical writing.  Since you use AI, just tell it to use the **crystal** (as in 'crystal clear writing') skill from `developer/skills/crystal` for polishing your final text. Explore the skill itself and see what it does by calling to the lower-level skills.
- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008362996 (@stanislaw 2026-09-14)
  > This sentence is not clear: `retains` in which sense? Does this mean that the output AsciiDoc file name and output path are constructed from the source doc's file name / relative directory?  Either way, please write with less abstraction by AI.
- https://github.com/strictdoc-project/strictdoc/issues/2121#issuecomment-2954137415 (@stanislaw 2025-06-08)
  > @thseiler some new information. This issue reproduces itself quite often. The recent failed job:  https://github.com/strictdoc-project/strictdoc/actions/runs/15519701080/job/43691247941?pr=2313  ``` error: Parallelizer: One of the child processes has exited prematurely. error: Parallelizer: Failed child process: PID: 5868, exit code: 3221356611. ```  Checking this with ChatGPT reveals that 3221356611 is a special exit code.  ``` RPC_NT_INTERNAL_ERROR 0xC0020043 (3221356611)  ```  I will check further what we could do with it.
- https://github.com/strictdoc-project/strictdoc/pull/2333#issuecomment-2974342531 (@stanislaw 2025-06-15)
  > @thseiler I was too fast with my wishful thinking and closed the issue yesterday but the issue appeared again. I became upset and finally set up the Windows machine. After some tinkering and talking with Copilot about Windows, I found that these two lines fix the issue.   ----  Along the way I became more motivated to finally solve this code climate issue where the SDReader catches some exceptions and does `sys.exit(1)` by itself whereas the better practice would be to only exit from one place and that is from the `main()` function. I will remove this chunk of code pretty soon and all exc
- https://github.com/strictdoc-project/strictdoc/issues/3041#issuecomment-4972690443 (@stanislaw 2026-07-14)
  > Hey @willem445,  This is what I currently do to simplify handling of draw.io in StrictDoc's own documentation: https://github.com/strictdoc-project/strictdoc/blob/432643a61c4c5bff13b3eb61cbc8f1f76e58ceec/tasks.py#L1267  I use the desktop version of draw.io and maintain the source of truth here: https://github.com/strictdoc-project/strictdoc/tree/main/developer/drawio. The Invoke task converts the drawio files to images and copies them to the assets folder. This is still manual effort but it is better than making screenshots manually.  In theory, we could make the web interface support opening 
- https://github.com/strictdoc-project/strictdoc/pull/3211#issuecomment-6255341679 (@stanislaw 2026-10-18)
  > Hey @yashi, I did a round of review and realized that I cannot merge this PR as is because it has too many AI patterns in it. I would prefer to avoid leaving a long list of review comments because I don't have enough time to give you instructions precise enough to avoid further rework and review iterations.  Instead, I would prefer to rework this change extensively from the ground up and integrate it myself. For this, I would need a good chunk of uninterrupted time, which I currently don't have. See https://github.com/strictdoc-project/strictdoc/issues/3174.  I encourage you to maintain a 

## Issue #3174
- https://github.com/strictdoc-project/strictdoc/issues/3174 > The StrictDoc core team is working at approximately 25-50% of its usual capacity until the end of 2026.
- https://github.com/strictdoc-project/strictdoc/pull/2742#pullrequestreview-4216866898 > Please also squash it to one commit on the way — it could help me review the next iterations locally.

## Triage of missing.txt (28 candidate AI-related comments)

Result: none of the 28 are real AI-related comments. They matched on other meanings of "generated": generated HTML, auto-generated changelogs, generated sites, and auto-generated content. One of them is still useful as a rule source (rule 8):

- https://github.com/strictdoc-project/strictdoc/pull/3211#discussion_r4008243992
  > I suggest creating a small separate compatibility repository or example project. Its CI can install Antora and build the generated site.
  > Please also pin the Antora version and commit package-lock.json so that the compatibility test remains reproducible.

Rejected as false hits (not AI-related):
- https://github.com/strictdoc-project/strictdoc/pull/282#issuecomment-753633870
- https://github.com/strictdoc-project/strictdoc/pull/444#issuecomment-893765381
- https://github.com/strictdoc-project/strictdoc/issues/494#issuecomment-944273774
- https://github.com/strictdoc-project/strictdoc/issues/462#issuecomment-1127016988
- https://github.com/strictdoc-project/strictdoc/issues/1093#issuecomment-1545599711
- https://github.com/strictdoc-project/strictdoc/issues/366#issuecomment-1596186268
- https://github.com/strictdoc-project/strictdoc/pull/1466#issuecomment-1817068767
- https://github.com/strictdoc-project/strictdoc/pull/1921#issuecomment-2241597974
- https://github.com/strictdoc-project/strictdoc/issues/2100#issuecomment-2707296584
- https://github.com/strictdoc-project/strictdoc/issues/2107#issuecomment-2724387719
- https://github.com/strictdoc-project/strictdoc/issues/2107#issuecomment-2732899058
- https://github.com/strictdoc-project/strictdoc/pull/2123#issuecomment-2744505316
- https://github.com/strictdoc-project/strictdoc/issues/2107#issuecomment-2799872477
- https://github.com/strictdoc-project/strictdoc/issues/2147#issuecomment-2817171262
- https://github.com/strictdoc-project/strictdoc/issues/2107#issuecomment-2845490350
- https://github.com/strictdoc-project/strictdoc/issues/2231#issuecomment-2873874939
- https://github.com/strictdoc-project/strictdoc/issues/2345#issuecomment-3014602947
- https://github.com/strictdoc-project/strictdoc/issues/2435#issuecomment-3218294747
- https://github.com/strictdoc-project/strictdoc/issues/2435#issuecomment-3221785238
- https://github.com/strictdoc-project/strictdoc/issues/2435#issuecomment-3223090471
- https://github.com/strictdoc-project/strictdoc/issues/2435#issuecomment-3227058518
- https://github.com/strictdoc-project/strictdoc/issues/2435#issuecomment-3248110092
- https://github.com/strictdoc-project/strictdoc/issues/2435#issuecomment-3263692802
- https://github.com/strictdoc-project/strictdoc/issues/2595#issuecomment-3673997808
- https://github.com/strictdoc-project/strictdoc/pull/2742#issuecomment-4071738337
- https://github.com/strictdoc-project/strictdoc/pull/2742#issuecomment-4078501102
- https://github.com/strictdoc-project/strictdoc/issues/2068#issuecomment-5231599015
