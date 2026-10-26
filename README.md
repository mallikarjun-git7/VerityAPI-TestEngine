# REST API QA Automation Framework

A production-quality test automation framework targeting the [JSONPlaceholder](https://jsonplaceholder.typicode.com) public REST API. Built to demonstrate real-world QA engineering skills: clean architecture, schema validation, parameterized testing, Selenium E2E coverage, and automated CI via GitHub Actions.

---

## Architecture

```
rest-api-automation/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions — runs on every push/PR
├── src/
│   └── client/
│       └── api_client.py       # Thin HTTP wrapper (requests); attaches elapsed_ms
├── tests/
│   ├── conftest.py             # Session fixtures, WebDriver setup, shared config
│   ├── api/
│   │   ├── test_posts.py       # GET/POST/PUT/DELETE + schema + negatives
│   │   ├── test_users.py       # Nested object validation, edge cases
│   │   └── test_comments.py    # Parameterized, filter tests, response time
│   └── e2e/
│       └── test_ui_workflow.py # Selenium: homepage smoke + route documentation
├── utils/
│   ├── schema_validator.py     # JSON Schema definitions + validate helpers
│   └── assertions.py           # Reusable assertion helpers with clear messages
├── pytest.ini                  # Markers, HTML report config, logging
└── requirements.txt
```

### Design Decisions

| Decision | Rationale |
|---|---|
| **Session-scoped API client** | One `requests.Session` is reused across all API tests — mirrors real app behaviour and avoids TCP handshake overhead per test |
| **Custom `elapsed_ms` attribute** | Attached by `APIClient._request()` so any test can assert response time without re-measuring or parsing headers |
| **Centralised schema definitions** | `utils/schema_validator.py` owns all schemas — a field change only touches one file |
| **Reusable assertion helpers** | `utils/assertions.py` produces human-readable failure messages; raw `assert` statements in tests stay minimal |
| **Module-scoped WebDriver** | One Chrome instance per test module balances isolation and speed |
| **Environment variable config** | `BASE_URL`, `API_TIMEOUT`, `RESPONSE_TIME_THRESHOLD_MS` can all be overridden in CI without code changes |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Google Chrome (for E2E tests)
- pip

### Setup

```bash
# Clone the repo
git clone <your-repo-url>
cd rest-api-automation

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Full Suite

```bash
pytest
```

This runs all tests and generates an HTML report at `reports/test_report.html`.

### Run Only API Tests

```bash
pytest tests/api/ -m api
```

### Run Only E2E Tests

```bash
pytest tests/e2e/ -m e2e
```

### Run a Specific Test File

```bash
pytest tests/api/test_posts.py -v
```

### Override Configuration

```bash
BASE_URL=https://staging.example.com \
RESPONSE_TIME_THRESHOLD_MS=500 \
pytest tests/api/
```

---

## Test Coverage Summary

| Module | Test Classes | Tests | Techniques |
|---|---|---|---|
| `test_posts.py` | 4 | ~20 | GET/POST/PUT/DELETE, schema validation, `@parametrize`, negatives |
| `test_users.py` | 3 | ~18 | Nested object/schema, boundary IDs, cross-resource relationships |
| `test_comments.py` | 4 | ~18 | Filter by query param, response time, `@parametrize`, negatives |
| `test_ui_workflow.py` | 3 | ~12 | Selenium, headless Chrome, `@parametrize`, JS error detection |

### What "production-ready" looks like here

- **Every test has a docstring** explaining what is being tested and why
- **`conftest.py`** centralises all fixtures — no setup code repeated across files
- **Parameterized tests** exercise multiple inputs with a single test function
- **Schema validation** on every successful response (not just status codes)
- **Negative test cases**: 404s, boundary IDs, non-integer path segments
- **Response time assertions** catch performance regressions before production
- **Custom assertion helpers** produce failure messages that name the field, expected value, and actual value
- **GitHub Actions CI** runs the full suite on every push against Python 3.11 and 3.12

---

## CI Pipeline

The `.github/workflows/ci.yml` pipeline runs on every push and pull request to `main`:

```
push / PR
  │
  ├── api-tests  (Python 3.11 + 3.12 matrix)
  │     └── pytest tests/api/ -m api
  │     └── Upload HTML report artifact
  │
  ├── e2e-tests  (Python 3.12, headless Chrome)
  │     └── pytest tests/e2e/ -m e2e
  │     └── Upload HTML report artifact
  │
  └── full-suite (gate job — fails if api-tests fail)
```

HTML reports are uploaded as GitHub Actions artifacts and retained for 30 days.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `https://jsonplaceholder.typicode.com` | API root URL |
| `API_TIMEOUT` | `10` | Request timeout in seconds |
| `RESPONSE_TIME_THRESHOLD_MS` | `2000` | Max acceptable response time (ms) |

---

## Reports

After running the suite, open the HTML report:

```
reports/test_report.html
```

The report includes:
- Pass/fail status per test
- Captured log output
- Test duration
- Environment metadata (Python version, platform, base URL)
