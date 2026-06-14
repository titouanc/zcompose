# Contributing to zcompose

Thanks for your interest in improving `zcompose`! Contributions of all kinds
(bug reports, fixes, documentation, new features, ...) are welcome.

## Pull request workflow

We use the standard GitHub Pull Request workflow:

1. **Fork** the repository and create a topic branch off `main`.
2. **Make your changes** in focused, logically separated commits.
3. **Test and lint** locally before submitting:

   ```console
   pip install -e .
   pip install pytest ruff
   pytest          # run the test suite
   ruff check .    # lint
   ```

4. **Open a pull request** against `main`. Describe what the change does and why,
   and link any relevant issues if applicable.
5. A maintainer will review your PR. Address review feedback by pushing
   additional commits to the same branch.

Please keep PRs reasonably small and self-contained — they are easier to review
and faster to merge.

## Commit messages

- Write clear, descriptive commit messages explaining *what* changed and *why*.
- Each commit should leave the tree in a working state (tests passing).

## AI coding assistants

The use of AI coding assistants (large language models, code-completion tools,
agentic coding tools, and similar) to help prepare contributions is **allowed**.
In fact, a large portion of the zcompose code base has been written by AI tools.

If any part of a contribution was generated or materially assisted by an AI tool,
this **must** be indicated in the commit message with an `Assisted-by` trailer.
Be specific: name the assistant **and the exact model and version** that was
used, so the contribution is traceable. The format follows the
[Zephyr AI policy](https://docs.zephyrproject.org/latest/contribute/guidelines.html#ai-coding-assistants):

```
Assisted-by: [Agent Name]:[Model Version] [Tool1] [Tool2]
```

where `[Agent Name]` is the name of the assistant or framework, `[Model Version]`
is the specific model and version, and `[Tool1] [Tool2]` are any optional
specialized tools the assistant invoked. For example:

```
Assisted-by: Claude Code:claude-opus-4-8
```

```
Assisted-by: GitHub Copilot:gpt-5
```

Do **not** list ordinary development tools (git, gcc, make, your editor, …) in
this trailer. Add one trailer per assisting agent, at the end of the commit
message alongside any other trailers (`Signed-off-by`, `Co-authored-by`, …).

### Your responsibility as a contributor

Whether or not you used an AI assistant, **you are fully responsible for every
contribution you submit.** By opening a pull request you assert that:

- You have **read, understood, and reviewed** the entire contribution, including
  any AI-generated portions, and you stand behind it as if you had written it
  yourself.
- The contribution is **correct**, does what it claims to do, and meets the
  quality and style of the surrounding code.
- You have the **right to submit** the contribution under the project's license
  (Apache-2.0), and it does not infringe anyone's intellectual property,
  copyright, or license terms. AI tools can reproduce code from their training
  data; it is your responsibility to ensure the contribution is original and
  properly licensed.

AI tools are an aid, not a substitute for your own judgement. Submissions that
appear to be unreviewed AI output — incorrect, untested, or not understood by
the author — will be rejected.

## License

By contributing, you agree that your contributions will be licensed under the
[Apache-2.0](LICENSE) license, the same license as the project.
