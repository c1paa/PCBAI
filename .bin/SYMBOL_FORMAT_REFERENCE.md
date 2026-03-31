# KiCad 9.0 Symbol Format Reference

## Correct Symbol Format

All symbols must follow this structure:

```lisp
(symbol "Library:Name"
  (in_bom yes)
  (on_board yes)
  (property "Reference" "R"
    (at x y rotation)
    (effects
      (font
        (size 1.27 1.27)
      )
    )
  )
  (property "Value" "R"
    (at x y rotation)
    (effects
      (font
        (size 1.27 1.27)
      )
    )
  )
  (property "Footprint" "Library:Footprint"
    (at x y rotation)
    (effects
      (font
        (size 1.27 1.27)
      )
      (hide yes)
    )
  )
  (symbol "Name_0_1"
    (graphics...)
  )
  (symbol "Name_1_1"
    (pin type direction
      (at x y rotation)
      (length L)
      (name "Name"
        (effects
          (font
            (size 1.27 1.27)
          )
        )
      )
      (number "1"
        (effects
          (font
            (size 1.27 1.27)
          )
        )
      )
    )
  )
  (embedded_fonts no)
)
```

## Key Rules

1. **NO** `pin_numbers`, `pin_names`, `exclude_from_sim` at top level
2. **Each property** must have proper nesting with `at` and `effects`
3. **Symbol parts** are separate `(symbol "Name_X_Y" ...)` blocks
4. **Pins** must have `type`, `direction`, `at`, `length`, `name`, `number`
5. **All effects** properly nested with `font` → `size`

## Fixed Symbols

See `src/pcba/schematic.py`:
- `_symbol_resistor()` - ✅ Fixed
- `_symbol_led()` - TODO
- `_symbol_capacitor()` - TODO
- `_symbol_generic_ic()` - TODO
- `_symbol_generic_sensor()` - TODO
- `_symbol_power_5v()` - TODO
- `_symbol_gnd()` - TODO

## Testing

After fixing each symbol:
1. Generate test schematic
2. Open in KiCad 9.0
3. Verify symbol renders correctly (no "?")
4. Run `pcba validate file.kicad_sch`
