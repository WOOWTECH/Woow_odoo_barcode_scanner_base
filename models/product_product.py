# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_ids = fields.One2many(
        comodel_name='product.barcode',
        inverse_name='product_id',
        string='Additional Barcodes',
        help="Additional barcodes for this product variant"
    )
    barcode_count = fields.Integer(
        string='Barcode Count',
        compute='_compute_barcode_count',
    )

    @api.depends('barcode_ids')
    def _compute_barcode_count(self):
        for product in self:
            product.barcode_count = len(product.barcode_ids)

    @api.model
    def find_by_barcode(self, barcode, company_id=None):
        """Find a product by barcode, QR code, or internal reference.

        Search order:
        1. Primary barcode field on product.product
        2. Additional barcodes in product.barcode
        3. Internal reference (default_code)

        Args:
            barcode: The barcode/QR/reference string to search for
            company_id: Optional company ID to filter by

        Returns:
            product.product recordset (single record or empty)
        """
        if not barcode:
            return self.browse()

        barcode = barcode.strip()
        company_id = company_id or self.env.company.id

        # 1. Search primary barcode field
        product = self.search([
            ('barcode', '=', barcode),
            '|', ('company_id', '=', False), ('company_id', '=', company_id)
        ], limit=1)
        if product:
            return product

        # 2. Search additional barcodes
        ProductBarcode = self.env['product.barcode']
        barcode_rec = ProductBarcode.search([
            ('name', '=', barcode),
            ('active', '=', True),
            '|', ('company_id', '=', False), ('company_id', '=', company_id)
        ], limit=1)
        if barcode_rec:
            return barcode_rec.product_id

        # 3. Search internal reference
        product = self.search([
            ('default_code', '=', barcode),
            '|', ('company_id', '=', False), ('company_id', '=', company_id)
        ], limit=1)
        if product:
            return product

        return self.browse()

    @api.model
    def find_by_barcode_with_info(self, barcode, company_id=None):
        """Find a product by barcode and return additional information.

        Args:
            barcode: The barcode string to search for
            company_id: Optional company ID to filter by

        Returns:
            dict with keys:
                - product: product.product record or False
                - barcode_type: type of barcode that matched
                - gs1_data: parsed GS1 data if applicable
                - error: error message if not found
        """
        result = {
            'product': False,
            'barcode_type': False,
            'gs1_data': {},
            'error': False,
        }

        if not barcode:
            result['error'] = _("No barcode provided")
            return result

        barcode = barcode.strip()

        # Check if this is a GS1-128 barcode
        GS1Parser = self.env['barcode.gs1.parser']
        gs1_data = GS1Parser.parse(barcode)

        if gs1_data.get('gtin'):
            # This is a GS1 barcode, search by GTIN
            result['gs1_data'] = gs1_data
            result['barcode_type'] = 'gs1_128'
            gtin = gs1_data['gtin']

            # GTIN can be 8, 12, 13, or 14 digits
            # Try to find product by GTIN
            product = self.find_by_barcode(gtin, company_id)
            if product:
                result['product'] = product
                return result

            # Try without leading zeros (GTIN-14 to GTIN-13 conversion)
            if len(gtin) == 14 and gtin.startswith('0'):
                product = self.find_by_barcode(gtin[1:], company_id)
                if product:
                    result['product'] = product
                    return result

        # Standard barcode search
        product = self.find_by_barcode(barcode, company_id)
        if product:
            result['product'] = product
            # Determine barcode type
            if product.barcode == barcode:
                result['barcode_type'] = 'primary'
            elif product.default_code == barcode:
                result['barcode_type'] = 'internal'
            else:
                # Find the matching additional barcode
                barcode_rec = self.env['product.barcode'].search([
                    ('name', '=', barcode),
                    ('product_id', '=', product.id),
                ], limit=1)
                if barcode_rec:
                    result['barcode_type'] = barcode_rec.barcode_type
            return result

        result['error'] = _("Product not found for barcode: %s") % barcode
        return result


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    barcode_ids = fields.One2many(
        comodel_name='product.barcode',
        inverse_name='product_tmpl_id',
        string='Additional Barcodes',
        help="Additional barcodes for product variants"
    )
    barcode_count = fields.Integer(
        string='Barcode Count',
        compute='_compute_barcode_count',
    )

    @api.depends('barcode_ids')
    def _compute_barcode_count(self):
        for template in self:
            template.barcode_count = len(template.barcode_ids)
