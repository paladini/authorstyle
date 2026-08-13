# Security policy

AuthorStyle handles private writing corpora, so privacy and local execution are
core security concerns.

## Supported versions

The project is in alpha. Security fixes target the current `main` branch until
versioned releases begin.

## Reporting a vulnerability

Report security issues privately through GitHub's security advisory workflow:

https://github.com/paladini/authorstyle/security/advisories/new

Do not open a public issue for vulnerabilities involving:

- Accidental corpus disclosure to remote providers
- Unsafe file handling during ingestion
- Prompt injection risks in Style Cards or generation prompts
- Unexpected network access when `LOCAL_ONLY` is configured
- Dependency vulnerabilities with practical exploit paths

## Security principles

- Profiling and analysis must work without network access.
- Raw corpus text must not be sent remotely unless the configured privacy mode
  explicitly permits it.
- Privacy mode behavior must be explicit in config and logs.
- Optional remote generation must be explicit and documented.
- Dependencies must stay minimal and justified.
