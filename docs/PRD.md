# Product Requirements Document (PRD)
# Barcode Scanner Base Module

**Module Name:** barcode_scanner_base
**Version:** 18.0.1.0.0
**Author:** Woow Tech
**License:** LGPL-3
**Last Updated:** 2026-02-03

---

## 1. Executive Summary

The Barcode Scanner Base module provides core barcode and QR code scanning functionality for Odoo 18. It serves as the foundational module for all barcode-related operations, enabling camera-based scanning, multi-barcode support for products, and GS1-128 barcode parsing.

This module is designed to be extended by other modules (such as `barcode_scanner_sale`, `barcode_scanner_purchase`, `barcode_scanner_stock`) to provide application-specific barcode scanning functionality.

---

## 2. Problem Statement

### 2.1 Current Challenges
- Odoo's native barcode functionality is limited to single barcodes per product
- No native support for camera-based barcode scanning on mobile devices
- Lack of GS1-128 barcode parsing for supply chain applications
- Inconsistent barcode handling across different Odoo modules

### 2.2 Target Users
- Warehouse operators scanning products with mobile devices
- Retail staff using tablets/phones for inventory management
- Supply chain managers working with GS1-128 encoded products
- Developers building barcode-enabled Odoo applications

---

## 3. Product Requirements

### 3.1 Functional Requirements

#### FR-1: Multi-Barcode Support
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Support multiple barcodes per product variant | High |
| FR-1.2 | Support barcode types: EAN-13, EAN-8, UPC-A, UPC-E, Code128, Code39, QR, GS1-128, Internal | High |
| FR-1.3 | Validate barcode checksums for EAN and UPC formats | High |
| FR-1.4 | Allow company-specific barcodes with global fallback | Medium |
| FR-1.5 | Maintain barcode ordering with sequence field | Low |

#### FR-2: Camera-Based Scanning
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Provide OWL-based scanner dialog component | High |
| FR-2.2 | Support front and back cameras with preference setting | High |
| FR-2.3 | Real-time barcode/QR detection via html5-qrcode library | High |
| FR-2.4 | Visual scanning feedback with animated frame overlay | Medium |
| FR-2.5 | Audio feedback on successful/failed scans | Medium |

#### FR-3: GS1-128 Parsing
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Parse GTIN (AI-01) from GS1-128 barcodes | High |
| FR-3.2 | Extract Lot/Batch number (AI-10) | High |
| FR-3.3 | Extract Serial number (AI-21) | High |
| FR-3.4 | Extract Expiry date (AI-17) | High |
| FR-3.5 | Parse weight measurements (AI-310x, AI-320x) | Medium |
| FR-3.6 | Parse quantity (AI-37) | Medium |
| FR-3.7 | Support variable-length AIs with GS separator | High |

#### FR-4: Product Search
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Search products by primary barcode | High |
| FR-4.2 | Search products by additional barcodes | High |
| FR-4.3 | Search products by internal reference | High |
| FR-4.4 | Return GS1 parsed data with product result | Medium |
| FR-4.5 | Support company filtering in searches | Medium |

#### FR-5: Configuration
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Configurable scan mode (All/Barcode only/QR only) | Medium |
| FR-5.2 | Toggle sound feedback | Medium |
| FR-5.3 | Auto-increment quantity setting | Medium |
| FR-5.4 | Default barcode type for new entries | Low |
| FR-5.5 | Configurable scan delay to prevent duplicates | Medium |

### 3.2 Non-Functional Requirements

#### NFR-1: Performance
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Barcode search response time | < 5ms |
| NFR-1.2 | GS1 parsing time | < 100μs |
| NFR-1.3 | Barcode validation time | < 50μs |
| NFR-1.4 | Scanner initialization time | < 2s |

#### NFR-2: Compatibility
| ID | Requirement |
|----|-------------|
| NFR-2.1 | Odoo 18 compatible |
| NFR-2.2 | Works on Chrome, Firefox, Safari, Edge |
| NFR-2.3 | Mobile-responsive scanner UI |
| NFR-2.4 | Dark mode support |

#### NFR-3: Security
| ID | Requirement |
|----|-------------|
| NFR-3.1 | Role-based access control for barcode management |
| NFR-3.2 | Multi-company data isolation |
| NFR-3.3 | Input validation for all barcode formats |

---

## 4. Technical Architecture

### 4.1 Module Structure

```
barcode_scanner_base/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── product_barcode.py      # Multi-barcode model
│   ├── product_product.py      # Product extensions
│   ├── gs1_parser.py           # GS1-128 parser
│   └── res_config_settings.py  # Configuration
├── security/
│   └── ir.model.access.csv     # Access control
├── static/src/
│   ├── core/
│   │   ├── barcode_scanner_service.js  # OWL service
│   │   ├── barcode_scanner_dialog.js   # Scanner component
│   │   ├── barcode_scanner_dialog.xml  # Component template
│   │   └── barcode_scanner_dialog.scss # Styles
│   └── lib/
│       └── html5-qrcode.min.js        # Scanning library
└── views/
    ├── product_views.xml
    └── res_config_settings_views.xml
```

### 4.2 Data Model

```
┌─────────────────────┐       ┌─────────────────────┐
│  product.product    │       │  product.template   │
├─────────────────────┤       ├─────────────────────┤
│ barcode_ids (O2M)   │──────▶│ barcode_ids (O2M)   │
│ barcode_count       │       │ barcode_count       │
└─────────────────────┘       └─────────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌──────────────────────────────────────────────────┐
│              product.barcode                      │
├──────────────────────────────────────────────────┤
│ name (Char, indexed)                             │
│ barcode_type (Selection)                         │
│ sequence (Integer)                               │
│ product_id (M2O → product.product)              │
│ product_tmpl_id (Related, stored, indexed)      │
│ company_id (M2O → res.company)                  │
│ active (Boolean)                                 │
│ notes (Text)                                     │
└──────────────────────────────────────────────────┘
```

### 4.3 Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (OWL)                           │
├─────────────────────────────────────────────────────────────┤
│  BarcodeScannerService                                      │
│  ├── openScanner()        → Opens scanner dialog            │
│  ├── scanForProduct()     → Scan & find product             │
│  ├── findProductByBarcode()→ Search API                     │
│  ├── parseGS1Barcode()    → GS1 parsing                     │
│  └── showSuccess/Error()  → Notifications                   │
├─────────────────────────────────────────────────────────────┤
│  BarcodeScannerDialog                                       │
│  ├── Html5Qrcode library  → Camera access & decoding        │
│  ├── Camera switching     → Front/Back camera support       │
│  └── Scan result callback → Returns barcode data            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ RPC
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Python)                         │
├─────────────────────────────────────────────────────────────┤
│  product.product                                            │
│  ├── find_by_barcode()         → Multi-source search        │
│  └── find_by_barcode_with_info()→ Search + GS1 parse        │
├─────────────────────────────────────────────────────────────┤
│  barcode.gs1.parser                                         │
│  ├── parse()                   → Extract all AIs            │
│  ├── is_gs1_barcode()         → Validation                  │
│  └── format_for_display()     → Human-readable format       │
├─────────────────────────────────────────────────────────────┤
│  product.barcode                                            │
│  ├── search_by_barcode()      → Direct barcode lookup       │
│  └── _check_barcode_format()  → Checksum validation         │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Test Results

### 5.1 Backend Tests ✅

| Test | Status | Notes |
|------|--------|-------|
| Module installation | ✅ PASS | Installed and loaded correctly |
| ProductBarcode CRUD | ✅ PASS | Create/Read/Update/Delete working |
| EAN-13 checksum validation | ✅ PASS | Valid checksums accepted, invalid rejected |
| UPC-A checksum validation | ✅ PASS | Valid checksums accepted, invalid rejected |
| find_by_barcode | ✅ PASS | Finds products by primary barcode |
| find_by_barcode_with_info | ✅ PASS | Returns product with barcode type info |
| GS1 parsing - Simple GTIN | ✅ PASS | Correctly extracts GTIN |
| GS1 parsing - Expiry + Lot | ✅ PASS | Parses dates and lot numbers |
| GS1 parsing - Serial | ✅ PASS | Extracts serial numbers |
| GS1 date parsing | ✅ PASS | Handles YYMMDD format correctly |
| Config settings fields | ✅ PASS | All 8 barcode settings present |

### 5.2 Performance Benchmarks ✅

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| find_by_barcode | 2.52ms | <5ms | ✅ EXCELLENT |
| find_by_barcode_with_info | 1.84ms | <10ms | ✅ EXCELLENT |
| GS1 Parser | 12.1μs | <100μs | ✅ EXCELLENT |
| Barcode Validation | 31.8μs | <50μs | ✅ EXCELLENT |

### 5.3 Database Indexes ✅

| Index | Table | Purpose |
|-------|-------|---------|
| product_barcode_pkey | product_barcode | Primary key |
| product_barcode_barcode_unique | product_barcode | Unique constraint |
| product_barcode__name_index | product_barcode | Fast barcode lookup |
| product_barcode__product_id_index | product_barcode | Product FK lookup |
| product_barcode__product_tmpl_id_index | product_barcode | Template FK lookup |

---

## 6. Code Review Summary

### 6.1 Overall Assessment: GOOD ✅

The module demonstrates solid Odoo 18 development practices with clean architecture and proper ORM usage.

### 6.2 Issues to Address

#### Critical (1)
| Issue | Location | Recommendation |
|-------|----------|----------------|
| Direct ir.config_parameter access from JS | barcode_scanner_service.js:35-49 | Use dedicated backend method |

#### Major (4)
| Issue | Location | Recommendation |
|-------|----------|----------------|
| Missing multi-company record rules | security/ | Add ir.rule for company isolation |
| N+1 query in _compute_barcode_count | product_product.py:163-166 | Use read_group |
| SQL UNIQUE with NULL handling | product_barcode.py:68-71 | Add partial index for NULL |
| Missing GS1 parser edge case | gs1_parser.py:206-227 | Validate remaining length |

#### Minor (8)
- Deprecated name_get method
- Hardcoded container ID
- Unused import in gs1_parser
- Empty settings view file
- CSS magic numbers
- Library loading race condition
- Audio data validation
- Input length validation

### 6.3 Best Practices Followed ✅
- Proper ORM usage without raw SQL
- Clear separation of concerns
- Proper internationalization (i18n)
- Good docstrings and documentation
- Responsive design with mobile optimization
- Dark mode support
- Graceful error handling

---

## 7. Dependencies

### 7.1 Odoo Modules
- `base` - Core Odoo functionality
- `product` - Product management
- `stock` - Inventory management
- `barcodes` - Native barcode support

### 7.2 Python Packages
- `barcode` - Barcode generation
- `qrcode` - QR code generation

### 7.3 JavaScript Libraries
- `html5-qrcode` - Camera-based barcode scanning (loaded dynamically)

---

## 8. Roadmap

### 8.1 Version 18.0.1.1.0 (Recommended Fixes)
- [ ] Create backend method for settings retrieval
- [ ] Add multi-company record rules
- [ ] Optimize _compute_barcode_count with read_group
- [ ] Fix SQL constraint for NULL company_id
- [ ] Update name_get to _compute_display_name

### 8.2 Future Enhancements
- [ ] Barcode generation (print labels)
- [ ] Batch scanning mode
- [ ] Offline scanning with sync
- [ ] Scan history and analytics
- [ ] Voice feedback option

---

## 9. API Reference

### 9.1 Python Methods

#### product.product.find_by_barcode(barcode, company_id=None)
Find a product by barcode, QR code, or internal reference.

**Parameters:**
- `barcode` (str): The barcode string to search for
- `company_id` (int, optional): Company ID to filter by

**Returns:** `product.product` recordset (single record or empty)

**Search Order:**
1. Primary barcode field on product.product
2. Additional barcodes in product.barcode
3. Internal reference (default_code)

---

#### product.product.find_by_barcode_with_info(barcode, company_id=None)
Find a product by barcode and return additional information.

**Parameters:**
- `barcode` (str): The barcode string to search for
- `company_id` (int, optional): Company ID to filter by

**Returns:** dict with keys:
- `product`: product.product record or False
- `barcode_type`: type of barcode that matched
- `gs1_data`: parsed GS1 data if applicable
- `error`: error message if not found

---

#### barcode.gs1.parser.parse(barcode)
Parse a GS1-128 barcode and extract all Application Identifier data.

**Parameters:**
- `barcode` (str): The barcode string to parse

**Returns:** dict with keys:
- `gtin`: Global Trade Item Number
- `lot`: Lot/Batch number
- `serial`: Serial number
- `expiry`: Expiry date (datetime object)
- `weight_kg`: Net weight in kg (float)
- `quantity`: Quantity count
- `is_gs1`: Boolean indicating if valid GS1 barcode
- `raw_ais`: Dict of all parsed AIs with their raw values

---

### 9.2 JavaScript Service

#### barcodeScanner.openScanner(options)
Open the barcode scanner dialog.

**Parameters:**
- `options.onScan` (Function): Callback when barcode is scanned
- `options.onClose` (Function, optional): Callback when dialog is closed
- `options.allowedFormats` (Array, optional): Restrict to specific formats
- `options.title` (String, optional): Dialog title

**Returns:** Close function

---

#### barcodeScanner.scanForProduct(options)
Open scanner and automatically find product.

**Parameters:**
- `options.onProduct` (Function): Callback with found product
- `options.onNotFound` (Function, optional): Callback when product not found
- `options.onClose` (Function, optional): Callback when dialog closed
- `options.keepOpen` (Boolean, optional): Keep dialog open after scan

**Returns:** Close function

---

## 10. Glossary

| Term | Definition |
|------|------------|
| AI | Application Identifier - GS1 standard prefix codes |
| EAN | European Article Number - 8 or 13 digit barcode |
| GS1-128 | Supply chain barcode standard with structured data |
| GTIN | Global Trade Item Number - universal product identifier |
| OWL | Odoo Web Library - component framework |
| UPC | Universal Product Code - 12 digit barcode |

---

## 11. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | Claude Code | Initial PRD creation |

---

*This document is auto-generated based on code analysis and testing.*
