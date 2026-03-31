"""
Natural Language Description Generator for KiCad Schematics.

Generates diverse, meaningful descriptions from parsed schematic data
for use as training input text.
"""

import random
from typing import Any

from .component_database import (
    get_component_description,
    get_component_category,
    CATEGORY_MCU, CATEGORY_SENSOR, CATEGORY_PASSIVE, CATEGORY_ACTIVE,
    CATEGORY_CONNECTOR, CATEGORY_POWER, CATEGORY_DISPLAY,
    CATEGORY_COMMUNICATION, CATEGORY_MOTOR, CATEGORY_RELAY,
    CATEGORY_SWITCH, CATEGORY_AUDIO, CATEGORY_MEMORY, CATEGORY_LOGIC,
    CATEGORY_MODULE,
)


# ============================================================================
# Circuit Pattern Detection
# ============================================================================

def detect_patterns(components: list[dict], connections: list[dict]) -> list[str]:
    """Detect common circuit patterns from components and connections."""
    patterns = []

    comp_by_ref = {c['ref']: c for c in components}
    categories = {c['ref']: get_component_category(c.get('lib_id', '')) for c in components}

    # LED + Resistor pattern
    led_refs = [ref for ref, cat in categories.items() if _is_led(comp_by_ref[ref])]
    resistor_refs = [ref for ref, cat in categories.items() if _is_resistor(comp_by_ref[ref])]
    if led_refs and resistor_refs:
        for conn in connections:
            from_ref = conn['from'].split(':')[0]
            to_ref = conn['to'].split(':')[0]
            if (from_ref in led_refs and to_ref in resistor_refs) or \
               (from_ref in resistor_refs and to_ref in led_refs):
                patterns.append("LED_INDICATOR")
                break

    # I2C bus detection (SDA/SCL labels or pin names)
    conn_pins = set()
    for conn in connections:
        conn_pins.add(conn['from'].split(':')[-1].upper())
        conn_pins.add(conn['to'].split(':')[-1].upper())
    if 'SDA' in conn_pins and 'SCL' in conn_pins:
        patterns.append("I2C_BUS")
    if 'MOSI' in conn_pins and 'MISO' in conn_pins and 'SCK' in conn_pins:
        patterns.append("SPI_BUS")

    # Button + pull-up/pull-down
    button_refs = [ref for ref, cat in categories.items() if cat == CATEGORY_SWITCH]
    if button_refs and resistor_refs:
        patterns.append("BUTTON_WITH_PULLUP")

    # Voltage regulator + filter caps
    power_refs = [ref for ref, cat in categories.items() if cat == CATEGORY_POWER]
    cap_refs = [ref for ref in comp_by_ref if _is_capacitor(comp_by_ref[ref])]
    if power_refs and cap_refs:
        patterns.append("REGULATED_POWER")

    # Motor driver
    motor_refs = [ref for ref, cat in categories.items() if cat == CATEGORY_MOTOR]
    if motor_refs:
        patterns.append("MOTOR_CONTROL")

    # Display
    display_refs = [ref for ref, cat in categories.items() if cat == CATEGORY_DISPLAY]
    if display_refs:
        patterns.append("DISPLAY_OUTPUT")

    # Sensor reading
    sensor_refs = [ref for ref, cat in categories.items() if cat == CATEGORY_SENSOR]
    if sensor_refs:
        patterns.append("SENSOR_INPUT")

    return list(set(patterns))


# ============================================================================
# Description Templates
# ============================================================================

# Templates for MCU-based circuits
MCU_TEMPLATES = [
    "{mcu} circuit with {peripherals}",
    "{mcu} project featuring {peripherals}",
    "{mcu} with {peripherals} connected",
    "{mcu} board controlling {peripherals}",
    "Circuit based on {mcu} with {peripherals}",
    "{mcu} schematic: {peripherals}",
    "Design with {mcu} and {peripherals}",
    "{mcu} driving {peripherals}",
    "Electronic circuit: {mcu} interfacing with {peripherals}",
    "{mcu} setup with {peripherals}",
]

# Templates for simple circuits (no MCU)
SIMPLE_TEMPLATES = [
    "Circuit with {components}",
    "Schematic containing {components}",
    "Electronic design with {components}",
    "Simple circuit: {components}",
    "{components} circuit",
    "Board with {components}",
    "Design featuring {components}",
    "Schematic: {components}",
]

# Templates with pattern context
PATTERN_TEMPLATES = {
    "LED_INDICATOR": [
        "{mcu} with LED indicator on {pin}",
        "{mcu} controlling {count} LEDs with current-limiting resistors",
        "LED blink circuit using {mcu}",
    ],
    "I2C_BUS": [
        "{mcu} communicating with {sensor} via I2C",
        "{mcu} reading {sensor} over I2C bus",
        "I2C sensor circuit: {mcu} with {sensor}",
    ],
    "SPI_BUS": [
        "{mcu} connected to {device} via SPI",
        "SPI communication between {mcu} and {device}",
    ],
    "SENSOR_INPUT": [
        "{mcu} reading data from {sensor}",
        "Sensor monitoring circuit: {mcu} with {sensor}",
        "{mcu} with {sensor} for environmental monitoring",
    ],
    "MOTOR_CONTROL": [
        "{mcu} controlling motors via {driver}",
        "Motor control circuit with {mcu} and {driver}",
    ],
    "DISPLAY_OUTPUT": [
        "{mcu} displaying data on {display}",
        "{mcu} with {display} output",
    ],
    "BUTTON_WITH_PULLUP": [
        "{mcu} with push button input",
        "Button input circuit for {mcu}",
    ],
    "REGULATED_POWER": [
        "Power supply circuit with {regulator}",
        "{regulator} providing stable voltage",
    ],
}

# Detail-level variations
DETAIL_SUFFIXES = [
    "",
    " with power connections",
    " including decoupling capacitors",
    " and ground plane",
    " on breadboard layout",
]


def generate_descriptions(
    components: list[dict],
    connections: list[dict],
    count: int = 2,
) -> list[str]:
    """
    Generate multiple natural language descriptions for a schematic.

    Args:
        components: List of component dicts with 'ref', 'lib_id', 'value'
        connections: List of connection dicts
        count: Number of description variants to generate

    Returns:
        List of description strings
    """
    if not components:
        return []

    # Analyze circuit
    categories = {}
    for comp in components:
        ref = comp.get('ref', '')
        lib_id = comp.get('lib_id', '')
        cat = get_component_category(lib_id)
        categories[ref] = cat

    # Find main MCU
    mcu = _find_main_mcu(components)
    mcu_name = get_component_description(mcu['lib_id']) if mcu else None

    # Categorize other components
    peripherals = _categorize_peripherals(components, mcu)
    patterns = detect_patterns(components, connections)

    descriptions = set()

    for _ in range(count * 3):  # Generate extra, then pick best
        if len(descriptions) >= count:
            break

        desc = _generate_single_description(
            mcu_name, peripherals, patterns, components, connections
        )
        if desc and len(desc) >= 10:
            descriptions.add(desc)

    result = list(descriptions)[:count]

    # Fallback: simple description
    if not result:
        result = [_generate_fallback_description(components)]

    return result


def _generate_single_description(
    mcu_name: str | None,
    peripherals: dict[str, list[str]],
    patterns: list[str],
    components: list[dict],
    connections: list[dict],
) -> str:
    """Generate a single description variant."""

    # Try pattern-based templates first
    if patterns and mcu_name:
        pattern = random.choice(patterns)
        templates = PATTERN_TEMPLATES.get(pattern, [])
        if templates:
            template = random.choice(templates)
            desc = _fill_pattern_template(
                template, mcu_name, peripherals, components, connections
            )
            if desc:
                return desc

    # MCU-based circuit
    if mcu_name:
        periph_text = _peripherals_to_text(peripherals)
        if periph_text:
            template = random.choice(MCU_TEMPLATES)
            desc = template.format(mcu=mcu_name, peripherals=periph_text)
            suffix = random.choice(DETAIL_SUFFIXES)
            return desc + suffix

        return f"{mcu_name} circuit"

    # Simple circuit (no MCU)
    comp_text = _components_to_text(components)
    if comp_text:
        template = random.choice(SIMPLE_TEMPLATES)
        return template.format(components=comp_text)

    return None


def _fill_pattern_template(
    template: str,
    mcu_name: str,
    peripherals: dict[str, list[str]],
    components: list[dict],
    connections: list[dict],
) -> str | None:
    """Fill in a pattern-specific template."""
    replacements = {'mcu': mcu_name}

    # Find sensor
    sensors = peripherals.get(CATEGORY_SENSOR, [])
    if sensors:
        replacements['sensor'] = sensors[0]

    # Find driver
    drivers = peripherals.get(CATEGORY_MOTOR, [])
    if drivers:
        replacements['driver'] = drivers[0]

    # Find display
    displays = peripherals.get(CATEGORY_DISPLAY, [])
    if displays:
        replacements['display'] = displays[0]

    # Find device (generic)
    all_periph = []
    for cat_items in peripherals.values():
        all_periph.extend(cat_items)
    if all_periph:
        replacements['device'] = all_periph[0]

    # Count LEDs
    led_count = sum(1 for c in components if _is_led(c))
    replacements['count'] = str(led_count) if led_count > 0 else '1'

    # Find a pin from connections
    if connections:
        pin = connections[0].get('from', '').split(':')[-1]
        replacements['pin'] = pin or 'digital pin'
    else:
        replacements['pin'] = 'digital pin'

    replacements['regulator'] = peripherals.get(CATEGORY_POWER, ['voltage regulator'])[0]

    try:
        return template.format(**replacements)
    except (KeyError, IndexError):
        return None


def _find_main_mcu(components: list[dict]) -> dict | None:
    """Find the main MCU/module in the component list."""
    mcu_priorities = [CATEGORY_MCU, CATEGORY_MODULE]

    for priority_cat in mcu_priorities:
        for comp in components:
            cat = get_component_category(comp.get('lib_id', ''))
            if cat == priority_cat:
                return comp
    return None


def _categorize_peripherals(
    components: list[dict],
    mcu: dict | None,
) -> dict[str, list[str]]:
    """Group non-MCU components by category with descriptions."""
    result: dict[str, list[str]] = {}
    mcu_ref = mcu['ref'] if mcu else None

    for comp in components:
        ref = comp.get('ref', '')
        if ref == mcu_ref:
            continue

        lib_id = comp.get('lib_id', '')
        cat = get_component_category(lib_id)

        # Skip basic passive components in peripheral list
        if cat == CATEGORY_PASSIVE and _is_basic_passive(comp):
            continue

        desc = get_component_description(lib_id)
        value = comp.get('value', '')
        if value and value != lib_id.split(':')[-1]:
            desc = f"{value} {desc}" if cat != CATEGORY_PASSIVE else f"{desc} ({value})"

        result.setdefault(cat, []).append(desc)

    return result


def _peripherals_to_text(peripherals: dict[str, list[str]]) -> str:
    """Convert peripherals dict to readable text."""
    parts = []

    # Priority ordering
    priority_order = [
        CATEGORY_SENSOR, CATEGORY_DISPLAY, CATEGORY_MOTOR,
        CATEGORY_COMMUNICATION, CATEGORY_LOGIC, CATEGORY_MEMORY,
        CATEGORY_AUDIO, CATEGORY_RELAY, CATEGORY_SWITCH,
        CATEGORY_POWER, CATEGORY_ACTIVE, CATEGORY_CONNECTOR,
    ]

    for cat in priority_order:
        items = peripherals.get(cat, [])
        if items:
            # Deduplicate and count
            item_counts = {}
            for item in items:
                item_counts[item] = item_counts.get(item, 0) + 1

            for item, count in item_counts.items():
                if count > 1:
                    parts.append(f"{count} {item}s")
                else:
                    parts.append(item)

    if not parts:
        return ""

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ', '.join(parts[:-1]) + f', and {parts[-1]}'


def _components_to_text(components: list[dict]) -> str:
    """Convert all components to readable text."""
    type_counts: dict[str, int] = {}
    for comp in components:
        lib_id = comp.get('lib_id', '')
        desc = get_component_description(lib_id)
        type_counts[desc] = type_counts.get(desc, 0) + 1

    parts = []
    for desc, count in type_counts.items():
        if count > 1:
            parts.append(f"{count} {desc}s")
        else:
            parts.append(desc)

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ', '.join(parts[:-1]) + f', and {parts[-1]}'


def _generate_fallback_description(components: list[dict]) -> str:
    """Generate simple fallback description."""
    type_counts: dict[str, int] = {}
    for comp in components:
        lib_id = comp.get('lib_id', '')
        desc = get_component_description(lib_id)
        type_counts[desc] = type_counts.get(desc, 0) + 1

    parts = []
    for desc, count in type_counts.items():
        if count > 1:
            parts.append(f"{count} {desc}s")
        else:
            parts.append(desc)

    return "Circuit with " + ', '.join(parts)


# ============================================================================
# Helper Functions
# ============================================================================

def _is_led(comp: dict) -> bool:
    lib_id = comp.get('lib_id', '').lower()
    return 'led' in lib_id

def _is_resistor(comp: dict) -> bool:
    lib_id = comp.get('lib_id', '')
    return lib_id in ('Device:R', 'Device:R_Small')

def _is_capacitor(comp: dict) -> bool:
    lib_id = comp.get('lib_id', '')
    return lib_id in ('Device:C', 'Device:C_Small', 'Device:C_Polarized')

def _is_basic_passive(comp: dict) -> bool:
    """Check if component is a basic passive (R, C, L) that shouldn't be listed as peripheral."""
    lib_id = comp.get('lib_id', '')
    basic = {'Device:R', 'Device:R_Small', 'Device:C', 'Device:C_Small',
             'Device:C_Polarized', 'Device:L'}
    return lib_id in basic
