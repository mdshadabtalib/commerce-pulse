#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

PASS=true
FAILED_TESTS=()

echo "============================================"
echo "CommercePulse Test Runner"
echo "============================================"
echo ""

run_section() {
    local title="$1"
    echo ""
    echo "--------------------------------------------"
    echo "  $title"
    echo "--------------------------------------------"
}

# ========================================
# Backend Tests
# ========================================
if [ -d "${BACKEND_DIR}" ] && [ -f "${BACKEND_DIR}/pyproject.toml" ]; then
    run_section "Backend: Ruff Lint Check"
    if [ -f "${BACKEND_DIR}/poetry.lock" ] || [ -f "${BACKEND_DIR}/pyproject.toml" ]; then
        if command -v poetry &> /dev/null; then
            cd "${BACKEND_DIR}"
            if poetry run ruff check . 2>&1; then
                echo "  PASS: Ruff lint"
            else
                echo "  FAIL: Ruff lint"
                PASS=false
                FAILED_TESTS+=("Backend: Ruff lint")
            fi
            cd "${ROOT_DIR}"
        else
            echo "  SKIP: Poetry not installed"
        fi
    else
        echo "  SKIP: No Python project detected"
    fi

    run_section "Backend: Ruff Format Check"
    if command -v poetry &> /dev/null; then
        cd "${BACKEND_DIR}"
        if poetry run ruff format --check . 2>&1; then
            echo "  PASS: Ruff format"
        else
            echo "  FAIL: Ruff format"
            PASS=false
            FAILED_TESTS+=("Backend: Ruff format")
        fi
        cd "${ROOT_DIR}"
    else
        echo "  SKIP: Poetry not installed"
    fi

    run_section "Backend: Pytest Unit Tests"
    if command -v poetry &> /dev/null; then
        cd "${BACKEND_DIR}"
        if poetry run pytest -v --tb=short 2>&1; then
            echo "  PASS: Pytest"
        else
            echo "  FAIL: Pytest"
            PASS=false
            FAILED_TESTS+=("Backend: Pytest")
        fi
        cd "${ROOT_DIR}"
    else
        echo "  SKIP: Poetry not installed"
    fi
else
    echo "[SKIP] Backend directory or pyproject.toml not found."
fi

# ========================================
# Frontend Tests
# ========================================
if [ -d "${FRONTEND_DIR}" ] && [ -f "${FRONTEND_DIR}/package.json" ]; then
    run_section "Frontend: ESLint Check"
    cd "${FRONTEND_DIR}"
    if npm run lint --if-present 2>&1; then
        echo "  PASS: ESLint"
    else
        echo "  FAIL: ESLint"
        PASS=false
        FAILED_TESTS+=("Frontend: ESLint")
    fi

    run_section "Frontend: TypeScript Type Check"
    if npx tsc --noEmit 2>&1; then
        echo "  PASS: TypeScript"
    else
        echo "  FAIL: TypeScript"
        PASS=false
        FAILED_TESTS+=("Frontend: TypeScript")
    fi

    run_section "Frontend: Jest Unit Tests"
    if npm test -- --passWithNoTests --ci 2>&1; then
        echo "  PASS: Jest"
    else
        echo "  FAIL: Jest"
        PASS=false
        FAILED_TESTS+=("Frontend: Jest")
    fi
    cd "${ROOT_DIR}"
else
    echo "[SKIP] Frontend directory or package.json not found."
fi

# ========================================
# Summary
# ========================================
echo ""
echo "============================================"
echo "Test Summary"
echo "============================================"
echo ""

if [ "$PASS" = true ]; then
    echo "All checks passed!  "
    exit 0
else
    echo "Some checks failed:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    echo "Please fix the failing checks and re-run."
    exit 1
fi
