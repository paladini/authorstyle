# Publishing AuthorStyle to PyPI

Distribution is **PyPI**, not Docker. Users install with
`pip install paladini-authorstyle`. The console script is still `authorstyle`.
Profiling stays local-first: nothing about packaging sends a corpus to a remote service.

The PyPI name `authorstyle` is already taken by
[Peter Muller](https://pypi.org/project/authorstyle/)
([mullerpeter/authorstyle](https://github.com/mullerpeter/authorstyle)).
`paladini-authorstyle` and `authorstyle-cli` were both unused on PyPI when this
was chosen; this project uses **`paladini-authorstyle`**.

That other distribution has no console-script entry point, so `authorstyle` as
the CLI name does not conflict. Both wheels install an `authorstyle` Python
package; do not mix them in one environment if you `import authorstyle`.

Releases are published from Git tags by GitHub Actions using **trusted publishing
(OIDC)**. There is no PyPI API token in this repository.

## Maintainer: cut a release

1. Confirm `project.version` in `pyproject.toml` and `CHANGELOG.md` match the tag.
2. Merge to `main`.
3. Create and push an annotated tag. `v0.2.1` already exists on `main` and must
   not be reused. The current project version is `0.2.2`:

   ```bash
   git tag -a v0.2.2 -m "paladini-authorstyle 0.2.2"
   git push origin v0.2.2
   ```

4. The [Publish](../.github/workflows/publish.yml) workflow runs tests, builds
   with `python -m build`, runs `twine check`, then uploads to PyPI.

The upload job fails until the one-time trusted-publisher setup below is done.
Do not work around that with a token in GitHub secrets.

## Owner: one-time trusted-publisher setup (paladini)

Do this on pypi.org. Do **not** create or paste a PyPI API token.

1. Sign in to [https://pypi.org](https://pypi.org) as **paladini**.
2. If `paladini-authorstyle` is not on PyPI yet, open
   **Account settings → Publishing → Add a new pending publisher**.
   If the project already exists, open
   **https://pypi.org/manage/project/paladini-authorstyle/settings/publishing/**
   instead.
3. Fill in:

   | Field | Value |
   |-------|--------|
   | PyPI project name | `paladini-authorstyle` |
   | Owner | `paladini` |
   | Repository name | `authorstyle` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

   Workflow name is the **filename** under `.github/workflows/`, not the `name:` key.
4. Save the publisher.
5. In GitHub: **Settings → Environments → New environment** named exactly `pypi`.
   Optional: add required reviewers so a tag cannot publish without approval.
6. Push a `v*` tag after this configuration exists. The first successful publish
   creates the PyPI project (if it was pending) and consumes the pending publisher.
7. Confirm [https://pypi.org/project/paladini-authorstyle/](https://pypi.org/project/paladini-authorstyle/)
   and `pip install paladini-authorstyle`. Then `authorstyle --help` should work.

GitHub → PyPI identity is the OIDC token from `id-token: write` on the `publish`
job. PyPI will reject uploads that do not match the publisher rows above.

## What CI already checks

Every pull request:

- pytest on Python 3.11, 3.12, and 3.13
- ruff
- `authorstyle --help`
- `python -m build` and `twine check --strict dist/*`
