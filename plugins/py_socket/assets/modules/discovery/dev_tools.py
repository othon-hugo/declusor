"""Module: development tool detection for the py_socket client agent.

Loaded on demand via the ``load`` command. Detects interpreters, compilers,
build tools and version control software available in PATH.
"""
import shutil

tools = [
    ("Python", "python3"),
    ("Python (legacy)", "python"),
    ("Ruby", "ruby"),
    ("Node.js", "node"),
    ("PHP", "php"),
    ("Perl", "perl"),
    ("Java", "java"),
    ("GCC", "gcc"),
    ("Clang", "clang"),
    ("Make", "make"),
    ("CMake", "cmake"),
    ("Git", "git"),
    ("Docker", "docker"),
    ("curl", "curl"),
    ("wget", "wget"),
    ("nc / ncat", "nc"),
    ("socat", "socat"),
]

results = []
for label, binary in tools:
    path = shutil.which(binary)
    status = path if path else "not found"
    results.append([label, binary, status])

headers = ["Tool", "Binary", "Path"]
table_output = format_table(headers, results)
print_with_label("Development & Recon Tools", table_output)
