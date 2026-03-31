# Custom Symbol Creation Guide

## Overview

When AI encounters an unknown component, it can create a simple rectangular symbol with pins.

## Symbol Format (KiCad 9.0)

```lisp
(symbol "Custom:ComponentName"
  (in_bom yes)
  (on_board yes)
  (property "Reference" "U"
    (at x y 0)
    (effects (font (size 1.27 1.27)))
  )
  (property "Value" "Value"
    (at x y 0)
    (effects (font (size 1.27 1.27)))
  )
  (symbol "ComponentName_0_1"
    (rectangle
      (start -7.62 -7.62)
      (end 7.62 7.62)
      (stroke (width 0.254) (type default))
      (fill (type background))
    )
  )
  (symbol "ComponentName_1_1"
    (pin passive line
      (at x y rotation)
      (length 2.54)
      (name "PinName"
        (effects (font (size 1.27 1.27)))
      )
      (number "1"
        (effects (font (size 1.27 1.27)))
      )
    )
    ... more pins ...
  )
  (embedded_fonts no)
)
```

## Pin Placement Rules

### For rectangular symbol (10x10mm):
- **Left side** (inputs): x = -7.62, y = -5.08, -2.54, 0, 2.54, 5.08
- **Right side** (outputs): x = 7.62, y = -5.08, -2.54, 0, 2.54, 5.08
- **Top side** (power): x = -5.08, -2.54, 0, 2.54, y = 7.62
- **Bottom side** (ground): x = -5.08, -2.54, 0, 2.54, y = -7.62

### Pin Directions:
- **Left pins**: rotation = 0 (pointing right)
- **Right pins**: rotation = 180 (pointing left)
- **Top pins**: rotation = 270 (pointing down)
- **Bottom pins**: rotation = 90 (pointing up)

## Example: 8-pin IC

```
        [1] [8]
         |   |
    VCC [2] [7] OUT
         |   |
    IN1  [3] [6] IN2
         |   |
    GND [4] [5] NC
         -----
```

## Implementation Steps

1. **Get component info from user:**
   - Component name
   - Number of pins
   - Pin names and functions

2. **Generate symbol:**
   - Create rectangle (10x10mm default)
   - Add pins on appropriate sides
   - Assign pin numbers sequentially

3. **Save to library:**
   - Add to `custom_symbols/` directory
   - Update component database

## Example Generation

**Input:**
```
Component: MySensor
Pins: 4
Pin 1: VCC
Pin 2: GND
Pin 3: DATA
Pin 4: CLK
```

**Output:**
- Rectangle symbol
- Pin 1 (VCC) on top
- Pin 2 (GND) on bottom
- Pin 3 (DATA) on left
- Pin 4 (CLK) on right

---

## Future Enhancements

1. **Auto-detect pinout from datasheet**
2. **Search online libraries**
3. **Import from existing KiCad libraries**
4. **Generate footprints automatically**
