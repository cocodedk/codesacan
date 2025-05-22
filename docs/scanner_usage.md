# Scanner Usage Guide

## Overview
The Scanner is a tool for analyzing Python code and building a Neo4j graph database that represents the code structure, relationships, and metrics.

## Basic Usage
```bash
python scanner.py --project-dir /path/to/your/project
```

This will scan all Python files in the specified directory and its subdirectories, analyze them, and store the results in a Neo4j database.

## Command Line Options

### Project Directory
```bash
python scanner.py --project-dir /path/to/your/project
```
This option specifies the directory to scan. If not provided, the current directory will be used.

### Test Detection Configuration
You can customize how test files and components are detected with these options:

```bash
python scanner.py --test-dirs "tests/,test_" --test-files "_test.py,test_.py" --test-funcs "test_" --test-classes "Test"
```

- `--test-dirs`: Comma-separated list of directory patterns that indicate test directories
- `--test-files`: Comma-separated list of file patterns that indicate test files
- `--test-funcs`: Comma-separated list of function name prefixes that indicate test functions
- `--test-classes`: Comma-separated list of class name patterns that indicate test classes

### Output Verbosity
You can control the amount of output with these flags:

```bash
# Quiet mode - minimal output
python scanner.py --quiet

# Verbose mode - detailed output showing every element found
python scanner.py --verbose
```

- `--quiet`: Reduce output verbosity to only show errors
- `--verbose`: Increase output verbosity to show all elements found during scanning

These flags are mutually exclusive. If both are provided, quiet mode takes precedence.

## Output
The scanner produces:

1. A progress bar showing files being scanned
2. A summary of the scanning results, including:
   - Time elapsed
   - Number of files scanned
   - Elements found (classes, functions, constants, etc.)
   - Unique elements
   - Any errors encountered
3. Neo4j database information and useful queries

## Examples

### Basic Scan
```bash
python scanner.py
```

### Scan a Specific Directory with Progress Bar
```bash
python scanner.py --project-dir ./my_project
```

### Quiet Mode (Minimal Output)
```bash
python scanner.py --quiet
```

### Verbose Mode (Detailed Output)
```bash
python scanner.py --verbose
```

### Custom Test Detection
```bash
python scanner.py --test-dirs "specs/" --test-files "_spec.py" --test-funcs "it_" --test-classes "Spec"
```
