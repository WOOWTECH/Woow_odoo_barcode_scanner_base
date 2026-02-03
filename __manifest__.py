# -*- coding: utf-8 -*-
{
    'name': 'Barcode Scanner Base',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Barcode',
    'summary': 'Core barcode and QR code scanning functionality for Odoo 18',
    'description': """
Barcode Scanner Base Module
===========================

This module provides core barcode and QR code scanning functionality:

* Multi-barcode support for products (EAN-13, EAN-8, UPC-A, UPC-E, Code128, QR)
* Camera-based barcode/QR code scanning using html5-qrcode library
* GS1-128 barcode parsing (GTIN, Lot, Serial, Expiry, Weight, Quantity)
* OWL-based scanner dialog component
* Configurable scan modes and feedback settings

This is the base module required by all barcode scanner integration modules.
    """,
    'author': 'Woow Tech',
    'website': 'https://github.com/woowtech',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'stock',
        'barcodes',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # OWL components (html5-qrcode library is loaded dynamically when scanner opens)
            'barcode_scanner_base/static/src/core/barcode_scanner_service.js',
            'barcode_scanner_base/static/src/core/barcode_scanner_dialog.js',
            'barcode_scanner_base/static/src/core/barcode_scanner_dialog.xml',
            'barcode_scanner_base/static/src/core/barcode_scanner_dialog.scss',
        ],
    },
    'external_dependencies': {
        'python': ['barcode', 'qrcode'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
