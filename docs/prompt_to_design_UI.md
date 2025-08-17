Prompt for AI Agent — Modern UI + Drag-and-Drop (PySide6)

Role: You are a senior PySide6/Qt UI engineer and UX designer.
Goal: Redesign the “LangExtractor GUI – MVP” (PySide6) to have a modern Windows-friendly theme (light/dark), polished components, and native drag-and-drop for importing files. Keep dependencies minimal (pure PySide6/Qt + current code). No internet resources or external theme frameworks.

Repo context (important):

Main entry: app/app.py

GUI: gui/main_window.py, gui/schema_editor.py, gui/settings_dialog.py

Core (don’t break signatures): core/…
The current widgets: QMainWindow, QListWidget, QPushButton, QComboBox, QCheckBox, QProgressDialog, dialogs.

Deliverables (must output all of these):

New theme system

QSS files:

assets/theme/light.qss

assets/theme/dark.qss

A small ThemeManager helper (gui/theme.py) to load QSS, apply design tokens, toggle light/dark, and support High-DPI.

Add a Theme switcher to the main window (a small toggle or menu) and persist user choice (use QSettings).

Drag-and-Drop UX

Make MainWindow (and the file list area) accept drops for .pdf, .docx, .xlsx, .xls.

Implement dragEnterEvent, dragMoveEvent, dropEvent, and a drop overlay (semi-transparent panel with dashed border and hint text).

Validate and de-duplicate dropped files; show a toast/snackbar or status hint for ignored duplicates.

Component polish

Buttons: rounded corners (8–12px), hover/pressed states, clear focus ring (accessible).

Lists/tables: alternating rows, subtle dividers, selected/hover states, file type icon per item (SVG in assets/icons/).

Inputs: consistent height (36–40px), padding, placeholder styling, error state.

Progress dialog: inline header with step label and determinate/indeterminate mode.

Spacing scale: 4/8/12/16/20/24 px; corner radius: 8/12 px; shadows only for overlays/menus.

Design tokens (use in QSS via comments/variables)

(Light)

--bg: #F7F7FB, --card: #FFFFFF, --text: #1A1A1E, --muted: #6B7280

--primary: #3B82F6, --primary-600: #2563EB

--success: #16A34A, --warning: #F59E0B, --danger: #EF4444

--border: #E5E7EB, --focus: #60A5FA

(Dark)

--bg: #0F1115, --card: #151922, --text: #E5E7EB, --muted: #9CA3AF

--primary: #60A5FA, --primary-600: #3B82F6

--success: #22C55E, --warning: #FBBF24, --danger: #F87171

--border: #273042, --focus: #93C5FD

Font: system default Segoe UI (Windows). Line height ~1.35.

Icon set

Add simple monochrome SVG icons (local files) in assets/icons/:

file-pdf.svg, file-docx.svg, file-xlsx.svg, trash.svg, add.svg, palette.svg, dropzone.svg.

Use QIcon from these SVGs; no network fetch.

Code changes

Modify gui/main_window.py to:

Install ThemeManager, add theme toggle, persist with QSettings.

Implement drag-and-drop with a DropOverlay QWidget.

Show icons in QListWidget items based on file extension.

Keep existing pipeline call sites intact (process_all, export_xlsx).

Optional minor polish for SchemaEditor/SettingsDialog to adopt theme and spacing (no logic changes).

Output format

Provide unified diffs (git patch) for modified files.

Provide full contents for new files (gui/theme.py, both QSS, SVGs as inline XML).

Short “How to test” steps.

Functional acceptance criteria:

Switching theme updates all visible widgets immediately and persists across app restarts.

Dragging valid files over main window shows a drop overlay; dropping adds them to the list with proper icons; duplicates are ignored with a toast/status message.

All controls have visible keyboard focus; contrast meets accessibility (WCAG-ish, no super-low contrast).

No new runtime dependency beyond PySide6/Qt. Works on Windows 10/11, High-DPI aware.

Implementation details & hints:

Enable drops: self.setAcceptDrops(True) in MainWindow.

Overlay: child QWidget with Qt.WA_TransparentForMouseEvents off; show/hide on drag events; paint dashed rounded rect and hint (“Thả file vào đây…”).

QSS scoping examples:

Buttons: QPushButton { border-radius: 8px; padding: 6px 12px; } QPushButton:focus { outline: none; border: 2px solid @focus; }

Inputs: QComboBox, QLineEdit { height: 36px; padding: 4px 8px; }

Lists: QListWidget::item { padding: 8px 10px; } QListWidget::item:selected { background: @primary-600; color: white; }

Provide a small ThemeManager.apply(app, theme_name) that loads QSS string, does token substitution (replace placeholders like @bg, @text, @primary), and sets QApplication.setStyleSheet(...).

Use QSettings("YourOrg","LangExtractor") to store theme=light|dark.

Keep code Python 3.11 compatible.

Now produce:

git diff patches for:

gui/main_window.py (theme toggle, drag-and-drop, icons, spacing tweaks)

(optional minimal style fixes in gui/schema_editor.py, gui/settings_dialog.py)

New files (full content):

gui/theme.py

assets/theme/light.qss

assets/theme/dark.qss

SVG icons listed above (inline XML)

A short “How to test” list.