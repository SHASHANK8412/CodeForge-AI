"""
The architecture contract given to the code agents comes from the architect's real output.

Regression: the architect is told to write Markdown sections, but anything that was not JSON was
replaced by a fixed design (Navbar/Sidebar/LoginForm, models User/Session/Item). Every project's
architecture.md in generated_projects/ was that placeholder, and code agents built it - the e2e
Contact Book imported models.session and models.item because of it.
"""
from backend.graph.architecture_check import validate_architecture_sections
from backend.services.validator import StageValidatorService, parse_architecture_markdown

ARCH_MD = """## 10. High-Level Architecture
Modular monolith: React SPA -> FastAPI REST API -> SQLite.

## 11. Database Schema
- **contacts**: id (int, PK), name (str), email (str, unique), phone (str)
  - id: integer primary key
- `tags` — id (int, PK), label (str)
### groups

## 12. API Specifications
- `GET /api/contacts` — list contacts
- `POST /api/contacts` — create a contact
- `DELETE /api/contacts/{contact_id}` — delete a contact
- GET /health — liveness

## 13. Folder Structure
```
backend/
  main.py
  models.py
frontend/src/
  App.jsx
  components/ContactList.jsx
```

## 14. Development Roadmap
M0 setup
"""


def test_markdown_architecture_becomes_the_contract():
    contract = parse_architecture_markdown(ARCH_MD)
    assert contract["routes"] == ["GET /api/contacts", "POST /api/contacts",
                                  "DELETE /api/contacts/{contact_id}", "GET /health"]
    assert contract["models"] == ["contacts", "tags", "groups"]
    assert contract["folder_structure"]["files"] == ["main.py", "models.py", "App.jsx", "components/ContactList.jsx"]
    assert contract["components"] == ["App", "ContactList"]


def test_validator_never_invents_an_architecture():
    ok, msg, contract = StageValidatorService().validate_architecture("I could not design this, sorry.")
    assert ok is False and "no API routes" in msg
    assert contract["routes"] == [] and contract["models"] == [] and contract["components"] == []
    for placeholder in ("Navbar", "Session", "Item", "LoginForm"):
        assert placeholder not in str(contract)


def test_validator_reads_markdown_and_json():
    ok, _, contract = StageValidatorService().validate_architecture(ARCH_MD)
    assert ok and contract["models"][0] == "contacts" and contract["document"] == ARCH_MD
    ok, _, contract = StageValidatorService().validate_architecture(
        'Here it is:\n```json\n{"routes": ["GET /items"], "models": ["Item"]}\n```')
    assert ok and contract["routes"] == ["GET /items"] and contract["components"] == []


def test_section_check_uses_the_same_document():
    complete, missing = validate_architecture_sections(ARCH_MD)
    assert complete is False
    assert "High-Level Architecture" not in missing and "Testing Strategy" in missing
