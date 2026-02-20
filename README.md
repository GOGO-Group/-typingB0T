# Auto Typing / Auto Key Presser

GUI application to emit automated key press events based on user-provided text.

## Quick start

1. Create and activate a Python environment (recommended):

```bash
python -m venv .venv
source .venv/Scripts/activate    # on Windows (bash)
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the GUI app:

```bash
python auto_key.py
```

## Features

- **Text Input**: Paste or type the text you want to emit in the main text area
- **Start/Stop Button**: Click to start emitting; click again to stop mid-process
- **Left Settings Panel**:
  - **Newline mode**: Choose between `Enter` or `Shift+Enter` for line breaks
  - **Whitespace**: Option to remove leading/trailing spaces from each line
  - **Character delay**: Control typing speed (in milliseconds between characters)

## How to use

1. Paste your text into the main text area
2. (Optional) Adjust settings on the left panel:
   - Select newline behavior
   - Toggle whitespace removal
   - Set character delay (lower = faster)
3. Click **"Start Emitting"** button
4. The status bar shows the current state
5. Click **"Stop Emitting"** to halt mid-process or wait for completion

## Notes

- The app emits characters one-by-one with a configurable delay between each
- Newlines in the text area will be handled according to your selected newline mode
- Set character delay to `0` for maximum speed, or use `50`–`100` ms for natural typing speed
- Use this responsibly; do not target secure system prompts or UAC dialogs

## License

No license.
