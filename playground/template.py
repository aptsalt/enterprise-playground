"""
Playground Template Framework
==============================
Provides the control panel, preview shell, and variation system.
The LLM generates ONLY the inner page content (nav, hero, sections, cards, footer).
This template wraps it with the full interactive playground framework.

Features:
  - Fixed 320px left control panel (dark theme)
  - Quick presets: Current TD, Modern, Minimal, Bold, Dark Mode, Corporate
  - Brand color pickers (primary, accent, background, text)
  - Hero layout toggles (Default, Centered, Split, Minimal) + height slider
  - Card style (Elevated, Bordered, Filled, Horizontal) + columns + border radius
  - Typography (System, Modern, Classic)
  - CTA/Button style (Rounded, Square, Pill)
  - Spacing (Compact, Default, Spacious)
  - Tools: Annotations, A/B Compare, Export CSS, Reset
  - Change log
  - Preview toolbar: Device switcher (Desktop/Tablet/Mobile) + Zoom
"""


def wrap_in_playground(content_html: str, title: str = "TD Bank UI/UX Playground") -> str:
    """
    Wrap LLM-generated content HTML inside the full playground framework.

    Args:
        content_html: The inner page content (nav, hero, sections, cards, footer).
                      Should use CSS classes: td-nav, td-hero, hero-content, product-grid,
                      product-card, promo-card, life-stage-card, cta-strip, td-footer, etc.
        title: The playground page title.

    Returns:
        Complete self-contained HTML string with control panel + preview area.
    """
    return TEMPLATE_HEAD + content_html + TEMPLATE_TAIL


# ══════════════════════════════════════════════════════════════════
# Template parts — split so we can inject content between them
# ══════════════════════════════════════════════════════════════════

TEMPLATE_HEAD = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TD Bank UI/UX Playground</title>
<style>
/* ========== PLAYGROUND FRAMEWORK ========== */
:root {
  --td-green: #1a5336;
  --td-green-light: #2d8659;
  --td-green-pale: #e8f5e9;
  --td-dark: #1d1d1d;
  --td-gray: #6b6b6b;
  --td-light-gray: #f5f5f5;
  --td-white: #ffffff;
  --td-accent: #008a4b;
  --td-blue: #0066cc;
  --td-red: #d32f2f;
  --border-radius: 8px;
  --shadow: 0 2px 8px rgba(0,0,0,0.1);
  --shadow-lg: 0 4px 20px rgba(0,0,0,0.15);
  --font-primary: 'Segoe UI', system-ui, -apple-system, sans-serif;
  --hero-height: 420px;
  --nav-height: 64px;
  --card-columns: 4;
  --cta-radius: 24px;
  --section-padding: 60px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: var(--font-primary); background: #f0f2f5; overflow-x: hidden; }

/* ========== CONTROL PANEL ========== */
#control-panel {
  position: fixed; top: 0; left: 0; width: 320px; height: 100vh;
  background: #1a1a2e; color: #e0e0e0; z-index: 1000;
  overflow-y: auto; box-shadow: 4px 0 20px rgba(0,0,0,0.3);
  transition: transform 0.3s ease;
  scrollbar-width: thin; scrollbar-color: #444 #1a1a2e;
}
#control-panel.collapsed { transform: translateX(-320px); }
#control-panel h2 {
  padding: 20px; background: linear-gradient(135deg, #16213e, #0f3460);
  font-size: 16px; letter-spacing: 0.5px; position: sticky; top: 0; z-index: 2;
  display: flex; align-items: center; justify-content: space-between;
}
#control-panel h2 span { opacity: 0.6; font-size: 11px; font-weight: 400; }
.panel-section {
  border-bottom: 1px solid rgba(255,255,255,0.06); padding: 16px 20px;
}
.panel-section h3 {
  font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px;
  color: #7f8fa6; margin-bottom: 12px; font-weight: 600;
}
.control-row {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;
}
.control-row label { font-size: 13px; color: #b0b0b0; }
input[type="color"] {
  width: 36px; height: 28px; border: 2px solid #333;
  border-radius: 4px; cursor: pointer; background: none;
}
input[type="range"] { width: 120px; accent-color: #4ecca3; }
select {
  background: #2a2a3e; color: #e0e0e0; border: 1px solid #444;
  padding: 6px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;
}
.toggle-btn-group { display: flex; gap: 4px; }
.toggle-btn {
  padding: 5px 10px; font-size: 11px; border: 1px solid #444;
  background: #2a2a3e; color: #aaa; border-radius: 4px; cursor: pointer; transition: all 0.2s;
}
.toggle-btn.active {
  background: #4ecca3; color: #1a1a2e; border-color: #4ecca3; font-weight: 600;
}
.preset-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.preset-card {
  padding: 10px; background: #2a2a3e; border: 1px solid #444;
  border-radius: 6px; cursor: pointer; text-align: center;
  transition: all 0.2s; font-size: 12px;
}
.preset-card:hover { border-color: #4ecca3; background: #333; }
.preset-card.active { border-color: #4ecca3; background: rgba(78,204,163,0.15); }
.preset-card .preset-icon { font-size: 22px; margin-bottom: 4px; }
.preset-card .preset-name { font-weight: 600; }
#toggle-panel {
  position: fixed; top: 12px; left: 12px; z-index: 1001;
  width: 40px; height: 40px; border-radius: 8px;
  background: #1a1a2e; color: #4ecca3; border: 1px solid #333;
  cursor: pointer; font-size: 18px; display: none;
  align-items: center; justify-content: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}
#control-panel.collapsed ~ #toggle-panel { display: flex; }

/* ========== PREVIEW AREA ========== */
#preview-area {
  margin-left: 320px; min-height: 100vh; transition: margin-left 0.3s ease;
}
#control-panel.collapsed ~ #preview-area { margin-left: 0; }
.preview-toolbar {
  background: #fff; padding: 10px 24px; display: flex;
  align-items: center; justify-content: space-between;
  border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 100;
}
.preview-toolbar .device-switcher { display: flex; gap: 6px; }
.preview-toolbar button {
  padding: 6px 14px; border: 1px solid #ddd; background: #fff;
  border-radius: 6px; cursor: pointer; font-size: 12px; transition: all 0.2s;
}
.preview-toolbar button.active { background: var(--td-green); color: #fff; border-color: var(--td-green); }
.preview-toolbar .zoom-control { display: flex; align-items: center; gap: 8px; font-size: 13px; }
#preview-frame {
  margin: 24px auto; background: #fff; box-shadow: var(--shadow-lg);
  transition: all 0.4s ease; overflow: hidden; border-radius: 8px;
  transform-origin: top center;
}
#preview-frame.desktop { width: 100%; max-width: 1280px; }
#preview-frame.tablet { width: 768px; }
#preview-frame.mobile { width: 375px; border-radius: 24px; }

/* ========== TD BANK PAGE STYLES ========== */
.td-nav {
  height: var(--nav-height); background: var(--td-green);
  display: flex; align-items: center; padding: 0 40px;
  justify-content: space-between; position: relative;
}
.td-nav .logo { font-size: 28px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }
.td-nav .logo span { color: #7fdb98; }
.td-nav-links { display: flex; gap: 24px; list-style: none; }
.td-nav-links a {
  color: rgba(255,255,255,0.9); text-decoration: none; font-size: 14px;
  font-weight: 500; padding: 8px 0; border-bottom: 2px solid transparent; transition: all 0.2s;
}
.td-nav-links a:hover { color: #fff; border-bottom-color: #7fdb98; }
.td-nav-actions { display: flex; gap: 12px; align-items: center; }
.td-nav-actions .btn-login {
  padding: 8px 20px; border-radius: var(--cta-radius);
  border: 1.5px solid rgba(255,255,255,0.6); background: transparent;
  color: #fff; font-size: 13px; cursor: pointer; transition: all 0.2s;
}
.td-nav-actions .btn-login:hover { background: rgba(255,255,255,0.15); }
.td-hero {
  height: var(--hero-height); background: linear-gradient(135deg, var(--td-green) 0%, #0d7a3e 50%, #2d8659 100%);
  display: flex; align-items: center; padding: 0 60px; position: relative; overflow: hidden;
}
.td-hero::after {
  content: ''; position: absolute; right: -40px; top: -40px;
  width: 500px; height: 500px; border-radius: 50%; background: rgba(255,255,255,0.04);
}
.td-hero::before {
  content: ''; position: absolute; right: 100px; bottom: -100px;
  width: 300px; height: 300px; border-radius: 50%; background: rgba(255,255,255,0.03);
}
.hero-content { max-width: 560px; position: relative; z-index: 1; }
.hero-content h1 { font-size: 42px; color: #fff; line-height: 1.15; margin-bottom: 16px; font-weight: 700; }
.hero-content p { font-size: 17px; color: rgba(255,255,255,0.85); line-height: 1.6; margin-bottom: 28px; }
.hero-content .btn-hero {
  padding: 14px 32px; background: #fff; color: var(--td-green);
  border: none; border-radius: var(--cta-radius); font-size: 15px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}
.hero-content .btn-hero:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.2); }
.td-section { padding: var(--section-padding) 40px; }
.td-section.alt-bg { background: var(--td-light-gray); }
.section-header { text-align: center; margin-bottom: 40px; }
.section-header h2 { font-size: 32px; color: var(--td-dark); margin-bottom: 12px; font-weight: 700; }
.section-header p { font-size: 16px; color: var(--td-gray); max-width: 600px; margin: 0 auto; }
.product-grid {
  display: grid; grid-template-columns: repeat(var(--card-columns), 1fr);
  gap: 20px; max-width: 1200px; margin: 0 auto;
}
.product-card {
  background: var(--td-white); border-radius: var(--border-radius);
  padding: 28px 24px; box-shadow: var(--shadow); transition: all 0.25s;
  border: 1px solid rgba(0,0,0,0.06); cursor: pointer; position: relative; overflow: hidden;
}
.product-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 3px; background: var(--td-accent); transform: scaleX(0);
  transition: transform 0.3s; transform-origin: left;
}
.product-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.product-card:hover::before { transform: scaleX(1); }
.product-card .card-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: var(--td-green-pale); display: flex;
  align-items: center; justify-content: center; font-size: 22px; margin-bottom: 16px;
}
.product-card h3 { font-size: 17px; margin-bottom: 8px; color: var(--td-dark); }
.product-card p { font-size: 13px; color: var(--td-gray); line-height: 1.5; }
.product-card .card-link {
  display: inline-block; margin-top: 14px; color: var(--td-accent);
  font-size: 13px; font-weight: 600; text-decoration: none;
}
.promo-banner {
  max-width: 1200px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
}
.promo-card {
  border-radius: var(--border-radius); padding: 36px;
  position: relative; overflow: hidden; color: #fff;
  min-height: 200px; display: flex; flex-direction: column; justify-content: center;
}
.promo-card.green-bg { background: linear-gradient(135deg, #1a5336, #2d8659); }
.promo-card.dark-bg { background: linear-gradient(135deg, #1d1d1d, #333); }
.promo-card h3 { font-size: 24px; margin-bottom: 10px; }
.promo-card p { font-size: 14px; opacity: 0.85; margin-bottom: 20px; }
.promo-card .btn-promo {
  padding: 10px 24px; background: #fff; color: var(--td-dark);
  border: none; border-radius: var(--cta-radius); font-size: 13px;
  font-weight: 600; cursor: pointer; width: fit-content;
}
.life-stage-grid {
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px;
  max-width: 1200px; margin: 0 auto;
}
.life-stage-card {
  border-radius: var(--border-radius); overflow: hidden;
  background: #fff; box-shadow: var(--shadow); transition: all 0.25s;
}
.life-stage-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.life-stage-card .stage-img {
  height: 180px; background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  display: flex; align-items: center; justify-content: center; font-size: 48px;
}
.life-stage-card .stage-content { padding: 24px; }
.life-stage-card h3 { font-size: 18px; margin-bottom: 8px; color: var(--td-dark); }
.life-stage-card p { font-size: 13px; color: var(--td-gray); line-height: 1.5; margin-bottom: 16px; }
.life-stage-card .btn-stage {
  color: var(--td-accent); font-size: 13px; font-weight: 600;
  text-decoration: none; cursor: pointer; background: none; border: none;
}
.cta-strip { background: var(--td-green); padding: 48px 40px; text-align: center; }
.cta-strip h2 { color: #fff; font-size: 28px; margin-bottom: 12px; }
.cta-strip p { color: rgba(255,255,255,0.8); margin-bottom: 24px; font-size: 15px; }
.cta-strip .btn-cta {
  padding: 14px 36px; background: #fff; color: var(--td-green);
  border: none; border-radius: var(--cta-radius); font-size: 15px; font-weight: 600; cursor: pointer;
}
.td-footer { background: #1d1d1d; color: #aaa; padding: 48px 40px 24px; }
.footer-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px;
  max-width: 1200px; margin: 0 auto 32px;
}
.footer-col h4 { color: #fff; font-size: 14px; margin-bottom: 16px; }
.footer-col a {
  display: block; color: #aaa; text-decoration: none;
  font-size: 13px; margin-bottom: 8px; transition: color 0.2s;
}
.footer-col a:hover { color: #4ecca3; }
.footer-bottom {
  border-top: 1px solid #333; padding-top: 20px;
  text-align: center; font-size: 12px; color: #666;
}

/* ========== FORM COMPONENTS ========== */
.td-form-section { max-width: 640px; margin: 0 auto; }
.td-form-group { margin-bottom: 20px; }
.td-form-group label {
  display: block; font-size: 14px; font-weight: 600;
  color: var(--td-dark); margin-bottom: 6px;
}
.td-form-group input,
.td-form-group select,
.td-form-group textarea {
  width: 100%; padding: 12px 16px; border: 1px solid #ccc;
  border-radius: var(--border-radius); font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.td-form-group input:focus,
.td-form-group select:focus,
.td-form-group textarea:focus {
  outline: none; border-color: var(--td-accent);
  box-shadow: 0 0 0 3px rgba(0,138,75,0.12);
}
.td-btn-primary {
  padding: 12px 28px; background: var(--td-accent); color: #fff;
  border: none; border-radius: var(--cta-radius); font-size: 15px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.td-btn-primary:hover { background: var(--td-green); }
.td-btn-secondary {
  padding: 12px 28px; background: transparent; color: var(--td-accent);
  border: 2px solid var(--td-accent); border-radius: var(--cta-radius);
  font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.td-btn-secondary:hover { background: var(--td-green-pale); }

/* Step indicator */
.td-steps { display: flex; justify-content: center; gap: 0; margin-bottom: 40px; }
.td-step {
  display: flex; align-items: center; font-size: 13px; color: var(--td-gray);
}
.td-step .step-num {
  width: 32px; height: 32px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; font-weight: 700;
  margin-right: 8px; background: #e0e0e0; color: #999; font-size: 14px;
  transition: all 0.3s;
}
.td-step.active .step-num { background: var(--td-accent); color: #fff; }
.td-step.completed .step-num { background: var(--td-green); color: #fff; }
.td-step-connector {
  width: 60px; height: 2px; background: #e0e0e0; margin: 0 8px;
}
.td-step.completed + .td-step-connector { background: var(--td-green); }

/* Tabs */
.td-tabs { display: flex; border-bottom: 2px solid #e0e0e0; margin-bottom: 24px; }
.td-tab {
  padding: 12px 24px; font-size: 14px; font-weight: 600; color: var(--td-gray);
  border: none; background: none; cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all 0.2s;
}
.td-tab:hover { color: var(--td-dark); }
.td-tab.active { color: var(--td-accent); border-bottom-color: var(--td-accent); }

/* Accordion */
.td-accordion { border: 1px solid #e0e0e0; border-radius: var(--border-radius); overflow: hidden; margin-bottom: 8px; }
.td-accordion-header {
  padding: 16px 20px; background: #fafafa; cursor: pointer;
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 600; font-size: 15px; color: var(--td-dark); transition: background 0.2s;
}
.td-accordion-header:hover { background: #f0f0f0; }
.td-accordion-body { padding: 16px 20px; display: none; color: var(--td-gray); line-height: 1.6; }
.td-accordion.open .td-accordion-body { display: block; }
.td-accordion.open .td-accordion-header { background: var(--td-green-pale); }

/* Table */
.td-table { width: 100%; border-collapse: collapse; }
.td-table th {
  padding: 12px 16px; text-align: left; font-size: 13px; font-weight: 600;
  color: var(--td-gray); background: #fafafa; border-bottom: 2px solid #e0e0e0;
}
.td-table td {
  padding: 12px 16px; font-size: 14px; border-bottom: 1px solid #f0f0f0;
}
.td-table tr:hover td { background: var(--td-green-pale); }

/* Badge */
.td-badge {
  display: inline-block; padding: 4px 10px; border-radius: 12px;
  font-size: 11px; font-weight: 600;
}
.td-badge-green { background: #e8f5e9; color: #1a5336; }
.td-badge-blue { background: #e3f2fd; color: #0d47a1; }
.td-badge-orange { background: #fff3e0; color: #e65100; }
.td-badge-red { background: #fce4ec; color: #c62828; }

/* ========== VARIATION CLASSES ========== */
.layout-centered .td-hero { text-align: center; justify-content: center; }
.layout-centered .hero-content { text-align: center; max-width: 700px; }
.layout-split .td-hero { display: grid; grid-template-columns: 1fr 1fr; }
.layout-split .hero-visual {
  display: flex; align-items: center; justify-content: center; font-size: 80px; opacity: 0.3;
}
.layout-minimal .td-hero { height: 280px; }
.layout-minimal .hero-content h1 { font-size: 32px; }
.cards-horizontal .product-card { display: flex; gap: 16px; align-items: flex-start; }
.cards-bordered .product-card { border: 2px solid #e0e0e0; box-shadow: none; }
.cards-bordered .product-card:hover { border-color: var(--td-accent); }
.cards-filled .product-card { background: var(--td-green-pale); border: none; }
.theme-dark { background: #121212; }
.theme-dark .td-section { background: #121212; }
.theme-dark .td-section.alt-bg { background: #1e1e1e; }
.theme-dark .section-header h2 { color: #e0e0e0; }
.theme-dark .section-header p { color: #888; }
.theme-dark .product-card { background: #1e1e1e; border-color: #333; }
.theme-dark .product-card h3 { color: #e0e0e0; }
.theme-dark .product-card p { color: #888; }
.theme-dark .life-stage-card { background: #1e1e1e; }
.theme-dark .life-stage-card h3 { color: #e0e0e0; }
.theme-dark .life-stage-card p { color: #888; }
.theme-dark .td-nav { background: #0d2818; }
.theme-dark .td-hero { background: linear-gradient(135deg, #0d2818, #1a5336); }
.theme-dark .td-form-group label { color: #e0e0e0; }
.theme-dark .td-form-group input,
.theme-dark .td-form-group select { background: #2a2a2a; color: #e0e0e0; border-color: #444; }
.theme-dark .td-accordion-header { background: #1e1e1e; color: #e0e0e0; }
.theme-dark .td-table th { background: #1e1e1e; color: #aaa; }
.theme-dark .td-table td { border-color: #333; color: #ccc; }
.cta-square .btn-hero,
.cta-square .btn-promo,
.cta-square .btn-cta,
.cta-square .btn-login,
.cta-square .td-btn-primary,
.cta-square .td-btn-secondary { border-radius: 4px !important; }
.cta-pill .btn-hero,
.cta-pill .btn-promo,
.cta-pill .btn-cta,
.cta-pill .btn-login,
.cta-pill .td-btn-primary,
.cta-pill .td-btn-secondary { border-radius: 50px !important; }
.spacing-compact .td-section { padding: 32px 40px; }
.spacing-compact .product-grid { gap: 12px; }
.spacing-compact .product-card { padding: 18px 16px; }
.spacing-spacious .td-section { padding: 80px 40px; }
.spacing-spacious .product-grid { gap: 28px; }
.spacing-spacious .product-card { padding: 36px 32px; }
.typo-modern h1, .typo-modern h2, .typo-modern h3 { font-weight: 800; letter-spacing: -0.5px; }
.typo-classic { font-family: Georgia, 'Times New Roman', serif; }
.typo-classic h1, .typo-classic h2, .typo-classic h3 { font-family: Georgia, serif; }

/* Annotation overlay */
.annotation-mode .product-card,
.annotation-mode .td-hero,
.annotation-mode .td-nav,
.annotation-mode .promo-card,
.annotation-mode .life-stage-card,
.annotation-mode .cta-strip,
.annotation-mode .td-footer,
.annotation-mode .td-form-section,
.annotation-mode .td-tabs,
.annotation-mode .td-accordion {
  outline: 2px dashed rgba(78,204,163,0.5); outline-offset: 2px; position: relative;
}
.annotation-mode *[data-label]::after {
  content: attr(data-label);
  position: absolute; top: 4px; right: 4px;
  background: #4ecca3; color: #1a1a2e; font-size: 10px;
  padding: 2px 8px; border-radius: 3px; font-weight: 600; z-index: 10;
}

/* A/B Labels */
.ab-label {
  position: absolute; top: 12px; left: 12px; z-index: 100;
  padding: 4px 14px; border-radius: 4px; font-size: 13px; font-weight: 700;
}
.ab-label.a { background: #4ecca3; color: #1a1a2e; }
.ab-label.b { background: #e94560; color: #fff; }
</style>
</head>
<body>

<!-- CONTROL PANEL -->
<div id="control-panel">
  <h2>TD UI/UX Playground <span>v2.0</span></h2>

  <!-- PRESETS -->
  <div class="panel-section">
    <h3>Quick Presets</h3>
    <div class="preset-grid">
      <div class="preset-card active" onclick="applyPreset('default')">
        <div class="preset-icon">&#9679;</div>
        <div class="preset-name">Current TD</div>
      </div>
      <div class="preset-card" onclick="applyPreset('modern')">
        <div class="preset-icon">&#9670;</div>
        <div class="preset-name">Modern</div>
      </div>
      <div class="preset-card" onclick="applyPreset('minimal')">
        <div class="preset-icon">&#9644;</div>
        <div class="preset-name">Minimal</div>
      </div>
      <div class="preset-card" onclick="applyPreset('bold')">
        <div class="preset-icon">&#9608;</div>
        <div class="preset-name">Bold</div>
      </div>
      <div class="preset-card" onclick="applyPreset('dark')">
        <div class="preset-icon">&#9790;</div>
        <div class="preset-name">Dark Mode</div>
      </div>
      <div class="preset-card" onclick="applyPreset('corporate')">
        <div class="preset-icon">&#9636;</div>
        <div class="preset-name">Corporate</div>
      </div>
    </div>
  </div>

  <!-- COLORS -->
  <div class="panel-section">
    <h3>Brand Colors</h3>
    <div class="control-row">
      <label>Primary Green</label>
      <input type="color" id="color-primary" value="#1a5336" onchange="updateColor('--td-green', this.value)">
    </div>
    <div class="control-row">
      <label>Accent</label>
      <input type="color" id="color-accent" value="#008a4b" onchange="updateColor('--td-accent', this.value)">
    </div>
    <div class="control-row">
      <label>Background</label>
      <input type="color" id="color-bg" value="#f5f5f5" onchange="updateColor('--td-light-gray', this.value)">
    </div>
    <div class="control-row">
      <label>Text</label>
      <input type="color" id="color-text" value="#1d1d1d" onchange="updateColor('--td-dark', this.value)">
    </div>
  </div>

  <!-- LAYOUT -->
  <div class="panel-section">
    <h3>Hero Layout</h3>
    <div class="toggle-btn-group">
      <button class="toggle-btn active" onclick="setLayout('default', this)">Default</button>
      <button class="toggle-btn" onclick="setLayout('centered', this)">Centered</button>
      <button class="toggle-btn" onclick="setLayout('split', this)">Split</button>
      <button class="toggle-btn" onclick="setLayout('minimal', this)">Minimal</button>
    </div>
    <div style="margin-top: 14px">
      <div class="control-row">
        <label>Hero Height</label>
        <input type="range" min="250" max="600" value="420" oninput="updateVar('--hero-height', this.value + 'px')">
      </div>
    </div>
  </div>

  <!-- CARDS -->
  <div class="panel-section">
    <h3>Card Style</h3>
    <div class="toggle-btn-group">
      <button class="toggle-btn active" onclick="setCardStyle('default', this)">Elevated</button>
      <button class="toggle-btn" onclick="setCardStyle('bordered', this)">Bordered</button>
      <button class="toggle-btn" onclick="setCardStyle('filled', this)">Filled</button>
      <button class="toggle-btn" onclick="setCardStyle('horizontal', this)">Horizontal</button>
    </div>
    <div style="margin-top: 14px">
      <div class="control-row">
        <label>Columns</label>
        <div class="toggle-btn-group">
          <button class="toggle-btn" onclick="setCols(2, this)">2</button>
          <button class="toggle-btn" onclick="setCols(3, this)">3</button>
          <button class="toggle-btn active" onclick="setCols(4, this)">4</button>
        </div>
      </div>
      <div class="control-row">
        <label>Border Radius</label>
        <input type="range" min="0" max="24" value="8" oninput="updateVar('--border-radius', this.value + 'px')">
      </div>
    </div>
  </div>

  <!-- TYPOGRAPHY -->
  <div class="panel-section">
    <h3>Typography</h3>
    <div class="toggle-btn-group">
      <button class="toggle-btn active" onclick="setTypo('default', this)">System</button>
      <button class="toggle-btn" onclick="setTypo('modern', this)">Modern</button>
      <button class="toggle-btn" onclick="setTypo('classic', this)">Classic</button>
    </div>
  </div>

  <!-- CTA STYLE -->
  <div class="panel-section">
    <h3>CTA / Button Style</h3>
    <div class="toggle-btn-group">
      <button class="toggle-btn active" onclick="setCtaStyle('default', this)">Rounded</button>
      <button class="toggle-btn" onclick="setCtaStyle('square', this)">Square</button>
      <button class="toggle-btn" onclick="setCtaStyle('pill', this)">Pill</button>
    </div>
  </div>

  <!-- SPACING -->
  <div class="panel-section">
    <h3>Spacing</h3>
    <div class="toggle-btn-group">
      <button class="toggle-btn" onclick="setSpacing('compact', this)">Compact</button>
      <button class="toggle-btn active" onclick="setSpacing('default', this)">Default</button>
      <button class="toggle-btn" onclick="setSpacing('spacious', this)">Spacious</button>
    </div>
  </div>

  <!-- TOOLS -->
  <div class="panel-section">
    <h3>Tools</h3>
    <div class="control-row">
      <label>Annotations</label>
      <button class="toggle-btn" onclick="toggleAnnotations(this)">Off</button>
    </div>
    <div class="control-row">
      <label>A/B Compare</label>
      <button class="toggle-btn" onclick="toggleABMode(this)">Off</button>
    </div>
    <div style="margin-top: 12px">
      <button class="toggle-btn" style="width:100%; padding: 10px;" onclick="exportCSS()">Export Custom CSS</button>
    </div>
    <div style="margin-top: 8px">
      <button class="toggle-btn" style="width:100%; padding: 10px;" onclick="resetAll()">Reset to Default</button>
    </div>
  </div>

  <!-- CHANGE LOG -->
  <div class="panel-section">
    <h3>Change Log</h3>
    <div id="change-log" style="font-size: 11px; max-height: 150px; overflow-y: auto; color: #888;">
      <div style="padding: 4px 0; border-bottom: 1px solid #2a2a3e;">Session started</div>
    </div>
  </div>
</div>

<!-- PANEL TOGGLE -->
<button id="toggle-panel" onclick="togglePanel()">&#9776;</button>

<!-- PREVIEW AREA -->
<div id="preview-area">
  <div class="preview-toolbar">
    <div class="device-switcher">
      <button class="active" onclick="setDevice('desktop', this)">Desktop</button>
      <button onclick="setDevice('tablet', this)">Tablet</button>
      <button onclick="setDevice('mobile', this)">Mobile</button>
    </div>
    <div style="font-size: 13px; color: #666;" id="current-preset-label">Preset: Current TD</div>
    <div class="zoom-control">
      <label>Zoom</label>
      <input type="range" min="50" max="100" value="100" oninput="setZoom(this.value)">
      <span id="zoom-val">100%</span>
    </div>
  </div>

  <div id="preview-frame" class="desktop">
    <!-- VARIATION A (main) -->
    <div id="variation-a" style="position: relative;">

'''

TEMPLATE_TAIL = r'''
    </div><!-- /variation-a -->
    <!-- VARIATION B (hidden, for A/B mode) -->
    <div id="variation-b" style="display: none; position: relative;"></div>
  </div><!-- /preview-frame -->
</div>

<!-- CSS EXPORT MODAL -->
<div id="css-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:2000; align-items:center; justify-content:center;">
  <div style="background:#1a1a2e; color:#e0e0e0; width:600px; max-height:80vh; border-radius:12px; overflow:hidden;">
    <div style="padding:20px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333;">
      <h3 style="font-size:16px;">Exported CSS Variables</h3>
      <button onclick="document.getElementById('css-modal').style.display='none'" style="background:none;border:none;color:#aaa;font-size:20px;cursor:pointer;">&times;</button>
    </div>
    <pre id="css-output" style="padding:20px; overflow:auto; max-height:60vh; font-size:12px; line-height:1.6; white-space:pre-wrap;"></pre>
    <div style="padding:12px 20px; border-top:1px solid #333; text-align:right;">
      <button onclick="copyCss()" style="padding:8px 20px;background:#4ecca3;color:#1a1a2e;border:none;border-radius:4px;cursor:pointer;font-weight:600;">Copy to Clipboard</button>
    </div>
  </div>
</div>

<script>
const frame = document.getElementById('preview-frame');
const varA = document.getElementById('variation-a');
const varB = document.getElementById('variation-b');
const changeLog = document.getElementById('change-log');

function log(msg) {
  const d = document.createElement('div');
  d.style.cssText = 'padding:4px 0;border-bottom:1px solid #2a2a3e;';
  d.textContent = new Date().toLocaleTimeString().slice(0,5) + ' - ' + msg;
  changeLog.prepend(d);
}

function updateColor(varName, value) {
  document.documentElement.style.setProperty(varName, value);
  if (varName === '--td-green') {
    document.querySelectorAll('.td-hero').forEach(el => {
      el.style.background = 'linear-gradient(135deg, ' + value + ' 0%, ' + lightenColor(value, 20) + ' 50%, ' + lightenColor(value, 40) + ' 100%)';
    });
    document.querySelectorAll('.td-nav').forEach(el => { el.style.background = value; });
    document.querySelectorAll('.cta-strip').forEach(el => { el.style.background = value; });
    document.querySelectorAll('.promo-card.green-bg').forEach(el => {
      el.style.background = 'linear-gradient(135deg, ' + value + ', ' + lightenColor(value, 30) + ')';
    });
  }
  log('Color ' + varName + ' changed to ' + value);
}

function lightenColor(hex, percent) {
  var num = parseInt(hex.replace('#',''), 16);
  var r = Math.min(255, (num >> 16) + Math.round(2.55 * percent));
  var g = Math.min(255, ((num >> 8) & 0x00FF) + Math.round(2.55 * percent));
  var b = Math.min(255, (num & 0x0000FF) + Math.round(2.55 * percent));
  return '#' + (1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1);
}

function updateVar(varName, value) {
  document.documentElement.style.setProperty(varName, value);
  log(varName + ' changed to ' + value);
}

function clearClasses(prefix) {
  frame.className = frame.className.split(' ').filter(function(c) { return !c.startsWith(prefix); }).join(' ');
}

function setLayout(layout, btn) {
  activateBtn(btn);
  clearClasses('layout-');
  var heroVisual = document.querySelector('.hero-visual');
  if (heroVisual) heroVisual.style.display = 'none';
  if (layout !== 'default') {
    frame.classList.add('layout-' + layout);
    if (layout === 'split' && heroVisual) heroVisual.style.display = 'flex';
  }
  log('Hero layout: ' + layout);
}

function setCardStyle(style, btn) {
  activateBtn(btn);
  clearClasses('cards-');
  if (style !== 'default') frame.classList.add('cards-' + style);
  log('Card style: ' + style);
}

function setCols(n, btn) {
  activateBtn(btn);
  document.documentElement.style.setProperty('--card-columns', n);
  log('Card columns: ' + n);
}

function setTypo(typo, btn) {
  activateBtn(btn);
  clearClasses('typo-');
  if (typo !== 'default') frame.classList.add('typo-' + typo);
  log('Typography: ' + typo);
}

function setCtaStyle(style, btn) {
  activateBtn(btn);
  clearClasses('cta-');
  if (style !== 'default') frame.classList.add('cta-' + style);
  log('CTA style: ' + style);
}

function setSpacing(spacing, btn) {
  activateBtn(btn);
  clearClasses('spacing-');
  if (spacing !== 'default') frame.classList.add('spacing-' + spacing);
  log('Spacing: ' + spacing);
}

function setDevice(device, btn) {
  document.querySelectorAll('.device-switcher button').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  frame.className = frame.className.split(' ').filter(function(c) { return !['desktop','tablet','mobile'].includes(c); }).join(' ');
  frame.classList.add(device);
  log('Device: ' + device);
}

function setZoom(val) {
  document.getElementById('zoom-val').textContent = val + '%';
  frame.style.transform = 'scale(' + (val/100) + ')';
  if (val < 100) frame.style.transformOrigin = 'top center';
}

function toggleAnnotations(btn) {
  frame.classList.toggle('annotation-mode');
  var isOn = frame.classList.contains('annotation-mode');
  btn.textContent = isOn ? 'On' : 'Off';
  btn.classList.toggle('active', isOn);
  log('Annotations ' + (isOn ? 'enabled' : 'disabled'));
}

function toggleABMode(btn) {
  var isOn = varB.style.display === 'none';
  if (isOn) {
    varB.innerHTML = varA.innerHTML;
    varB.style.display = 'block';
    varB.style.borderLeft = '3px solid #e94560';
    var labelA = document.createElement('div');
    labelA.className = 'ab-label a'; labelA.textContent = 'A - Current';
    labelA.id = 'label-a'; varA.prepend(labelA);
    var labelB = document.createElement('div');
    labelB.className = 'ab-label b'; labelB.textContent = 'B - Variation';
    labelB.id = 'label-b'; varB.prepend(labelB);
    frame.style.display = 'grid';
    frame.style.gridTemplateColumns = '1fr 1fr';
  } else {
    varB.style.display = 'none'; varB.innerHTML = '';
    frame.style.display = 'block'; frame.style.gridTemplateColumns = '';
    var la = document.getElementById('label-a');
    var lb = document.getElementById('label-b');
    if (la) la.remove(); if (lb) lb.remove();
  }
  btn.textContent = isOn ? 'On' : 'Off';
  btn.classList.toggle('active', isOn);
  log('A/B mode ' + (isOn ? 'enabled' : 'disabled'));
}

function activateBtn(btn) {
  if (!btn) return;
  btn.parentElement.querySelectorAll('.toggle-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
}

function togglePanel() {
  document.getElementById('control-panel').classList.toggle('collapsed');
}

function applyPreset(preset) {
  resetAll(true);
  document.querySelectorAll('.preset-card').forEach(function(c) { c.classList.remove('active'); });
  if (event && event.currentTarget) event.currentTarget.classList.add('active');
  var label = document.getElementById('current-preset-label');
  switch(preset) {
    case 'modern':
      updateColor('--td-green', '#0d4f2b');
      updateColor('--td-accent', '#00b860');
      updateVar('--border-radius', '16px');
      updateVar('--cta-radius', '50px');
      frame.classList.add('typo-modern', 'spacing-spacious', 'cta-pill');
      label.textContent = 'Preset: Modern';
      break;
    case 'minimal':
      updateColor('--td-green', '#2c5f3f');
      updateVar('--hero-height', '300px');
      updateVar('--border-radius', '4px');
      frame.classList.add('layout-minimal', 'spacing-compact', 'cards-bordered', 'cta-square');
      label.textContent = 'Preset: Minimal';
      break;
    case 'bold':
      updateColor('--td-green', '#003d1e');
      updateColor('--td-accent', '#00c853');
      updateVar('--hero-height', '520px');
      updateVar('--border-radius', '12px');
      frame.classList.add('layout-centered', 'typo-modern', 'cards-filled');
      label.textContent = 'Preset: Bold';
      break;
    case 'dark':
      frame.classList.add('theme-dark');
      updateColor('--td-accent', '#4ecca3');
      label.textContent = 'Preset: Dark Mode';
      break;
    case 'corporate':
      updateVar('--border-radius', '2px');
      updateVar('--cta-radius', '2px');
      frame.classList.add('typo-classic', 'cta-square', 'cards-bordered');
      label.textContent = 'Preset: Corporate';
      break;
    default:
      label.textContent = 'Preset: Current TD';
  }
  log('Preset applied: ' + preset);
}

function resetAll(silent) {
  frame.className = 'desktop';
  var defaults = {
    '--td-green': '#1a5336', '--td-green-light': '#2d8659', '--td-green-pale': '#e8f5e9',
    '--td-dark': '#1d1d1d', '--td-gray': '#6b6b6b', '--td-light-gray': '#f5f5f5',
    '--td-accent': '#008a4b', '--td-blue': '#0066cc',
    '--border-radius': '8px', '--hero-height': '420px', '--nav-height': '64px',
    '--card-columns': '4', '--cta-radius': '24px', '--section-padding': '60px'
  };
  for (var k in defaults) {
    document.documentElement.style.setProperty(k, defaults[k]);
  }
  document.querySelectorAll('.td-hero, .td-nav, .cta-strip, .promo-card.green-bg').forEach(function(el) {
    el.style.background = '';
  });
  var hv = document.querySelector('.hero-visual');
  if (hv) hv.style.display = 'none';
  document.getElementById('color-primary').value = '#1a5336';
  document.getElementById('color-accent').value = '#008a4b';
  document.getElementById('color-bg').value = '#f5f5f5';
  document.getElementById('color-text').value = '#1d1d1d';
  varB.style.display = 'none'; varB.innerHTML = '';
  frame.style.display = 'block'; frame.style.gridTemplateColumns = '';
  var la = document.getElementById('label-a'); if (la) la.remove();
  if (!silent) {
    document.getElementById('current-preset-label').textContent = 'Preset: Current TD';
    log('Reset to defaults');
  }
}

function exportCSS() {
  var styles = getComputedStyle(document.documentElement);
  var vars = [
    '--td-green','--td-green-light','--td-green-pale','--td-dark','--td-gray',
    '--td-light-gray','--td-accent','--td-blue','--border-radius','--hero-height',
    '--nav-height','--card-columns','--cta-radius','--section-padding'
  ];
  var css = '/* TD Bank UI/UX Playground - Exported CSS */\n:root {\n';
  vars.forEach(function(v) { css += '  ' + v + ': ' + styles.getPropertyValue(v).trim() + ';\n'; });
  css += '}\n\n/* Active variation classes: */\n';
  css += '/* ' + frame.className + ' */\n';
  document.getElementById('css-output').textContent = css;
  document.getElementById('css-modal').style.display = 'flex';
}

function copyCss() {
  var text = document.getElementById('css-output').textContent;
  navigator.clipboard.writeText(text);
  log('CSS copied to clipboard');
}

/* ========== INTERACTIVE CONTENT JS ========== */
/* Toggle accordion items within the content */
document.addEventListener('click', function(e) {
  var header = e.target.closest('.td-accordion-header');
  if (header) {
    var accordion = header.parentElement;
    accordion.classList.toggle('open');
  }
  /* Tab switching */
  var tab = e.target.closest('.td-tab');
  if (tab) {
    var tabGroup = tab.closest('.td-tabs');
    var contentParent = tabGroup ? tabGroup.parentElement : null;
    if (contentParent) {
      tabGroup.querySelectorAll('.td-tab').forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      var target = tab.getAttribute('data-tab');
      if (target) {
        contentParent.querySelectorAll('.td-tab-content').forEach(function(c) { c.style.display = 'none'; });
        var panel = contentParent.querySelector('#' + target);
        if (panel) panel.style.display = 'block';
      }
    }
  }
});
</script>
</body>
</html>
'''


# CSS class reference for the LLM prompt
CONTENT_CSS_CLASSES = """
Available CSS classes for content (already defined by the framework):

NAVIGATION:
  .td-nav - Green top navigation bar
  .td-nav .logo - Brand logo text (use <span> for accent color)
  .td-nav-links - Horizontal nav link list
  .td-nav-actions .btn-login - Sign-in button

HERO:
  .td-hero - Full-width hero section with gradient
  .hero-content - Content container inside hero
  .hero-content h1 - Main headline
  .hero-content p - Subtext
  .hero-content .btn-hero - Primary CTA button

SECTIONS:
  .td-section - Standard content section
  .td-section.alt-bg - Alternating background section
  .section-header h2/p - Centered section title + subtitle

PRODUCT CARDS:
  .product-grid - CSS grid for cards (uses --card-columns)
  .product-card - Individual card with hover animation
  .product-card .card-icon - Icon container
  .product-card h3/p - Card title + description
  .product-card .card-link - "Learn more" link

PROMOTIONS:
  .promo-banner - Two-column promo grid
  .promo-card.green-bg / .promo-card.dark-bg - Promo card variants
  .promo-card h3/p/.btn-promo - Promo content

LIFE STAGES:
  .life-stage-grid - Three-column grid
  .life-stage-card - Card with image area + content
  .life-stage-card .stage-img - Top image area
  .life-stage-card .stage-content - Bottom content

CTA STRIP:
  .cta-strip - Full-width green CTA section
  .cta-strip h2/p/.btn-cta - CTA content

FOOTER:
  .td-footer - Dark footer
  .footer-grid / .footer-col - Four-column footer layout
  .footer-bottom - Copyright line

FORMS:
  .td-form-section - Form container (max-width 640px)
  .td-form-group - Form field wrapper
  .td-form-group label/input/select/textarea - Form elements
  .td-btn-primary / .td-btn-secondary - Action buttons

STEPS:
  .td-steps - Step indicator container
  .td-step / .td-step.active / .td-step.completed - Step items
  .td-step .step-num - Step number circle
  .td-step-connector - Line between steps

TABS:
  .td-tabs - Tab bar
  .td-tab / .td-tab.active - Individual tab (use data-tab="id")
  .td-tab-content - Tab panel (use id matching data-tab)

ACCORDIONS:
  .td-accordion - Accordion container
  .td-accordion-header - Clickable header
  .td-accordion-body - Collapsible body

TABLES:
  .td-table - Styled table
  .td-table th/td - Table cells

BADGES:
  .td-badge-green / .td-badge-blue / .td-badge-orange / .td-badge-red

DATA LABELS (for annotation mode):
  Add data-label="Name" to any element for annotation overlays
"""
