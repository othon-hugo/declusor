import shutil

label: type
format_table: type

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

try:
    results: list[list[str]] = []

    for name, binary in tools:
        path = shutil.which(binary)
        status = path if path else "not found"

        results.append([name, binary, status])

    headers = ["Tool", "Binary", "Path"]

    table_output = format_table(headers, results)
    label("Development Tools", table_output)
except Exception as e:
    label("Development Tools", e)
