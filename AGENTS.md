# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is an E-commerce Product Reviews Analysis System — a single-service Python/Streamlit app backed by MySQL. The main entry point is `app.py`, with `db.py` for database connectivity and `sentiment.py` for NLP (TextBlob/VADER).

### Required services

| Service | How to start |
|---------|-------------|
| MySQL 8 | `sudo mysqld --user=mysql --datadir=/var/lib/mysql &` (already installed as system package) |
| Streamlit app | `DB_PASSWORD=rootpass streamlit run app.py --server.port 8501 --server.headless true` |

### Database setup

MySQL root password is set to `rootpass` (auth via `mysql_native_password`). The app reads credentials from env vars `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (defaults: `localhost`, `root`, `your password`, `openfeedback`). You **must** set `DB_PASSWORD=rootpass` when running the app or tests.

Schema initialization: `mysql -u root -prootpass openfeedback < schema.sql`

### Gotchas

- MySQL's `dpkg` post-install script fails in the container environment; the server still installs correctly and can be started manually with the command above.
- Streamlit binary installs to `~/.local/bin` — ensure `PATH` includes it (e.g. `export PATH="$HOME/.local/bin:$PATH"`).
- The app uses a persistent MySQL connection object (`conn`) at module level in `app.py` for form submissions. If MySQL restarts, the Streamlit app must also be restarted.
- No linter or test framework is configured in this repository. Code quality checks can be done with `python3 -m py_compile app.py db.py sentiment.py`.
