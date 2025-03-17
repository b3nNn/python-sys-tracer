import json
from collections import Counter
import matplotlib.pyplot as plt
from reporter.reporter import Reporter, HeadingWidget, TableWidget, ChartWidget  # Assuming these are defined in the reporter module

def audit_analysis_widgets(document):
    """
    Analyze the audit log and return a list of widgets for the reporter.
    
    Args:
        document (str): The audit log as a string with JSON objects separated by newlines.
    
    Returns:
        list: A list of reporter widgets for rendering the analysis.
    """
    # Parse entries
    entries = [json.loads(line) for line in document.strip().split('\n') if line.strip()]
    
    # Extract module, class, function tuples
    calls = [(entry['module'], entry['class'], entry['function']) for entry in entries]
    
    # Count frequencies
    call_counter = Counter(calls)
    
    # Get unique modules
    modules = set(entry['module'] for entry in entries)
    
    # Module frequencies
    module_counter = Counter(entry['module'] for entry in entries)
    
    # Class frequencies per module
    class_counter = {}
    for module in modules:
        class_counter[module] = Counter(entry['class'] for entry in entries if entry['module'] == module)
    
    # Top 50 functions
    top_functions = sorted(call_counter.items(), key=lambda x: x[1], reverse=True)[:50]
    
    # Execution flow (first 150 calls)
    N = 150
    execution_flow = calls[:N]
    
    # Overview statistics
    unique_functions = len(set(calls))
    unique_classes = len(set((module, cls) for module, cls, _ in calls))
    overview_data = [
        ["Total audit entries", len(entries)],
        ["Unique modules", len(modules)],
        ["Unique classes", unique_classes],
        ["Unique functions", unique_functions]
    ]
    
    # Module usage data
    module_data = sorted(module_counter.items(), key=lambda x: x[1], reverse=True)
    
    # Class usage data
    class_data = []
    for module in modules:
        for cls, freq in class_counter[module].items():
            class_data.append([module, cls, freq])
    class_data.sort(key=lambda x: (x[0], -x[2]))  # Sort by module, then frequency descending
    
    # Top functions data
    top_functions_data = [list(func) + [count] for func, count in top_functions]
    
    # Execution flow data
    execution_flow_data = [[i + 1, module, cls, func] for i, (module, cls, func) in enumerate(execution_flow)]
    
    # Create widgets
    widgets = []
    
    # Overview
    widgets.append(HeadingWidget("Overview", level=2))
    widgets.append(TableWidget(overview_data, ["Statistic", "Value"]))
    
    # Module Usage
    widgets.append(HeadingWidget("Module Usage", level=2))
    widgets.append(TableWidget(module_data, ["Module", "Frequency"]))
    
    # Class Usage
    widgets.append(HeadingWidget("Class Usage", level=2))
    widgets.append(TableWidget(class_data, ["Module", "Class", "Frequency"]))
    
    # Function Call Frequency
    widgets.append(HeadingWidget("Function Call Frequency", level=2))
    widgets.append(TableWidget(top_functions_data, ["Module", "Class", "Function", "Frequency"]))
    
    # Execution Flow
    widgets.append(HeadingWidget("Execution Flow (First 150 Calls)", level=2))
    widgets.append(TableWidget(execution_flow_data, ["Step", "Module", "Class", "Function"]))
    
    # Chart for top 50 functions
    def create_top_functions_chart(image_path):
        top_funcs = top_functions[:50]
        labels = [f"{func[1]}.{func[2]}" for func, count in top_funcs]
        counts = [count for func, count in top_funcs]
        plt.figure(figsize=(16, 12))
        plt.barh(labels, counts)
        plt.xlabel("Frequency")
        plt.title("Top 50 Most Frequently Called Functions")
        plt.tight_layout()
        plt.savefig(image_path)
        plt.close()
    
    widgets.append(ChartWidget(create_top_functions_chart, "top_functions.png"))
    
    return widgets

# Example usage
if __name__ == "__main__":
    # Replace with the actual audit log string
    with open("audit.jsonl", "r") as f:
        document = f.read()
    
    reporter = Reporter()
    reporter.add_widget(HeadingWidget("Audit Analysis Report", level=1))
    analysis_widgets = audit_analysis_widgets(document)
    for widget in analysis_widgets:
        reporter.add_widget(widget)
    reporter.save_to_file("audit_report.md")