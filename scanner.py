import os
import ast
import builtins
import inspect
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Neo4j connection details
NEO4J_HOST = os.getenv("NEO4J_HOST", "localhost")
NEO4J_PORT_BOLT = os.getenv("NEO4J_PORT_BOLT", "7600")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "demodemo")
NEO4J_URI = f"bolt://{NEO4J_HOST}:{NEO4J_PORT_BOLT}"

# Directories to ignore during analysis
IGNORE_DIRS = ['.git', 'drp_venv', '__pycache__', 'venv', '.venv', 'node_modules', 'build', 'dist', '.cache', 'tests', 'examples']

# Set of built-in functions to ignore
BUILTIN_FUNCTIONS = set(dir(builtins))

def is_stdlib_module(module_name):
    """Check if a module is part of the Python standard library."""
    if module_name in sys.builtin_module_names:
        return True

    for path in sys.path:
        if path.startswith(sys.prefix) and not "site-packages" in path:
            if os.path.exists(os.path.join(path, module_name)) or os.path.exists(os.path.join(path, f"{module_name}.py")):
                return True

    return False

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path, session):
        self.file_path = file_path
        self.session = session
        self.current_class = None
        self.current_function = None

    def visit_ClassDef(self, node):
        class_name = node.name
        line_num = getattr(node, 'lineno', -1)
        print(f"Visiting class: {class_name} in {self.file_path} at line {line_num}")
        self.current_class = class_name
        self.session.run(
            "MERGE (c:Class {name: $name, file: $file, line: $line, end_line: $end_line})",
            name=class_name,
            file=self.file_path,
            line=line_num,
            end_line=getattr(node, 'end_lineno', -1)
        )
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        function_name = node.name

        # Skip special methods and private methods if desired
        if function_name.startswith('__') and function_name.endswith('__'):
            print(f"Skipping dunder method: {function_name} in {self.file_path}")
            return

        # Get line number information
        line_num = getattr(node, 'lineno', -1)
        end_line_num = getattr(node, 'end_lineno', -1)

        print(f"Visiting function: {function_name} in {self.file_path} at line {line_num}")
        full_name = f"{self.current_class}.{function_name}" if self.current_class else function_name
        self.current_function = full_name

        # Choose labels
        labels = ":Function"
        if function_name == "main":
            labels += ":MainFunction"
        if self.current_class:
            labels += ":ClassFunction"

        # Check if a reference node for this function already exists
        result = self.session.run(
            f"""
            MATCH (f{labels} {{name: $name, is_reference: true}})
            RETURN f
            """,
            name=function_name
        ).data()

        # First create or update the function node
        self.session.run(
            f"""
            MERGE (f{labels} {{
                name: $name,
                file: $file,
                is_reference: false,
                line: $line,
                end_line: $end_line
            }})
            """,
            name=full_name,
            file=self.file_path,
            line=line_num,
            end_line=end_line_num
        )

        # If we previously created a reference node for this function by name only,
        # link any calls to the reference node to this defined function
        if result:
            self.session.run(
                """
                MATCH (ref:Function {name: $simple_name, is_reference: true})
                MATCH (defined:Function {name: $full_name, file: $file, is_reference: false})
                MATCH (caller)-[r:CALLS]->(ref)
                MERGE (caller)-[:CALLS {color: $edge_color}]->(defined)
                WITH ref, r
                DELETE r
                """,
                simple_name=function_name,
                full_name=full_name,
                file=self.file_path,
                edge_color="#FF9800"  # Orange for calls relationships
            )
        if self.current_class:
            self.session.run(
                """
                MATCH (c:Class {name: $class_name, file: $file})
                WITH c
                MATCH (f:Function {name: $func_name, file: $file})
                MERGE (c)-[:CONTAINS {color: $edge_color}]->(f)
                """,
                class_name=self.current_class,
                func_name=full_name,
                file=self.file_path,
                edge_color="#9C27B0"  # Purple for contains relationships
            )
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        module_name = None
        # Get line number information for the call
        line_num = getattr(node, 'lineno', -1)

        # Extract both function name and module if available
        if isinstance(node.func, ast.Name):
            called_func = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called_func = node.func.attr
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
        else:
            called_func = None

        # Extract argument names or values
        arg_names = []
        for arg in node.args:
            if isinstance(arg, ast.Name):
                arg_names.append(arg.id)
            elif isinstance(arg, ast.Constant):
                arg_names.append(repr(arg.value))
            else:
                arg_names.append(ast.dump(arg))
        args_str = ', '.join(arg_names)

        # Skip built-in functions and standard library calls
        if called_func in BUILTIN_FUNCTIONS:
            print(f"  Skipping builtin function: {called_func} in {self.file_path}")
            return

        if module_name and is_stdlib_module(module_name):
            print(f"  Skipping stdlib call: {module_name}.{called_func} in {self.file_path}")
            return

        print(f"Visiting call: {called_func}{f' from module {module_name}' if module_name else ''} in {self.file_path} at line {line_num} with args: [{args_str}]")

        if called_func and self.current_function:
            # First check if this function already exists
            result = self.session.run(
                """
                MATCH (f:Function {name: $name})
                RETURN f.file AS file
                """,
                name=called_func
            ).data()

            # If the function has been defined in a file we know about, use that
            if result and result[0]['file'] is not None:
                # Use the first file we found that defined this function
                known_file = result[0]['file']
                self.session.run(
                    """
                    MATCH (called:Function {name: $called_name, file: $known_file})
                    WITH called
                    MATCH (caller:Function {name: $caller_name, file: $caller_file})
                    MERGE (caller)-[:CALLS {color: $edge_color, line: $line, args: $args}]->(called)
                    """,
                    called_name=called_func,
                    known_file=known_file,
                    caller_name=self.current_function,
                    caller_file=self.file_path,
                    edge_color="#FF9800",  # Orange for calls relationships
                    line=line_num,
                    args=args_str
                )
            else:
                # Function not yet defined anywhere we've seen, create a reference node
                self.session.run(
                    """
                    MERGE (called:Function:ReferenceFunction {name: $called_name, is_reference: true, file: $file, line: $line, end_line: $end_line})
                    WITH called
                    MATCH (caller:Function {name: $caller_name, file: $file})
                    MERGE (caller)-[:CALLS {line: $line, args: $args}]->(called)
                    """,
                    called_name=called_func,
                    caller_name=self.current_function,
                    file=self.file_path,
                    line=line_num,
                    end_line=-1,
                    args=args_str
                )
        self.generic_visit(node)

def is_project_file(file_path, base_dir):
    """Check if a file is part of the project (not in standard library)."""
    abs_path = os.path.abspath(file_path)
    return abs_path.startswith(os.path.abspath(base_dir))

def analyze_file(file_path, session, base_dir):
    # Skip standard library files
    if not is_project_file(file_path, base_dir):
        print(f"Skipping non-project file: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        print(f"Analyzing file: {file_path}")
        try:
            tree = ast.parse(f.read(), filename=file_path)
            analyzer = CodeAnalyzer(file_path, session)
            analyzer.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
        except UnicodeDecodeError:
            print(f"Unable to decode file: {file_path} - skipping")

def analyze_directory(directory, session, ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = IGNORE_DIRS

    # Store the base directory to identify project files
    base_dir = os.path.abspath(directory)

    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to avoid traversing ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                analyze_file(full_path, session, base_dir)

def clear_database(session):
    """Clear all nodes and relationships in the database."""
    print("Clearing database...")
    session.run("MATCH (n) DETACH DELETE n")

def main():
    # Get project directory from environment
    project_dir = os.getenv("PROJECT_DIR", "/home/bba/0-projects/iman-drp")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Clear the database to start fresh
        clear_database(session)

        # Print which directories will be ignored
        print(f"Ignoring directories: {', '.join(IGNORE_DIRS)}")

        # Print connection details
        print(f"Connected to Neo4j at {NEO4J_URI}")
        print(f"Analyzing project at {project_dir}")

        # Analyze the directory from environment variable
        analyze_directory(project_dir, session)

        print("Analysis complete. View the graph in Neo4j Browser with commands:")
        print(f"- Neo4j Browser: http://{NEO4J_HOST}:{os.getenv('NEO4J_PORT_HTTP', '7400')}")
        print("- Show all nodes: MATCH (n) RETURN n")
        print("- Find functions by line: MATCH (f:Function) WHERE f.line > 100 RETURN f")
        print("- Show relationships: MATCH (n)-[r]->(m) RETURN n, r, m")
        print("- Show calls at specific line: MATCH ()-[r:CALLS {line: 42}]->() RETURN r")
    driver.close()

if __name__ == "__main__":
    main()
