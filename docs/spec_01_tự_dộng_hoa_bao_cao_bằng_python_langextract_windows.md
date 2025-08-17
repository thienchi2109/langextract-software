# SPEC-01 – Tự động hóa báo cáo bằng Python + langextract (Windows)

## Background

Công cụ dạng **GUI trên Windows** cho phép người dùng **import thủ công** (kéo‑thả hoặc nút “Chọn file…”) các file báo cáo (PDF, DOCX, Excel…). Người dùng có **ô input cấu hình schema trích xuất** (tên trường, mô tả/ngữ cảnh, loại dữ liệu…), sau đó bấm **“Tạo report”** để chạy trích xuất với **langextract** và xuất ra **Excel (.xlsx)** duy nhất. Hệ thống không cố định schema; người dùng có thể **tạo/lưu/tải lại template** trích xuất linh hoạt cho từng đợt.

Mục tiêu là rút ngắn thời gian đọc/tổng hợp báo cáo, duy trì tính nhất quán dữ liệu giữa nguồn nội dung không đồng nhất, đồng thời đơn giản hóa thao tác cho người dùng không rành kỹ thuật.

## Requirements

### MoSCoW

**Must have**

- Ứng dụng desktop Windows 10/11, GUI thân thiện (kéo‑thả hoặc duyệt file).
- Hỗ trợ import nhiều định dạng: PDF, DOCX, XLSX/XLS; (tùy chọn CSV).
- Người dùng cấu hình **schema trích xuất động**: thêm/xóa/sửa trường; nhập mô tả/ngữ cảnh; chọn **kiểu dữ liệu** (text/number/date/currency).
- **OCR PDF scan bằng EasyOCR** (Tiếng Việt + Tiếng Anh) để tạo text đầu vào cho langextract.
- Chạy trích xuất bằng **langextract** theo schema người dùng; có **bản xem trước** kết quả theo từng file và bảng tổng hợp.
- **Xuất báo cáo: chỉ Excel (.xlsx)**.
- **Lưu/Load Template** trích xuất (schema + tham số parser/OCR) để tái sử dụng.
- **Bảo mật & mạng**: xử lý file **cục bộ**; chỉ gửi **đoạn văn bản cần trích xuất** tới **Gemini API** để suy luận; không ghi log nội dung nhạy cảm; có tuỳ chọn **mask** dữ liệu (số tài khoản, số CMND/CCCD…).
- **Mask PII mặc định BẬT**: tự động ẩn một phần dãy số dài, số tài khoản, CMND/CCCD, email/điện thoại… trước khi gửi sang Gemini.
- **Cảnh báo & đồng ý**: khi **bật OCR/Proofread/Extraction dùng Gemini**, GUI hiển thị banner cảnh báo “văn bản sẽ được gửi ra ngoài”. Khi **tắt các chức năng online**, công cụ chạy **hoàn toàn offline** (chỉ đọc file & OCR cục bộ, không gọi mạng).
- Log lỗi theo file, thông báo rõ ràng các case không đọc được/thiếu dữ liệu.

**Should have**

- Công tắc bật/tắt OCR và chọn ngôn ngữ OCR.
- Hỗ trợ PDF có mật khẩu (người dùng nhập mật khẩu).
- Gộp nhiều sheet Excel; chuyển dữ liệu bảng → văn bản có ngữ cảnh cho langextract.
- Tính toán cơ bản trên cột số (sum/avg/min/max) và group‑by theo 1 trường chọn.
- Đa ngôn ngữ UI (VI/EN) và khả năng đặt định dạng số/ngày.
- Mở rộng import CSV (nếu cần).
- **Quản lý API Key Gemini**: nhập lần đầu trong GUI, lưu an toàn (Windows Credential Manager/DPAPI), cho phép đổi/xoá.
- **Tùy chọn “Sửa dấu bằng Gemini trước khi trích xuất”** (mặc định **BẬT**; có thể tắt để giữ dữ liệu 100% cục bộ).

**Could have**

- Thư viện **Template Gallery** cho các use case (Tài chính, Nhân sự, Vận hành…).
- **Biểu đồ trong Excel** (tạo chart sheet/embedded chart khi xuất).
- Plugin cho định dạng khác (PPTX, HTML, hình ảnh) khi export (không bắt buộc v1).

**Won’t have (v1)**

- Xuất **CSV** hoặc **PDF**.
- Lịch chạy tự động/scheduler và tích hợp dashboard BI trực tiếp.
- Gửi email tóm tắt ra ngoài Internet.

## Method

### 1) Kiến trúc tổng thể

```plantuml
@startuml
skinparam sequenceMessageAlign center
actor User
User -> GUI: Import files + định nghĩa Schema
GUI -> TemplateManager: Save/Load Template (JSON)
User -> GUI: Click "Tạo report"
GUI -> Ingestor: Liệt kê & phân loại file
Ingestor -> PDF: PyMuPDF.extract_text()
Ingestor -> DOCX: python-docx.read()
Ingestor -> XLS(X): pandas.read_excel()
PDF --> Preprocess: Nếu text trống → render page->image
Preprocess -> EasyOCR: OCR(vi,en) => text
EasyOCR --> PIIMasker: Ẩn PII trước khi ra ngoài
DOCX/PDF/Text/Table2Text --> PIIMasker
PIIMasker --> Proofreader: (Optional) Gemini sửa dấu
Proofreader --> LangExtract: Chuỗi đã hiệu đính (đã mask)
LangExtract -> Gemini 2.5 Pro: HTTPS (API key)
LangExtract --> Aggregator: Kết quả chuẩn hóa (list[dict])
Aggregator -> Exporter: DataFrame, Summary
Exporter -> User: Excel .xlsx
@enduml
```

### 2) Quyền riêng tư & Chế độ chạy

- **Online (mặc định)**: dùng Gemini cho Proofread/Extraction ⇒ văn bản **đã mask PII** sẽ được gửi ra ngoài; GUI hiển thị banner cảnh báo + yêu cầu người dùng đồng ý.
- **Offline**: tắt Proofread và (tuỳ chọn) backend offline ⇒ chỉ xử lý cục bộ.
- **Nhật ký**: cho xuất **Minimized logs** (không chứa văn bản gốc).

### 3) PII Mask logic (tóm tắt)

- Ẩn giữa của dãy **≥8 chữ số** (số tài khoản, CCCD 12 số, CMND 9 số…).
- Ẩn phần local của **email** (`j***@example.com`).
- Chuẩn hoá & ẩn **số điện thoại** (giữ 3 số đầu & 2 số cuối).
- Mask **không phá nghĩa**: vẫn đủ ngữ cảnh để trích xuất chỉ số tổng hợp.

### 4) Định nghĩa **Template** (schema động) – JSON

```json
{
  "name": "financial_generic_v1",
  "prompt_description": "Trích xuất các chỉ số kinh doanh cốt lõi từ văn bản báo cáo. Chỉ dùng số liệu xuất hiện trong văn bản.",
  "fields": [
    {"name": "ten_chi_nhanh", "type": "text", "description": "Tên chi nhánh"},
    {"name": "ky_bao_cao", "type": "text"},
    {"name": "doanh_thu", "type": "number", "number_locale": "vi-VN"},
    {"name": "loi_nhuan", "type": "number"},
    {"name": "nhan_xet_chinh", "type": "text", "optional": true}
  ],
  "examples": [
    {
      "text": "Báo cáo chi nhánh Hà Nội: Doanh thu 5 tỷ, lợi nhuận 450 triệu trong Quý 3/2025.",
      "extractions": [
        {"class": "ten_chi_nhanh", "text": "Hà Nội"},
        {"class": "ky_bao_cao", "text": "Quý 3/2025"},
        {"class": "doanh_thu", "text": "5000000000"},
        {"class": "loi_nhuan", "text": "450000000"}
      ]
    }
  ],
  "provider": {"type": "gemini", "model_id": "gemini-2.5-pro", "api_base": "https://generativelanguage.googleapis.com"},
  "run_options": {"max_workers": 8, "extraction_passes": 2, "max_char_buffer": 1200}
}
```

- Người dùng có thể thêm/xóa **fields** ngay trong UI; có nút **Xuất/Import Template**.

### 5) Chi tiết triển khai từng loại file

**PDF**

- Dùng `page.get_text("text")` hoặc `get_text("blocks")` để cải thiện thứ tự đọc; fallback OCR khi đoạn trống hoặc có tỷ lệ ký tự không phải chữ quá cao.
- Với trang ảnh: `page.get_pixmap(dpi=300)` → EasyOCR.

**DOCX**

- Duyệt `document.paragraphs` + (tuỳ chọn) `document.tables` → nối thành text theo thứ tự xuất hiện.

**Excel (XLSX/XLS)**

- Dùng `pandas.read_excel(file, sheet_name=None)` để lấy tất cả sheet → chuẩn hoá cột/kiểu.
- **Table→Text**: Với mỗi hàng quan trọng, ghép câu dựa theo tiêu đề cột. Ví dụ:
  > "Chi nhánh {Branch} có Doanh thu {Revenue} và Lợi nhuận {Profit} trong {Period}."
- Có tuỳ chọn người dùng chọn **các cột chính** để sinh câu.

### 6) Adapter **langextract** (Gemini API)

- Cấu hình mẫu:

```python
import langextract as lx
from .masking import mask_for_cloud

result = lx.extract(
    text_or_documents=raw_text,
    prompt_description=template.prompt_description,
    examples=template.examples,  # map JSON -> lx.data.ExampleData
    model_id=template.provider.model_id,        # "gemini-2.5-pro"
    fence_output=False,
    use_schema_constraints=False,
    extraction_passes=template.run_options.extraction_passes,
    max_workers=template.run_options.max_workers,
    max_char_buffer=template.run_options.max_char_buffer,
)
```

- **API Key**: Lấy từ **Windows Credential Manager** nếu đã lưu; nếu chưa có, GUI hiển thị dialog nhập và kiểm tra quyền truy cập (gọi `/models` test).
- Cho phép đổi model trong UI (ví dụ `gemini-2.5-flash` để tiết kiệm chi phí/nhanh hơn), có hiển thị chú thích tốc độ/chi phí.

### 7) Ép kiểu & kiểm tra dữ liệu

- Casting `number/date/currency` với `locale`; loại bỏ đơn vị; chuẩn hoá dấu thập phân, nghìn.
- Cảnh báo giá trị thiếu/bất thường (ví dụ doanh\_thu < 0).

### 8) Xuất Excel

- Sử dụng `pandas.ExcelWriter(engine="xlsxwriter")`.
- **Sheet **``: cột theo **thứ tự schema động** (`template.fields`). Tự động **thêm cột thiếu** và **ép kiểu** theo `type` (number/date/text) trước khi ghi.
- **Sheet **``: nếu người dùng chọn `group_by` (một trường trong schema), hệ thống tự tổng hợp **các trường kiểu **`` (sum) và xuất sang sheet.
- **Cột kỹ thuật (tuỳ chọn)**: nếu có `source_file`, `parsed_at` trong dữ liệu thì thêm sau nhóm cột schema.
- Định dạng chất lượng sống: auto‑fit độ rộng cột, **freeze header**, định dạng số/ngày cơ bản.

### 9) Lưu trữ & cấu hình

- **Template**: JSON trong `%APPDATA%/LangExtractor/templates/*.json`.
- **API Key**: lưu bằng **Windows Credential Manager** (DPAPI) với tên bí danh `LangExtractor.GeminiAPIKey`; chỉ đọc trong phiên chạy; có nút *Sign out* để xoá.
- **Log**: `%LOCALAPPDATA%/LangExtractor/logs/*.log` (rotating) — **mask** chuỗi nhạy cảm (số tài khoản, số thẻ…).
- **Tài nguyên OCR**: thư mục model của EasyOCR (cache) — có thể **đóng gói sẵn** để không cần Internet khi tải lần đầu.

### 10) Hiệu năng & độ tin cậy

- Đa luồng đọc file & tiền xử lý; giới hạn song song khi gọi Gemini theo quota.
- Theo dõi tiến trình per‑file; cho phép **Cancel** an toàn.
- Kiểm thử trên bộ 50–200 file; PDF tối đa \~300 trang/file như đã thống nhất.

## Implementation

### A) Cài đặt & phụ thuộc

- **Python 3.11 (64-bit)**.
- Cài gói:
  ```bash
  pip install -U pyside6 pymupdf python-docx pandas openpyxl xlsxwriter easyocr keyring langextract[full] google-genai
  ```
  > `langextract[full]` theo khuyến nghị mới để tránh lỗi `libmagic`. EasyOCR sẽ tự tải trọng số ở lần đầu nếu `download_enabled=True`.

### B) Cấu trúc dự án (đề xuất)

```
app/
  gui/
    main_window.py
    schema_editor.py
    preview_panel.py
    settings_dialog.py
  core/
    ingest.py
    ocr.py
    masking.py
    proofread.py
    excel_text.py
    extract.py
    aggregate.py
    export_excel.py
    keychain.py
    templates.py
    config.py
  assets/
  app.py
```

### C) Lưu API key Gemini (Windows Credential Manager)

```python
# core/keychain.py
import keyring
SERVICE = "LangExtractor.Gemini"
USERNAME = "APIKey"

def save_api_key(value: str):
    keyring.set_password(SERVICE, USERNAME, value)

def load_api_key() -> str | None:
    return keyring.get_password(SERVICE, USERNAME)

def delete_api_key():
    keyring.delete_password(SERVICE, USERNAME)
```

- GUI: khi người dùng nhập API key hợp lệ → `save_api_key()`; lần sau tự `load_api_key()`.
- **Banner cảnh báo**: Khi bật Proofread/Extraction (dùng Gemini), hiển thị thông báo: *“Văn bản (đã mask PII) sẽ được gửi ra ngoài để xử lý bởi Gemini.”* Người dùng phải **đồng ý** trước khi chạy lần đầu.

### D) Ingest & OCR tối ưu cho **PDF scan từ máy photocopy** (OCR cục bộ)

```python
# core/ocr.py
import fitz
import easyocr
import unicodedata
from pathlib import Path

MODELS_DIR = r"C:\ProgramData\LangExtractor\easyocr_models"

_reader = None

def get_reader(download_first_time=True):
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(
            ['vi', 'en'],
            gpu=False,
            model_storage_directory=MODELS_DIR,
            download_enabled=download_first_time
        )
    return _reader

def pdf_to_text(pdf_path: str, dpi=350) -> str:
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        t = page.get_text("text")
        if t and len(t.strip()) > 50:
            texts.append(t)
            continue
        # Fallback OCR for image-only pages
        pix = page.get_pixmap(dpi=dpi)
        png_path = Path(pdf_path).with_suffix(f".p{page.number:03d}.png")
        pix.save(str(png_path))
        res = get_reader().readtext(
            str(png_path),
            paragraph=True,
            rotation_info=[90, 180, 270],
            contrast_ths=0.1,
            adjust_contrast=0.6,
            mag_ratio=2.0,
            text_threshold=0.6,
            low_text=0.3,
            link_threshold=0.4,
            decoder='greedy'
        )
        page_txt = "
".join([x[1] for x in res])
        texts.append(page_txt)
    raw = "

".join(texts)
    return unicodedata.normalize('NFC', raw)
```

- Lần chạy đầu: gọi `get_reader(download_first_time=True)`; sau khi model đã tải về `MODELS_DIR`, các lần sau đặt `False` (qua cờ trong file cấu hình).

### E) Tuỳ chọn **Sửa dấu bằng Gemini** (mặc định BẬT, **mask PII trước khi gửi**)

```python
# core/proofread.py
from google import genai
from .keychain import load_api_key
from .masking import mask_for_cloud

SYSTEM_HINT = (
    "Bạn là bộ kiểm lỗi OCR tiếng Việt. Chỉ sửa lỗi dấu và khoảng trắng, KHÔNG diễn giải, "
    "KHÔNG thêm/gỡ ý. Giữ nguyên số, đơn vị, dấu câu. Trả về đúng nguyên văn đã hiệu đính."
)

_client = None

def _client_once():
    global _client
    if _client is None:
        _client = genai.Client(api_key=load_api_key())
    return _client

def proofread_vi(text: str, enabled: bool = True, model: str = "gemini-2.5-pro") -> str:
    if not enabled or not text.strip():
        return text
    c = _client_once()
    masked = mask_for_cloud(text)
    resp = c.models.generate_content(
        model=model,
        contents=[{"role": "user",
                   "parts": [{"text": f"{SYSTEM_HINT}

Văn bản:
{masked}"}]}],
    )
    return resp.text or text
```

- GUI có công tắc **Proofread bằng Gemini**; khi tắt → giữ dữ liệu 100% local.

### F) Chuyển Excel bảng → câu tự nhiên

```python
# core/excel_text.py
import pandas as pd

def table_rows_to_text(df: pd.DataFrame, cols: list[str], period_col: str | None=None) -> str:
    lines = []
    for _, r in df.iterrows():
        branch = r.get(cols[0], "")
        rev = r.get(cols[1], "")
        prof = r.get(cols[2], "")
        prd = r.get(period_col, "") if period_col else ""
        s = f"Chi nhánh {branch} có doanh thu {rev} và lợi nhuận {prof}{' trong ' + str(prd) if prd else ''}."
        lines.append(str(s))
    return "
".join(lines)
```

### G) Gọi **langextract** theo schema động

```python
# core/extract.py
import langextract as lx
from .masking import mask_for_cloud

def run_langextract(text: str, template: dict) -> list[dict]:
    masked = mask_for_cloud(text)
    return lx.extract(
        text_or_documents=masked,
        prompt_description=template["prompt_description"],
        examples=template.get("examples", []),
        model_id=template.get("provider", {}).get("model_id", "gemini-2.5-pro"),
        fence_output=False,
        use_schema_constraints=False,
        extraction_passes=template.get("run_options", {}).get("extraction_passes", 2),
        max_workers=template.get("run_options", {}).get("max_workers", 8),
        max_char_buffer=template.get("run_options", {}).get("max_char_buffer", 1200),
    )
```

### H) Tổng hợp & xuất Excel

```python
# core/export_excel.py
import pandas as pd
from pandas import ExcelWriter

def export_xlsx(rows: list[dict], out_path: str, template: dict, group_by: str | None=None):
    df = pd.DataFrame(rows)

    # 1) Thứ tự cột theo schema động
    schema_cols = [f.get("name") for f in template.get("fields", []) if f.get("name")]
    for c in schema_cols:
        if c not in df.columns:
            df[c] = None

    # 2) Ép kiểu theo schema
    for f in template.get("fields", []):
        name, ftype = f.get("name"), f.get("type", "text")
        if name in df.columns:
            if ftype == "number":
                df[name] = pd.to_numeric(df[name], errors="coerce")
            elif ftype == "date":
                df[name] = pd.to_datetime(df[name], errors="coerce")

    # 3) Sắp xếp cột: schema → cột kỹ thuật → cột khác
    tech_cols = [c for c in ["source_file", "parsed_at"] if c in df.columns]
    other_cols = [c for c in df.columns if c not in schema_cols + tech_cols]
    df = df[schema_cols + tech_cols + other_cols]

    with ExcelWriter(out_path, engine="xlsxwriter") as xw:
        # Data
        df.to_excel(xw, sheet_name="Data", index=False)
        wb, ws = xw.book, xw.sheets["Data"]
        header_fmt = wb.add_format({"bold": True})
        ws.set_row(0, None, header_fmt)
        ws.freeze_panes(1, 0)
        # auto-fit đơn giản
        for idx, col in enumerate(df.columns):
            maxlen = max(len(str(col)), int(df[col].astype(str).map(len).max() if not df.empty else 0))
            ws.set_column(idx, idx, min(maxlen + 2, 60))

        # Summary (nếu có)
        if group_by and group_by in df.columns:
            num_cols = [f.get("name") for f in template.get("fields", []) if f.get("type") == "number" and f.get("name") in df.columns]
            if num_cols:
                pv = df.groupby(group_by)[num_cols].sum().reset_index()
                pv.to_excel(xw, sheet_name="Summary", index=False)
                ws2 = xw.sheets["Summary"]
                ws2.freeze_panes(1, 0)
```

### I) Điều phối chạy & tiến trình

```python
# core/aggregate.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from .ocr import pdf_to_text
from .proofread import proofread_vi
from .extract import run_langextract


def process_file(path, template, proofread=True):
    raw = pdf_to_text(path)
    clean = proofread_vi(raw, enabled=proofread)
    result = run_langextract(clean, template)
    return result


def process_all(paths, template, proofread):
    rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(process_file, p, template, proofread): p for p in paths}
        for fut in as_completed(futs):
            rows.extend(fut.result())
    return rows
```

### J) Đóng gói .exe (PyInstaller)

- File spec: thêm `--add-data` nếu muốn đóng gói sẵn model EasyOCR; ví dụ:
  ```bash
  pyinstaller -F -n LangExtractorGUI apppp.py \
    --add-data "C:\ProgramData\LangExtractor\easyocr_models;easyocr_models" \
    --hidden-import easyocr
  ```
- Kiểm thử: chạy trên Windows 10/11 sạch, không Internet (khi tắt proofread) để xác minh đường dẫn model.

### K) Cấu hình & lần chạy đầu tiên

- Nếu `MODELS_DIR` chưa có trọng số EasyOCR → bật `download_enabled=True` và hiển thị tiến trình tải.
- Sau khi tải xong, ghi vào config `easyocr_downloaded=true` → các lần sau khởi tạo Reader với `download_enabled=False` để khóa offline.
- Nếu bật Proofread/Extraction nhưng thiếu API key Gemini → hiện dialog bắt buộc nhập; nếu người dùng **không đồng ý** gửi dữ liệu, đề xuất chạy **chế độ offline**.

### L) Masking PII (code mẫu)

```python
# core/masking.py
import re

EMAIL = re.compile("([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+[.][A-Za-z]{2,})")
PHONE = re.compile("([+]?([0-9]{1,3})[- ]?)?([0-9]{3})([0-9]{3,4})([0-9]{2})")
LONG_DIGITS = re.compile("(?<![0-9])([0-9]{8,})(?![0-9])")  # tài khoản, CCCD 12 số, CMND 9 số, v.v.

def _mask_middle(s: str, vis_left=3, vis_right=2, mask_char='*') -> str:
    if len(s) <= vis_left + vis_right:
        return mask_char * len(s)
    return s[:vis_left] + (mask_char * (len(s) - vis_left - vis_right)) + s[-vis_right:]

def mask_for_cloud(text: str) -> str:
    if not text:
        return text
    t = EMAIL.sub(lambda m: m.group(1) + '***' + m.group(2), text)
    t = LONG_DIGITS.sub(lambda m: _mask_middle(m.group(1), 3, 2), t)
    t = PHONE.sub(lambda m: (m.group(1) or '') + m.group(3) + '***' + m.group(5), t)
    return t
```

- Mask chạy **tự động** trước khi gọi Gemini ở cả bước **Proofread** và **Extraction**.

## Milestones

**M0 – Khởi tạo & khung GUI (1 tuần)**

- Khởi tạo project, màn hình chính PySide6 (drag‑drop, danh sách file, progress bar).
- Module `keychain.py` + dialog nhập/lưu API key.
- **AC**: Chạy được `.exe` dev; nhập API key và lưu thành công.

**M1 – Ingestor & Preview (1–2 tuần)**

- Đọc DOCX/Excel/PDF text; bảng Excel → text; preview văn bản thô theo file.
- **AC**: 10 file mẫu nhiều định dạng hiển thị preview đúng thứ tự.

**M2 – OCR & PII Mask (1–2 tuần)**

- OCR EasyOCR cho PDF scan; cơ chế tải model lần đầu; PII Masker.
- **AC**: PDF scan 300 DPI cho ra text; banner cảnh báo xuất hiện khi bật online.

**M3 – Proofread & LangExtract (1–2 tuần)**

- Proofread bằng `gemini-2.5-pro` (bật/tắt); tích hợp `langextract` theo template động.
- **AC**: Template mẫu hoạt động; trả về list[dict] đúng schema; xử lý lỗi mạng.

**M4 – Export Excel & Summary (1 tuần)**

- Xuất `.xlsx` có sheet `Data` + `Summary`; định dạng số/ngày cơ bản.
- **AC**: Tập dữ liệu demo tạo file Excel mở được trên Office/Excel.

**M5 – Hiệu năng, Đóng gói & QA (1–2 tuần)**

- Tối ưu đa luồng; profiling bộ 200 file; đóng gói PyInstaller; bộ test smoke.
- **AC**: Xử lý 200 file ổn định; `.exe` chạy trên Win10/11 sạch.

## Gathering Results

**Mục tiêu đánh giá**

- **Độ chính xác trích xuất** (Field‑level F1): ≥ 0.9 trên bộ mẫu đã gán nhãn.
- **WER OCR tiếng Việt**: ≤ 10% trên scan 300–400 DPI (mục tiêu).
- **Thông lượng**: ≥ N trang/phút trên máy chuẩn (ghi rõ cấu hình khi đo).
- **Tỷ lệ lỗi**: < 1% file thất bại; không crash, có log nguyên nhân.

**Cách đo**

- Tạo **bộ kiểm thử** \~100 tài liệu đa định dạng; chuẩn hoá ground truth JSON.
- Script so sánh: so trường số (sai số 0), so trường text (token F1), báo cáo `summary.xlsx`.
- Theo dõi thời gian xử lý/CPU/RAM.

**Nghiệm thu**

- Demo end‑to‑end trên 20 tài liệu đại diện.
- Ký biên bản bàn giao: mã nguồn, hướng dẫn cài đặt, bộ mẫu, tài liệu vận hành.

## Need Professional Help in Developing Your Architecture?

Please contact me at [sammuti.com](https://sammuti.com) :)

