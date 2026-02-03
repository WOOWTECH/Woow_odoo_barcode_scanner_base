# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductBarcode(models.Model):
    _name = 'product.barcode'
    _description = 'Product Barcode'
    _order = 'sequence, id'

    name = fields.Char(
        string='Barcode',
        required=True,
        index=True,
        help="The barcode value (EAN-13, EAN-8, UPC-A, UPC-E, Code128, QR, etc.)"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Determines the order of barcodes"
    )
    barcode_type = fields.Selection(
        selection=[
            ('ean13', 'EAN-13'),
            ('ean8', 'EAN-8'),
            ('upca', 'UPC-A'),
            ('upce', 'UPC-E'),
            ('code128', 'Code 128'),
            ('code39', 'Code 39'),
            ('qr', 'QR Code'),
            ('gs1_128', 'GS1-128'),
            ('internal', 'Internal Reference'),
        ],
        string='Barcode Type',
        default='ean13',
        required=True,
        help="Type of barcode for validation and generation purposes"
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Variant',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        related='product_id.product_tmpl_id',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Leave empty to make this barcode available for all companies"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    notes = fields.Text(
        string='Notes',
        help="Additional notes about this barcode"
    )

    _sql_constraints = [
        ('barcode_company_unique', 'UNIQUE(name, company_id)',
         'A barcode must be unique per company!'),
    ]

    @api.constrains('name', 'company_id')
    def _check_barcode_unique_global(self):
        """Ensure global barcodes (company_id=False) are unique.

        PostgreSQL UNIQUE constraint treats NULL as distinct values,
        so we need a Python constraint to enforce uniqueness for global barcodes.
        """
        for record in self:
            if record.company_id:
                continue  # Company-specific barcodes are handled by SQL constraint

            # Check for duplicate global barcodes
            duplicates = self.search([
                ('name', '=', record.name),
                ('company_id', '=', False),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicates:
                raise ValidationError(
                    _("A global barcode '%s' already exists!") % record.name
                )

    @api.constrains('name', 'barcode_type')
    def _check_barcode_format(self):
        """Validate barcode format based on type."""
        for record in self:
            if not record.name:
                continue

            barcode = record.name.strip()

            if record.barcode_type == 'ean13':
                if not barcode.isdigit() or len(barcode) != 13:
                    raise ValidationError(
                        _("EAN-13 barcode must be exactly 13 digits: %s") % barcode
                    )
                if not self._validate_ean_checksum(barcode):
                    raise ValidationError(
                        _("Invalid EAN-13 checksum for barcode: %s") % barcode
                    )

            elif record.barcode_type == 'ean8':
                if not barcode.isdigit() or len(barcode) != 8:
                    raise ValidationError(
                        _("EAN-8 barcode must be exactly 8 digits: %s") % barcode
                    )
                if not self._validate_ean_checksum(barcode):
                    raise ValidationError(
                        _("Invalid EAN-8 checksum for barcode: %s") % barcode
                    )

            elif record.barcode_type == 'upca':
                if not barcode.isdigit() or len(barcode) != 12:
                    raise ValidationError(
                        _("UPC-A barcode must be exactly 12 digits: %s") % barcode
                    )
                if not self._validate_upc_checksum(barcode):
                    raise ValidationError(
                        _("Invalid UPC-A checksum for barcode: %s") % barcode
                    )

            elif record.barcode_type == 'upce':
                if not barcode.isdigit() or len(barcode) != 8:
                    raise ValidationError(
                        _("UPC-E barcode must be exactly 8 digits: %s") % barcode
                    )

    @staticmethod
    def _validate_ean_checksum(barcode):
        """Validate EAN-8 or EAN-13 checksum."""
        if not barcode.isdigit():
            return False

        digits = [int(d) for d in barcode]
        # Calculate checksum (odd positions * 1, even positions * 3)
        # For EAN-13: positions 1,3,5,7,9,11 * 1 and 2,4,6,8,10,12 * 3
        checksum = 0
        for i, digit in enumerate(digits[:-1]):
            if i % 2 == 0:
                checksum += digit
            else:
                checksum += digit * 3
        calculated_check = (10 - (checksum % 10)) % 10
        return calculated_check == digits[-1]

    @staticmethod
    def _validate_upc_checksum(barcode):
        """Validate UPC-A checksum."""
        if not barcode.isdigit() or len(barcode) != 12:
            return False

        digits = [int(d) for d in barcode]
        # UPC-A: odd positions * 3, even positions * 1
        checksum = 0
        for i, digit in enumerate(digits[:-1]):
            if i % 2 == 0:
                checksum += digit * 3
            else:
                checksum += digit
        calculated_check = (10 - (checksum % 10)) % 10
        return calculated_check == digits[-1]

    @api.model
    def search_by_barcode(self, barcode, company_id=None):
        """Search for a product barcode record by barcode value.

        Args:
            barcode: The barcode string to search for
            company_id: Optional company ID to filter by

        Returns:
            product.barcode recordset (may be empty)
        """
        domain = [('name', '=', barcode), ('active', '=', True)]
        if company_id:
            domain.append(('company_id', 'in', [company_id, False]))
        else:
            domain.append(('company_id', '=', False))
        return self.search(domain, limit=1)

    def _compute_display_name(self):
        """Compute display name with barcode type."""
        for record in self:
            record.display_name = f"{record.name} ({record.barcode_type})"
