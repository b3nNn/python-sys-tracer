import os
import matplotlib.pyplot as plt

# Base Widget class
class Widget:
    def to_markdown(self):
        """Generate markdown content for the widget."""
        raise NotImplementedError("Subclasses must implement to_markdown()")

# TextWidget for plain text or markdown-formatted text
class TextWidget(Widget):
    def __init__(self, text):
        self.text = text

    def to_markdown(self):
        return self.text

# HeadingWidget for section headings
class HeadingWidget(Widget):
    def __init__(self, text, level=1):
        self.text = text
        self.level = max(1, min(level, 6))  # Ensure level is between 1 and 6

    def to_markdown(self):
        return "#" * self.level + " " + self.text

# ImageWidget for embedding images
class ImageWidget(Widget):
    def __init__(self, image_path, alt_text):
        self.image_path = image_path
        self.alt_text = alt_text

    def to_markdown(self):
        return f"![{self.alt_text}]({self.image_path})"

# TableWidget for generating markdown tables
class TableWidget(Widget):
    def __init__(self, data, headers, alignments=None):
        self.data = data  # List of lists, each inner list is a row
        self.headers = headers
        self.alignments = alignments or ['left'] * len(headers)

    def to_markdown(self):
        if not self.headers or not self.data:
            return ""
        
        # Generate header row
        header_row = "| " + " | ".join(self.headers) + " |"
        
        # Generate separator row with alignment
        separator = []
        for align in self.alignments:
            if align == 'right':
                separator.append("---:")
            elif align == 'center':
                separator.append(":---:")
            else:  # default to left
                separator.append(":---")
        separator_row = "| " + " | ".join(separator) + " |"
        
        safe_data = [[str(row) for row in rows] for rows in self.data]

        # Generate data rows
        data_rows = ["| " + " | ".join(row) + " |" for row in safe_data]
        
        return header_row + "\n" + separator_row + "\n" + "\n".join(data_rows)

# CodeWidget for code blocks with syntax highlighting
class CodeWidget(Widget):
    def __init__(self, code, language=""):
        self.code = code
        self.language = language

    def to_markdown(self):
        return f"```{self.language}\n{self.code}\n```"

# ChartWidget for generating and embedding charts as images
class ChartWidget(Widget):
    def __init__(self, chart_function, image_path):
        self.chart_function = chart_function  # Function that generates the chart
        self.image_path = image_path

    def prepare(self, output_dir):
        """Generate the chart image."""
        image_filename = os.path.basename(self.image_path)
        full_image_path = os.path.join(output_dir, image_filename)
        self.chart_function(full_image_path)
        self.image_path = image_filename  # Update to relative path

    def to_markdown(self):
        return f"![Chart]({self.image_path})"

# SectionWidget for grouping widgets under a heading
class SectionWidget(Widget):
    def __init__(self, title, level=1):
        self.title = title
        self.level = max(1, min(level, 6))
        self.widgets = []

    def add_widget(self, widget):
        if isinstance(widget, Widget):
            self.widgets.append(widget)
        else:
            raise ValueError("Only Widget instances can be added")

    def prepare(self, output_dir):
        """Prepare any sub-widgets that need it."""
        for widget in self.widgets:
            if hasattr(widget, 'prepare'):
                widget.prepare(output_dir)

    def to_markdown(self):
        md = "#" * self.level + " " + self.title + "\n\n"
        for widget in self.widgets:
            md += widget.to_markdown() + "\n\n"
        return md.strip()

# Reporter class to manage widgets and generate the report
class Reporter:
    def __init__(self):
        self.widgets = []

    def add_widget(self, widget):
        """Add a widget to the report."""
        if isinstance(widget, Widget):
            self.widgets.append(widget)
        else:
            raise ValueError("Only Widget instances can be added")

    def prepare(self, output_dir):
        """Prepare widgets that generate files (e.g., charts)."""
        for widget in self.widgets:
            if hasattr(widget, 'prepare'):
                widget.prepare(output_dir)

    def generate_markdown(self):
        """Generate the full markdown content."""
        return "\n\n".join(widget.to_markdown() for widget in self.widgets).strip()

    def save_to_file(self, filename):
        """Save the markdown report to a file, preparing any necessary files."""
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.prepare(output_dir)
        with open(filename, 'w') as f:
            f.write(self.generate_markdown())
