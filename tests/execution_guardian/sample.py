"""
Small deterministic projects for the Execution Guardian, and fixed agent answers used in place of the local coding
model. Each broken variant fails in exactly one way.
"""

from pathlib import Path

CALC = '''def add(a, b):
    return a + b


def discount(price, pct):
    return round(price * (1 - pct / 100), 2)
'''
CALC_TESTS = '''from calc import add, discount


def test_add():
    assert add(2, 3) == 5


def test_discount():
    assert discount(200, 10) == 180.0
'''
CALC_WRONG = CALC.replace("return round(price * (1 - pct / 100), 2)", "return round(price * (1 + pct / 100), 2)")   # a logic bug
CALC_SYNTAX = CALC.replace("def add(a, b):", "def add(a, b)")                                                      # a syntax error
CALC_UNDEFINED = CALC + '''

def to_json(value):
    return json.dumps(value)
'''                                                                                                                  # json not imported
CALC_UNDEFINED_TESTS = CALC_TESTS + '''

def test_to_json():
    from calc import to_json
    assert to_json({"a": 1}) == '{"a": 1}'
'''
CALC_RUNTIME = CALC.replace("return a + b", "return a + b + undefined_helper()")                                   # NameError at runtime

API = '''from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}
'''
API_BROKEN_STARTUP = API.replace("app = FastAPI()", "app = FastAPI()\nraise RuntimeError('startup failed: missing setting')")

PACKAGE_JSON = '''{
  "name": "shop-ui",
  "private": true,
  "type": "module",
  "scripts": {"build": "node build.js"}
}
'''
BUILD_JS = '''import fs from "node:fs";
const src = fs.readFileSync("src/App.js", "utf8");
new Function(src);                       // a syntax error in the source fails the build
fs.mkdirSync("dist", { recursive: true });
fs.writeFileSync("dist/app.js", src);
console.log("built");
'''
APP_JS = 'export const greet = (name) => `Hello ${name}`;\n'.replace("export ", "")
APP_JS_BROKEN = 'const greet = (name) => `Hello ${name}`;;\nconst x = ;\n'


def write(root, files) -> Path:
    root = Path(root)
    for rel, content in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content, encoding="utf-8")
    return root


def python_project(root, calc=CALC, tests=CALC_TESTS, extra=None) -> Path:
    return write(root, {"calc.py": calc, "tests/test_calc.py": tests, **(extra or {})})


def fixed_agent(answers):
    """generate(system, prompt): returns answers[agent marker] - the n-th call gets the n-th answer (last repeats).
    Which agent was asked is read from its system prompt (the routed agent's own prompt)."""
    calls = []

    def generate(system, prompt):
        calls.append({"system": system, "prompt": prompt})
        seq = answers if isinstance(answers, list) else [answers]
        return seq[min(len(calls), len(seq)) - 1]
    generate.calls = calls
    return generate


def file_answer(path, content):
    return f"### {path}\n```\n{content}```\n"
