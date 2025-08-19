# Demo Scripts - LangExtractor

Thư mục này chứa các demo scripts để test và showcase các tính năng của LangExtractor.

## 🚀 Demo Scripts chính

### **Ứng dụng hoàn chỉnh:**
- **`demo_complete_with_settings.py`** - Demo hoàn chỉnh với Settings Dialog (GUI 100%)
- **`demo_simple_app.py`** - Demo ứng dụng đơn giản (workflow cốt lõi)
- **`demo_complete_workflow.py`** - Demo workflow hoàn chỉnh với OCR + AI + Excel

### **Settings & Configuration:**
- **`demo_settings.py`** - Test Settings Dialog với API key management
- **`demo_schema_editor.py`** - Test Schema Editor với Vietnamese field names
- **`demo_config_template.py`** - Test configuration và template management
- **`demo_keychain.py`** - Test secure credential storage

### **Core Components:**
- **`demo_task8_extractor.py`** - Test LangExtract AI extraction
- **`demo_task7_proofreader.py`** - Test OCR proofreading
- **`demo_task10_excel.py`** - Test Excel export functionality
- **`demo_task11_gui.py`** - Test GUI components

### **Integration & Advanced:**
- **`demo_phase3_charts.py`** - Test charts và analytics (legacy)
- **`demo_phase4_integration.py`** - Test real-time processing integration
- **`demo_excel_export_integration.py`** - Test Excel export integration
- **`demo_preview_panel.py`** - Test preview functionality (basic)
- **`demo_preview_panel_phase2.py`** - Test advanced preview features

## 📋 Cách sử dụng

### **Bắt đầu với ứng dụng hoàn chỉnh:**
```bash
# Method 1: Dùng launcher từ root directory (khuyến nghị)
python launch_app.py

# Method 2: Chạy trực tiếp từ demo_scripts  
python demo_scripts/demo_complete_with_settings.py

# Method 3: Ứng dụng đơn giản
python demo_scripts/demo_simple_app.py
```

### **Test components riêng biệt:**
```bash
# Test Settings Dialog
python demo_scripts/demo_settings.py

# Test Schema Editor
python demo_scripts/demo_schema_editor.py

# Test Excel Export
python demo_scripts/demo_task10_excel.py
```

## 🎯 Workflow khuyến nghị

1. **Bắt đầu**: `demo_complete_with_settings.py` cho GUI đầy đủ
2. **Settings**: Nhập API key Gemini
3. **Schema**: Cấu hình extraction schema (tiếng Việt OK)
4. **Processing**: Import files → Process → Preview → Export Excel

## ✨ Tính năng highlight

- 🔑 **API Key Management**: Secure storage với Windows Credential Manager
- 🌐 **Vietnamese Support**: Schema fields, UI, error messages
- 📊 **Excel Export**: Professional formatting với Data + Summary sheets
- 🔒 **Privacy Controls**: PII masking, offline mode options
- 🎨 **Modern GUI**: Clean, professional interface

## 📝 Lưu ý

- Cần API key Gemini để sử dụng AI extraction
- Lấy miễn phí tại: https://aistudio.google.com/app/apikey
- Demo scripts được organize theo thứ tự phát triển (tasks)
- Legacy scripts vẫn được giữ để tham khảo
- **Import paths đã được sửa** để chạy từ demo_scripts/ directory
- **Khuyến nghị**: Dùng `python launch_app.py` từ root directory để dễ dàng nhất 