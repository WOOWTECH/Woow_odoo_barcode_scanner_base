# -*- coding: utf-8 -*-
"""
GS1-128 Barcode Parser

Parses GS1-128 (formerly EAN-128/UCC-128) barcodes containing Application Identifiers (AIs).

Supported AIs:
- (01) GTIN - Global Trade Item Number (14 digits)
- (02) GTIN of contained items (14 digits)
- (10) Lot/Batch Number (variable, up to 20 chars)
- (11) Production Date (YYMMDD)
- (13) Packaging Date (YYMMDD)
- (15) Best Before Date (YYMMDD)
- (17) Expiry Date (YYMMDD)
- (21) Serial Number (variable, up to 20 chars)
- (30) Count of items (variable, up to 8 digits)
- (310x) Net Weight in kg (6 digits with decimal)
- (320x) Net Weight in lb (6 digits with decimal)
- (37) Quantity (variable, up to 8 digits)
- (310x-316x) Various weight/dimension measures
- (414) Location code (13 digits)
"""

from datetime import datetime
from odoo import api, models


class GS1Parser(models.AbstractModel):
    _name = 'barcode.gs1.parser'
    _description = 'GS1-128 Barcode Parser'

    # GS1 Application Identifiers definitions
    # Format: 'AI': {'length': fixed_length or None for variable, 'decimal': decimal_positions or None}
    AI_DEFINITIONS = {
        # Product identification
        '01': {'length': 14, 'type': 'gtin', 'name': 'GTIN'},
        '02': {'length': 14, 'type': 'gtin_contained', 'name': 'GTIN of contained items'},

        # Lot and Serial
        '10': {'length': None, 'max_length': 20, 'type': 'lot', 'name': 'Lot/Batch Number'},
        '21': {'length': None, 'max_length': 20, 'type': 'serial', 'name': 'Serial Number'},

        # Dates (YYMMDD format)
        '11': {'length': 6, 'type': 'date', 'name': 'Production Date'},
        '13': {'length': 6, 'type': 'date', 'name': 'Packaging Date'},
        '15': {'length': 6, 'type': 'date', 'name': 'Best Before Date'},
        '17': {'length': 6, 'type': 'date', 'name': 'Expiry Date'},

        # Quantities
        '30': {'length': None, 'max_length': 8, 'type': 'quantity', 'name': 'Item Count'},
        '37': {'length': None, 'max_length': 8, 'type': 'quantity', 'name': 'Quantity'},

        # Weights (kg) - 310x where x is decimal positions
        '3100': {'length': 6, 'type': 'weight_kg', 'decimal': 0, 'name': 'Net Weight (kg)'},
        '3101': {'length': 6, 'type': 'weight_kg', 'decimal': 1, 'name': 'Net Weight (kg)'},
        '3102': {'length': 6, 'type': 'weight_kg', 'decimal': 2, 'name': 'Net Weight (kg)'},
        '3103': {'length': 6, 'type': 'weight_kg', 'decimal': 3, 'name': 'Net Weight (kg)'},
        '3104': {'length': 6, 'type': 'weight_kg', 'decimal': 4, 'name': 'Net Weight (kg)'},
        '3105': {'length': 6, 'type': 'weight_kg', 'decimal': 5, 'name': 'Net Weight (kg)'},

        # Weights (lb) - 320x where x is decimal positions
        '3200': {'length': 6, 'type': 'weight_lb', 'decimal': 0, 'name': 'Net Weight (lb)'},
        '3201': {'length': 6, 'type': 'weight_lb', 'decimal': 1, 'name': 'Net Weight (lb)'},
        '3202': {'length': 6, 'type': 'weight_lb', 'decimal': 2, 'name': 'Net Weight (lb)'},
        '3203': {'length': 6, 'type': 'weight_lb', 'decimal': 3, 'name': 'Net Weight (lb)'},
        '3204': {'length': 6, 'type': 'weight_lb', 'decimal': 4, 'name': 'Net Weight (lb)'},
        '3205': {'length': 6, 'type': 'weight_lb', 'decimal': 5, 'name': 'Net Weight (lb)'},

        # Location
        '414': {'length': 13, 'type': 'location', 'name': 'Location Code (GLN)'},

        # Additional identifiers
        '240': {'length': None, 'max_length': 30, 'type': 'additional_id', 'name': 'Additional Product ID'},
        '241': {'length': None, 'max_length': 30, 'type': 'customer_part', 'name': 'Customer Part Number'},
        '250': {'length': None, 'max_length': 30, 'type': 'secondary_serial', 'name': 'Secondary Serial Number'},
        '251': {'length': None, 'max_length': 30, 'type': 'ref_source', 'name': 'Reference to Source Entity'},
    }

    # Group separator character (GS = ASCII 29)
    GS = '\x1d'
    # Function 1 character (FNC1 = ASCII 232 in some systems, but typically stripped)
    FNC1 = '\u00e8'

    @api.model
    def parse(self, barcode):
        """Parse a GS1-128 barcode and extract all Application Identifier data.

        Args:
            barcode: The barcode string to parse

        Returns:
            dict with parsed data:
                - gtin: Global Trade Item Number
                - lot: Lot/Batch number
                - serial: Serial number
                - expiry: Expiry date (datetime object)
                - production_date: Production date (datetime object)
                - best_before: Best before date (datetime object)
                - weight_kg: Net weight in kg (float)
                - weight_lb: Net weight in lb (float)
                - quantity: Quantity count
                - location: Location code (GLN)
                - raw_ais: Dict of all parsed AIs with their raw values
                - is_gs1: Boolean indicating if valid GS1 barcode
        """
        result = {
            'gtin': None,
            'lot': None,
            'serial': None,
            'expiry': None,
            'expiry_str': None,
            'production_date': None,
            'best_before': None,
            'weight_kg': None,
            'weight_lb': None,
            'quantity': None,
            'location': None,
            'raw_ais': {},
            'is_gs1': False,
        }

        if not barcode:
            return result

        # Clean the barcode - remove FNC1 characters and whitespace
        barcode = barcode.replace(self.FNC1, '').strip()

        # Check if this looks like a GS1 barcode
        # GS1-128 typically starts with ]C1 or ]e0 symbology identifier, or directly with AI
        if barcode.startswith(']C1'):
            barcode = barcode[3:]
        elif barcode.startswith(']e0'):
            barcode = barcode[3:]

        # Parse Application Identifiers
        pos = 0
        while pos < len(barcode):
            ai, value, new_pos = self._extract_ai(barcode, pos)
            if ai is None:
                # Not a recognized AI, might not be GS1
                break

            result['raw_ais'][ai] = value
            result['is_gs1'] = True

            # Map parsed values to result fields
            ai_def = self.AI_DEFINITIONS.get(ai)
            if ai_def:
                ai_type = ai_def.get('type')

                if ai_type == 'gtin':
                    result['gtin'] = value
                elif ai_type == 'lot':
                    result['lot'] = value
                elif ai_type == 'serial':
                    result['serial'] = value
                elif ai_type == 'date':
                    date_obj = self._parse_date(value)
                    if ai == '17':
                        result['expiry'] = date_obj
                        result['expiry_str'] = value
                    elif ai == '11':
                        result['production_date'] = date_obj
                    elif ai == '15':
                        result['best_before'] = date_obj
                elif ai_type == 'weight_kg':
                    decimal = ai_def.get('decimal', 0)
                    result['weight_kg'] = self._parse_decimal(value, decimal)
                elif ai_type == 'weight_lb':
                    decimal = ai_def.get('decimal', 0)
                    result['weight_lb'] = self._parse_decimal(value, decimal)
                elif ai_type == 'quantity':
                    try:
                        result['quantity'] = int(value)
                    except ValueError:
                        pass
                elif ai_type == 'location':
                    result['location'] = value

            pos = new_pos

        return result

    def _extract_ai(self, barcode, start_pos):
        """Extract an Application Identifier and its value from the barcode.

        Args:
            barcode: The full barcode string
            start_pos: Position to start parsing from

        Returns:
            tuple: (ai, value, new_position) or (None, None, start_pos) if no AI found
        """
        remaining = barcode[start_pos:]

        # Try to match AI patterns (2, 3, or 4 digit AIs)
        for ai_length in [4, 3, 2]:
            if len(remaining) < ai_length:
                continue

            potential_ai = remaining[:ai_length]
            ai_def = self.AI_DEFINITIONS.get(potential_ai)

            if ai_def:
                value_start = ai_length
                fixed_length = ai_def.get('length')

                if fixed_length:
                    # Fixed length AI - validate remaining length
                    if len(remaining) < value_start + fixed_length:
                        # Not enough characters for fixed-length AI
                        return (None, None, start_pos)
                    value = remaining[value_start:value_start + fixed_length]
                    new_pos = start_pos + ai_length + fixed_length
                else:
                    # Variable length AI - read until GS or end
                    max_length = ai_def.get('max_length', 30)
                    value_end = remaining.find(self.GS, value_start)
                    if value_end == -1:
                        value_end = min(value_start + max_length, len(remaining))
                    else:
                        value_end = min(value_end, value_start + max_length)

                    value = remaining[value_start:value_end]
                    new_pos = start_pos + value_end
                    # Skip the GS if present
                    if new_pos < len(barcode) and barcode[new_pos] == self.GS:
                        new_pos += 1

                return (potential_ai, value, new_pos)

        return (None, None, start_pos)

    @staticmethod
    def _parse_date(date_str):
        """Parse a GS1 date string (YYMMDD) to a datetime object.

        Args:
            date_str: Date string in YYMMDD format

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str or len(date_str) != 6:
            return None

        try:
            year = int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])

            # Handle century: 00-49 = 2000-2049, 50-99 = 1950-1999
            if year < 50:
                year += 2000
            else:
                year += 1900

            # Day 00 means last day of month
            if day == 0:
                if month == 12:
                    day = 31
                else:
                    # Get last day of month
                    import calendar
                    day = calendar.monthrange(year, month)[1]

            return datetime(year, month, day)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_decimal(value_str, decimal_places):
        """Parse a numeric string with implicit decimal places.

        Args:
            value_str: Numeric string (e.g., "001234")
            decimal_places: Number of decimal places (e.g., 2 means "001234" -> 12.34)

        Returns:
            float or None if parsing fails
        """
        if not value_str:
            return None

        try:
            value = int(value_str)
            if decimal_places > 0:
                return value / (10 ** decimal_places)
            return float(value)
        except (ValueError, TypeError):
            return None

    @api.model
    def is_gs1_barcode(self, barcode):
        """Check if a barcode appears to be a GS1-128 barcode.

        Args:
            barcode: The barcode string to check

        Returns:
            bool: True if barcode appears to be GS1-128
        """
        result = self.parse(barcode)
        return result.get('is_gs1', False)

    @api.model
    def format_for_display(self, barcode):
        """Format a GS1 barcode for human-readable display.

        Args:
            barcode: The GS1 barcode string

        Returns:
            str: Human-readable formatted string
        """
        result = self.parse(barcode)
        if not result.get('is_gs1'):
            return barcode

        parts = []
        if result.get('gtin'):
            parts.append(f"GTIN: {result['gtin']}")
        if result.get('lot'):
            parts.append(f"Lot: {result['lot']}")
        if result.get('serial'):
            parts.append(f"Serial: {result['serial']}")
        if result.get('expiry'):
            parts.append(f"Expiry: {result['expiry'].strftime('%Y-%m-%d')}")
        if result.get('quantity'):
            parts.append(f"Qty: {result['quantity']}")
        if result.get('weight_kg'):
            parts.append(f"Weight: {result['weight_kg']} kg")

        return ' | '.join(parts) if parts else barcode
