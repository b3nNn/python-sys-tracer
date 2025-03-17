import filelock

class FileStreamWriter:
    def __init__(self, filename):
        """Initialize the writer with the target filename."""
        self.filename = filename
        self.lock = filelock.FileLock(filename + '.lock')
        self.file = None

    def __enter__(self):
        """Open the file in append mode when entering the context."""
        self.file = open(self.filename, 'a')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Close the file when exiting the context."""
        if self.file:
            self.file.close()

    def write(self, content):
        """Write content to the file, synchronized with a file lock."""
        if self.file is None:
            raise ValueError("File is not open")
        with self.lock:
            self.file.write(content)

    def flush(self):
        """Flush the file buffer to ensure data is written to disk."""
        if self.file:
            self.file.flush()