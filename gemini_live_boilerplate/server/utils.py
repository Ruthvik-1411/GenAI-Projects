"""common utils file"""
# pylint: disable=too-many-positional-arguments
from enum import Enum
import inspect
from typing import get_type_hints, Optional, Union, get_args, get_origin, Annotated

class OpenAPITypes(Enum):
    """The basic data types defined by OpenAPI 3.0"""

    # https://swagger.io/docs/specification/v3_0/data-models/data-types/

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

# Mapping Python types to Open API types
PYTHON_TO_OPENAPI_TYPE_MAP = {
    str: OpenAPITypes.STRING,
    int:  OpenAPITypes.INTEGER,
    float:  OpenAPITypes.NUMBER,
    bool:  OpenAPITypes.BOOLEAN,
    dict:  OpenAPITypes.OBJECT,
    list:  OpenAPITypes.ARRAY,
}

class Schema:
    """Defines the schema for a function's parameters or return value.
    This aligns with OpenAPI schema.
    """
    def __init__(self, type: OpenAPITypes, properties: Optional[dict] = None,
                 required: Optional[list[str]] = None, description: Optional[str] = None,
                 items: Optional['Schema'] = None,
                 enum: Optional[list[str]] = None,
                 default: Optional[any] = None):
        self.arg_type = type
        self.properties = properties if properties is not None else {}
        self.required = required if required is not None else []
        self.description = description
        self.items = items      # For array types
        self.enum = enum        # For enum types
        self.default = default

    def oas_format(self):
        """Converts the Schema object to a dictionary for API consumption."""
        schema_dict = {
            "type": self.arg_type.value,
        }
        if self.description:
            schema_dict["description"] = self.description
        if self.properties:
            schema_dict["properties"] = {k: v.oas_format() for k, v in self.properties.items()}
        if self.required:
            schema_dict["required"] = self.required
        if self.items:
            schema_dict["items"] = self.items.oas_format()
        if self.enum:
            schema_dict["enum"] = self.enum
        # We need to handle non-serializable defaults like Enums
        if self.default is not None:
            if isinstance(self.default, Enum):
                schema_dict["default"] = self.default.value
            else:
                schema_dict["default"] = self.default
        return schema_dict

class FunctionDeclaration:
    """Represents a function's declaration suitable for llm consumption."""
    def __init__(self, name: str, description: str, parameters: Schema):
        self.name = name
        self.description = description
        self.parameters = parameters

    def oas_format(self) -> dict:
        """Converts the FunctionDeclaration object to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters.oas_format()
        }

class FunctionSchemaBuilder:
    """Builds a Schema object for a given Python function's parameters."""
    def __init__(self, func):
        self._func = func
        self._signature = inspect.signature(func)
        # include_extras allows to see Annotated
        self._type_hints = get_type_hints(func, include_extras=True)
        self.properties: dict[str, Schema] = {}
        self.required: list[str] = []
        self._process_parameters()

    def _create_schema_from_type(self, py_type: type) -> Schema:
        """Recursively creates a Schema object from a Python type hint."""
        # Handle list[type]
        if get_origin(py_type) in (list, list, tuple):
            # Get the inner type, default to 'str' if not specified (like just 'list')
            inner_type = get_args(py_type)[0] if get_args(py_type) else str
            return Schema(
                type=OpenAPITypes.ARRAY,
                items=self._create_schema_from_type(inner_type)
            )

        # Handle Optional[type] or Union[type, None]
        if get_origin(py_type) is Union:
            # Filter out NoneType to find the actual type
            args = [arg for arg in get_args(py_type) if arg is not type(None)]
            if args:
                # Recurse with the actual type
                return self._create_schema_from_type(args[0])

        # Handle Enums
        # Use issubclass() and check that it's not the base Enum class itself
        if inspect.isclass(py_type) and issubclass(py_type, Enum):
            # Assuming enum values are strings, which is common.
            # NOTE: You could add logic here to check the type of enum values.
            return Schema(
                type=OpenAPITypes.STRING,
                enum=[member.value for member in py_type]
            )

        # Handle basic types
        openapi_type = PYTHON_TO_OPENAPI_TYPE_MAP.get(py_type, OpenAPITypes.STRING)
        return Schema(type=openapi_type)

    def _process_parameters(self):
        """Analyzes function parameters to build properties and required lists."""
        for name, param in self._signature.parameters.items():
            if name == "self":  # Skip 'self' for methods
                continue

            py_type = self._type_hints.get(name, str) # Default to str if no hint
            description = f"Parameter '{name}'." # Default description

            # Handle Annotated[type, "description"]
            actual_type = py_type
            if get_origin(py_type) is Annotated:
                # Unpack the annotated type and its description
                actual_type, description_annotation = get_args(py_type)
                description = description_annotation

            # Create the base schema from the actual type
            param_schema = self._create_schema_from_type(actual_type)

            # Add the description we found
            param_schema.description = description

            # Add default value if it exists
            if param.default is not inspect.Parameter.empty:
                param_schema.default = param.default
            else:
                # A parameter is required ONLY if it has no default value.
                self.required.append(name)

            self.properties[name] = param_schema

    def build(self) -> Schema:
        """Returns the constructed Schema object for the function's parameters."""
        return Schema(
            type=OpenAPITypes.OBJECT,
            properties=self.properties,
            required=self.required
        )

class FunctionTool:
    """A class to simplify the creation of function declaration objects
    from python functions.
    """
    def __init__(self, func):
        self._func = func
        self.name = func.__name__
        self.description = func.__doc__ if func.__doc__ else f"Function for '{self.name}'."
        self.parameters_schema = FunctionSchemaBuilder(func).build()

    def to_declaration(self) -> FunctionDeclaration:
        """Converts the function into a FunctionDeclaration object."""
        return FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema
        )

def function_tool(func):
    """Decorator to attach FunctionTool metadata to a function,
    making it easy to generate its FunctionDeclaration.
    """
    func.tool_metadata = FunctionTool(func).to_declaration().oas_format
    return func
