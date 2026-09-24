# Declusor Visual Assets Guide

This directory holds screenshots, GIFs, and media assets used in the main [README.md](../../README.md) and documentation.

## Required Assets

| Asset File     | Target Purpose                                                                                                                             | Recommended Dimensions      | Format         |
| :------------- | :----------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------- | :------------- |
| `demo.gif`     | Animated terminal session demonstrating listener startup, client connection, tab completion, command execution, and module loading         | 900x520 px (or 16:9 aspect) | GIF / WebM     |
| `overview.png` | Clean, high-resolution terminal screenshot highlighting listener output, generated stager command, and the interactive `[declusor]` prompt | 1200x675 px (16:9)          | PNG (lossless) |

## Recording `demo.gif` with VHS

You can produce reproducible, terminal recordings using [VHS](https://github.com/charmbracelet/vhs).

### Step 1: Install VHS

```bash
# Via Go
go install github.com/charmbracelet/vhs@latest

# Via Homebrew / Linuxbrew
brew install vhs

# Or via package manager (Ubuntu / Debian / Arch)
# https://github.com/charmbracelet/vhs#installation
```

### Step 2: Create a Tape File (`demo.tape`)

Create a file named `demo.tape` with the following recipe:

```tape
# Output file configuration
Output docs/assets/demo.gif

# Terminal appearance
Set FontSize 15
Set FontFamily "JetBrains Mono"
Set Width 920
Set Height 520
Set Padding 20
Set Theme "Catppuccin Mocha"

# 1. Start Declusor listener
Type "declusor 0.0.0.0 4444" Sleep 500ms Enter
Sleep 2s

# (At this point, connect a target agent in background or via mock socket)
Sleep 1.5s

# 2. Inspect session help
Type "help" Sleep 500ms Enter
Sleep 2s

# 3. Run remote command with streaming output
Type "command uname -a && whoami" Sleep 500ms Enter
Sleep 2.5s

# 4. Load a discovery module
Type "load discovery/system_info.py" Sleep 500ms Enter
Sleep 3s

# 5. Clean exit
Type "exit" Sleep 500ms Enter
Sleep 1s
```

### Step 3: Render the GIF

```bash
vhs demo.tape
```

Move the resulting `demo.gif` directly to this directory (`docs/assets/demo.gif`).

## Capturing `overview.png`

1. Open your terminal in a window configured with:
   - Window size: ~100-120 columns wide, 25-30 rows high.
   - Dark theme (e.g. Catppuccin Mocha, Tokyo Night, One Dark).
   - Modern monospace font (JetBrains Mono, Fira Code, Hack).
2. Start Declusor:
   ```bash
   declusor 0.0.0.0 4444
   ```
3. Take a focused window screenshot (excluding desktop background or taskbars).
4. Save the image as `docs/assets/overview.png`.
