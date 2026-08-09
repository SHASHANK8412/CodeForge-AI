# AIForge Evaluation Engine & Quality Benchmarking Guide

## Overview & Purpose
The AIForge Evaluation Engine is a permanent quality measurement system designed to objectively verify whether code, prompt, routing, or agent changes improve or degrade AIForge quality.

It sits **OUTSIDE** the production generation pipeline and measures performance against a dataset of **100 Golden Test Prompts**.

---

## Architecture Topology
```
┌───────────────────────────┐
│ GOLDEN DATASET            │ (100 Typed Golden Test Cases)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ EVALUATION RUNNER         │ (backend/evaluation/runner.py)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ AIFORGE GENERATION        │ (Intent Classifier -> Agent -> Model -> LLM)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ QUALITY SCORER            │ (OutputValidator + Contract & Element Checks)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ REGRESSION ANALYZER       │ (CURRENT vs BASELINE Comparison)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ BENCHMARK REPORTS         │ (latest.json & latest.md)
└───────────────────────────┘
```

---

## 🚀 Execution CLI Commands

### 1. Fast Benchmark Mode (Default Developer Loop)
Runs golden dataset evaluation with fast response generation:
```bash
python -m evaluation.runner --mode fast
```

### 2. Mock Benchmark Mode (Infrastructure & Test Suite Validation)
Verifies dataset loading, routing evaluation, scoring, and report generation without invoking local LLMs:
```bash
python -m evaluation.runner --mode mock
```

### 3. Full Benchmark Mode (Complete Generation & Quality Measurement)
Runs full LLM generations and quality validation:
```bash
python -m evaluation.runner --mode full --no-cache
```

### 4. Single Test Mode (e.g. Flagship Formula 1 Test)
Runs only the specified test case ID:
```bash
python -m evaluation.runner --test EXP_FORMULA1
```

### 5. Category-Specific Benchmark Mode
Runs evaluation for a specific intent category (e.g., `explanation`, `coding`, `debugging`, `rag`, `resume`, `project`, `ambiguous`):
```bash
python -m evaluation.runner --category explanation
```

### 6. Save & Compare Against Baseline
Save current evaluation run as permanent baseline:
```bash
python -m evaluation.runner --mode fast --save-baseline
```
Compare current evaluation run against saved baseline:
```bash
python -m evaluation.runner --mode fast --compare-baseline
```

---

## 🎯 Quality Gates & Exit Code Standards

The Evaluation Runner exits with code `0` when all quality gates pass, and non-zero `1` if a critical regression occurs:

| Quality Gate | Standard Threshold | Action on Failure |
| :--- | :--- | :--- |
| **Routing Accuracy** | >= 95.0% | Quality Gate Warning / Fail |
| **Agent Accuracy** | >= 95.0% | Quality Gate Warning / Fail |
| **Profile Accuracy** | >= 95.0% | Quality Gate Warning / Fail |
| **Overall Pass Rate** | >= 90.0% | Quality Gate Fail |
| **Critical Golden Tests** | 100.0% Pass | **CRITICAL REGRESSION (Exit Code 1)** |
| **Baseline Regression** | No Critical Drop | **REGRESSION (Exit Code 1)** |

---

## 🔄 Recommended Development Workflow

```
1. MAKE CODE / PROMPT / ROUTER CHANGE
           │
           ▼
2. RUN RELEVANT TEST CASE (e.g. python -m evaluation.runner --test EXP_FORMULA1)
           │
           ▼
3. RUN CATEGORY EVALUATION (e.g. python -m evaluation.runner --category explanation)
           │
           ▼
4. RUN FAST BENCHMARK (python -m evaluation.runner --mode fast --compare-baseline)
           │
           ▼
5. VERIFY NO REGRESSION DETECTED -> MERGE & COMMIT
```
