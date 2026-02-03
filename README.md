# Barcode Scanner Base

Core barcode and QR code scanning functionality for Odoo 18.

---

# 條碼掃描基礎模組

Odoo 18 條碼與 QR Code 掃描核心功能模組。

---

## Features / 功能特色

### English

- **Multi-barcode Support**: Assign multiple barcodes (EAN-13, EAN-8, UPC-A, Code128, QR) to products
- **Camera Scanning**: OWL-based scanner dialog with html5-qrcode library
- **GS1-128 Parser**: Extract GTIN, lot, serial, expiry, weight, and quantity from GS1 barcodes
- **Barcode Validation**: Automatic checksum validation for EAN and UPC formats
- **Configurable Settings**: Customize scan mode, sound feedback, auto-increment, and more

### 繁體中文

- **多條碼支援**：為產品指定多個條碼（EAN-13、EAN-8、UPC-A、Code128、QR）
- **相機掃描**：基於 OWL 的掃描對話框，使用 html5-qrcode 函式庫
- **GS1-128 解析器**：從 GS1 條碼擷取 GTIN、批號、序號、有效期限、重量及數量
- **條碼驗證**：自動驗證 EAN 及 UPC 格式的檢查碼
- **可設定選項**：自訂掃描模式、音效回饋、自動累加等功能

---

## Dependencies / 相依性

### Odoo Modules / Odoo 模組
- `base`
- `product`
- `stock`
- `barcodes`

### Python Libraries / Python 函式庫
```bash
pip install python-barcode[images] qrcode[pil]
```

---

## Installation / 安裝

### English

1. Install Python dependencies:
   ```bash
   pip install python-barcode[images] qrcode[pil]
   ```

2. Copy module to addons directory

3. Update Apps List and install "Barcode Scanner Base"

### 繁體中文

1. 安裝 Python 相依套件：
   ```bash
   pip install python-barcode[images] qrcode[pil]
   ```

2. 複製模組到 addons 目錄

3. 更新應用程式清單並安裝「Barcode Scanner Base」

---

## Configuration / 設定

### English

Go to **Settings > General Settings > Barcode Scanner**:

- **Scan Mode**: All / Barcodes Only / QR Codes Only
- **Enable Sound Feedback**: Play sound on successful scan
- **Auto-Increment Quantity**: Increase qty when scanning same product
- **Default Barcode Type**: Default type for new barcodes
- **Show Stock Info on Scan**: Display on-hand quantity
- **Camera Preference**: Back / Front / Ask Every Time
- **Scan Delay**: Minimum delay between scans (milliseconds)
- **Enable GS1-128 Parsing**: Auto-parse GS1 barcodes

### 繁體中文

前往 **設定 > 一般設定 > 條碼掃描器**：

- **掃描模式**：全部 / 僅條碼 / 僅 QR Code
- **啟用音效回饋**：掃描成功時播放音效
- **自動累加數量**：掃描相同產品時增加數量
- **預設條碼類型**：新增條碼時的預設類型
- **掃描時顯示庫存資訊**：顯示現有庫存數量
- **相機偏好**：後置 / 前置 / 每次詢問
- **掃描延遲**：連續掃描間的最小延遲（毫秒）
- **啟用 GS1-128 解析**：自動解析 GS1 條碼

---

## Usage / 使用方式

### Adding Multiple Barcodes / 新增多條碼

**English:**
1. Open a Product form
2. Go to "Barcodes" tab
3. Click "Add a line"
4. Enter barcode value and select type
5. Save the product

**繁體中文：**
1. 開啟產品表單
2. 前往「條碼」分頁
3. 點擊「新增一行」
4. 輸入條碼值並選擇類型
5. 儲存產品

### Product Lookup by Barcode / 以條碼查詢產品

```python
# Find product by any barcode (primary, additional, or internal reference)
product = self.env['product.product'].find_by_barcode('4012345678901')

# Find with additional GS1 info
result = self.env['product.product'].find_by_barcode_with_info('(01)04012345678901(17)251231')
# Returns: {'product': record, 'barcode_type': 'gs1_128', 'gs1_data': {...}}
```

### GS1-128 Parsing / GS1-128 解析

```python
parser = self.env['barcode.gs1.parser']
result = parser.parse('(01)04012345678901(17)251231(10)LOT123')

# Result:
# {
#     'gtin': '04012345678901',
#     'expiry': datetime(2025, 12, 31),
#     'lot': 'LOT123',
#     'is_gs1': True,
#     ...
# }
```

---

## Models / 資料模型

### product.barcode

| Field | Type | Description | 說明 |
|-------|------|-------------|------|
| `name` | Char | Barcode value | 條碼值 |
| `barcode_type` | Selection | Type (ean13, qr, etc.) | 類型 |
| `product_id` | Many2one | Product variant | 產品變體 |
| `company_id` | Many2one | Company | 公司 |
| `sequence` | Integer | Display order | 顯示順序 |

### barcode.gs1.parser

Abstract model for parsing GS1-128 barcodes. / 用於解析 GS1-128 條碼的抽象模型。

---

## API Reference / API 參考

### product.product

| Method | Description | 說明 |
|--------|-------------|------|
| `find_by_barcode(barcode, company_id)` | Find product by barcode | 以條碼查詢產品 |
| `find_by_barcode_with_info(barcode, company_id)` | Find with GS1 data | 查詢並附帶 GS1 資料 |

### barcode.gs1.parser

| Method | Description | 說明 |
|--------|-------------|------|
| `parse(barcode)` | Parse GS1-128 barcode | 解析 GS1-128 條碼 |
| `is_gs1_barcode(barcode)` | Check if GS1 format | 檢查是否為 GS1 格式 |
| `format_for_display(barcode)` | Human-readable format | 人類可讀格式 |

---

## License / 授權

LGPL-3.0

---

**Author / 作者:** Woow Tech

**Version / 版本:** 18.0.1.0.0
