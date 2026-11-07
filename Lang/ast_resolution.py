from .scratch_ast import *
from .smart_iterator import SmartIterator
from dataclasses import fields


class ASTResolutionException(Exception):
    """
    Exception that occurs when any of ast resolution fails
    """
    pass


def raise_ast_resolution_exception(node: ASTNode, message: str):
    """
    Raises an ASTResolutionException at specific node with specified message
    :param node: Node where exception occurs
    :param message: Message to be displayed inside the exception
    """
    location = f"line: {node.line}, column: {node.column}"
    # if self.current_file:
    #     location = f"file: {self.current_file}, {location}"
    raise ASTResolutionException(f"{message}, {location}")


class NameResolver:
    def __init__(self, ast: list[ASTNode]):
        self.ast = ast
        self._current_parameters = {}
        self._unique_prefix_counter = 0

        self.global_variables: dict[str, str] = {}
        self.local_variables: dict[str, dict[str, str]] = {}

    def _get_unique_prefix(self) -> int:
        """
        Creates new unique integer for name resolution prefix
        :return: Unique integer value for name resolution
        """
        self._unique_prefix_counter += 1
        return self._unique_prefix_counter

    def get_unique_prefixed_name(self, name: str) -> str:
        """
        Adds a unique prefix to a name so no collisions occur
        :param name: name to add the prefix to
        :return: resolved name
        """
        prefix = self._get_unique_prefix()
        return f"{prefix}-{name}"

    def _resolve_nodes(self, nodes: list[ASTNode], scope: dict[str, str]):
        """
        Recursively resolves VariableReference variable identifier property based on the scope.
        Resolves converting VariableReference into ParameterReference if name matches parameter
        :param nodes: list of nodes (ast)
        :param scope: map of existing variables
        """
        for node_controller, node in SmartIterator(nodes):
            if isinstance(node, VariableDeclaration):
                scope[node.variable_name] = self.get_unique_prefixed_name(node.variable_name)
                node_controller.dispose()
                continue

            if isinstance(node, VariableReference):
                if node.variable_name in self._current_parameters:
                    node_controller.replace(
                        ParameterReference(
                            line=node.line,
                            column=node.column,
                            parameter_name=node.variable_name,
                            parameter_identifier=self._current_parameters[node.variable_name]
                        )
                    )
                    continue

                resolved_variable_identifier = scope.get(node.variable_name, None)
                if resolved_variable_identifier is None:
                    raise_ast_resolution_exception(node, f"Failed to find a variable with name '{node.variable_name}'")
                node.variable_identifier = resolved_variable_identifier
                continue

            if isinstance(node, VariableSet):
                variable_identifier = scope.get(node.variable_name, None)
                if variable_identifier is None:
                    raise_ast_resolution_exception(node, f"Failed to find a variable with name '{node.variable_name}'")
                node.variable_identifier = variable_identifier
                continue

            if isinstance(node, ProcedureDefinition):
                self._current_parameters = {
                    parameter_name: self.get_unique_prefixed_name(parameter_name) for parameter_name in node.parameters
                }

            if hasattr(node, "body"):
                body = getattr(node, "body")
                self._resolve_nodes(body, scope.copy())

            for node_field in fields(node):
                inner_node = getattr(node, node_field.name)
                if isinstance(inner_node, ASTNode):
                    self._resolve_nodes([inner_node], scope)

            if isinstance(node, ProcedureDefinition):
                self._current_parameters.clear()

    def resolve(self):
        """
        Resolves variable names as well as parameters inside function/procedure body
        Each variable declaration maps variable name to a unique variable identifier so no collisions occur.
        Changes VariableReference to ParameterReference if name corresponds to a parameter rather than a variable
        """
        self._resolve_nodes(self.ast, {})
