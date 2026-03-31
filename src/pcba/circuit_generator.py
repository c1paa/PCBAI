"""
Circuit connection generator.

Generates electrical connections between components based on
configuration type (series, parallel, custom).
"""

from typing import Any


class ConnectionGenerator:
    """Generate connections between components based on circuit topology."""

    def generate_connections(
        self,
        components: list[dict],
        configuration: str = 'parallel',
        mcu_pin: str | None = None,
    ) -> list[dict[str, str]]:
        """Generate connections based on configuration.

        Args:
            components: List of expanded component dicts (each with ref, type, value)
            configuration: "series", "parallel", or "custom"
            mcu_pin: Optional MCU pin to connect to

        Returns:
            List of connection dicts with from/to/net keys
        """
        if configuration == 'series':
            return self._series(components, mcu_pin)
        elif configuration == 'parallel':
            return self._parallel(components, mcu_pin)
        else:
            return self._custom(components, mcu_pin)

    def _series(
        self,
        components: list[dict],
        mcu_pin: str | None,
    ) -> list[dict[str, str]]:
        """Series: source → R1 → LED1 → LED2 → ... → GND.

        Current flows through all LEDs one after another.
        """
        connections: list[dict[str, str]] = []
        resistors = [c for c in components if c.get('type') == 'resistor']
        leds = [c for c in components if c.get('type') == 'led']
        others = [c for c in components if c.get('type') not in ('resistor', 'led')]

        if not leds:
            return self._custom(components, mcu_pin)

        # Build chain: [source] → R1 → LED1 → LED2 → ... → GND
        chain: list[tuple[str, str, str]] = []  # (ref, pin_from, pin_to)

        # Source connection
        source = f"Arduino:Pin{mcu_pin}" if mcu_pin else "+5V"

        # First element: resistor if present
        if resistors:
            r = resistors[0]
            connections.append({
                'from': source,
                'to': f"{r['ref']}:1",
                'net': f"Net_{source.replace(':', '_')}",
            })
            prev_ref = r['ref']
            prev_pin = '2'
        else:
            prev_ref = None
            prev_pin = None

        # Chain LEDs in series
        for i, led in enumerate(leds):
            net_name = f"Net_{'R1' if i == 0 and resistors else f'LED{i}'}_LED{i + 1}"

            if prev_ref:
                connections.append({
                    'from': f"{prev_ref}:{prev_pin}",
                    'to': f"{led['ref']}:2",  # Anode
                    'net': net_name,
                })
            else:
                connections.append({
                    'from': source,
                    'to': f"{led['ref']}:2",  # Anode
                    'net': net_name,
                })

            prev_ref = led['ref']
            prev_pin = '1'  # Cathode

        # Last LED to GND
        if prev_ref:
            connections.append({
                'from': f"{prev_ref}:{prev_pin}",
                'to': 'GND',
                'net': 'GND',
            })

        # Handle extra resistors (pull-ups, etc.)
        for r in resistors[1:]:
            connections.append({
                'from': '+5V',
                'to': f"{r['ref']}:1",
                'net': f"Net_{r['ref']}_pullup",
            })

        # Handle other components
        for comp in others:
            self._connect_generic(comp, connections)

        return connections

    def _parallel(
        self,
        components: list[dict],
        mcu_pin: str | None,
    ) -> list[dict[str, str]]:
        """Parallel: source → R1 → node → (LED1 || LED2 || ...) → GND.

        Each LED gets its own path from the common node to GND.
        In proper parallel LED circuit, each LED needs its own resistor.
        If only one resistor is provided, it's shared (simplified).
        """
        connections: list[dict[str, str]] = []
        resistors = [c for c in components if c.get('type') == 'resistor']
        leds = [c for c in components if c.get('type') == 'led']
        others = [c for c in components if c.get('type') not in ('resistor', 'led')]

        if not leds:
            return self._custom(components, mcu_pin)

        source = f"Arduino:Pin{mcu_pin}" if mcu_pin else "+5V"

        if len(resistors) >= len(leds):
            # Each LED has its own resistor: source → Ri → LEDi → GND
            for i, led in enumerate(leds):
                r = resistors[i]
                connections.append({
                    'from': source,
                    'to': f"{r['ref']}:1",
                    'net': f"Net_source_{r['ref']}",
                })
                connections.append({
                    'from': f"{r['ref']}:2",
                    'to': f"{led['ref']}:2",  # Anode
                    'net': f"Net_{r['ref']}_{led['ref']}",
                })
                connections.append({
                    'from': f"{led['ref']}:1",  # Cathode
                    'to': 'GND',
                    'net': 'GND',
                })
        elif resistors:
            # Shared resistor: source → R1 → common_node → (LED1 || LED2) → GND
            r = resistors[0]
            connections.append({
                'from': source,
                'to': f"{r['ref']}:1",
                'net': f"Net_source_{r['ref']}",
            })

            common_net = f"Net_{r['ref']}_common"
            for led in leds:
                connections.append({
                    'from': f"{r['ref']}:2",
                    'to': f"{led['ref']}:2",  # Anode
                    'net': common_net,
                })
                connections.append({
                    'from': f"{led['ref']}:1",  # Cathode
                    'to': 'GND',
                    'net': 'GND',
                })
        else:
            # No resistor: source → LEDs → GND
            for led in leds:
                connections.append({
                    'from': source,
                    'to': f"{led['ref']}:2",
                    'net': 'Net_source_leds',
                })
                connections.append({
                    'from': f"{led['ref']}:1",
                    'to': 'GND',
                    'net': 'GND',
                })

        # Extra resistors not used for LEDs
        for r in resistors[max(1, len(leds)):]:
            connections.append({
                'from': '+5V',
                'to': f"{r['ref']}:1",
                'net': f"Net_{r['ref']}_pullup",
            })

        for comp in others:
            self._connect_generic(comp, connections)

        return connections

    def _custom(
        self,
        components: list[dict],
        mcu_pin: str | None,
    ) -> list[dict[str, str]]:
        """Custom: connect each component to power/ground generically."""
        connections: list[dict[str, str]] = []
        for comp in components:
            self._connect_generic(comp, connections)
        return connections

    def _connect_generic(
        self,
        comp: dict,
        connections: list[dict[str, str]],
    ) -> None:
        """Add generic power/ground connections for a component."""
        ref = comp.get('ref', 'U1')
        comp_type = comp.get('type', '')

        if comp_type in ('mcu', 'sensor', 'ic'):
            connections.append({
                'from': '+5V',
                'to': f"{ref}:VCC",
                'net': 'VCC',
            })
            connections.append({
                'from': f"{ref}:GND",
                'to': 'GND',
                'net': 'GND',
            })
        elif comp_type == 'capacitor':
            # Decoupling cap between VCC and GND
            connections.append({
                'from': '+5V',
                'to': f"{ref}:1",
                'net': 'VCC',
            })
            connections.append({
                'from': f"{ref}:2",
                'to': 'GND',
                'net': 'GND',
            })
