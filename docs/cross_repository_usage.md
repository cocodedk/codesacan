# Using CodeScan Across Different Python Repositories

CodeScan is designed to work with various Python repository structures. This document explains how to effectively use and configure CodeScan for different project layouts.

## Customizing Test Detection

Different Python projects follow different conventions for structuring tests. CodeScan is configurable to handle these variations.

### Configuration Options

CodeScan provides several configuration options that can be set through environment variables, command-line arguments, or in code:

| Option                   | Description                   | Default Value           |
|--------------------------|-------------------------------|-------------------------|
| `TEST_DIR_PATTERNS`      | Patterns for test directories | `tests/,test/,testing/` |
| `TEST_FILE_PATTERNS`     | Patterns for test file names  | `test_*.py,*_test.py`   |
| `TEST_FUNCTION_PREFIXES` | Prefixes for test functions   | `test_`                 |
| `TEST_CLASS_PATTERNS`    | Patterns for test class names | `Test*,*Test`           |

### Common Repository Structures

CodeScan automatically adapts to these common repository structures:

#### 1. Standard Django/Flask/Pytest Structure
```
myproject/
  └─ tests/
     ├─ test_models.py
     ├─ test_views.py
     └─ test_api.py
```

#### 2. Module-Level Tests
```
myproject/
  ├─ module1/
  │  └─ tests/
  │     └─ test_module1.py
  └─ module2/
     └─ tests/
        └─ test_module2.py
```

#### 3. Tests Alongside Code
```
myproject/
  ├─ module1.py
  ├─ test_module1.py
  ├─ module2.py
  └─ test_module2.py
```

## Configuration Methods

### 1. Environment Variables

Set environment variables before running CodeScan:

```bash
export TEST_DIR_PATTERNS="tests/,test/,spec/"
export TEST_FILE_PATTERNS="test_*.py,*_test.py,*_spec.py"
export TEST_FUNCTION_PREFIXES="test_,should_,spec_"
export TEST_CLASS_PATTERNS="Test*,*Test,*TestCase"
```

### 2. Command-Line Arguments

Use command-line arguments when running the scanner directly:

```bash
python scanner.py --project-dir=/path/to/project \
  --test-dirs=tests/,test/,spec/ \
  --test-files=test_*.py,*_test.py,*_spec.py \
  --test-funcs=test_,should_,spec_ \
  --test-classes=Test*,*Test,*TestCase
```

### 3. Configuration File

You can also create a `.codescan.conf` file in your project root:

```ini
[test_patterns]
dirs = tests/,test/,spec/
files = test_*.py,*_test.py,*_spec.py
functions = test_,should_,spec_
classes = Test*,*Test,*TestCase
```

Then run the scanner with:

```bash
python scanner.py --config=.codescan.conf
```

## Examples for Specific Frameworks

### Pytest Projects

Pytest typically uses filenames starting with `test_` and functions starting with `test_`:

```bash
python scanner.py --test-dirs=tests/ --test-files=test_*.py --test-funcs=test_
```

### Unittest Projects

Unittest typically uses `TestCase` classes:

```bash
python scanner.py --test-classes=*TestCase
```

### Django Projects

Django tests are usually in a `tests.py` file or a `tests/` directory:

```bash
python scanner.py --test-dirs=tests/ --test-files=tests.py,test_*.py
```

## Generating Project-Specific Configuration

CodeScan can generate a suggested configuration based on your project structure:

```bash
python scanner.py --analyze-project-structure --output-config=.codescan.conf
```

This command analyzes your project structure and suggests appropriate test pattern configurations.
