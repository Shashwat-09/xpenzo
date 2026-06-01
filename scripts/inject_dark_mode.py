"""
Xpenz Dark Mode Injector
Adds dark mode CSS overrides + toggle button to all 47 mobile screen HTML files.
Uses CSS override approach (injected <style> block) rather than per-element class changes.
"""

from __future__ import annotations

import os
import glob

UI_DIR = r"c:\Shashwat\projects\Xpenzo\UI-UX"
ADMIN_DIR = os.path.join(UI_DIR, "admin")

DARK_CSS = r"""<style id="xpenz-dark-mode">
/* ===== XPENZ DARK MODE - Design System Tokens ===== */
/* BG Dark: #111521 | Card Dark: #1a1f30 | Sidebar Dark: #0d1117 */

html.dark body {
  background-color: #111521 !important;
  color: #e2e8f0 !important;
}

/* Main container overrides */
html.dark .bg-white { background-color: #1a1f30 !important; }
html.dark .bg-slate-50, html.dark .bg-gray-50 { background-color: #111521 !important; }
html.dark .bg-slate-100, html.dark .bg-gray-100 { background-color: #1e2536 !important; }
html.dark .bg-slate-200, html.dark .bg-gray-200 { background-color: #252d3f !important; }
html.dark .bg-background-light { background-color: #111521 !important; }
html.dark .bg-surface-light { background-color: #1a1f30 !important; }
html.dark .bg-card-light { background-color: #1a1f30 !important; }
html.dark .bg-\[\#ffffff\], html.dark .bg-\[\#FFFFFF\] { background-color: #1a1f30 !important; }
html.dark .bg-\[\#f8f6f6\], html.dark .bg-\[\#F7F6F3\], html.dark .bg-\[\#f6f6f8\] { background-color: #111521 !important; }
html.dark .bg-\[\#f5f5f5\], html.dark .bg-\[\#f9fafb\] { background-color: #111521 !important; }

/* White/near-white backgrounds on inner cards */
html.dark .bg-white\/80 { background-color: rgba(26, 31, 48, 0.9) !important; }
html.dark .bg-white\/90 { background-color: rgba(26, 31, 48, 0.95) !important; }

/* Text color overrides */
html.dark .text-black, html.dark .text-text-main, html.dark .text-\[\#000000\], html.dark .text-\[\#111\] {
  color: #f1f5f9 !important;
}
html.dark .text-slate-900, html.dark .text-gray-900 { color: #f1f5f9 !important; }
html.dark .text-slate-800, html.dark .text-gray-800 { color: #e2e8f0 !important; }
html.dark .text-slate-700, html.dark .text-gray-700 { color: #cbd5e1 !important; }
html.dark .text-slate-600, html.dark .text-gray-600, html.dark .text-text-muted { color: #94a3b8 !important; }
html.dark .text-slate-500, html.dark .text-gray-500 { color: #64748b !important; }
html.dark .text-slate-400, html.dark .text-gray-400 { color: #94a3b8 !important; }

/* Border overrides */
html.dark .border-slate-100, html.dark .border-gray-100 { border-color: #1e293b !important; }
html.dark .border-slate-200, html.dark .border-gray-200 { border-color: #334155 !important; }
html.dark .border-slate-300, html.dark .border-gray-300 { border-color: #475569 !important; }
html.dark .border-white { border-color: #1e293b !important; }

/* Divide overrides */
html.dark .divide-slate-100 > :not(:first-child) { border-color: #1e293b !important; }
html.dark .divide-slate-200 > :not(:first-child) { border-color: #334155 !important; }
html.dark .divide-gray-100 > :not(:first-child) { border-color: #1e293b !important; }
html.dark .divide-gray-200 > :not(:first-child) { border-color: #334155 !important; }

/* Shadow adjustments */
html.dark .shadow-sm, html.dark .shadow, html.dark .shadow-md, html.dark .shadow-lg, html.dark .shadow-xl, html.dark .shadow-2xl {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}
html.dark .shadow-none { box-shadow: none !important; }

/* Input/form overrides */
html.dark input, html.dark textarea, html.dark select {
  background-color: #1e2536 !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}
html.dark input::placeholder, html.dark textarea::placeholder {
  color: #64748b !important;
}
html.dark input:focus, html.dark textarea:focus, html.dark select:focus {
  border-color: #1b3fc0 !important;
  box-shadow: 0 0 0 2px rgba(27, 63, 192, 0.25) !important;
}

/* Backdrop blur */
html.dark .backdrop-blur-md { background-color: rgba(17, 21, 33, 0.85) !important; }
html.dark .backdrop-blur-lg { background-color: rgba(17, 21, 33, 0.9) !important; }

/* Ring overrides */
html.dark .ring-slate-100, html.dark .ring-gray-100 { --tw-ring-color: #1e293b !important; }
html.dark .ring-white { --tw-ring-color: #1a1f30 !important; }

/* Emerald/green accents preserved */
html.dark .bg-emerald-50, html.dark .bg-green-50 { background-color: rgba(16, 185, 129, 0.1) !important; }
html.dark .border-emerald-100, html.dark .border-green-100 { border-color: rgba(16, 185, 129, 0.2) !important; }
html.dark .bg-emerald-100, html.dark .bg-green-100 { background-color: rgba(16, 185, 129, 0.15) !important; }

/* Red/danger accents */
html.dark .bg-red-50 { background-color: rgba(239, 68, 68, 0.1) !important; }
html.dark .border-red-100 { border-color: rgba(239, 68, 68, 0.2) !important; }
html.dark .bg-red-100 { background-color: rgba(239, 68, 68, 0.15) !important; }

/* Amber/warning accents */
html.dark .bg-amber-50, html.dark .bg-yellow-50 { background-color: rgba(245, 158, 11, 0.1) !important; }
html.dark .border-amber-100 { border-color: rgba(245, 158, 11, 0.2) !important; }
html.dark .bg-amber-100, html.dark .bg-yellow-100 { background-color: rgba(245, 158, 11, 0.15) !important; }

/* Blue accents */
html.dark .bg-blue-50 { background-color: rgba(59, 130, 246, 0.1) !important; }
html.dark .border-blue-100 { border-color: rgba(59, 130, 246, 0.2) !important; }
html.dark .bg-blue-100 { background-color: rgba(59, 130, 246, 0.15) !important; }

/* Purple accents */
html.dark .bg-purple-50, html.dark .bg-violet-50 { background-color: rgba(139, 92, 246, 0.1) !important; }
html.dark .bg-purple-100, html.dark .bg-violet-100 { background-color: rgba(139, 92, 246, 0.15) !important; }

/* Indigo accents (used as primary in some screens) */
html.dark .bg-indigo-50 { background-color: rgba(99, 102, 241, 0.1) !important; }
html.dark .bg-indigo-100 { background-color: rgba(99, 102, 241, 0.15) !important; }

/* Primary-tinted backgrounds */
html.dark .bg-primary\/5, html.dark .bg-primary\/10 { background-color: rgba(27, 63, 192, 0.15) !important; }
html.dark .bg-primary { background-color: #1b3fc0 !important; }

/* Bottom nav / fixed bars */
html.dark nav, html.dark nav.fixed {
  background-color: #0d1117 !important;
  border-color: #1e293b !important;
}

/* Card/panel specific */
html.dark [class*="rounded"][class*="bg-white"],
html.dark [class*="rounded"][class*="bg-slate-50"],
html.dark [class*="rounded"][class*="bg-gray-50"] {
  background-color: #1a1f30 !important;
}

/* Modal / overlay */
html.dark .bg-black\/50, html.dark .bg-black\/40, html.dark .bg-black\/30 {
  background-color: rgba(0, 0, 0, 0.7) !important;
}

/* Gradient overrides */
html.dark .from-white { --tw-gradient-from: #1a1f30 !important; }
html.dark .to-white { --tw-gradient-to: #1a1f30 !important; }
html.dark .from-slate-50 { --tw-gradient-from: #111521 !important; }

/* Scrollbar styling */
html.dark ::-webkit-scrollbar-track { background: #111521; }
html.dark ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }

/* Hover states */
html.dark .hover\:bg-slate-100:hover, html.dark .hover\:bg-gray-100:hover { background-color: #252d3f !important; }
html.dark .hover\:bg-slate-50:hover, html.dark .hover\:bg-gray-50:hover { background-color: #1e2536 !important; }
html.dark .hover\:bg-white:hover { background-color: #1a1f30 !important; }

/* Active states */
html.dark .active\:bg-slate-100:active, html.dark .active\:bg-gray-100:active { background-color: #252d3f !important; }

/* Toggle / Switch backgrounds */
html.dark .bg-slate-300, html.dark .bg-gray-300 { background-color: #475569 !important; }

/* Status bar area */
html.dark .bg-\[\#1D40C0\], html.dark .bg-\[\#1d40bf\], html.dark .bg-\[\#4f46e5\] {
  background-color: #1b3fc0 !important;
}

/* Smooth transition for all color changes */
html.dark * {
  transition: background-color 0.2s ease, color 0.15s ease, border-color 0.2s ease;
}
</style>"""

TOGGLE_BTN = """<!-- Xpenz Dark Mode Toggle -->
<button onclick="document.documentElement.classList.toggle('dark'); localStorage.setItem('xpenz-dark', document.documentElement.classList.contains('dark')); updateDMToggle();"
  id="dm-toggle-btn"
  style="position:fixed;top:12px;right:12px;z-index:9999;width:36px;height:36px;border-radius:12px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(148,163,184,0.3);cursor:pointer;transition:all 0.2s;background:rgba(255,255,255,0.9);backdrop-filter:blur(8px);">
  <span class="material-symbols-outlined" style="font-size:18px;color:#64748b;" id="dm-icon">dark_mode</span>
</button>
<script>
  // Persist dark mode preference
  if (localStorage.getItem('xpenz-dark') === 'true') {
    document.documentElement.classList.add('dark');
  }
  function updateDMToggle() {
    var isDark = document.documentElement.classList.contains('dark');
    var btn = document.getElementById('dm-toggle-btn');
    var icon = document.getElementById('dm-icon');
    if (icon) icon.textContent = isDark ? 'light_mode' : 'dark_mode';
    if (btn) {
      btn.style.background = isDark ? 'rgba(26,31,48,0.9)' : 'rgba(255,255,255,0.9)';
      btn.style.borderColor = isDark ? 'rgba(51,65,85,0.5)' : 'rgba(148,163,184,0.3)';
    }
    if (icon) icon.style.color = isDark ? '#94a3b8' : '#64748b';
  }
  // Apply on load
  updateDMToggle();
</script>"""


def process_file(filepath: str) -> str:
    """Inject dark mode CSS and toggle into a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has dark mode
    if 'xpenz-dark-mode' in content:
        return 'skip'

    # Inject CSS before </head>
    if '</head>' in content:
        content = content.replace('</head>', DARK_CSS + '\n</head>', 1)
    elif '</HEAD>' in content:
        content = content.replace('</HEAD>', DARK_CSS + '\n</HEAD>', 1)
    else:
        # No </head> tag — inject at very top
        content = DARK_CSS + '\n' + content

    # Inject toggle + script before </body>
    if '</body>' in content:
        content = content.replace('</body>', TOGGLE_BTN + '\n</body>', 1)
    elif '</BODY>' in content:
        content = content.replace('</BODY>', TOGGLE_BTN + '\n</BODY>', 1)
    else:
        # No </body> tag — append at end
        content = content + '\n' + TOGGLE_BTN

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return 'ok'


def main() -> None:
    # Find all code.html files, excluding admin folder
    all_files: list[str] = glob.glob(os.path.join(UI_DIR, '*', 'code.html'))
    mobile_files = [f for f in all_files if not f.startswith(ADMIN_DIR)]
    mobile_files.sort()

    print(f"Found {len(mobile_files)} mobile screen HTML files\n")

    processed = 0
    skipped = 0
    errors: list[str] = []

    for filepath in mobile_files:
        folder_name = os.path.basename(os.path.dirname(filepath))
        try:
            result = process_file(filepath)
            if result == 'skip':
                skipped += 1
                print(f"  SKIP: {folder_name} (already has dark mode)")
            else:
                processed += 1
                print(f"  OK:   {folder_name}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{folder_name}: {e}")
            print(f"  ERR:  {folder_name} - {e}")

    print(f"\n{'='*50}")
    print(f"DARK MODE INJECTION COMPLETE")
    print(f"{'='*50}")
    print(f"Processed: {processed}")
    print(f"Skipped:   {skipped}")
    print(f"Errors:    {len(errors)}")
    if errors:
        for e in errors:
            print(f"  - {e}")


if __name__ == '__main__':
    main()
