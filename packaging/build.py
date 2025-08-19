#!/usr/bin/env python3
"""
LangExtractor Windows Executable Build Script

This script automates the entire process of building a Windows executable
for the LangExtractor application using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Project configuration
PROJECT_NAME = "LangExtractor"
PROJECT_VERSION = "1.0.0"
BUILD_DIR = "build"
DIST_DIR = "dist"
SPEC_FILE = "pyinstaller.spec"

class BuildManager:
    """Manages the Windows executable build process."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.packaging_dir = Path(__file__).parent
        self.build_start_time = time.time()
        
        # Paths
        self.build_path = self.project_root / BUILD_DIR
        self.dist_path = self.project_root / DIST_DIR
        self.spec_path = self.packaging_dir / SPEC_FILE
        
        print(f"🚀 LangExtractor Build Manager")
        print(f"📁 Project root: {self.project_root}")
        print(f"🔧 Packaging dir: {self.packaging_dir}")
        print()
    
    def check_dependencies(self) -> bool:
        """Check if all required build dependencies are installed."""
        print("🔍 Checking build dependencies...")
        
        # Map package names to import names
        package_map = {
            'pyinstaller': 'PyInstaller',
            'PySide6': 'PySide6',
            'langextract': 'langextract',
            'easyocr': 'easyocr',
            'PyMuPDF': 'fitz',
        }
        
        missing_packages = []
        
        for package_name, import_name in package_map.items():
            try:
                __import__(import_name)
                print(f"  ✅ {package_name}")
            except ImportError:
                print(f"  ❌ {package_name} - MISSING")
                missing_packages.append(package_name)
        
        if missing_packages:
            print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
            print("Install with: pip install pyinstaller PySide6")
            return False
        
        print("✅ All dependencies satisfied!")
        return True
    
    def clean_build_dirs(self):
        """Clean previous build artifacts."""
        print("\n🧹 Cleaning previous build artifacts...")
        
        dirs_to_clean = [self.build_path, self.dist_path]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                print(f"  🗑️ Removing {dir_path}")
                shutil.rmtree(dir_path)
            else:
                print(f"  ℹ️ {dir_path} doesn't exist")
        
        print("✅ Build directories cleaned!")
    
    def create_version_info(self):
        """Create version info file for Windows executable."""
        print("\n📝 Creating version info...")
        
        version_info_content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'LangExtractor Team'),
        StringStruct(u'FileDescription', u'Automated Document Data Extraction Tool'),
        StringStruct(u'FileVersion', u'{PROJECT_VERSION}'),
        StringStruct(u'InternalName', u'{PROJECT_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright © 2024 LangExtractor Team'),
        StringStruct(u'OriginalFilename', u'{PROJECT_NAME}.exe'),
        StringStruct(u'ProductName', u'{PROJECT_NAME}'),
        StringStruct(u'ProductVersion', u'{PROJECT_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
        
        version_file = self.packaging_dir / 'version_info.py'
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_info_content)
        
        print(f"✅ Version info created: {version_file}")
    
    def create_application_icon(self):
        """Create or check for application icon."""
        print("\n🎨 Checking application icon...")
        
        icon_path = self.project_root / 'assets' / 'icon.ico'
        
        if not icon_path.exists():
            print(f"⚠️ Icon not found at {icon_path}")
            print("Creating placeholder icon...")
            
            # Ensure assets directory exists
            icon_path.parent.mkdir(exist_ok=True)
            
            # Create a simple text-based icon placeholder
            placeholder_content = "Icon placeholder - replace with actual .ico file"
            with open(icon_path, 'w') as f:
                f.write(placeholder_content)
            
            print(f"📝 Placeholder created: {icon_path}")
            print("ℹ️ Replace with actual .ico file for professional appearance")
        else:
            print(f"✅ Icon found: {icon_path}")
    
    def run_pyinstaller(self) -> bool:
        """Run PyInstaller to build the executable."""
        print("\n🔨 Building Windows executable...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(self.spec_path)
        ]
        
        print(f"🔧 Command: {' '.join(cmd)}")
        print("⏳ This may take several minutes...")
        
        try:
            # Change to project root for build
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print("✅ PyInstaller build successful!")
                return True
            else:
                print(f"❌ PyInstaller build failed!")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running PyInstaller: {e}")
            return False
    
    def optimize_executable(self):
        """Optimize the built executable."""
        print("\n⚡ Optimizing executable...")
        
        exe_path = self.dist_path / PROJECT_NAME / f"{PROJECT_NAME}.exe"
        
        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return
        
        # Get file size
        file_size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"📊 Executable size: {file_size_mb:.1f} MB")
        
        # Additional optimization suggestions
        print("\n💡 Optimization suggestions:")
        print("  • Consider excluding unused dependencies")
        print("  • Use UPX compression (already enabled)")
        print("  • Minimize asset file sizes")
        
        print("✅ Optimization complete!")
    
    def create_installer_script(self):
        """Create NSIS installer script."""
        print("\n📦 Creating installer script...")
        
        nsis_script = f'''
; LangExtractor Windows Installer Script
; Generated by build.py

!define APPNAME "{PROJECT_NAME}"
!define APPVERSION "{PROJECT_VERSION}"
!define APPEXE "${{APPNAME}}.exe"
!define APPDIR "$PROGRAMFILES\\${{APPNAME}}"

Name "${{APPNAME}} ${{APPVERSION}}"
OutFile "{PROJECT_NAME}-{PROJECT_VERSION}-Setup.exe"
InstallDir "${{APPDIR}}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR
    File /r "dist\\{PROJECT_NAME}\\*"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPEXE}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    
    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPEXE}}"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    ; Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayVersion" "${{APPVERSION}}"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\${{APPNAME}}\\*"
    RMDir "$SMPROGRAMS\\${{APPNAME}}"
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
SectionEnd
'''
        
        installer_script = self.packaging_dir / f'{PROJECT_NAME}.nsi'
        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(nsis_script)
        
        print(f"✅ NSIS installer script created: {installer_script}")
        print("ℹ️ Use NSIS to compile this script into a Windows installer")
    
    def test_executable(self) -> bool:
        """Test the built executable."""
        print("\n🧪 Testing executable...")
        
        exe_path = self.dist_path / PROJECT_NAME / f"{PROJECT_NAME}.exe"
        
        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return False
        
        print(f"📁 Executable location: {exe_path}")
        print("ℹ️ Manual testing required - launch the executable to verify functionality")
        print("  • Check GUI loads correctly")
        print("  • Verify Settings dialog works")
        print("  • Test document processing")
        print("  • Confirm Excel export")
        
        return True
    
    def generate_build_report(self):
        """Generate final build report."""
        build_time = time.time() - self.build_start_time
        
        print("\n" + "="*60)
        print("🎉 BUILD COMPLETE!")
        print("="*60)
        print(f"⏱️ Build time: {build_time:.1f} seconds")
        print(f"📦 Project: {PROJECT_NAME} v{PROJECT_VERSION}")
        
        exe_path = self.dist_path / PROJECT_NAME / f"{PROJECT_NAME}.exe"
        if exe_path.exists():
            file_size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📊 Executable size: {file_size_mb:.1f} MB")
            print(f"📁 Location: {exe_path}")
        
        print("\n🎯 Next Steps:")
        print("1. Test the executable manually")
        print("2. Compile NSIS installer (optional)")
        print("3. Distribute to users")
        print("="*60)
    
    def build(self):
        """Execute complete build process."""
        try:
            if not self.check_dependencies():
                return False
            
            self.clean_build_dirs()
            self.create_version_info()
            self.create_application_icon()
            
            if not self.run_pyinstaller():
                return False
            
            self.optimize_executable()
            self.create_installer_script()
            self.test_executable()
            self.generate_build_report()
            
            return True
            
        except Exception as e:
            print(f"❌ Build failed with error: {e}")
            return False


if __name__ == "__main__":
    print("🏗️ LangExtractor Windows Build Process Starting...")
    print()
    
    builder = BuildManager()
    success = builder.build()
    
    if success:
        print("✅ Build process completed successfully!")
        sys.exit(0)
    else:
        print("❌ Build process failed!")
        sys.exit(1) 