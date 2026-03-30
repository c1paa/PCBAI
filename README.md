# PCBAI — AI-Powered KiCad Schematic Generator

**KiCad 9.0 compatible** • **Interactive Dialog** • **Russian Language Support**

## Quick Start

```bash
# Activate environment
source venv/bin/activate

# Start interactive dialog
pcba dialog

# Or generate directly
pcba schematic "LED with 330 ohm resistor to Arduino pin 5" -o circuit.kicad_sch

# Open in KiCad
open circuit.kicad_sch
```

## Features

✅ **Interactive Dialog** — Chat with AI to design schematics
✅ **KiCad 9.0 Format** — Correct symbol libraries and footprints
✅ **Component Database** — Official KiCad libraries mapped
✅ **PCB Routing** — FreeRouting integration
✅ **Validation** — kicad-cli syntax checking

## Commands

| Command | Description |
|---------|-------------|
| `pcba dialog` | Interactive AI design session |
| `pcba schematic "description"` | Generate schematic from text |
| `pcba route file.kicad_pcb` | Auto-route PCB traces |
| `pcba validate file.kicad_sch` | Validate with kicad-cli |
| `pcba check` | System requirements check |

## Example Session

```
$ pcba dialog

🔹 Вы: Светодиод с резистором к Arduino на pin 5

AI: Понял! Вот схема:

Компоненты:
  • R1: Резистор 330Ω
  • LED1: Светодиод красный
  • U1: ATmega328P

Подключение:
  • Arduino Pin 5 → Резистор 330Ω
  • Резистор → Анод светодиода
  • Катод → GND

Сохранить? (save led.kicad_sch)

🔹 Вы: save led.kicad_sch

✅ Saved: led.kicad_sch
```

## Project Structure

```
PCBAI/
├── src/pcba/
│   ├── cli.py           # CLI commands
│   ├── dialog.py        # Interactive dialog
│   ├── schematic.py     # KiCad 9.0 generator
│   ├── parser.py        # PCB file parser
│   ├── exporter.py      # DSN exporter
│   └── routing.py       # FreeRouting integration
├── knowledge_base/
│   ├── config.json      # LLM API config
│   └── components.json  # Component database
├── agent_state/         # Session state files
├── .bin/                # Archived files
└── README.md            # This file
```

## Configuration

### LLM API Setup

Edit `knowledge_base/config.json`:

```json
{
  "default_provider": "google",
  "llm_providers": {
    "google": {
      "enabled": true,
      "api_key": "YOUR_GOOGLE_AI_STUDIO_KEY"
    }
  }
}
```

Get API key: https://aistudio.google.com/app/apikey

### Alternatives

- **Puter.js** — Free, no key needed (set `"default_provider": "puter"`)
- **Ollama** — Local, unlimited (requires `ollama serve`)

## Continuation Guide

### Resume from Another Device

```bash
# Clone repository
git clone <your-repo-url>
cd PCBAI

# Read current state
cat agent_state/project_state.md
cat agent_state/project_progress.json

# Activate and continue
source venv/bin/activate
pcba dialog
```

### Session State Files

| File | Purpose |
|------|---------|
| `agent_state/project_state.md` | Human-readable status |
| `agent_state/project_progress.json` | Machine-readable progress |
| `agent_state/task_log.md` | Task history |
| `IMPLEMENTATION_PLAN.md` | Detailed implementation plan |

## Requirements

- **Python 3.10+**
- **KiCad 9.0** (optional, for validation)
- **Java** (for FreeRouting)
- **LLM API** (Google AI Studio / Puter.js / Ollama)

## Development Status

**Progress: 85% Complete**

- ✅ Core functionality
- ✅ KiCad 9.0 format
- ✅ Component database
- ✅ Dialog mode
- 🔄 Testing & validation
- 🔄 Custom symbol generation

## Troubleshooting

### Symbols show as "question marks"
- Check that component uses correct KiCad 9.0 lib_id
- Verify symbol library is loaded in KiCad
- Run `pcba validate file.kicad_sch`

### kicad-cli not found
- Install KiCad 9.0 from https://www.kicad.org/download/
- Validation will skip if not installed (optional)

### LLM API errors
- Check API key in `knowledge_base/config.json`
- Verify internet connection
- Try fallback provider (Puter.js)

## License

MIT License

## Resources

- **KiCad 9.0 Docs:** https://docs.kicad.org/9.0/
- **Symbol Libraries:** https://gitlab.com/kicad/libraries/kicad-symbols
- **Footprint Libraries:** https://gitlab.com/kicad/libraries/kicad-footprints
