# How we work

Two people, both [collaborators](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository) on [KartikAg13/flow](https://github.com/KartikAg13/flow). No pull requests. You branch, you merge into `main`, you push.

Git basics if you want the manual: [git-branch](https://git-scm.com/docs/git-branch), [git-merge](https://git-scm.com/docs/git-merge), [git-pull](https://git-scm.com/docs/git-pull).

---

## Rules

Work on a branch, not on `main`. One task per branch. Pull `main` before you merge so you do not overwrite the other person.

Branch names: `phase-<n>/<nn>-<slug>`, for example `phase-1/01-problem`.

Do not commit `.env`, anything under `data/raw/`, Chroma dirs, or empty `test_*.py`.

---

## Merge into main

1. Save your work on the branch and get `main` current.
2. Merge `main` into your branch (so conflicts happen on the branch, not on `main`).
3. Check tests if you touched Python.
4. Check out `main`, merge the branch, push `main`.
5. Delete the local branch.

```bash
# 1. on your task branch, commit first, then:
git fetch origin
git checkout main
git pull origin main

# 2. go back to the task branch and bring main in
git checkout phase-1/01-problem
git merge main

# 3. if you changed Python
uv run pytest
uv run ruff check src tests

# 4. land it
git checkout main
git merge phase-1/01-problem
git push origin main

# 5. tidy up
git branch -d phase-1/01-problem
```

If Git stops on conflicts: open the listed files, delete the `<<<<<<<` / `=======` / `>>>>>>>` markers, keep the right code, then:

```bash
git add <the files>
git merge --continue
```

Docs: [How to resolve conflicts](https://git-scm.com/docs/git-merge#_how_to_resolve_conflicts).

---

## Example

Kartik adds oil import seeds. Teammate is also writing. Kartik does not commit on `main`.

```bash
git checkout main
git pull origin main
git checkout -b phase-2/01-oil-seeds

# edit data/seeds/oil/imports.json
# edit src/flow/data/ as needed

git add data/seeds/oil/imports.json src/flow/data/
git commit -m "Add 2024 PPAC crude import shares"

git fetch origin
git checkout main && git pull origin main
git checkout phase-2/01-oil-seeds
git merge main
uv run pytest

git checkout main
git merge phase-2/01-oil-seeds
git push origin main
git branch -d phase-2/01-oil-seeds
```

The teammate then `git checkout main && git pull origin main` before starting their next branch.

---

## Commands we use a lot

```bash
uv sync --group dev
uv run pytest
uv run ruff check src tests
uv run flow version
```

This file: `CONTRIBUTING.md`. Data notes: `data/README.md`. Code you are likely to touch on a data branch: `data/seeds/`, `src/flow/data/`, `src/flow/intel/`, `tests/`.
