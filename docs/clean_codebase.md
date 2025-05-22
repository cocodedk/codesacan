# Codebase Cleanup for Public Repository

## Requirements

To prepare the codebase for a public repository, we need to:
1. Remove all host-specific paths (like `/home/bba/...`)
2. Remove or replace any sensitive information (passwords, tokens, etc.)
3. Ensure no private information is leaked
4. Create proper example configuration files

## Issues Identified

1. **Hardcoded paths**:
   - `scanner.py`: Default project directory is set to "/home/bba/0-projects/iman-drp"
   - `README.md`: Contains absolute paths in examples

2. **Sensitive information**:
   - `constants.py`: Default Neo4j password "demodemo" should be replaced with a placeholder

3. **Missing configuration template**:
   - No `.env.example` file exists for users to create their own configuration

## Implementation Steps

1. Fix hardcoded paths in `scanner.py`
2. Update examples in `README.md` to use relative paths
3. Replace sensitive information in `constants.py`
4. Create a proper `.env.example` file with placeholders
5. Perform a final check for any other instances of sensitive information
