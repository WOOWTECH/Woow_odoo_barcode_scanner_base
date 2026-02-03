# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BarcodeScannerSettings(models.AbstractModel):
    """Abstract model to provide barcode scanner settings to frontend."""
    _name = 'barcode.scanner.settings'
    _description = 'Barcode Scanner Settings Provider'

    @api.model
    def get_scanner_settings(self):
        """Get barcode scanner settings for frontend use.

        This method provides a secure way to access scanner settings
        without directly querying ir.config_parameter from JavaScript.

        Returns:
            dict with scanner settings
        """
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'enable_sound': ICP.get_param('barcode_scanner.enable_sound', 'True') != 'False',
            'scan_mode': ICP.get_param('barcode_scanner.scan_mode', 'all'),
            'auto_increment': ICP.get_param('barcode_scanner.auto_increment', 'True') != 'False',
            'camera_preference': ICP.get_param('barcode_scanner.camera_preference', 'back'),
            'scan_delay_ms': int(ICP.get_param('barcode_scanner.scan_delay', '500') or 500),
            'enable_gs1_parsing': ICP.get_param('barcode_scanner.enable_gs1', 'True') != 'False',
            'default_type': ICP.get_param('barcode_scanner.default_type', 'ean13'),
            'show_stock_info': ICP.get_param('barcode_scanner.show_stock_info', 'True') != 'False',
        }


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    barcode_scan_mode = fields.Selection(
        selection=[
            ('all', 'All (Barcodes and QR Codes)'),
            ('barcode_only', 'Barcodes Only'),
            ('qr_only', 'QR Codes Only'),
        ],
        string='Scan Mode',
        default='all',
        config_parameter='barcode_scanner.scan_mode',
        help="Select which types of codes the scanner should recognize"
    )

    barcode_enable_sound = fields.Boolean(
        string='Enable Sound Feedback',
        default=True,
        config_parameter='barcode_scanner.enable_sound',
        help="Play a sound when a barcode is scanned successfully or fails"
    )

    barcode_auto_increment = fields.Boolean(
        string='Auto-Increment Quantity',
        default=True,
        config_parameter='barcode_scanner.auto_increment',
        help="Automatically increment quantity when scanning the same product multiple times"
    )

    barcode_default_type = fields.Selection(
        selection=[
            ('ean13', 'EAN-13'),
            ('ean8', 'EAN-8'),
            ('upca', 'UPC-A'),
            ('code128', 'Code 128'),
            ('qr', 'QR Code'),
            ('internal', 'Internal Reference'),
        ],
        string='Default Barcode Type',
        default='ean13',
        config_parameter='barcode_scanner.default_type',
        help="Default barcode type when creating new barcodes"
    )

    barcode_show_stock_info = fields.Boolean(
        string='Show Stock Info on Scan',
        default=True,
        config_parameter='barcode_scanner.show_stock_info',
        help="Display on-hand quantity when scanning a product"
    )

    barcode_camera_preference = fields.Selection(
        selection=[
            ('back', 'Back Camera (Recommended)'),
            ('front', 'Front Camera'),
            ('ask', 'Ask Every Time'),
        ],
        string='Camera Preference',
        default='back',
        config_parameter='barcode_scanner.camera_preference',
        help="Which camera to use for scanning on mobile devices"
    )

    barcode_scan_delay_ms = fields.Integer(
        string='Scan Delay (ms)',
        default=500,
        config_parameter='barcode_scanner.scan_delay',
        help="Minimum delay between consecutive scans to prevent duplicates (milliseconds)"
    )

    barcode_enable_gs1_parsing = fields.Boolean(
        string='Enable GS1-128 Parsing',
        default=True,
        config_parameter='barcode_scanner.enable_gs1',
        help="Automatically parse GS1-128 barcodes to extract lot, serial, expiry, etc."
    )
