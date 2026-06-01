# Dark Mode Injector for Xpenzo Mobile UI Screens
# Adds dark mode CSS overrides + toggle button to all 47 mobile screen HTML files

$uiDir = "c:\Shashwat\projects\Xpenzo\UI-UX"
$adminDir = Join-Path $uiDir "admin"

# Dark mode CSS block - comprehensive overrides matching the Xpenz design system
$darkCSS = @'
<style id="xpenz-dark-mode">
/* ===== XPENZ DARK MODE — Design System Tokens ===== */
/* BG Dark: #111521 | Card Dark: #1a1f30 | Sidebar Dark: #0d1117 */
/* Matches the admin dashboard design system for visual coherence */

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

/* Border overrides */
html.dark .border-slate-100, html.dark .border-gray-100 { border-color: #1e293b !important; }
html.dark .border-slate-200, html.dark .border-gray-200 { border-color: #334155 !important; }
html.dark .border-slate-300, html.dark .border-gray-300 { border-color: #475569 !important; }
html.dark .border-white { border-color: #1e293b !important; }

/* Divide overrides */
html.dark .divide-slate-100 > :not(:first-child) { border-color: #1e293b !important; }
html.dark .divide-slate-200 > :not(:first-child) { border-color: #334155 !important; }

/* Shadow adjustments */
html.dark .shadow-sm, html.dark .shadow, html.dark .shadow-md, html.dark .shadow-lg, html.dark .shadow-xl, html.dark .shadow-2xl {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

/* Input/form overrides */
html.dark input, html.dark textarea, html.dark select {
  background-color: #1e2536 !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}
html.dark input::placeholder, html.dark textarea::placeholder {
  color: #64748b !important;
}

/* Backdrop blur */
html.dark .backdrop-blur-md { background-color: rgba(17, 21, 33, 0.85) !important; }
html.dark .backdrop-blur-lg { background-color: rgba(17, 21, 33, 0.9) !important; }

/* Ring overrides */
html.dark .ring-slate-100, html.dark .ring-gray-100 { --tw-ring-color: #1e293b !important; }

/* Emerald/green accents preserved */
html.dark .bg-emerald-50, html.dark .bg-green-50 { background-color: rgba(16, 185, 129, 0.1) !important; }
html.dark .border-emerald-100, html.dark .border-green-100 { border-color: rgba(16, 185, 129, 0.2) !important; }

/* Red/danger accents */
html.dark .bg-red-50 { background-color: rgba(239, 68, 68, 0.1) !important; }
html.dark .border-red-100 { border-color: rgba(239, 68, 68, 0.2) !important; }

/* Amber/warning accents */
html.dark .bg-amber-50, html.dark .bg-yellow-50 { background-color: rgba(245, 158, 11, 0.1) !important; }
html.dark .border-amber-100 { border-color: rgba(245, 158, 11, 0.2) !important; }

/* Purple accents */
html.dark .bg-purple-50, html.dark .bg-violet-50 { background-color: rgba(139, 92, 246, 0.1) !important; }

/* Primary-tinted backgrounds */
html.dark .bg-primary\/5, html.dark .bg-primary\/10 { background-color: rgba(27, 63, 192, 0.15) !important; }

/* Bottom nav / fixed bars */
html.dark nav.fixed, html.dark .fixed.bottom-0, html.dark [class*="bottom-nav"] {
  background-color: #0d1117 !important;
  border-color: #1e293b !important;
}

/* Scrollbar styling */
html.dark ::-webkit-scrollbar-track { background: #111521; }
html.dark ::-webkit-scrollbar-thumb { background: #334155; }

/* Progress bars & charts keep their brand colors — no override needed */

/* SVG and icon adjustments */
html.dark svg text { fill: #94a3b8; }

/* Hover states */
html.dark .hover\:bg-slate-100:hover, html.dark .hover\:bg-gray-100:hover { background-color: #252d3f !important; }
html.dark .hover\:bg-slate-50:hover, html.dark .hover\:bg-gray-50:hover { background-color: #1e2536 !important; }
</style>
'@

# Dark mode toggle button HTML
$toggleBtn = @'
<!-- Dark Mode Toggle -->
<button onclick="document.documentElement.classList.toggle('dark'); localStorage.setItem('xpenz-dark', document.documentElement.classList.contains('dark'))" 
  style="position:fixed;top:12px;right:12px;z-index:9999;width:36px;height:36px;border-radius:12px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(148,163,184,0.3);cursor:pointer;transition:all 0.2s;background:rgba(255,255,255,0.9);backdrop-filter:blur(8px);"
  onmouseover="this.style.background='rgba(241,245,249,1)'" onmouseout="this.style.background='rgba(255,255,255,0.9)'">
  <span class="material-symbols-outlined" style="font-size:18px;color:#64748b;" id="dm-icon">dark_mode</span>
</button>
<script>
  // Persist dark mode preference
  if (localStorage.getItem('xpenz-dark') === 'true') {
    document.documentElement.classList.add('dark');
  }
  // Update toggle button appearance in dark mode
  const observer = new MutationObserver(() => {
    const isDark = document.documentElement.classList.contains('dark');
    const btn = document.querySelector('[onclick*="xpenz-dark"]');
    const icon = document.getElementById('dm-icon');
    if (btn && icon) {
      icon.textContent = isDark ? 'light_mode' : 'dark_mode';
      btn.style.background = isDark ? 'rgba(26,31,48,0.9)' : 'rgba(255,255,255,0.9)';
      btn.style.borderColor = isDark ? 'rgba(51,65,85,0.5)' : 'rgba(148,163,184,0.3)';
      icon.style.color = isDark ? '#94a3b8' : '#64748b';
    }
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  // Trigger initial state
  setTimeout(() => observer.takeRecords(), 50);
  if (document.documentElement.classList.contains('dark')) {
    const icon = document.getElementById('dm-icon');
    const btn = document.querySelector('[onclick*="xpenz-dark"]');
    if (icon) icon.textContent = 'light_mode';
    if (btn) { btn.style.background = 'rgba(26,31,48,0.9)'; btn.style.borderColor = 'rgba(51,65,85,0.5)'; }
    if (icon) icon.style.color = '#94a3b8';
  }
</script>
'@

# Get all mobile screen HTML files (exclude admin folder)
$files = Get-ChildItem -Path $uiDir -Filter "code.html" -Recurse | 
  Where-Object { $_.FullName -notlike "*\admin\*" }

$processed = 0
$skipped = 0
$errors = @()

foreach ($file in $files) {
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        
        # Skip if already has dark mode injected
        if ($content -match "xpenz-dark-mode") {
            $skipped++
            Write-Host "  SKIP: $($file.Directory.Name) (already has dark mode)" -ForegroundColor Yellow
            continue
        }
        
        # Inject dark CSS before </head>
        $content = $content -replace '</head>', "$darkCSS`n</head>"
        
        # Inject toggle button before </body>
        $content = $content -replace '</body>', "$toggleBtn`n</body>"
        
        # Write back
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        
        $processed++
        Write-Host "  OK: $($file.Directory.Name)" -ForegroundColor Green
    }
    catch {
        $errors += "$($file.Directory.Name): $($_.Exception.Message)"
        Write-Host "  ERR: $($file.Directory.Name) — $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n===== DARK MODE INJECTION COMPLETE =====" -ForegroundColor Cyan
Write-Host "Processed: $processed" -ForegroundColor Green
Write-Host "Skipped:   $skipped" -ForegroundColor Yellow
$errColor = if ($errors.Count -gt 0) { "Red" } else { "Green" }
Write-Host "Errors:    $($errors.Count)" -ForegroundColor $errColor
if ($errors.Count -gt 0) {
    foreach ($e in $errors) { Write-Host "  - $e" -ForegroundColor Red }
}
