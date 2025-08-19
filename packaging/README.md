# LangExtractor Windows Executable Packaging

This directory contains all the tools and configurations needed to build a Windows executable for the LangExtractor application.

## 🚀 Quick Start

### 1. Install Build Dependencies
```bash
pip install -r requirements-build.txt
```

### 2. Build the Executable
```bash
python build.py
```

### 3. Find Your Executable
The built executable will be located at:
```
dist/LangExtractor/LangExtractor.exe
```

## 📁 Package Contents

### Core Files
- `pyinstaller.spec` - PyInstaller specification file
- `build.py` - Automated build script
- `requirements-build.txt` - Build dependencies
- `README.md` - This documentation

### Generated Files (after build)
- `version_info.py` - Windows version information
- `LangExtractor.nsi` - NSIS installer script
- `build/` - Temporary build artifacts
- `dist/` - Final executable and dependencies

## 🔧 Build Process Details

### PyInstaller Configuration

The `pyinstaller.spec` file includes:

- **Entry Point**: `launch_app.py` (main application launcher)
- **Hidden Imports**: All necessary modules for PySide6, LangExtract, OCR, etc.
- **Assets**: GUI resources, templates, configuration files
- **Exclusions**: Unused frameworks and development tools to reduce size
- **Compression**: UPX compression enabled for smaller executable

### Build Script Features

The `build.py` script provides:

- ✅ **Dependency Checking**: Verifies all required packages are installed
- 🧹 **Clean Builds**: Removes previous build artifacts
- 📝 **Version Info**: Creates Windows version information
- 🎨 **Icon Management**: Handles application icon
- 🔨 **PyInstaller Execution**: Runs the build process
- ⚡ **Optimization**: Size and performance optimization
- 📦 **Installer Creation**: Generates NSIS installer script
- 🧪 **Testing Guidance**: Instructions for testing the executable

## 📊 Expected Results

### Executable Size
- **Typical Size**: 200-400 MB (includes all dependencies)
- **Dependencies**: PySide6, torch/easyocr, langextract, etc.
- **Optimization**: UPX compression reduces size by ~30%

### Distribution Structure
```
dist/LangExtractor/
├── LangExtractor.exe          # Main executable
├── _internal/                 # Dependencies and libraries
│   ├── PySide6/              # GUI framework
│   ├── torch/                # OCR dependencies
│   ├── langextract/          # AI extraction
│   └── [other libraries]
├── assets/                   # Application assets
└── [configuration files]
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Missing Dependencies
**Error**: `ModuleNotFoundError` during build
**Solution**: Install missing packages:
```bash
pip install pyinstaller
pip install -r requirements-build.txt
```

#### 2. Large Executable Size
**Causes**: Unnecessary dependencies included
**Solutions**:
- Review `excludes` list in `pyinstaller.spec`
- Use `--exclude-module` for specific modules
- Consider lazy loading for large dependencies

#### 3. Runtime Errors
**Error**: Application fails to start
**Solutions**:
- Check `hiddenimports` in `pyinstaller.spec`
- Test with `--debug` flag in PyInstaller
- Verify all assets are included in `datas`

#### 4. OCR Model Issues
**Error**: EasyOCR models not found
**Solution**: OCR models are downloaded on first use
- Ensure internet connection for first run
- Consider pre-bundling models for offline distribution

### Testing the Executable

After building, test these features:

1. **GUI Loading**: Application starts without errors
2. **Settings Dialog**: API key management works
3. **File Processing**: Document ingestion and processing
4. **OCR Functionality**: Vietnamese and English text recognition
5. **AI Extraction**: LangExtract with Gemini integration
6. **Excel Export**: Professional report generation
7. **Error Handling**: Graceful error messages

## 📦 Creating an Installer

### Using NSIS (Recommended)

1. **Install NSIS**: Download from https://nsis.sourceforge.io/
2. **Use Generated Script**: The build process creates `LangExtractor.nsi`
3. **Compile Installer**:
   ```bash
   makensis LangExtractor.nsi
   ```
4. **Result**: `LangExtractor-1.0.0-Setup.exe`

### Installer Features
- ✅ **Start Menu**: Creates program shortcuts
- ✅ **Desktop Icon**: Optional desktop shortcut
- ✅ **Uninstaller**: Clean removal capability
- ✅ **Registry**: Add/Remove Programs integration
- ✅ **Admin Rights**: Proper installation permissions

## ⚡ Optimization Tips

### Reducing Size
```python
# Add to excludes in pyinstaller.spec
excludes = [
    'scipy',       # Large scientific library
    'sympy',       # Symbolic mathematics
    'jupyter',     # Development environment
    'pytest',      # Testing framework
]
```

### Improving Performance
- Use `--onefile` for single executable (slower startup)
- Use directory distribution (faster startup, current default)
- Enable UPX compression (smaller size, slightly slower startup)

### Advanced Configuration
```python
# Custom PyInstaller options
a = Analysis(
    [main_script],
    excludes=['unused_module'],
    hiddenimports=['required_hidden_module'],
    optimize=2,  # Python optimization level
)
```

## 🌐 Distribution Checklist

Before distributing the executable:

- [ ] **Functionality Testing**: All features work correctly
- [ ] **Performance Testing**: Acceptable startup and processing times
- [ ] **Security Scanning**: Antivirus false positive check
- [ ] **Documentation**: User guide and installation instructions
- [ ] **System Requirements**: Windows 10/11 compatibility verified
- [ ] **Dependencies**: All required components included
- [ ] **Licensing**: Proper license and attribution files included

## 📞 Support

For build issues:

1. **Check Logs**: Review PyInstaller output for errors
2. **Dependencies**: Verify all requirements are installed
3. **Specification**: Review `pyinstaller.spec` configuration
4. **Testing**: Test in clean environment without Python installed

## 🎯 Next Steps

After successful packaging:

1. **Quality Assurance**: Comprehensive testing
2. **Performance Optimization**: Task 22 implementation
3. **User Documentation**: Installation and usage guides
4. **Distribution**: Upload to distribution channels
5. **Maintenance**: Update process for future versions 