# Import Paths Fix - Demo Scripts Organization

## 🐛 **Problem**
After organizing demo scripts into `demo_scripts/` directory, import statements failed with:
```
ModuleNotFoundError: No module named 'gui'
```

## 🔧 **Root Cause**
When demo scripts were moved from root directory to `demo_scripts/` subdirectory, the Python import paths broke because:
- Scripts tried to import `gui.simple_main_window` 
- Python couldn't find `gui` module from the new nested location
- `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` only added `demo_scripts/` to path

## ✅ **Solution**

### **1. Fixed Import Paths in Demo Scripts**
Changed from:
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

To:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

This adds the parent directory (project root) to Python path instead of current directory.

### **2. Created Main Launcher**
Added `launch_app.py` in root directory:
```python
#!/usr/bin/env python3
# Handles path management automatically
from demo_scripts.demo_complete_with_settings import main
```

### **3. Updated Documentation**
- Updated `README.md` with multiple launch methods
- Updated `demo_scripts/README.md` with new instructions
- Clear guidance on recommended usage

## 🎯 **Fixed Files**
- ✅ `demo_scripts/demo_complete_with_settings.py`
- ✅ `demo_scripts/demo_simple_app.py`  
- ✅ `demo_scripts/demo_settings.py`
- ✅ `demo_scripts/demo_schema_editor.py`
- ✅ `demo_scripts/demo_complete_workflow.py`

## 🚀 **Usage Now**

### **Method 1: Launcher (Recommended)**
```bash
python launch_app.py
```
- ✅ No import path issues
- ✅ Automatic directory management
- ✅ Clean and simple

### **Method 2: Direct Demo Scripts**
```bash
python demo_scripts/demo_complete_with_settings.py
```
- ✅ Works from project root
- ✅ Import paths fixed
- ✅ All dependencies resolved

### **Method 3: Component Testing**
```bash
python demo_scripts/demo_settings.py
python demo_scripts/demo_schema_editor.py
```
- ✅ Individual components work
- ✅ Testing isolated features

## 📈 **Benefits**
- 🗂️ **Clean Project Structure**: Organized demo scripts in dedicated directory
- 🚀 **Easy Launch**: Simple `python launch_app.py` command
- 🔧 **Maintainable**: All import paths consistent and working
- 📚 **Well Documented**: Clear instructions for different use cases
- ✅ **Tested**: All demo scripts verified working

## 🎉 **Result**
LangExtractor application now has:
- ✅ Clean, organized project structure
- ✅ Working demo scripts in `demo_scripts/` directory  
- ✅ Easy-to-use launcher from root directory
- ✅ Complete documentation and guides
- ✅ All functionality preserved and working

**Ready for production use!** 🚀 