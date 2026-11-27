# Third-Party Licences

This file lists every third-party component that the Hunting Association MVP installs, loads or builds on, together with
its licence. It covers the whole project (Student A's membership module and Student B's public site share one
`requirements.txt`, one Docker image and one base template).

The project's own source code is **not** covered here: its ownership and licence are settled by the code assignment /
licence agreement with the association that Assignment A asks for.

> Licences were read from the package metadata that `pip` installs (`importlib.metadata`) in a clean virtual environment
> created from `requirements.txt` on **2026-11-27**. `requirements.txt` pins only version *ranges*, so a later install may
> resolve newer versions; the licences of these projects have been stable, but re-run the commands in
> [How to re-check](#how-to-re-check) before a release. This is an engineering inventory, not legal advice.

## 1. Python packages declared in `requirements.txt`

| Package | Range in `requirements.txt` | Version resolved on 2026-11-27 | Licence (SPDX) | Used for | Project home |
|---------|----------------------------|--------------------------------|----------------|----------|--------------|
| Django | `>=5.0,<5.2` | 5.1.15 | BSD-3-Clause | web framework, ORM, auth, admin, test runner (the whole application) | <https://www.djangoproject.com/> |
| psycopg2-binary | `>=2.9,<3.0` | 2.9.13 | LGPL-3.0-or-later *with exceptions* (the metadata says "LGPL with exceptions") | PostgreSQL database driver | <https://www.psycopg.org/> |
| python-dotenv | `>=1.0,<2.0` | 1.2.4 | BSD-3-Clause | declared for reading `.env` files; **not imported by the code** (see section 5) | <https://github.com/theskumar/python-dotenv> |
| pytest | `>=8.0,<9.0` | 8.4.2 | MIT | declared test runner; **not used**, tests run with Django's runner (section 5) | <https://docs.pytest.org/> |
| pytest-django | `>=4.8,<5.0` | 4.14.0 | BSD-3-Clause | declared pytest plugin; **not used** (section 5) | <https://pytest-django.readthedocs.io/> |

## 2. Python packages installed automatically (transitive dependencies)

| Package | Version resolved on 2026-11-27 | Licence (SPDX) | Required by |
|---------|-------------------------------|----------------|-------------|
| asgiref | 3.13.0 | BSD-3-Clause | Django |
| sqlparse | 0.6.1 | BSD-3-Clause (metadata classifier: "BSD License") | Django |
| iniconfig | 2.3.1 | MIT | pytest |
| packaging | 26.4 | Apache-2.0 OR BSD-2-Clause (dual-licensed, either may be chosen) | pytest |
| pluggy | 1.7.0 | MIT | pytest |
| Pygments | 2.21.0 | BSD-2-Clause | pytest |

The binary wheel of `psycopg2-binary` also bundles shared libraries (for example OpenSSL and libpq, which is released
under the PostgreSQL licence) inside the wheel; their notices are part of the wheel's own `licenses` folder.

## 3. Front-end resources loaded at run time

| Component | How it is used | Licence | Source |
|-----------|----------------|---------|--------|
| Tailwind CSS (Play CDN script) | `<script src="https://cdn.tailwindcss.com">` in `src/public_site/templates/public_site/base.html`; the colour configuration is inline in the same template and every member-area page inherits it. Nothing is installed or copied into the repository. | MIT | <https://tailwindcss.com/> |
| Article cover photos from Unsplash | `seed_articles` stores `https://images.unsplash.com/...` URLs (six photos) in the demo articles; the browser loads them from Unsplash, nothing is copied into the repository (Student B's public site). | Unsplash License (free use, no attribution required) | <https://unsplash.com/license> |
| Inline SVG icons | pasted as `<svg>` path data in the templates. The chevron, arrow, menu and warning icons match the Heroicons set; the Facebook, Instagram and YouTube marks in the footer are the brand logos of those companies (Student B's footer). The authors did not record where the paths came from. | Heroicons: MIT. Brand logos: trademarks of their owners, shown only as links to the profiles | <https://heroicons.com/> |

Not used: icon fonts, web fonts (the pages use the system font stack), JavaScript libraries other than the Tailwind script,
and any image file stored in the repository (there are no static image files).

Two points to confirm before a real release: the Tailwind team documents the Play CDN as a development convenience, so a
production deployment should replace it with a compiled stylesheet (still MIT); and the demo article photos should be
replaced by images the association owns or has licensed. The Unsplash and icon rows come from Student B's templates and
seed data, so Student B should confirm them.

## 4. Container images and system packages

These are not Python dependencies, but they end up in the running stack, so they are listed for completeness. They are
pulled from public registries by `docker compose up --build`; the project does not modify or redistribute them.

| Component | Where | Licence (upstream) |
|-----------|-------|--------------------|
| `python:3.12-slim` (Debian base image with CPython 3.12) | `Dockerfile`, `FROM` | Python: PSF licence; the Debian packages in the image keep their own free-software licences |
| `gcc`, `libpq-dev` (installed with `apt-get`, used to build and link database-driver code) | `Dockerfile`, build step | gcc: GPL-3.0-or-later with the GCC Runtime Library Exception; libpq-dev: PostgreSQL licence |
| `postgres:16-alpine` (PostgreSQL 16 on Alpine Linux) | `docker-compose.yml`, `image:` | PostgreSQL: PostgreSQL licence (BSD-style); the Alpine packages keep their own licences |

## 5. Notes and open points

- **LGPL component.** `psycopg2-binary` is LGPL (with exceptions). The project only imports it as an unmodified library
  installed from PyPI, which the licence permits. If the project is ever redistributed with this library bundled, keep
  its licence file and allow replacing the library.
- **Declared but unused packages.** A search of the repository found no `import dotenv` and no pytest configuration or
  `conftest.py`; the 54 automated tests run with `python manage.py test` (see [`docs/test-report.md`](docs/test-report.md)).
  `python-dotenv`, `pytest` and `pytest-django` (and the four packages they pull in) are therefore installed but not
  needed today. Removing them from `requirements.txt` would shrink the image and this list; they are kept here because
  they are currently declared.
- **Packages not in `requirements.txt`.** `coverage.py` (Apache-2.0) was used once during the AI-assisted documentation
  work to measure the 94 % coverage quoted in the test report; it is not a project dependency. Pillow is not used.
- **Licence texts.** Each installed package carries its full licence text in its `*.dist-info/licenses` folder. Inside the
  running container the files can be listed with
  `docker compose exec web sh -c "ls /usr/local/lib/python3.12/site-packages/*.dist-info/licenses"`.
- **Own code.** The repository root contains no `LICENSE` file; the terms for the project's own code come from the
  agreement with the association, not from this inventory.

## How to re-check

Create a clean environment and print the licence fields of every installed package:

```bash
python -m venv .venv-licences
source .venv-licences/bin/activate          # Windows PowerShell: .venv-licences\Scripts\Activate.ps1
pip install -r requirements.txt
python - <<'PY'
from importlib.metadata import distributions
for d in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
    m = d.metadata
    print(m["Name"], d.version, "|", m.get("License-Expression") or m.get("License") or "see classifiers")
PY
```

On Windows PowerShell, run the Python snippet from a file (for example `licences.py`) because the `<<'PY'` here-document
is bash syntax. Update the tables above if a version or licence differs, and keep the "resolved on" date current.
