import ast
from .constants import BUILTIN_FUNCTIONS, TEST_FUNCTION_PREFIXES
from .utils import is_stdlib_module

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path, session, is_test_file=False):
        self.file_path = file_path
        self.session = session
        self.current_class = None
        self.current_function = None
        self.is_test_file = is_test_file
        self.is_example_file = self._is_example_file(file_path)

    def _is_example_file(self, file_path):
        """
        Local method to check if a file is an example file.
        This is a duplicate of the is_example_file function from utils.py,
        but used here to avoid circular imports.
        """
        import os
        normalized_path = os.path.normpath(file_path).replace('\\', '/')
        path_parts = normalized_path.split('/')
        return '/examples/' in normalized_path or 'examples/' in normalized_path or any(part == 'examples' for part in path_parts)

    def visit_ClassDef(self, node):
        class_name = node.name
        line_num = getattr(node, 'lineno', -1)
        print(f"Visiting class: {class_name} in {self.file_path} at line {line_num}")
        self.current_class = class_name

        # Choose appropriate labels based on file type
        if self.is_test_file:
            self.session.run(
                "MERGE (c:Class:Test:TestClass {name: $name, file: $file, line: $line, end_line: $end_line})",
                name=class_name,
                file=self.file_path,
                line=line_num,
                end_line=getattr(node, 'end_lineno', -1)
            )
        elif self.is_example_file:
            self.session.run(
                "MERGE (c:Class:Example:ExampleClass {name: $name, file: $file, line: $line, end_line: $end_line})",
                name=class_name,
                file=self.file_path,
                line=line_num,
                end_line=getattr(node, 'end_lineno', -1)
            )
        else:
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

        # Choose labels based on file type and other conditions
        if self.is_test_file:
            labels = ":Function:Test:TestFunction"
        elif self.is_example_file:
            labels = ":Function:Example:ExampleFunction"
        else:
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

    def visit_Import(self, node):
        """
        Process Import nodes and track imports in test files.
        """
        for alias in node.names:
            imported_name = alias.name
            alias_name = alias.asname or imported_name

            if self.is_test_file:
                print(f"Import in test file: {imported_name} as {alias_name}")
                # Track imports for later analysis of test relationships
                self.session.run("""
                    MERGE (i:Import {name: $name, alias: $alias, file: $file})
                    WITH i
                    MATCH (f:Function {name: $func_name, file: $file})
                    MERGE (f)-[:IMPORTS {color: $edge_color}]->(i)
                """, name=imported_name, alias=alias_name, file=self.file_path,
                    func_name=self.current_function, edge_color="#4CAF50")  # Green for imports

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Process ImportFrom nodes and track imports in test files.
        """
        module = node.module
        for alias in node.names:
            imported_name = alias.name
            alias_name = alias.asname or imported_name
            full_import = f"{module}.{imported_name}" if module else imported_name

            if self.is_test_file:
                print(f"ImportFrom in test file: {full_import} as {alias_name}")
                # Track imports for later analysis of test relationships
                self.session.run("""
                    MERGE (i:Import {name: $name, module: $module, alias: $alias, file: $file})
                    WITH i
                    MATCH (f:Function {name: $func_name, file: $file})
                    MERGE (f)-[:IMPORTS {color: $edge_color}]->(i)
                """, name=imported_name, module=module, alias=alias_name,
                    file=self.file_path, func_name=self.current_function, edge_color="#4CAF50")

        self.generic_visit(node)

    def process_test_relationships(self, custom_patterns=None):
        """
        Process relationships between test code and production code.
        Called at the end of analyze_file for test files.

        Args:
            custom_patterns: Dictionary with custom test patterns
        """
        if not self.is_test_file:
            return

        # Use custom patterns if provided, otherwise use defaults from constants
        function_prefixes = custom_patterns['test_funcs'] if custom_patterns and 'test_funcs' in custom_patterns else TEST_FUNCTION_PREFIXES

        # Process based on configurable naming patterns
        for prefix in function_prefixes:
            prefix_len = len(prefix)
            self.session.run("""
                MATCH (test:TestFunction)
                WHERE test.name STARTS WITH $prefix
                WITH test, substring(test.name, $prefix_len) AS tested_name
                MATCH (prod:Function)
                WHERE NOT prod:TestFunction AND prod.name = tested_name
                MERGE (test)-[:TESTS {method: 'naming_pattern', color: $edge_color}]->(prod)
            """, prefix=prefix, prefix_len=prefix_len, edge_color="#3F51B5")  # Indigo for tests

        # Process based on imports
        self.session.run("""
            MATCH (test:TestFunction)-[:IMPORTS]->(i:Import)
            MATCH (prod:Function)
            WHERE NOT prod:TestFunction AND prod.name = i.name
            MERGE (test)-[:TESTS {method: 'import', color: $edge_color}]->(prod)
        """, edge_color="#3F51B5")

        # Process based on calls
        self.session.run("""
            MATCH (test:TestFunction)-[:CALLS]->(prod:Function)
            WHERE NOT prod:TestFunction
            MERGE (test)-[:TESTS {method: 'call', color: $edge_color}]->(prod)
        """, edge_color="#3F51B5")
