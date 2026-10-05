import base64
import subprocess
from pathlib import Path


def _std_sh_path() -> Path:
    return Path(__file__).parent.parent / "assets" / "helpers" / "std.sh"


def _run_in_std(command: str) -> subprocess.CompletedProcess[str]:
    std_path = _std_sh_path()
    script = f'. "{std_path}"\n{command}'
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


class TestShellSocketStdHelpersEncoding:
    """Unit tests for encoding and decoding primitives in std.sh."""

    def test_decode_b64__valid_input__decodes_to_bytes(self) -> None:
        """Verify decode_b64 decodes base64 string and piped input."""

        b64_str = base64.b64encode(b"hello declusor shell").decode()
        proc1 = _run_in_std(f'decode_b64 "{b64_str}"')
        assert proc1.stdout == "hello declusor shell"

        proc2 = _run_in_std(f'printf "%s" "{b64_str}" | decode_b64')
        assert proc2.stdout == "hello declusor shell"

    def test_encode_b64__valid_input__encodes_to_ascii(self) -> None:
        """Verify encode_b64 encodes raw input to base64 string."""

        proc = _run_in_std('printf "test payload" | encode_b64')
        expected = base64.b64encode(b"test payload").decode()
        assert proc.stdout.strip() == expected

    def test_hash_value__string_input__produces_sha256(self) -> None:
        """Verify hash_value calculates deterministic SHA-256."""

        proc = _run_in_std('printf "sample text" | hash_value')
        assert len(proc.stdout.strip()) == 64


class TestShellSocketStdHelpersStorage:
    """Unit tests for storage and removal primitives in std.sh."""

    def test_store_file__with_target_path__writes_bytes_and_returns_path(self, tmp_path: Path) -> None:
        """Verify store_file writes piped data to the specified destination path."""

        dest = tmp_path / "out.txt"
        proc = _run_in_std(f'printf "stored content" | store_file "{dest}"')

        assert proc.stdout.strip() == str(dest)
        assert dest.read_text() == "stored content"

    def test_store_file__without_target_path__generates_temp_file(self) -> None:
        """Verify store_file generates an ephemeral path when destination is omitted."""

        proc = _run_in_std('printf "ephemeral content" | store_file')
        stored_path = proc.stdout.strip()
        assert Path(stored_path).exists()
        assert Path(stored_path).read_text() == "ephemeral content"

        # Cleanup
        _run_in_std(f'remove_file "{stored_path}"')
        assert not Path(stored_path).exists()

    def test_remove_file__existing_and_nonexistent__handles_safely(self, tmp_path: Path) -> None:
        """Verify remove_file deletes target file and handles non-existent paths gracefully."""

        target = tmp_path / "to_delete.txt"
        target.write_text("temporary")
        assert target.exists()

        _run_in_std(f'remove_file "{target}"')
        assert not target.exists()

        # Non-existent file should exit with code 0
        proc = _run_in_std(f'remove_file "{tmp_path / "missing.txt"}"')
        assert proc.returncode == 0


class TestShellSocketStdHelpersExecution:
    """Unit tests for execution primitives in std.sh."""

    def test_execute_source__valid_script__executes_in_scope(self) -> None:
        """Verify execute_source evaluates shell code in the current shell scope."""

        proc = _run_in_std("execute_source 'VAR=42; echo val=$VAR'")
        assert "val=42" in proc.stdout

    def test_execute_source__with_arguments__forwards_positional_parameters(self) -> None:
        """Verify execute_source forwards positional arguments to the evaluated code."""

        proc = _run_in_std("execute_source 'echo arg1=$1 arg2=$2' 'foo' 'bar'")
        assert "arg1=foo arg2=bar" in proc.stdout

    def test_execute_binary__executable_script__runs_and_cleans_up(self, tmp_path: Path) -> None:
        """Verify execute_binary executes binary and unlinks it when --cleanup is passed."""

        script_path = tmp_path / "test_bin.sh"
        script_path.write_text("#!/bin/sh\necho 'binary run ok'\n")

        proc = _run_in_std(f'execute_binary --cleanup "{script_path}"')
        assert "binary run ok" in proc.stdout
        assert not script_path.exists()


class TestShellSocketStdHelpersUtilities:
    """Unit tests for formatting utilities in std.sh."""

    def test_column__formats_aligned_table(self) -> None:
        """Verify column formats delimiter-separated text into aligned columns."""

        proc = _run_in_std('printf "A;B\n123;4\n" | column -t -s ";"')
        assert "A" in proc.stdout
        assert "B" in proc.stdout

    def test_label__prints_header_and_content(self) -> None:
        """Verify label prints an underlined title before stream contents."""

        proc = _run_in_std('printf "payload data\n" | label "Header Title"')
        assert "HEADER TITLE" in proc.stdout
        assert "------------" in proc.stdout
        assert "payload data" in proc.stdout
