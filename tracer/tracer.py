import datetime
import json
import sys
import jsonpickle
import pathspec
import json
from dataclasses import dataclass
from typing import List
import jsonschema
from tracer.stream import FileStreamWriter

# Define the Filter dataclass
@dataclass
class Filter:
    name: str
    files: List[str]
    modules: List[str]
    functions: List[str]
    classes: List[str]

# Define the Config dataclass
@dataclass
class Config:
    version: str
    filters: List[Filter]

# Define the Filter dataclass
@dataclass
class TracerFilter:
    name: str
    files_spec: pathspec.PathSpec
    modules_spec: pathspec.PathSpec
    functions_spec: pathspec.PathSpec
    classes_spec: pathspec.PathSpec

# Define the configuration schema
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "filters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "files": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "modules": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "functions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "classes": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name", "files", "modules", "functions", "classes"],
                "additionalProperties": False
            }
        }
    },
    "required": ["version", "filters"],
    "additionalProperties": False
}

# Function to load and validate the configuration
def load_config(file_path: str) -> Config:
    """
    Loads and validates configuration data from a JSON file into a Config object.
    
    Args:
        file_path (str): Path to the JSON configuration file.
    
    Returns:
        Config: An instance of the Config class with validated data.
    
    Raises:
        ValueError: If the configuration does not match the expected schema.
    """
    # Read the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Validate against the schema
    try:
        jsonschema.validate(instance=data, schema=CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}")
    
    # Create Filter objects
    filters = [Filter(**filter_dict) for filter_dict in data['filters']]
    
    # Create and return Config object
    return Config(version=data['version'], filters=filters)

class Tracer:
    def trace_func(self, frame, event, arg):
        """
        Trace function to handle all events and log them to a JSONL file.
        """
        if event != "call":
            return self

        file_name = frame.f_code.co_filename
        line_number = frame.f_lineno
        method_name = frame.f_code.co_name
        module_name = frame.f_globals.get('__name__', None)
        
        class_name = None
        if 'self' in frame.f_locals:
            obj = frame.f_locals['self']
            if isinstance(obj, type):  # If 'self' is a class (classmethod)
                class_name = obj.__name__
            else:  # If 'self' is an instance
                class_name = obj.__class__.__name__

        if self._do_ignore_class(class_name):
            return self

        ok, filter = self._get_filter(module_name, file_name, class_name, method_name)

        if not ok:
            return self

        metadata = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "filter": filter.name,
            "file": file_name,
            "line": line_number,
            "function": method_name,
            "class": class_name,
            "module": module_name,
        }

        self.writer.write(f"{jsonpickle.encode(metadata, warn=False)}\n")

        uid = f'{module_name}.{class_name}.{method_name}'
        if uid not in self.visited:
            self.visited.append(uid)
            print(f"Tracing call: Module={module_name}, Class={class_name}, Method={method_name}")

        return self

    def _read_config(self, config: Config):
        for filter in config.filters:
            files = list(filter.files) if filter.files else []
            if len(files) == 0:
                files.append("*")

            modules = list(filter.modules) if filter.modules else []
            if len(modules) == 0:
                modules.append("*")

            functions = list(filter.functions) if filter.functions else []
            if len(functions) == 0:
                functions.append("*")

            classes = list(filter.classes) if filter.classes else []
            if len(classes) == 0:
                classes.append("*")

            self.filters.append(
                TracerFilter(filter.name,
                             pathspec.PathSpec.from_lines('gitwildmatch', files),
                             pathspec.PathSpec.from_lines('gitwildmatch', modules),
                             pathspec.PathSpec.from_lines('gitwildmatch', functions),
                             pathspec.PathSpec.from_lines('gitwildmatch', classes)
                             )
                        )

    def _do_ignore_class(self, class_name):
        if class_name is None:
            return False
        
        return class_name in self._ignore_classes

    def _get_filter(self, module_name, file_name, class_name, function_name) -> tuple[bool, TracerFilter]:
        for filter in self.filters:
            try:
                if module_name is not None and not filter.modules_spec.match_file(module_name):
                    continue
                if file_name is not None and not filter.files_spec.match_file(file_name):
                    continue
                if class_name is not None and not filter.classes_spec.match_file(class_name):
                    continue
                if function_name is not None and not filter.functions_spec.match_file(function_name):
                    continue
            except:
                continue

            return True, filter
        return False, None

    def __init__(self, writer: FileStreamWriter, config: Config):
        self.writer = writer
        self.visited = list[str]()
        self.filters = list[TracerFilter]()
        self._ignore_classes = ["Tracer", "FileStreamWriter"]
        self._read_config(config)

    def __enter__(self):
        sys.settrace(self.trace_func)
        return self

    def __call__(self, *args, **kwds):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.writer.flush()

    def __del__(self):
        sys.settrace(None)

