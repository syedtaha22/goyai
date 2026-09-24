# Contributing to goyai

Thanks for helping out. The project is still early, so these guidelines are short and will change as the codebase takes shape.

## Workflow

1. Don't commit directly to `main`. Create a branch for each change:
   - `feat/<short-name>` for new features
   - `fix/<short-name>` for bug fixes
   - `docs/<short-name>` for documentation
   - `research/<short-name>` for corpus, evaluation, or study materials
   - `experiment/<short-name>` for experimental code that may not be merged
2. Keep each pull request focused on one change.
3. Open a pull request into `main`. At least one other team member should review it before it is merged.

## Commit messages

- Write in the imperative mood: "Add tile grid layout", not "Added tile grid layout".
- Keep the first line under about 72 characters. Add a body if the reason for the change isn't obvious.

## Research data and ethics

This project involves a vulnerable participant population. Before committing, check that:

- **No participant data is committed.** That covers session logs, recordings, consent forms, identifying information, and anything participants wrote on the board. Keep it outside the repository or in the git-ignored folders listed in `.gitignore`.
- **No secrets are committed.** API keys and credentials go in a local `.env` file, which is git-ignored.
- **Corpus sentences are not taken from participants.** Only add sentences to the curated Urdu/code-mixed corpus if they were written by the team or come from a source that allows reuse.
- **Wording avoids deficit framing.** In docs, UI text, and reports, describe participants as people using a communication tool, not as problems to be fixed.

## Urdu and code-mixed text

- Save all files as UTF-8.
- Check any UI change on a right-to-left layout.
- Test prediction changes on both monolingual Urdu and Urdu-English code-mixed input.

## Questions

For questions or larger design changes, open an issue before writing code.
