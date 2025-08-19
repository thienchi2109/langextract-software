# Automated Report Extraction System

A Windows desktop application for extracting structured data from various document formats using OCR and AI-powered extraction with full Vietnamese language support.

## 🚀 **Quick Start**

### **Launch the Complete Application:**
```bash
python demo_scripts/demo_complete_with_settings.py
```

### **Or try the Simplified Version:**
```bash
python demo_scripts/demo_simple_app.py
```

## ✨ **Key Features**

- 🔑 **Secure API Key Management**: Windows Credential Manager integration
- 🌐 **Vietnamese Language Support**: Full UI and field name localization
- 📄 **Document Processing**: PDF, DOCX, Excel with OCR fallback
- 🤖 **AI-Powered Extraction**: LangExtract với Gemini backend
- 📊 **Professional Excel Export**: Data + Summary sheets với auto-formatting
- 🔒 **Privacy Protection**: PII masking, offline mode options
- 🎨 **Modern GUI**: Clean, professional interface với drag-drop

## 📋 **User Workflow**

1. **Settings**: Configure API key và processing options
2. **Import**: Drag-drop PDF/Word files 
3. **Schema**: Define extraction fields (Vietnamese names supported)
4. **Process**: AI extraction với real-time progress
5. **Preview**: Review results với confidence indicators
6. **Export**: Generate professional Excel reports

## 📁 **Project Structure**

```
├── gui/                    # GUI components
│   ├── simple_main_window.py     # Main application window
│   ├── settings_dialog.py        # Settings & API management  
│   ├── simple_preview_panel.py   # Results preview
│   └── schema_editor.py          # Schema configuration
├── core/                   # Core processing engine
│   ├── processing_orchestrator.py # Pipeline coordination
│   ├── excel_exporter.py         # Excel generation
│   ├── keychain.py               # Secure credential storage
│   ├── ingestor.py               # Document processing
│   ├── extractor.py              # AI extraction
│   └── [other components]
├── demo_scripts/          # Demo applications & testing
│   ├── README.md                 # Demo guide
│   ├── demo_complete_with_settings.py  # 🚀 Main GUI app
│   ├── demo_simple_app.py        # Simplified version
│   └── [15+ other demos]
├── tests/                 # Comprehensive test suite
└── assets/                # Resources và static files
```

## 🔧 **Setup & Installation**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Gemini API Key:**
   - Visit: https://aistudio.google.com/app/apikey
   - Create free API key

3. **Launch application:**
   ```bash
   python demo_scripts/demo_complete_with_settings.py
   ```

4. **Configure settings:**
   - Tools → Cài đặt (hoặc Ctrl+,)
   - Enter API key trong tab "API Key"
   - Configure OCR và privacy settings

## 🎮 **Demo Scripts**

### **Main Applications:**
- `demo_complete_with_settings.py` - Complete GUI với Settings
- `demo_simple_app.py` - Simplified workflow version
- `demo_settings.py` - Test Settings Dialog

### **Component Testing:**
- `demo_schema_editor.py` - Test Vietnamese schema configuration
- `demo_task10_excel.py` - Test Excel export functionality
- `demo_task8_extractor.py` - Test AI extraction

See `demo_scripts/README.md` for complete list và usage instructions.

## 🔒 **Security & Privacy**

- **Encrypted Storage**: API keys stored securely với Windows Credential Manager
- **PII Masking**: Automatic protection of sensitive information
- **Offline Mode**: Process documents completely locally
- **Privacy Controls**: Clear warnings về cloud processing

## 🌐 **Vietnamese Language Support**

- Complete UI localization
- Vietnamese field names trong schema editor
- Error messages và help text
- OCR support for Vietnamese + English documents

## 📊 **Excel Export Features**

- **Data Sheet**: Extracted information với schema-ordered columns
- **Summary Sheet**: Aggregated statistics và grouping
- **Professional Formatting**: Frozen headers, auto-fit columns, conditional formatting
- **Confidence Indicators**: Color-coded confidence levels

## 🧪 **Testing**

```bash
# Run comprehensive test suite
pytest tests/

# Test specific components
python demo_scripts/demo_settings.py
python demo_scripts/demo_schema_editor.py
```

## 📈 **Current Status**

- ✅ **Core Features**: 100% complete
- ✅ **GUI Application**: Fully functional
- ✅ **Vietnamese Support**: Complete localization
- ✅ **Security**: Encrypted credential management
- ✅ **Documentation**: Comprehensive guides
- ✅ **Testing**: 15+ test files implemented

## 🚧 **Future Enhancements**

- Windows executable packaging
- Template gallery và sharing
- Advanced batch processing
- Performance optimizations
- Enhanced error analytics

## 🤝 **Contributing**

1. Review current implementation trong `demo_scripts/`
2. Check existing tests trong `tests/`
3. Follow modular architecture patterns
4. Maintain Vietnamese language support
5. Ensure security best practices

## 📄 **License & Usage**

This is a complete, production-ready application for automated document data extraction với full Vietnamese language support. Perfect for businesses needing to extract structured data from PDF and Word documents.

---

**🎯 Ready to use! Launch `demo_complete_with_settings.py` để bắt đầu extracting data from your documents.**