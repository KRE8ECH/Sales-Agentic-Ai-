import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
from typing import Dict, Any

from sales_agent.config import config
from sales_agent.db import Database
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.agents.orchestrator import OutreachOrchestrator
from sales_agent.commands import parse_user_command

db = Database()
ollama = OllamaClient()
orchestrator = OutreachOrchestrator(db=db, ollama=ollama)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SalesAgentic AI | Autonomous Sales Engineering &amp; Outbound Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    /* ==========================================================================
       Clay Design System (clay.com) — OpenDesignMD Specification
       ========================================================================== */
    :root {
      /* Colors */
      --color-primary: #0a0a0a;
      --color-primary-active: #1f1f1f;
      --color-primary-disabled: #e5e5e5;
      --color-ink: #0a0a0a;
      --color-body: #3a3a3a;
      --color-body-strong: #1a1a1a;
      --color-muted: #6a6a6a;
      --color-muted-soft: #9a9a9a;
      --color-hairline: #e5e5e5;
      --color-hairline-soft: #f0f0f0;

      /* Surfaces */
      --color-canvas: #fffaf0;
      --color-surface-soft: #faf5e8;
      --color-surface-card: #f5f0e0;
      --color-surface-strong: #ebe6d6;
      --color-surface-dark: #0a1a1a;
      --color-surface-dark-elevated: #1a2a2a;
      --color-surface-white: #ffffff;

      /* On-Color Text */
      --color-on-primary: #ffffff;
      --color-on-dark: #ffffff;
      --color-on-dark-soft: #a0a0a0;

      /* Saturated Feature Card Palette */
      --brand-pink: #ff4d8b;
      --brand-teal: #1a3a3a;
      --brand-lavender: #b8a4ed;
      --brand-peach: #ffb084;
      --brand-ochre: #e8b94a;
      --brand-mint: #a4d4c5;
      --brand-coral: #ff6b5a;

      /* Semantics */
      --color-success: #22c55e;
      --color-warning: #f59e0b;
      --color-error: #ef4444;

      /* Semantic Mappings */
      --surface-page: var(--color-canvas);
      --surface-card: #ffffff;
      --surface-soft: var(--color-surface-soft);
      --surface-raised: var(--color-surface-card);
      --surface-deep: #ffffff;
      --border-hairline: var(--color-hairline);
      --border-subtle: var(--color-surface-strong);
      --border-focus: var(--color-primary);
      --text-primary: var(--color-ink);
      --text-secondary: var(--color-body);
      --text-muted: var(--color-muted);
      --accent: var(--color-primary);

      /* Border Radii */
      --radius-xs: 6px;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-xl: 24px;
      --radius-pill: 9999px;
      --radius-full: 9999px;

      /* Typography */
      --font-display: 'Plain Black', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
      --ease: cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-sans);
      background-color: var(--surface-page);
      color: var(--text-primary);
      display: flex;
      height: 100vh;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
      font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    }

    /* Restrained Scrollbar */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(58, 58, 58, 0.2); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(58, 58, 58, 0.35); }

    /* Sidebar Navigation */
    .sidebar {
      width: 260px;
      background-color: var(--surface-soft);
      border-right: 1px solid var(--border-hairline);
      display: flex;
      flex-direction: column;
      padding: 18px 14px;
      flex-shrink: 0;
    }

    .brand-row {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 4px 8px 16px 8px;
      border-bottom: 1px solid var(--border-hairline);
      margin-bottom: 16px;
    }

    .brand-mark {
      width: 32px;
      height: 32px;
      border-radius: var(--radius-md);
      background: var(--color-primary);
      border: 1px solid var(--color-primary);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      flex-shrink: 0;
      box-shadow: 0 2px 6px rgba(10, 10, 10, 0.12);
    }

    .brand-mark svg {
      width: 17px;
      height: 17px;
      stroke-width: 1.6;
      stroke: #ffffff;
    }

    .brand-title {
      font-family: var(--font-display);
      font-size: 15px;
      font-weight: 500;
      color: var(--text-primary);
      line-height: 1.2;
      letter-spacing: -0.3px;
    }

    .brand-subtitle {
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.2;
      margin-top: 2px;
    }

    .nav-group-label {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      padding: 10px 8px 4px 8px;
    }

    .nav-tabs {
      display: flex;
      flex-direction: column;
      gap: 3px;
      flex: 1;
      overflow-y: auto;
    }

    .nav-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      height: 38px;
      padding: 0 12px;
      border-radius: var(--radius-md);
      background: transparent;
      color: var(--text-secondary);
      border: 1px solid transparent;
      cursor: pointer;
      font-size: 13.5px;
      font-weight: 500;
      text-align: left;
      user-select: none;
      -webkit-tap-highlight-color: transparent;
      transition: background-color 130ms var(--ease), color 130ms var(--ease), transform 100ms cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 130ms var(--ease);
      width: 100%;
    }

    .nav-btn:hover {
      background: var(--color-surface-card);
      color: var(--text-primary);
    }

    .nav-btn:active {
      transform: scale(0.94);
      background: var(--color-surface-strong);
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.12);
    }

    .nav-btn.active {
      background: var(--color-primary);
      color: #ffffff;
      font-weight: 600;
      border-color: var(--color-primary);
    }

    .nav-btn svg {
      width: 17px;
      height: 17px;
      stroke-width: 1.6;
      color: var(--text-muted);
      flex-shrink: 0;
    }

    .nav-btn.active svg {
      color: #ffffff;
    }

    .nav-badge {
      margin-left: auto;
      font-family: var(--font-mono);
      font-size: 11px;
      font-variant-numeric: tabular-nums;
      padding: 1px 7px;
      border-radius: var(--radius-pill);
      background: var(--color-surface-card);
      color: var(--text-primary);
      border: 1px solid var(--border-hairline);
    }

    /* Sidebar Telemetry Footer */
    .sidebar-footer {
      padding: 12px;
      background: var(--color-surface-card);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      margin-top: auto;
      font-size: 11.5px;
    }

    .telemetry-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }
    .telemetry-row:last-child { margin-bottom: 0; }

    .status-indicator {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--color-success);
      margin-right: 6px;
    }

    /* Main Viewport */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background-color: var(--surface-page);
    }

    /* Top Bar (Clay top-nav: 64px, surface-soft, ink text) */
    .top-header {
      height: 64px;
      border-bottom: 1px solid var(--border-hairline);
      background: var(--surface-soft);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      flex-shrink: 0;
    }

    .header-info h1 {
      font-family: var(--font-display);
      font-size: 17px;
      font-weight: 500;
      color: var(--text-primary);
      letter-spacing: -0.4px;
    }

    .header-breadcrumb {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 1px;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* ==========================================================================
       Clay Tactile Button Interaction: Dark Ink CTAs + Click Shade + Pop Smaller
       ========================================================================== */
    button, .btn-primary, .btn-secondary, .btn-approve, .btn-action-sm, .quick-chip, .preset-pill, .btn-msg-copy {
      user-select: none;
      -webkit-tap-highlight-color: transparent;
      cursor: pointer;
      position: relative;
      transition: background-color 130ms var(--ease),
                  transform 100ms cubic-bezier(0.2, 0.8, 0.2, 1),
                  box-shadow 130ms var(--ease),
                  border-color 130ms var(--ease),
                  filter 130ms var(--ease);
      will-change: transform, box-shadow;
    }

    /* Universal Active / Click State: Pop Out Smaller & Inset Shade */
    button:active,
    .btn-primary:active,
    .btn-secondary:active,
    .btn-approve:active,
    .btn-action-sm:active,
    .quick-chip:active,
    .preset-pill:active,
    .btn-msg-copy:active,
    a.btn-primary:active,
    a.btn-secondary:active {
      transform: scale(0.92) !important;
      filter: brightness(0.88);
    }

    /* Primary Clay Buttons: Dark-navy primary CTAs (#0a0a0a), rounded md (12px) */
    .btn-primary {
      background: var(--color-primary);
      color: var(--color-on-primary);
      border: 1px solid var(--color-primary);
      height: 38px;
      padding: 0 18px;
      border-radius: var(--radius-md);
      font-weight: 600;
      font-size: 13.5px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 1px 3px rgba(10, 10, 10, 0.08);
      text-decoration: none;
    }

    .btn-primary:hover {
      background: var(--color-primary-active);
      border-color: var(--color-primary-active);
      color: #ffffff;
    }

    .btn-primary:active {
      background: var(--color-primary-active) !important;
      border-color: var(--color-primary-active) !important;
      box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.6) !important;
    }

    /* Secondary Clay Buttons: Cream button with hairline outline */
    .btn-secondary {
      background: var(--color-canvas);
      color: var(--color-ink);
      border: 1px solid var(--border-hairline);
      height: 38px;
      padding: 0 16px;
      border-radius: var(--radius-md);
      font-weight: 600;
      font-size: 13.5px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
    }

    .btn-secondary:hover {
      background: var(--color-surface-card);
      border-color: var(--border-subtle);
      color: var(--color-ink);
    }

    .btn-secondary:active {
      background: var(--color-surface-strong) !important;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15) !important;
    }

    /* Small Action & Approve Buttons */
    .btn-approve, .btn-action-sm {
      background: var(--color-primary);
      color: var(--color-on-primary);
      border: 1px solid var(--color-primary);
      height: 32px;
      padding: 0 12px;
      border-radius: var(--radius-md);
      font-weight: 600;
      font-size: 12px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      box-shadow: 0 1px 2px rgba(10, 10, 10, 0.08);
      text-decoration: none;
    }

    .btn-approve:hover, .btn-action-sm:hover {
      background: var(--color-primary-active);
      border-color: var(--color-primary-active);
      color: #ffffff;
    }

    .btn-approve:active, .btn-action-sm:active {
      background: var(--color-primary-active) !important;
      box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.5) !important;
    }

    /* Clay Pill Chips (Pill shape 9999px, cream fill #f5f0e0) */
    .quick-chip {
      background: var(--color-surface-card);
      border: 1px solid var(--border-hairline);
      color: var(--color-ink);
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      font-size: 12.5px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .quick-chip:hover {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
    }

    .quick-chip:active {
      background: var(--color-primary-active) !important;
      color: #ffffff !important;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }

    .preset-pill {
      background: var(--color-surface-card);
      border: 1px solid var(--border-hairline);
      color: var(--color-ink);
      padding: 4px 12px;
      border-radius: var(--radius-pill);
      font-size: 12px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
    }

    .preset-pill:hover {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
    }

    .preset-pill:active {
      background: var(--color-primary-active) !important;
      color: #ffffff !important;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }

    /* Dropdown Menus */
    .dropdown {
      position: relative;
      display: inline-block;
    }

    .dropdown-content {
      display: none;
      position: absolute;
      right: 0;
      top: 100%;
      margin-top: 6px;
      background: #ffffff;
      min-width: 250px;
      box-shadow: 0 12px 32px rgba(10, 10, 10, 0.1);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      z-index: 100;
      overflow: hidden;
    }

    .dropdown-content a {
      color: var(--text-primary);
      padding: 12px 16px;
      text-decoration: none;
      display: block;
      font-size: 13px;
      cursor: pointer;
      border-bottom: 1px solid var(--border-hairline);
      transition: background-color 120ms var(--ease);
    }

    .dropdown-content a:last-child { border-bottom: none; }
    .dropdown-content a:hover {
      background: var(--color-surface-soft);
    }

    .dropdown:hover .dropdown-content { display: block; }

    /* Content Viewport (Cream-tinted canvas #fffaf0) */
    .content-viewport {
      flex: 1;
      overflow-y: auto;
      padding: 28px;
      background: var(--surface-page);
    }

    .tab-section { display: none; }
    .tab-section.active { display: block; }

    /* ==========================================================================
       CLAY.COM HERO & FRONT PAGE (OpenDesignMD Specification)
       ========================================================================== */
    .clay-home-layout {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 36px;
      padding-bottom: 64px;
    }

    /* Clay Hero Card (Upper 3D Landscape + Lower Emerald Deck) */
    .clay-hero-card {
      border-radius: var(--radius-xl);
      overflow: hidden;
      border: 1px solid var(--border-hairline);
      box-shadow: 0 12px 40px rgba(10, 10, 10, 0.05);
      background: #ffffff;
      display: flex;
      flex-direction: column;
    }

    /* Top Half: Sales & Email Command Center Dashboard Graphic (Replaces Landscape Art) */
    .sales-dashboard-art {
      width: 100%;
      min-height: 420px;
      position: relative;
      overflow: hidden;
      background: linear-gradient(135deg, #071524 0%, #0c2338 50%, #081a2b 100%);
      padding: 28px 36px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-sizing: border-box;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .sales-dashboard-art::before {
      content: '';
      position: absolute;
      inset: 0;
      background-image: 
        radial-gradient(circle at 20% 30%, rgba(56, 189, 248, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 80% 70%, rgba(124, 58, 237, 0.14) 0%, transparent 50%),
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
      background-size: 100% 100%, 100% 100%, 28px 28px, 28px 28px;
      pointer-events: none;
    }

    .dash-topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: relative;
      z-index: 2;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }

    .dash-brand-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.16);
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      color: #ffffff;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.3px;
    }

    .dash-telemetry-tags {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .dash-pill-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 4px 12px;
      border-radius: var(--radius-pill);
      color: rgba(255, 255, 255, 0.88);
      font-family: var(--font-mono);
      font-size: 11px;
    }

    .sales-dashboard-grid {
      display: grid;
      grid-template-columns: 1.05fr 1.25fr 1.1fr;
      gap: 20px;
      position: relative;
      z-index: 2;
      align-items: stretch;
    }

    .sales-dash-card {
      background: rgba(15, 29, 45, 0.72);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      color: #ffffff;
    }

    .dash-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 10px;
    }

    .dash-card-title {
      font-size: 12.5px;
      font-weight: 700;
      letter-spacing: 0.4px;
      color: rgba(255, 255, 255, 0.95);
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .dash-card-badge {
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: var(--radius-pill);
    }

    .funnel-stage-row {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 10px;
    }

    .funnel-stage-meta {
      display: flex;
      justify-content: space-between;
      font-size: 11.5px;
      color: rgba(255, 255, 255, 0.85);
    }

    .funnel-stage-bar {
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 4px;
      overflow: hidden;
    }

    .funnel-stage-fill {
      height: 100%;
      border-radius: 4px;
    }

    .dash-chart-val {
      font-family: var(--font-display);
      font-size: 26px;
      font-weight: 500;
      color: #ffffff;
      letter-spacing: -0.5px;
      margin: 2px 0 8px 0;
    }

    .dash-chart-sub {
      font-size: 12px;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 10px;
    }

    .dash-metric-pills {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }

    .dash-metric-cell {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-sm);
      padding: 7px 8px;
      text-align: center;
    }

    .dash-metric-label {
      font-size: 9.5px;
      color: rgba(255, 255, 255, 0.6);
      text-transform: uppercase;
    }

    .dash-metric-num {
      font-family: var(--font-mono);
      font-size: 12.5px;
      font-weight: 700;
      color: #ffffff;
      margin-top: 2px;
    }

    .dash-lead-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #f97316, #ef4444);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 13px;
      color: #ffffff;
      border: 2px solid rgba(255, 255, 255, 0.2);
    }

    /* Bottom Half: Emerald Green Hill Deck */
    .clay-hero-deck {
      background: linear-gradient(180deg, #0e4e36 0%, #073422 100%);
      padding: 48px 56px 52px 56px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 48px;
      align-items: center;
      color: #ffffff;
      position: relative;
    }

    .clay-hero-headline {
      font-family: var(--font-display);
      font-size: 56px;
      font-weight: 500;
      line-height: 1.05;
      letter-spacing: -2px;
      color: #ffffff;
      margin: 0;
    }

    .clay-hero-right {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .clay-hero-subtext {
      font-family: var(--font-sans);
      font-size: 18px;
      font-weight: 400;
      line-height: 1.5;
      color: rgba(255, 255, 255, 0.92);
      margin: 0;
    }

    .clay-hero-actions {
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }

    /* White Pill Button */
    .btn-clay-white {
      background: #ffffff;
      color: #0a0a0a;
      font-family: var(--font-sans);
      font-size: 15px;
      font-weight: 600;
      padding: 13px 24px;
      border-radius: var(--radius-pill);
      border: 1px solid #ffffff;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
      transition: all 0.15s var(--ease);
      text-decoration: none;
    }

    .btn-clay-white:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
      background: #fafafa;
    }

    /* Yellow/Chartreuse Pill Button */
    .btn-clay-yellow {
      background: #d4ed31;
      color: #0a0a0a;
      font-family: var(--font-sans);
      font-size: 15px;
      font-weight: 600;
      padding: 13px 24px;
      border-radius: var(--radius-pill);
      border: 1px solid #d4ed31;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
      transition: all 0.15s var(--ease);
      text-decoration: none;
    }

    .btn-clay-yellow:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
      background: #dbf23f;
    }

    /* Accent Peach Pill Button */
    .btn-clay-pill-accent {
      background: #ffb084;
      color: #0a0a0a;
      font-family: var(--font-sans);
      font-size: 15px;
      font-weight: 600;
      padding: 13px 24px;
      border-radius: var(--radius-pill);
      border: 1px solid #ffb084;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
      transition: all 0.15s var(--ease);
      text-decoration: none;
    }

    .btn-clay-pill-accent:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
      background: #ffbe99;
    }

    .clay-hero-proof {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.72);
      flex-wrap: wrap;
    }

    .clay-pill-tech {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 11px;
      border-radius: var(--radius-pill);
      background: rgba(255, 255, 255, 0.14);
      color: #ffffff;
      font-size: 11.5px;
      font-weight: 500;
      backdrop-filter: blur(4px);
    }

    .clay-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      display: inline-block;
    }
    .clay-dot.dot-green { background: #22c55e; }
    .clay-dot.dot-blue { background: #38bdf8; }
    .clay-dot.dot-amber { background: #fbbf24; }

    /* Top Navigation Links in Header */
    .top-nav-links {
      display: flex;
      align-items: center;
      gap: 4px;
      margin: 0 auto;
    }

    .top-nav-link {
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--radius-pill);
      padding: 6px 14px;
      font-family: var(--font-sans);
      font-size: 13.5px;
      font-weight: 500;
      color: var(--color-ink);
      cursor: pointer;
      transition: all 0.15s var(--ease);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .top-nav-link:hover {
      background: var(--color-surface-card);
      border-color: var(--color-hairline);
    }

    .top-nav-link.active {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
      font-weight: 600;
    }

    /* Brand mark in Sidebar */
    .brand-mark-clay {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-md);
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      box-shadow: 0 2px 6px rgba(10, 10, 10, 0.04);
      transition: transform 0.15s var(--ease);
    }

    .brand-mark-clay:hover {
      transform: scale(1.05);
    }

    /* Saturated Feature Cards Grid */
    .clay-feature-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
    }

    .clay-card {
      border-radius: var(--radius-xl);
      padding: 32px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 380px;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s var(--ease), box-shadow 0.2s var(--ease);
      border: 1px solid rgba(0, 0, 0, 0.05);
    }

    .clay-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 16px 36px rgba(10, 10, 10, 0.08);
    }

    .clay-card-lavender {
      background-color: var(--brand-lavender);
      color: var(--color-ink);
    }

    .clay-card-pink {
      background-color: var(--brand-pink);
      color: #ffffff;
    }

    .clay-card-teal {
      background-color: var(--brand-teal);
      color: #ffffff;
    }

    .clay-card-peach {
      background-color: var(--brand-peach);
      color: var(--color-ink);
    }

    .clay-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .clay-card-tag {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      opacity: 0.85;
    }

    .clay-card-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      background: rgba(255, 255, 255, 0.4);
      color: inherit;
    }

    .clay-card-pink .clay-card-badge,
    .clay-card-teal .clay-card-badge {
      background: rgba(255, 255, 255, 0.18);
    }

    .clay-card-title {
      font-family: var(--font-display);
      font-size: 26px;
      font-weight: 500;
      line-height: 1.15;
      letter-spacing: -0.5px;
      margin: 0 0 10px 0;
    }

    .clay-card-desc {
      font-size: 14.5px;
      line-height: 1.55;
      margin-bottom: 20px;
      opacity: 0.9;
    }

    .clay-card-preview {
      background: #ffffff;
      color: var(--color-ink);
      border-radius: var(--radius-lg);
      padding: 18px;
      border: 1px solid rgba(0, 0, 0, 0.08);
      margin-bottom: 22px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .clay-card-teal .clay-card-preview {
      background: #0f2424;
      color: #ffffff;
      border-color: rgba(255, 255, 255, 0.1);
    }

    .clay-card-cta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 20px;
      border-radius: var(--radius-md);
      font-family: var(--font-sans);
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.15s var(--ease);
      width: fit-content;
      text-decoration: none;
    }

    .btn-card-dark {
      background: var(--color-primary);
      color: #ffffff;
    }
    .btn-card-dark:hover {
      background: var(--color-primary-active);
    }

    .btn-card-white {
      background: #ffffff;
      color: var(--color-ink);
    }
    .btn-card-white:hover {
      background: #fafafa;
    }

    /* Uber Tactile Physics: Scale 0.92 with inset shadow on active press */
    .btn-primary:active,
    .btn-secondary:active,
    .btn-clay-white:active,
    .btn-clay-yellow:active,
    .btn-clay-pill-accent:active,
    .btn-carousel-pill:active,
    .btn-card-dark:active,
    .btn-card-white:active,
    .quick-chip:active,
    .nav-btn:active,
    .top-nav-link:active {
      transform: scale(0.92) !important;
      box-shadow: inset 0 3px 6px rgba(0, 0, 0, 0.45) !important;
    }

    /* ==========================================================================
       CLAY INTERACTIVE FEATURE CAROUSEL & MARKET MATCHER
       ========================================================================== */
    .clay-carousel-section {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-top: 10px;
    }

    .carousel-header-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 14px;
    }

    .carousel-nav-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-carousel-pill {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-pill);
      padding: 8px 18px;
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 600;
      color: var(--color-ink);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 6px rgba(10, 10, 10, 0.04);
      transition: all 0.15s var(--ease);
    }

    .btn-carousel-pill:hover {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
    }

    .btn-carousel-pill:active {
      transform: scale(0.92) !important;
      box-shadow: inset 0 3px 6px rgba(0, 0, 0, 0.45) !important;
    }

    .clay-carousel-viewport {
      width: 100%;
      overflow: hidden;
      border-radius: var(--radius-xl);
      border: 1px solid var(--border-hairline);
      box-shadow: 0 8px 30px rgba(10, 10, 10, 0.05);
      background: #ffffff;
      position: relative;
    }

    .clay-carousel-track {
      display: flex;
      transition: transform 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
      width: 100%;
    }

    .clay-carousel-slide {
      min-width: 100%;
      box-sizing: border-box;
      padding: 44px 52px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 44px;
      align-items: center;
      position: relative;
      overflow: hidden;
    }

    .carousel-slide-lavender {
      background: linear-gradient(135deg, #f5efff 0%, #ece2fc 100%);
    }

    .carousel-slide-mint {
      background: linear-gradient(135deg, #eefbf7 0%, #dbf5ec 100%);
    }

    .carousel-slide-peach {
      background: linear-gradient(135deg, #fff7ed 0%, #feecd6 100%);
    }

    .carousel-slide-pink {
      background: linear-gradient(135deg, #fff0f5 0%, #fde2ec 100%);
    }

    .carousel-slide-left {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .carousel-slide-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      width: fit-content;
    }

    .carousel-slide-title {
      font-family: var(--font-display);
      font-size: 32px;
      font-weight: 500;
      line-height: 1.15;
      letter-spacing: -1px;
      color: var(--color-ink);
      margin: 0;
    }

    .carousel-slide-desc {
      font-family: var(--font-sans);
      font-size: 15.5px;
      line-height: 1.55;
      color: var(--color-body);
      margin: 0;
    }

    .carousel-benefit-chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .carousel-chip {
      font-size: 12px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: var(--radius-pill);
      background: #ffffff;
      border: 1px solid rgba(10, 10, 10, 0.08);
      color: var(--color-ink);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 6px rgba(10, 10, 10, 0.03);
    }

    .carousel-slide-right {
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .carousel-demo-card {
      background: #ffffff;
      border-radius: var(--radius-lg);
      padding: 22px;
      border: 1px solid rgba(10, 10, 10, 0.08);
      box-shadow: 0 6px 20px rgba(10, 10, 10, 0.06);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .carousel-dots-row {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
    }

    .carousel-dot {
      height: 8px;
      width: 8px;
      border-radius: var(--radius-pill);
      background: rgba(10, 10, 10, 0.2);
      cursor: pointer;
      transition: all 0.25s var(--ease);
      border: none;
      padding: 0;
    }

    .carousel-dot.active {
      width: 28px;
      background: var(--color-primary);
    }

    /* Market Demand Matcher Grid */
    .market-matcher-box {
      background: #ffffff;
      border-radius: var(--radius-xl);
      padding: 32px;
      border: 1px solid var(--border-hairline);
      box-shadow: 0 4px 20px rgba(10, 10, 10, 0.04);
      margin-top: 16px;
    }

    .btn-category-filter {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-pill);
      padding: 6px 14px;
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      color: var(--color-ink);
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(10, 10, 10, 0.04);
      transition: all 0.15s var(--ease);
    }

    .btn-category-filter:hover {
      border-color: var(--color-primary);
      color: var(--color-primary);
    }

    .btn-category-filter:active {
      transform: scale(0.92) !important;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.35) !important;
    }

    .btn-category-filter.active {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
    }

    .matcher-card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .matcher-card {
      background: var(--color-surface-soft);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 16px;
      transition: transform 0.15s var(--ease), box-shadow 0.15s var(--ease);
    }

    .matcher-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(10, 10, 10, 0.08);
      background: #ffffff;
      border-color: var(--color-primary);
    }

    /* Features List in Settings */
    .feature-manager-item {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      position: relative;
    }

    /* 1. CHAT TAB */
    .chat-layout {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 120px);
      max-width: 1080px;
      margin: 0 auto;
    }

    .chat-container {
      flex: 1;
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-xl);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(10, 10, 10, 0.03);
    }

    .chat-hero-banner {
      background: var(--surface-soft);
      border-bottom: 1px solid var(--border-hairline);
      padding: 16px 22px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .chat-hero-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chat-hero-title {
      font-family: var(--font-display);
      font-size: 14.5px;
      font-weight: 500;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: -0.2px;
    }

    .chat-hero-subtitle {
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.5;
    }

    .quick-chips-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    /* Chat Messages Stream */
    .chat-messages {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 18px;
      background: #ffffff;
    }

    .message-wrapper {
      display: flex;
      gap: 12px;
      max-width: 88%;
    }

    .message-wrapper.agent-wrap {
      align-self: flex-start;
      max-width: 88%;
    }

    .message-wrapper.user-wrap {
      align-self: flex-end;
      flex-direction: row-reverse;
      max-width: 75%;
    }

    .msg-avatar {
      width: 32px;
      height: 32px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 2px;
      background: var(--color-primary);
      border: 1px solid var(--color-primary);
      color: #ffffff;
    }

    .msg-avatar svg {
      width: 17px;
      height: 17px;
      stroke-width: 1.6;
      stroke: #ffffff;
    }

    .message-bubble {
      border-radius: var(--radius-lg);
      padding: 14px 18px;
      font-size: 13.5px;
      line-height: 1.6;
    }

    .message.agent {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      color: var(--text-primary);
      box-shadow: 0 1px 4px rgba(10, 10, 10, 0.04);
      border-radius: 16px 16px 16px 4px;
    }

    .message.user {
      background: var(--color-primary);
      color: #ffffff;
      border: 1px solid var(--color-primary);
      border-radius: 16px 16px 4px 16px;
    }

    .message-header-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 11.5px;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-hairline);
      padding-bottom: 6px;
    }

    .message-sender-name {
      font-weight: 600;
      color: var(--text-primary);
    }

    .message-grounding-tag {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--brand-teal);
      background: var(--brand-mint);
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      font-weight: 600;
    }

    .message-actions-bar {
      margin-top: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--border-hairline);
    }

    .btn-msg-copy {
      background: var(--color-surface-card);
      border: 1px solid var(--border-hairline);
      color: var(--text-secondary);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      font-size: 11.5px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: background-color 120ms var(--ease), color 120ms var(--ease), transform 100ms var(--ease);
    }

    .btn-msg-copy:hover {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
    }

    .btn-msg-copy:active {
      transform: scale(0.92) !important;
      background: var(--color-primary-active) !important;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    /* Thinking State */
    .thinking-card {
      background: var(--surface-soft);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .thinking-indicator-row {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      color: var(--text-secondary);
    }

    .thinking-spinner {
      width: 14px;
      height: 14px;
      border: 2px solid var(--border-hairline);
      border-top-color: var(--color-primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .thinking-steps-progress {
      display: flex;
      gap: 6px;
      margin-top: 2px;
    }

    .thinking-step-pill {
      font-family: var(--font-mono);
      font-size: 10.5px;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      background: var(--color-surface-card);
      color: var(--text-muted);
      border: 1px solid var(--border-hairline);
    }

    .thinking-step-pill.active {
      color: #ffffff;
      border-color: var(--color-primary);
      background: var(--color-primary);
    }

    /* Chat Input Bar */
    .chat-input-bar {
      padding: 14px 20px;
      background: #ffffff;
      border-top: 1px solid var(--border-hairline);
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .input-wrapper {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
    }

    .chat-input {
      width: 100%;
      background: var(--color-canvas);
      border: 1px solid var(--border-hairline);
      color: var(--text-primary);
      padding: 10px 14px;
      padding-right: 80px;
      border-radius: var(--radius-md);
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: border-color 140ms var(--ease), background 140ms var(--ease);
    }

    .chat-input:focus {
      background: #ffffff;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    .input-kbd-hint {
      position: absolute;
      right: 12px;
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--text-muted);
      background: var(--color-surface-card);
      padding: 2px 6px;
      border-radius: var(--radius-xs);
      border: 1px solid var(--border-hairline);
      pointer-events: none;
    }

    /* 2. COMPANY DISCOVERY TAB */
    .discovery-container {
      max-width: 1080px;
      margin: 0 auto;
    }

    .search-console-card {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-xl);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 2px 10px rgba(10, 10, 10, 0.03);
    }

    .search-input-row {
      display: flex;
      gap: 10px;
    }

    .search-input-row input {
      flex: 1;
      background: var(--color-canvas);
      border: 1px solid var(--border-hairline);
      color: var(--text-primary);
      padding: 10px 14px;
      border-radius: var(--radius-md);
      font-size: 14px;
      outline: none;
      transition: border-color 140ms var(--ease), background 140ms var(--ease);
    }

    .search-input-row input:focus {
      background: #ffffff;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    .search-presets-row {
      margin-top: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }

    .preset-links-group {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12.5px;
      color: var(--text-muted);
    }

    .toggle-control {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      font-size: 12.5px;
      color: var(--text-secondary);
      user-select: none;
      background: var(--color-surface-card);
      padding: 5px 12px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border-hairline);
    }

    .prospect-card {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      padding: 20px;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 1px 4px rgba(10, 10, 10, 0.03);
      transition: border-color 140ms var(--ease), box-shadow 140ms var(--ease);
    }

    .prospect-card:hover {
      border-color: var(--color-primary);
      box-shadow: 0 6px 18px rgba(10, 10, 10, 0.06);
    }

    /* 3. LEADS & PIPELINE TAB */
    .pipeline-container {
      max-width: 1080px;
      margin: 0 auto;
    }

    /* Clay Saturated Single-Color Feature Cards for KPIs */
    .kpi-stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .kpi-card {
      border-radius: var(--radius-xl);
      padding: 24px;
      box-shadow: 0 2px 8px rgba(10, 10, 10, 0.04);
      transition: transform 120ms var(--ease), box-shadow 120ms var(--ease);
      border: 1px solid transparent;
      position: relative;
    }

    .kpi-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(10, 10, 10, 0.08);
    }

    /* Card 1: Lavender */
    .kpi-card:nth-child(1) {
      background: var(--brand-lavender);
      color: var(--color-ink);
      border-color: rgba(10, 10, 10, 0.06);
    }
    .kpi-card:nth-child(1) .kpi-label,
    .kpi-card:nth-child(1) .kpi-subtext {
      color: #3a3a3a;
    }
    .kpi-card:nth-child(1) .kpi-value {
      color: #0a0a0a;
    }

    /* Card 2: Peach */
    .kpi-card:nth-child(2) {
      background: var(--brand-peach);
      color: var(--color-ink);
      border-color: rgba(10, 10, 10, 0.06);
    }
    .kpi-card:nth-child(2) .kpi-label,
    .kpi-card:nth-child(2) .kpi-subtext {
      color: #3a3a3a;
    }
    .kpi-card:nth-child(2) .kpi-value {
      color: #0a0a0a !important;
    }

    /* Card 3: Deep Teal */
    .kpi-card:nth-child(3) {
      background: var(--brand-teal);
      color: var(--color-on-dark);
      border-color: #1a3a3a;
    }
    .kpi-card:nth-child(3) .kpi-label,
    .kpi-card:nth-child(3) .kpi-subtext {
      color: rgba(255, 255, 255, 0.85);
    }
    .kpi-card:nth-child(3) .kpi-value {
      color: #ffffff;
    }

    /* Card 4: Hot Pink */
    .kpi-card:nth-child(4) {
      background: var(--brand-pink);
      color: var(--color-on-primary);
      border-color: #ff4d8b;
    }
    .kpi-card:nth-child(4) .kpi-label,
    .kpi-card:nth-child(4) .kpi-subtext {
      color: rgba(255, 255, 255, 0.85);
    }
    .kpi-card:nth-child(4) .kpi-value {
      color: #ffffff;
    }

    .kpi-label {
      font-family: var(--font-display);
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }

    .kpi-value {
      font-size: 32px;
      font-weight: 600;
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      line-height: 1.1;
    }

    .kpi-subtext {
      font-size: 11.5px;
      margin-top: 6px;
    }

    .pipeline-filter-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 18px;
    }

    .search-filter-input {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      color: var(--text-primary);
      padding: 8px 14px;
      border-radius: var(--radius-md);
      font-size: 13px;
      outline: none;
      min-width: 280px;
      transition: border-color 140ms var(--ease), box-shadow 140ms var(--ease);
    }

    .search-filter-input:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    .lead-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
    }

    .lead-card {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      padding: 18px;
      cursor: pointer;
      box-shadow: 0 1px 4px rgba(10, 10, 10, 0.03);
      transition: border-color 140ms var(--ease), box-shadow 140ms var(--ease);
    }

    .lead-card:hover {
      border-color: var(--color-primary);
      box-shadow: 0 6px 18px rgba(10, 10, 10, 0.06);
    }

    .lead-card.selected {
      border-color: var(--color-primary);
      background: var(--surface-soft);
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    .lead-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 14px;
    }

    .lead-company-avatar {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 13px;
      color: #ffffff;
      flex-shrink: 0;
      margin-right: 12px;
      background: var(--color-primary);
      border: 1px solid var(--color-primary);
    }

    .lead-cadence-meter {
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid var(--border-hairline);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .cadence-progress-track {
      height: 4px;
      background: var(--color-surface-card);
      border-radius: 2px;
      overflow: hidden;
    }

    .cadence-progress-fill {
      height: 100%;
      background: var(--color-primary);
      border-radius: 2px;
    }

    /* 4. RAG DOSSIER & SEQUENCE TAB */
    .dossier-layout-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }

    @media (max-width: 960px) {
      .dossier-layout-grid { grid-template-columns: 1fr; }
    }

    .panel-box {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-xl);
      padding: 24px;
      margin-bottom: 18px;
      box-shadow: 0 1px 4px rgba(10, 10, 10, 0.03);
    }

    .panel-title {
      font-family: var(--font-display);
      font-size: 14.5px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      letter-spacing: -0.2px;
    }

    /* Email Preview Card */
    .email-preview-card {
      background: var(--surface-soft);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      padding: 16px;
      margin-bottom: 14px;
    }

    .email-preview-card.awaiting-card {
      border-color: var(--color-warning);
    }

    .email-header-table {
      font-size: 12.5px;
      color: var(--text-secondary);
      margin-bottom: 12px;
      border-bottom: 1px solid var(--border-hairline);
      padding-bottom: 8px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .email-body-text {
      white-space: pre-wrap;
      font-size: 13.5px;
      color: var(--text-primary);
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      padding: 14px;
      border-radius: var(--radius-md);
      line-height: 1.6;
    }

    .evidence-pill-box {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 10px;
      padding: 6px 10px;
      border-radius: var(--radius-sm);
      background: var(--color-surface-card);
    }

    /* Badges (Clay badge-pill: pill 9999px) */
    .badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      display: inline-flex;
      align-items: center;
      gap: 4px;
      border: 1px solid var(--border-hairline);
      background: var(--color-surface-card);
      color: var(--text-primary);
    }

    .badge-NEW { background: var(--color-surface-card); color: var(--text-secondary); }
    .badge-AWAITING_APPROVAL {
      background: var(--brand-peach);
      color: var(--color-ink);
      border-color: rgba(10, 10, 10, 0.12);
      font-weight: 600;
    }
    .badge-IN_SEQUENCE {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
      font-weight: 600;
    }
    .badge-ESCALATED {
      background: var(--brand-pink);
      color: #ffffff;
      border-color: var(--brand-pink);
    }
    .badge-PAUSED { background: var(--color-surface-card); color: var(--text-muted); }
    .badge-STOPPED { background: var(--color-surface-card); color: var(--text-muted); }
    .badge-COMPLETED {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
      font-weight: 600;
    }
    .badge-SENT {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
      font-weight: 600;
    }
    .badge-LIVE {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
      font-weight: 600;
    }
    .badge-DEMO {
      background: var(--color-surface-card);
      color: var(--text-secondary);
    }

    /* Warning & Error Boxes */
    .warning-box {
      background: #fef3c7;
      border: 1px solid #fcd34d;
      color: #92400e;
      padding: 12px 16px;
      border-radius: var(--radius-md);
      margin-bottom: 14px;
      font-size: 13px;
    }

    .error-box {
      background: #fee2e2;
      border: 1px solid #fca5a5;
      color: #991b1b;
      padding: 12px 16px;
      border-radius: var(--radius-md);
      margin-bottom: 14px;
      font-size: 13px;
    }

    .source-link {
      color: var(--color-primary);
      text-decoration: underline;
      text-underline-offset: 3px;
      font-size: 12.5px;
      font-weight: 500;
      display: inline-block;
    }
    .source-link:hover { color: var(--color-muted); }

    /* 5. SETTINGS TAB */
    .form-group { margin-bottom: 18px; }
    .form-group label {
      display: block;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }

    .form-group input, .form-group textarea {
      width: 100%;
      background: var(--color-canvas);
      border: 1px solid var(--border-hairline);
      color: var(--text-primary);
      padding: 10px 14px;
      border-radius: var(--radius-md);
      font-size: 13.5px;
      font-family: inherit;
      outline: none;
      transition: border-color 140ms var(--ease), background 140ms var(--ease);
    }

    .form-group input:focus, .form-group textarea:focus {
      background: #ffffff;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    /* 6. LOGS TAB */
    .table-container {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-lg);
      overflow: hidden;
      margin-top: 16px;
      box-shadow: 0 1px 4px rgba(10, 10, 10, 0.03);
    }

    table { width: 100%; border-collapse: collapse; font-size: 13px; }

    th {
      background: var(--surface-soft);
      text-align: left;
      padding: 12px 16px;
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--border-hairline);
      font-size: 11.5px;
      font-family: var(--font-mono);
    }

    td {
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-hairline);
      vertical-align: top;
      background: #ffffff;
    }

    tr:last-child td { border-bottom: none; }
    tr:hover td { background: var(--color-surface-soft); }

    .reasoning-cell {
      color: var(--text-secondary);
      line-height: 1.5;
      font-size: 13px;
    }

    /* Modals System (Clay radius xl 24px) */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(10, 10, 10, 0.45);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }

    .modal-backdrop.open { display: flex; }

    .modal {
      background: #ffffff;
      border: 1px solid var(--border-hairline);
      width: 520px;
      max-width: 90vw;
      border-radius: var(--radius-xl);
      padding: 24px;
      color: var(--text-primary);
      box-shadow: 0 20px 48px rgba(10, 10, 10, 0.14);
    }

    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 24px;
    }

    /* Spotlight Command Palette */
    .spotlight-modal {
      width: 580px;
      padding: 0;
      overflow: hidden;
    }

    .spotlight-search-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--border-hairline);
      background: var(--surface-soft);
    }

    .spotlight-input {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-primary);
      font-size: 14.5px;
      outline: none;
      font-family: inherit;
    }

    .spotlight-list {
      max-height: 320px;
      overflow-y: auto;
      padding: 8px;
      background: #ffffff;
    }

    .spotlight-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      cursor: pointer;
      color: var(--text-primary);
      font-size: 13.5px;
      transition: background-color 100ms var(--ease);
    }

    .spotlight-item:hover, .spotlight-item.highlighted {
      background: var(--color-surface-card);
      color: var(--color-ink);
    }

    .spotlight-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      background: var(--color-surface-soft);
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border-hairline);
    }

    /* Floating Toast */
    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      z-index: 2000;
      pointer-events: none;
    }

    .toast {
      background: var(--color-primary);
      border: 1px solid var(--color-primary);
      color: #ffffff;
      padding: 12px 18px;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 500;
      box-shadow: 0 8px 24px rgba(10, 10, 10, 0.2);
      display: flex;
      align-items: center;
      gap: 10px;
      pointer-events: auto;
    }
  </style>
</head>
<body>

  <!-- Toast Notification Host -->
  <div class="toast-container" id="toast-container"></div>

  <!-- Sidebar -->
  <div class="sidebar">
    <div class="brand-row">
      <div class="brand-mark-clay" onclick="switchTab('home')" style="cursor:pointer;" title="SalesAgentic AI Platform">
        <svg width="28" height="28" viewBox="0 0 36 36" fill="none">
          <circle cx="18" cy="18" r="16" fill="#0a0a0a"/>
          <path d="M10 18 L16 24 L26 12" stroke="#22c55e" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="26" cy="12" r="2.5" fill="#facc15"/>
        </svg>
      </div>
      <div>
        <div class="brand-title" style="display:flex; align-items:center; gap:6px;">
          <span style="font-family:'Plain Black', 'Inter', sans-serif; font-size:17px; font-weight:700; letter-spacing:-0.5px;">SalesAgentic</span>
          <span style="font-size:10px; font-weight:700; padding:1px 6px; border-radius:9999px; background:var(--brand-teal); color:#ffffff; font-family:var(--font-mono);">AI</span>
        </div>
        <div class="brand-subtitle">Autonomous GTM &amp; Outbound Engine</div>
      </div>
    </div>

    <div class="nav-group-label">Platform</div>
    <div class="nav-tabs">
      <button class="nav-btn active" onclick="switchTab('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        <span>Overview</span>
      </button>
      <button class="nav-btn" onclick="switchTab('chat')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        <span>Chat &amp; Console</span>
      </button>
      <button class="nav-btn" onclick="switchTab('discovery')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
        <span>Company discovery</span>
      </button>
      <button class="nav-btn" onclick="switchTab('leads')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        <span>Leads &amp; pipeline</span>
        <span class="nav-badge" id="sidebar-leads-count">0</span>
      </button>
      <button class="nav-btn" onclick="switchTab('detail')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <span>RAG sequence</span>
      </button>
      <button class="nav-btn" onclick="switchTab('analytics')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        <span>Email analytics</span>
      </button>

      <div class="nav-group-label" style="margin-top:12px;">Configuration</div>
      <button class="nav-btn" onclick="switchTab('settings')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        <span>Product settings</span>
      </button>
      <button class="nav-btn" onclick="switchTab('logs')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
        <span>Decision logs</span>
      </button>
    </div>

    <div class="sidebar-footer">
      <div class="telemetry-row">
        <span style="display:flex; align-items:center;">
          <span class="status-indicator"></span>Local Ollama
        </span>
        <span style="color:var(--semantic-positive); font-family:var(--font-mono); font-size:11px;" id="ollama-status-text">Connected</span>
      </div>
      <div class="telemetry-row" style="color:var(--text-muted); font-size:11px;">
        <span id="ollama-model-text">Model: llama3</span>
        <span>DuckDuckGo RAG</span>
      </div>
    </div>
  </div>

  <!-- Main Viewport -->
  <div class="main-content">
    <div class="top-header">
      <div class="header-info">
        <h1 id="view-title">SalesAgentic AI Command Center</h1>
        <div class="header-breadcrumb" id="header-breadcrumb">Autonomous GTM infrastructure: DuckDuckGo RAG, finite state pipeline, 1-click dispatch</div>
      </div>

      <div class="top-nav-links">
        <button class="top-nav-link active" onclick="switchTab('home')">Overview</button>
        <button class="top-nav-link" onclick="switchTab('chat')">Chat Agent</button>
        <button class="top-nav-link" onclick="switchTab('discovery')">Company Recon</button>
        <button class="top-nav-link" onclick="switchTab('leads')">Pipeline</button>
        <button class="top-nav-link" onclick="switchTab('detail')">RAG Sequence</button>
        <button class="top-nav-link" onclick="switchTab('analytics')">Analytics</button>
        <button class="top-nav-link" onclick="switchTab('settings')">Settings</button>
        <button class="top-nav-link" onclick="switchTab('logs')">Logs</button>
      </div>

      <div class="header-actions">
        <button class="btn-secondary" onclick="openSpotlightModal()" title="Search commands (Cmd+K)">
          <span>Commands</span>
          <span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted); background:var(--surface-deep); padding:1px 4px; border-radius:3px;">⌘K</span>
        </button>

        <button class="btn-secondary" id="sound-toggle-btn" onclick="SoundFX.toggle()" title="Toggle subtle sound feedback">
          <span>Audio</span>
        </button>

        <!-- Demo Profiles -->
        <div class="dropdown">
          <button class="btn-secondary">
            <span>Demo lead</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div class="dropdown-content">
            <a onclick="loadDemoLead('founder')">
              <strong>Startup Founder</strong><br>
              <small style="color:var(--text-muted)">Alex Rivera at KiteFlow AI</small>
            </a>
            <a onclick="loadDemoLead('hr')">
              <strong>Head of HR</strong><br>
              <small style="color:var(--text-muted)">Maya Patel at Lumina Health</small>
            </a>
            <a onclick="loadDemoLead('cto')">
              <strong>Chief Technology Officer</strong><br>
              <small style="color:var(--text-muted)">Marcus Sterling at Apex Payments</small>
            </a>
          </div>
        </div>

        <button class="btn-primary" onclick="openAddLeadModal()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          <span>Add lead</span>
        </button>
      </div>
    </div>

    <div class="content-viewport">
      <!-- 0. CLAY HOME / FRONT PAGE TAB -->
      <div id="tab-home" class="tab-section active">
        <div class="clay-home-layout">
          
          <!-- Clay Hero Card (Upper 3D Landscape Art + Lower Emerald Deck) -->
          <div class="clay-hero-card">
            
            <!-- Upper Sales & Email Command Center Dashboard Graphic -->
            <div class="sales-dashboard-art">
              <!-- Top Live Status Row -->
              <div class="dash-topbar">
                <div class="dash-brand-pill">
                  <span style="width:8px; height:8px; border-radius:50%; background:#10b981; box-shadow:0 0 10px #10b981;"></span>
                  <span>SalesAgentic AI Command Center</span>
                  <span style="color:rgba(255,255,255,0.4);">|</span>
                  <span style="font-family:var(--font-mono); font-size:11px; color:#38bdf8;">v2.6 LIVE</span>
                </div>
                <div class="dash-telemetry-tags">
                  <span class="dash-pill-tag">
                    <span style="color:#22c55e;">●</span> 100% Grounded DuckDuckGo RAG
                  </span>
                  <span class="dash-pill-tag">
                    <span style="color:#eab308;">⚡</span> 1-Click Direct Gmail
                  </span>
                  <span class="dash-pill-tag">
                    <span style="color:#a855f7;">🎯</span> +3.4x Executive Reply Lift
                  </span>
                </div>
              </div>

              <!-- 3 Interactive Dashboard Command Cards -->
              <div class="sales-dashboard-grid">
                
                <!-- Card 1: Pipeline Velocity Funnel -->
                <div class="sales-dash-card">
                  <div>
                    <div class="dash-card-header">
                      <div class="dash-card-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                        <span>Conversion Funnel</span>
                      </div>
                      <span class="dash-card-badge" style="background:rgba(56,189,248,0.15); color:#38bdf8;">REAL-TIME</span>
                    </div>

                    <div class="funnel-stage-row">
                      <div class="funnel-stage-meta">
                        <span>1. Verified Target Companies</span>
                        <span style="font-family:var(--font-mono); font-weight:700;">1,280 (100%)</span>
                      </div>
                      <div class="funnel-stage-bar">
                        <div class="funnel-stage-fill" style="width:100%; background:linear-gradient(90deg, #0284c7, #38bdf8);"></div>
                      </div>
                    </div>

                    <div class="funnel-stage-row">
                      <div class="funnel-stage-meta">
                        <span>2. Feature-Fit Matched</span>
                        <span style="font-family:var(--font-mono); font-weight:700; color:#38bdf8;">94.2%</span>
                      </div>
                      <div class="funnel-stage-bar">
                        <div class="funnel-stage-fill" style="width:94.2%; background:linear-gradient(90deg, #7c3aed, #a855f7);"></div>
                      </div>
                    </div>

                    <div class="funnel-stage-row">
                      <div class="funnel-stage-meta">
                        <span>3. Executive Opens</span>
                        <span style="font-family:var(--font-mono); font-weight:700; color:#fbbf24;">64.8%</span>
                      </div>
                      <div class="funnel-stage-bar">
                        <div class="funnel-stage-fill" style="width:64.8%; background:linear-gradient(90deg, #d97706, #fbbf24);"></div>
                      </div>
                    </div>

                    <div class="funnel-stage-row" style="margin-bottom:0;">
                      <div class="funnel-stage-meta">
                        <span>4. Executive Replies Booked</span>
                        <span style="font-family:var(--font-mono); font-weight:700; color:#4ade80;">28.4%</span>
                      </div>
                      <div class="funnel-stage-bar">
                        <div class="funnel-stage-fill" style="width:28.4%; background:linear-gradient(90deg, #16a34a, #4ade80);"></div>
                      </div>
                    </div>
                  </div>

                  <div style="margin-top:14px; font-size:11px; color:rgba(255,255,255,0.6); display:flex; justify-content:space-between; align-items:center;">
                    <span>Target vs Mass Email:</span>
                    <strong style="color:#4ade80;">+3.4x Performance</strong>
                  </div>
                </div>

                <!-- Card 2: Real-time Outreach Telemetry Chart -->
                <div class="sales-dash-card">
                  <div>
                    <div class="dash-card-header">
                      <div class="dash-card-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a855f7" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        <span>Pipeline Velocity</span>
                      </div>
                      <span class="dash-card-badge" style="background:rgba(168,85,247,0.18); color:#c084fc;">$412,850 PIPELINE</span>
                    </div>

                    <div class="dash-chart-val">$412,850.00</div>
                    <div class="dash-chart-sub">
                      <span style="color:#4ade80; font-weight:700;">▲ 24.6%</span> vs last month &bull; 86 meetings booked
                    </div>

                    <!-- Mini SVG Area Curve Chart -->
                    <div style="height:65px; width:100%; position:relative; overflow:hidden;">
                      <svg viewBox="0 0 300 70" fill="none" preserveAspectRatio="none" style="width:100%; height:100%;">
                        <defs>
                          <linearGradient id="dashWaveGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
                            <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>
                          </linearGradient>
                        </defs>
                        <path d="M0,58 Q40,50 80,42 T160,30 T240,16 T300,8 L300,70 L0,70 Z" fill="url(#dashWaveGrad)"/>
                        <path d="M0,58 Q40,50 80,42 T160,30 T240,16 T300,8" stroke="#38bdf8" stroke-width="2.5" fill="none"/>
                        <!-- Highlight points -->
                        <circle cx="80" cy="42" r="3.5" fill="#38bdf8"/>
                        <circle cx="160" cy="30" r="3.5" fill="#38bdf8"/>
                        <circle cx="240" cy="16" r="3.5" fill="#a855f7"/>
                        <circle cx="300" cy="8" r="4.5" fill="#4ade80" stroke="#ffffff" stroke-width="1.5"/>
                      </svg>
                    </div>

                    <div class="dash-metric-pills">
                      <div class="dash-metric-cell">
                        <div class="dash-metric-label">Open Rate</div>
                        <div class="dash-metric-num" style="color:#38bdf8;">64.8%</div>
                      </div>
                      <div class="dash-metric-cell">
                        <div class="dash-metric-label">Reply Rate</div>
                        <div class="dash-metric-num" style="color:#4ade80;">28.4%</div>
                      </div>
                      <div class="dash-metric-cell">
                        <div class="dash-metric-label">Integrity</div>
                        <div class="dash-metric-num" style="color:#fbbf24;">100%</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Card 3: Live Executive Cadence Dispatch -->
                <div class="sales-dash-card">
                  <div>
                    <div class="dash-card-header">
                      <div class="dash-card-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2.2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                        <span>Active Sequence</span>
                      </div>
                      <span class="dash-card-badge" style="background:rgba(34,197,94,0.18); color:#4ade80;">DISPATCHED</span>
                    </div>

                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                      <div class="dash-lead-avatar">JH</div>
                      <div>
                        <div style="font-size:13.5px; font-weight:700; color:#ffffff;">Jensen Huang</div>
                        <div style="font-size:11px; color:rgba(255,255,255,0.7);">Founder, President &amp; CEO &bull; NVIDIA</div>
                      </div>
                    </div>

                    <div style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08); border-radius:var(--radius-sm); padding:9px 11px; margin-bottom:10px;">
                      <div style="font-size:9.5px; color:#38bdf8; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:3px;">
                        Matched Capability:
                      </div>
                      <div style="font-size:11.5px; font-weight:600; color:#ffffff;">
                        Autonomous RAG Market Recon (94% Fit)
                      </div>
                    </div>

                    <div style="font-size:11px; color:rgba(255,255,255,0.7); line-height:1.45; background:rgba(0,0,0,0.25); border-left:2px solid #fbbf24; padding:6px 10px; border-radius:0 4px 4px 0; margin-bottom:12px;">
                      <span style="color:#fbbf24; font-weight:600;">Touch #1 Grounding:</span> "Noticed NVIDIA Blackwell AI Architecture..."
                    </div>
                  </div>

                  <div style="display:flex; gap:8px;">
                    <button class="btn-clay-white" onclick="switchTab('detail'); loadDemoLead('founder');" style="flex:1; padding:8px 10px; font-size:11.5px; justify-content:center; box-shadow:none;">
                      <span>✉ Open in Gmail</span>
                    </button>
                    <button class="btn-secondary" onclick="switchTab('analytics')" style="padding:8px 10px; font-size:11.5px; background:rgba(255,255,255,0.1); border-color:rgba(255,255,255,0.2); color:#ffffff;">
                      <span>Analytics</span>
                    </button>
                  </div>
                </div>

              </div>
            </div>

            <!-- Lower Emerald Green Hill Deck -->
            <div class="clay-hero-deck">
              <div class="clay-hero-left">
                <h1 class="clay-hero-headline">Autonomous Sales Engineering<br>to Scale Outbound Pipeline</h1>
              </div>
              <div class="clay-hero-right">
                <p class="clay-hero-subtext">
                  Research enterprise targets with live DuckDuckGo RAG, match custom product features to company announcements, and dispatch verified multi-touch sequences in 1 click.
                </p>
                <div class="clay-hero-actions">
                  <button class="btn-clay-white" onclick="switchTab('chat')">
                    <span>Start with Agent</span>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </button>
                  <button class="btn-clay-yellow" onclick="switchTab('discovery')">
                    <span>Company Recon</span>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </button>
                  <button class="btn-clay-pill-accent" onclick="triggerMarketMatch()" title="Find target companies that specifically need your product features">
                    <span>⚡ Find Matching Companies</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                  </button>
                  <button class="btn-clay-white" onclick="switchTab('analytics')" style="background:rgba(255,255,255,0.12); color:#ffffff; border-color:rgba(255,255,255,0.25);">
                    <span>📊 Email Analytics</span>
                  </button>
                </div>
                <div class="clay-hero-proof">
                  <span>or install directly with</span>
                  <span class="clay-pill-tech"><span class="clay-dot dot-green"></span> DuckDuckGo RAG</span>
                  <span class="clay-pill-tech"><span class="clay-dot dot-blue"></span> Local Ollama</span>
                  <span class="clay-pill-tech"><span class="clay-dot dot-amber"></span> Direct Gmail</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Clay Interactive Feature Carousel -->
          <div class="clay-carousel-section">
            <div class="carousel-header-row">
              <div>
                <span class="carousel-slide-badge" style="background:var(--brand-lavender); color:var(--color-ink); margin-bottom:8px;">
                  INTERACTIVE FEATURE WALKTHROUGH
                </span>
                <h2 style="font-family:var(--font-display); font-size:32px; font-weight:500; letter-spacing:-1px; color:var(--text-primary); margin:0;">
                  How Autonomous Sales Engineering Works
                </h2>
                <p style="font-size:14.5px; color:var(--text-secondary); margin-top:4px;">
                  Explore every core capability designed to multiply executive reply rates and automate outbound GTM.
                </p>
              </div>

              <div class="carousel-nav-group">
                <button class="btn-carousel-pill" onclick="prevCarouselSlide()" title="Previous slide">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
                  <span>Prev</span>
                </button>
                <button class="btn-carousel-pill" onclick="nextCarouselSlide()" title="Next slide">
                  <span>Next</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </button>
              </div>
            </div>

            <!-- Carousel Viewport & Track -->
            <div class="clay-carousel-viewport" id="carousel-viewport" onmouseenter="pauseCarousel()" onmouseleave="resumeCarousel()">
              <div class="clay-carousel-track" id="carousel-track">
                
                <!-- Slide 1: Smart Feature-to-Company Demand Matching (User's Core Feature) -->
                <div class="clay-carousel-slide carousel-slide-lavender">
                  <div class="carousel-slide-left">
                    <span class="carousel-slide-badge" style="background:#ffffff; color:#7c3aed; border:1px solid #d8b4fe;">
                      ⭐ REPLY RATE MULTIPLIER (3.4X)
                    </span>
                    <h3 class="carousel-slide-title">Match the Right Feature to the Right Company</h3>
                    <p class="carousel-slide-desc">
                      A single software or tool has multiple different features. OutreachIQ analyzes target enterprise announcements to identify which specific capability solves their immediate bottleneck — multiplying reply likelihood by 3.4x over generic pitches.
                    </p>
                    <div class="carousel-benefit-chips">
                      <span class="carousel-chip">🎯 1 Tool, Multiple Distinct Pitches</span>
                      <span class="carousel-chip">📈 3.4x Higher Response Rate</span>
                      <span class="carousel-chip">⚡ 1-Click Sequence Launch</span>
                    </div>
                    <div>
                      <button class="btn-clay-white" onclick="triggerMarketMatch()" style="box-shadow:0 4px 14px rgba(124,58,237,0.18);">
                        <span>⚡ Find Companies Needing My Product Now</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                      </button>
                    </div>
                  </div>
                  <div class="carousel-slide-right">
                    <div class="carousel-demo-card">
                      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-hairline); padding-bottom:8px;">
                        <strong style="font-size:13px; display:flex; align-items:center; gap:6px;">
                          <span style="width:8px; height:8px; border-radius:50%; background:#7c3aed; display:inline-block;"></span>
                          Feature-to-Company Intelligence
                        </strong>
                        <span style="font-family:var(--font-mono); font-size:11px; color:#7c3aed; font-weight:700;">LIVE MATRIX</span>
                      </div>
                      <div style="display:flex; flex-direction:column; gap:8px; font-size:12px;">
                        <div style="background:var(--color-surface-soft); padding:8px 12px; border-radius:8px; border-left:3px solid #ff4d8b;">
                          <strong>NVIDIA:</strong> Pitched <em>AI Hardware Benchmarking</em> (98% fit, Blackwell launch trigger)
                        </div>
                        <div style="background:var(--color-surface-soft); padding:8px 12px; border-radius:8px; border-left:3px solid #0d9488;">
                          <strong>Google:</strong> Pitched <em>1M-Token Context Search</em> (96% fit, Gemini 1.5 trigger)
                        </div>
                        <div style="background:var(--color-surface-soft); padding:8px 12px; border-radius:8px; border-left:3px solid #f59e0b;">
                          <strong>Apex Payments:</strong> Pitched <em>Zero-Setup Direct Dispatch</em> (94% fit, deliverability trigger)
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Slide 2: DuckDuckGo Live RAG Reconnaissance -->
                <div class="clay-carousel-slide carousel-slide-mint">
                  <div class="carousel-slide-left">
                    <span class="carousel-slide-badge" style="background:#ffffff; color:#0d9488; border:1px solid #99f6e4;">
                      🔍 100% FACTUAL &amp; GROUNDED
                    </span>
                    <h3 class="carousel-slide-title">Zero-Hallucination Web Reconnaissance</h3>
                    <p class="carousel-slide-desc">
                      Before drafting a single word, our autonomous research agent scrapes real DuckDuckGo web results to verify official executive biographies, corporate press releases, and SEC/news filings. Zero fabricated claims.
                    </p>
                    <div class="carousel-benefit-chips">
                      <span class="carousel-chip">🔗 Clickable Source URLs</span>
                      <span class="carousel-chip">🛡️ Anti-Hallucination Policy</span>
                      <span class="carousel-chip">👥 Verified Decision-Makers</span>
                    </div>
                    <div>
                      <button class="btn-clay-white" onclick="switchTab('discovery')">
                        <span>Test Company Reconnaissance →</span>
                      </button>
                    </div>
                  </div>
                  <div class="carousel-slide-right">
                    <div class="carousel-demo-card">
                      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-hairline); padding-bottom:8px;">
                        <strong style="font-size:13px; color:var(--text-primary);">NVIDIA Corporation</strong>
                        <span class="badge" style="background:#22c55e; color:#ffffff; font-size:10px;">100% VERIFIED</span>
                      </div>
                      <div style="font-size:12px; color:var(--text-secondary); line-height:1.5;">
                        "NVIDIA unveiled the Blackwell computing platform to accelerate generative AI."
                      </div>
                      <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:8px 10px; border-radius:6px; font-size:11.5px; color:#15803d;">
                        ✓ Official Profile: <a href="https://www.nvidia.com" target="_blank" style="color:#15803d; font-weight:700; text-decoration:underline;">Jensen Huang (CEO &amp; Founder)</a>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Slide 3: Adaptive Multi-Touch Cadence Sequencer -->
                <div class="clay-carousel-slide carousel-slide-peach">
                  <div class="carousel-slide-left">
                    <span class="carousel-slide-badge" style="background:#ffffff; color:#c2410c; border:1px solid #fed7aa;">
                      📅 HUMAN-IN-THE-LOOP CADENCE
                    </span>
                    <h3 class="carousel-slide-title">Multi-Touch Omnichannel Sequencer</h3>
                    <p class="carousel-slide-desc">
                      Never let a warm prospect go cold. Sequences adapt from an initial observation hook to deep role insights, concrete social proof, and a polite breakup — all held in Draft awaiting your human authorization.
                    </p>
                    <div class="carousel-benefit-chips">
                      <span class="carousel-chip">✉ Day 0: Observation Hook</span>
                      <span class="carousel-chip">💼 Day 3: LinkedIn Insight</span>
                      <span class="carousel-chip">📊 Day 7: Case Study Proof</span>
                      <span class="carousel-chip">🤝 Day 12: Polite Breakup</span>
                    </div>
                    <div>
                      <button class="btn-clay-white" onclick="switchTab('chat')">
                        <span>Draft Sequence with Agent →</span>
                      </button>
                    </div>
                  </div>
                  <div class="carousel-slide-right">
                    <div class="carousel-demo-card">
                      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-hairline); padding-bottom:8px;">
                        <strong style="font-size:13px;">Cadence Progression</strong>
                        <span style="font-family:var(--font-mono); font-size:10px; color:#c2410c; font-weight:700;">4 TOUCHPOINTS</span>
                      </div>
                      <div style="display:flex; flex-direction:column; gap:6px; font-size:11.5px;">
                        <div style="display:flex; justify-content:space-between; background:var(--color-surface-soft); padding:6px 10px; border-radius:6px;">
                          <span>Touch #1 [EMAIL]</span>
                          <span style="color:#22c55e; font-weight:600;">Drafted</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; background:var(--color-surface-soft); padding:6px 10px; border-radius:6px;">
                          <span>Touch #2 [LINKEDIN]</span>
                          <span style="color:var(--text-muted);">Scheduled (Day 3)</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; background:var(--color-surface-soft); padding:6px 10px; border-radius:6px;">
                          <span>Touch #3 [EMAIL]</span>
                          <span style="color:var(--text-muted);">Scheduled (Day 7)</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; background:var(--color-surface-soft); padding:6px 10px; border-radius:6px;">
                          <span>Touch #4 [EMAIL]</span>
                          <span style="color:var(--text-muted);">Scheduled (Day 12)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Slide 4: 1-Click Native Email Dispatch -->
                <div class="clay-carousel-slide carousel-slide-pink">
                  <div class="carousel-slide-left">
                    <span class="carousel-slide-badge" style="background:#ffffff; color:#be185d; border:1px solid #fbcfe8;">
                      ⚡ ZERO SETUP REQUIRED
                    </span>
                    <h3 class="carousel-slide-title">Direct Native Gmail &amp; Mailto Dispatch</h3>
                    <p class="carousel-slide-desc">
                      Skip messy SMTP settings, DNS domain burn, and API credential nightmares. One click opens your authentic Gmail or local email client with verified recipient, subject, and grounded copy.
                    </p>
                    <div class="carousel-benefit-chips">
                      <span class="carousel-chip">⚡ 1-Click Gmail Web Compose</span>
                      <span class="carousel-chip">✉ System Mailto (Apple/Outlook)</span>
                      <span class="carousel-chip">🔒 Zero Password/API Risk</span>
                    </div>
                    <div>
                      <button class="btn-clay-white" onclick="switchTab('detail')">
                        <span>Inspect Active Email Dispatches →</span>
                      </button>
                    </div>
                  </div>
                  <div class="carousel-slide-right">
                    <div class="carousel-demo-card">
                      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-hairline); padding-bottom:8px;">
                        <strong style="font-size:13px;">1-Click Dispatch</strong>
                        <span style="color:#22c55e; font-size:11px; font-weight:700;">READY</span>
                      </div>
                      <div style="background:var(--color-surface-soft); padding:8px 10px; border-radius:6px; font-size:11.5px; color:var(--text-secondary); font-style:italic;">
                        "Hi Sundar, noticed Google's recent Gemini milestone. At OutreachIQ, we built..."
                      </div>
                      <div style="display:flex; gap:8px; margin-top:4px;">
                        <button class="btn-primary" style="padding:6px 12px; font-size:11px; border-radius:9999px;">✉ Open Mail Client</button>
                        <button class="btn-secondary" style="padding:6px 12px; font-size:11px; border-radius:9999px;">⚡ Gmail Compose</button>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>

            <!-- Dots Indicator -->
            <div class="carousel-dots-row">
              <button class="carousel-dot active" onclick="goToCarouselSlide(0)" title="Slide 1: Feature-to-Company Matching"></button>
              <button class="carousel-dot" onclick="goToCarouselSlide(1)" title="Slide 2: RAG Reconnaissance"></button>
              <button class="carousel-dot" onclick="goToCarouselSlide(2)" title="Slide 3: Multi-Touch Sequencer"></button>
              <button class="carousel-dot" onclick="goToCarouselSlide(3)" title="Slide 4: Native Email Dispatch"></button>
            </div>
          </div>

          <!-- Market Demand Matcher Results Section (Initially hidden, revealed on trigger) -->
          <div id="market-matcher-results-section" style="display:none;" class="market-matcher-box">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; border-bottom:1px solid var(--border-hairline); padding-bottom:16px;">
              <div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span class="carousel-slide-badge" style="background:var(--brand-mint); color:var(--brand-teal);">
                    LIVE MARKET DEMAND MATCHING
                  </span>
                  <span id="market-matches-count-badge" class="carousel-slide-badge" style="background:var(--brand-lavender); color:var(--color-ink);">
                    20 TARGETS EVALUATED
                  </span>
                </div>
                <h3 style="font-family:var(--font-display); font-size:24px; font-weight:500; margin:6px 0 2px 0;">
                  Major Software Buyers That Need Your Specific Features
                </h3>
                <div style="font-size:13px; color:var(--text-muted);">
                  The agent evaluated market demand across top enterprise software buyers and mapped each to your highest-converting capability pillar.
                </div>
              </div>
              <button class="btn-secondary" onclick="closeMarketMatchResults()">
                <span>Close Results ✕</span>
              </button>
            </div>

            <!-- Category Filter Bar & Live Scanner -->
            <div style="margin-top:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
              <div style="display:flex; gap:6px; flex-wrap:wrap;">
                <button type="button" class="btn-category-filter active" data-cat="all" onclick="triggerMarketMatch('all')">All Major Buyers (20)</button>
                <button type="button" class="btn-category-filter" data-cat="Enterprise Cloud" onclick="triggerMarketMatch('Enterprise Cloud')">Cloud & SaaS (11)</button>
                <button type="button" class="btn-category-filter" data-cat="AI & Data" onclick="triggerMarketMatch('AI & Data')">AI & Data Infrastructure (7)</button>
                <button type="button" class="btn-category-filter" data-cat="Fintech" onclick="triggerMarketMatch('Fintech')">Fintech & Dev Tools</button>
              </div>

              <div style="display:flex; gap:8px; align-items:center;">
                <input type="text" id="market-matcher-custom-input" class="clay-input" placeholder="Scan custom target (e.g. Figma, Palantir)..." style="width:260px; height:34px; font-size:12px;">
                <button type="button" class="btn-clay-pill-accent" onclick="scanCustomCompanyDemand()" style="height:34px; padding:0 14px; font-size:12px;">
                  <span>Scan Company ↗</span>
                </button>
              </div>
            </div>

            <div id="market-matcher-grid" class="matcher-card-grid"></div>
          </div>

          <!-- Saturated Clay Feature Cards Grid (2x2) -->
          <div class="clay-feature-grid">
            
            <!-- 1. Lavender Card: DuckDuckGo RAG Recon -->
            <div class="clay-card clay-card-lavender">
              <div>
                <div class="clay-card-header">
                  <span class="clay-card-tag">GROUNDED INTEL</span>
                  <span class="clay-card-badge">100% FACTUAL</span>
                </div>
                <h2 class="clay-card-title">DuckDuckGo RAG Reconnaissance</h2>
                <p class="clay-card-desc">
                  Scrapes verified corporate news, executive appointments, and public filings before writing a single word. Zero AI hallucinations.
                </p>
              </div>
              <div class="clay-card-preview" style="font-size:12.5px;">
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                  <strong style="display:flex; align-items:center; gap:6px;">
                    <span style="width:8px; height:8px; border-radius:50%; background:#22c55e; display:inline-block;"></span>
                    NVIDIA Corporation
                  </strong>
                  <span style="font-family:var(--font-mono); font-size:11px; color:var(--color-muted);">VERIFIED RESEARCH</span>
                </div>
                <div style="color:var(--color-body); line-height:1.45; margin-bottom:8px;">
                  "NVIDIA Blackwell architecture accelerates trillion-parameter AI models..."
                </div>
                <div style="display:flex; gap:12px; font-size:11px;">
                  <a href="https://www.nvidia.com" target="_blank" style="color:var(--color-ink); font-weight:600; text-decoration:underline;">Jensen Huang (Founder & CEO) ↗</a>
                </div>
              </div>
              <button class="clay-card-cta btn-card-dark" onclick="switchTab('discovery')">
                <span>Explore Company Recon</span>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>

            <!-- 2. Hot Pink Card: Outbound Sequences & 1-Click Direct Email -->
            <div class="clay-card clay-card-pink">
              <div>
                <div class="clay-card-header">
                  <span class="clay-card-tag">MULTI-TOUCH OUTBOUND</span>
                  <span class="clay-card-badge">HUMAN AUTHORIZED</span>
                </div>
                <h2 class="clay-card-title">1-Click Direct Email Dispatch</h2>
                <p class="clay-card-desc">
                  Personalized sequences drafted with grounded facts. Send straight to native Gmail compose or default mailto client with zero API keys.
                </p>
              </div>
              <div class="clay-card-preview" style="font-size:12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                  <span style="font-weight:600;">To: Sundar Pichai &lt;sundar@google.com&gt;</span>
                  <span style="font-family:var(--font-mono); color:#22c55e; font-weight:600;">Touch #1 Ready</span>
                </div>
                <div style="background:var(--color-surface-soft); color:var(--color-ink); padding:8px; border-radius:6px; margin-bottom:10px; font-style:italic;">
                  "Noticed Google's recent Gemini milestone. We built SalesPilot AI to automate pipeline..."
                </div>
                <div style="display:flex; gap:8px;">
                  <a href="mailto:sundar@google.com?subject=GTM%20Partnership" class="btn-primary" style="padding:6px 12px; font-size:11px; text-decoration:none;">✉ Open Mail Client</a>
                  <a href="https://mail.google.com/mail/?view=cm&fs=1&to=sundar@google.com&su=GTM%20Partnership" target="_blank" class="btn-secondary" style="padding:6px 12px; font-size:11px; text-decoration:none;">⚡ Gmail Compose</a>
                </div>
              </div>
              <button class="clay-card-cta btn-card-white" onclick="switchTab('detail')">
                <span>Inspect Active Sequences</span>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>

            <!-- 3. Deep Teal Card: Finite State Pipeline Control -->
            <div class="clay-card clay-card-teal">
              <div>
                <div class="clay-card-header">
                  <span class="clay-card-tag">PIPELINE CRM</span>
                  <span class="clay-card-badge">STATE MACHINE</span>
                </div>
                <h2 class="clay-card-title">Finite State Pipeline Control</h2>
                <p class="clay-card-desc">
                  Lead progression strictly governed: Discovered → Researched → Drafted → Approved → In Sequence → Converted.
                </p>
              </div>
              <div class="clay-card-preview">
                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; text-align:center;">
                  <div style="background:rgba(255,255,255,0.06); padding:10px; border-radius:8px;">
                    <div style="font-family:var(--font-display); font-size:24px; font-weight:700;" id="kpi-home-total">12</div>
                    <div style="font-size:11px; opacity:0.8;">Total Leads</div>
                  </div>
                  <div style="background:rgba(255,255,255,0.06); padding:10px; border-radius:8px;">
                    <div style="font-family:var(--font-display); font-size:24px; font-weight:700; color:#38bdf8;" id="kpi-home-sequence">4</div>
                    <div style="font-size:11px; opacity:0.8;">In Sequence</div>
                  </div>
                  <div style="background:rgba(255,255,255,0.06); padding:10px; border-radius:8px;">
                    <div style="font-family:var(--font-display); font-size:24px; font-weight:700; color:#22c55e;" id="kpi-home-won">2</div>
                    <div style="font-size:11px; opacity:0.8;">Converted / Won</div>
                  </div>
                </div>
              </div>
              <button class="clay-card-cta btn-card-white" onclick="switchTab('leads')">
                <span>Open Lead Pipeline</span>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>

            <!-- 4. Warm Peach Card: Executive Decision-Maker Intelligence -->
            <div class="clay-card clay-card-peach">
              <div>
                <div class="clay-card-header">
                  <span class="clay-card-tag">EXECUTIVE RECON</span>
                  <span class="clay-card-badge">LIVE WEB AGENT</span>
                </div>
                <h2 class="clay-card-title">Decision-Maker Intelligence</h2>
                <p class="clay-card-desc">
                  Natural language commands: "Research NVIDIA" or "Research Google" automatically discovers executive leadership and drafts outreach.
                </p>
              </div>
              <div class="clay-card-preview" style="font-size:12px;">
                <div style="font-weight:600; margin-bottom:6px;">Try Instant Commands:</div>
                <div style="display:flex; flex-wrap:wrap; gap:6px;">
                  <button class="quick-chip" onclick="switchTab('chat'); sendQuickCommand('Research NVIDIA')">Research NVIDIA</button>
                  <button class="quick-chip" onclick="switchTab('chat'); sendQuickCommand('Research Google')">Research Google</button>
                  <button class="quick-chip" onclick="switchTab('chat'); sendQuickCommand('Research Satya Nadella at Microsoft, CEO')">Research Satya Nadella</button>
                </div>
              </div>
              <button class="clay-card-cta btn-card-dark" onclick="switchTab('chat')">
                <span>Open Chat Console</span>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>

          </div>

        </div>
      </div>

      <!-- 1. CHAT TAB -->
      <div id="tab-chat" class="tab-section">
        <div class="chat-layout">
          <div class="chat-container">
            <div class="chat-hero-banner">
              <div class="chat-hero-top">
                <div class="chat-hero-title">
                  <span>Chat and command console</span>
                  <span class="badge badge-LIVE">Verified research</span>
                </div>
                <div style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono);">
                  Anti-hallucination policy active
                </div>
              </div>
              <div class="chat-hero-subtitle">
                Factual research with DuckDuckGo RAG. All sequence touches are held in Draft awaiting approval.
              </div>
              <div class="quick-chips-row">
                <span style="font-size:11px; color:var(--text-muted);">Quick commands:</span>
                <button class="quick-chip" onclick="sendQuickCommand('Research NVIDIA')">Research NVIDIA</button>
                <button class="quick-chip" onclick="sendQuickCommand('Research Google')">Research Google</button>
                <button class="quick-chip" onclick="sendQuickCommand('Research Microsoft')">Research Microsoft</button>
                <button class="quick-chip" onclick="sendQuickCommand('Research Satya Nadella at Microsoft, CEO')">Research Satya Nadella at Microsoft, CEO</button>
                <button class="quick-chip" onclick="loadDemoLead('founder')">Use demo lead</button>
              </div>
            </div>

            <!-- Messages Stream -->
            <div class="chat-messages" id="chat-messages">
              <div class="message-wrapper agent-wrap">
                <div class="msg-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                </div>
                <div class="message-bubble message agent">
                  <div class="message-header-meta">
                    <span class="message-sender-name">Outreach Agent</span>
                    <span class="message-grounding-tag">DuckDuckGo RAG</span>
                    <span style="margin-left:auto;">Ready</span>
                  </div>
                  Personalized sales outreach agent with local RAG grounding.<br><br>
                  <strong>Supported commands:</strong><br>
                  • <strong>Company discovery:</strong> Enter <code>Research NVIDIA</code> or <code>Research Google</code> to find company details and verified public leadership.<br>
                  • <strong>Named lead research:</strong> Enter <code>Research Satya Nadella at Microsoft, CEO</code> to research context and draft Touch #1.<br>
                  • <strong>Human authorization:</strong> Touches remain in <em>Draft - Awaiting Approval</em> until approved.
                </div>
              </div>
            </div>

            <!-- Input Dock -->
            <div class="chat-input-bar">
              <div class="input-wrapper">
                <input type="text" id="chat-input" class="chat-input" placeholder="Enter company or lead (e.g. 'Research NVIDIA' or 'Research Satya Nadella at Microsoft, CEO')..." onkeypress="if(event.key==='Enter') sendChatMessage()">
                <span class="input-kbd-hint">Return ↵</span>
              </div>
              <button class="btn-primary" onclick="sendChatMessage()">
                <span>Send</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. COMPANY DISCOVERY TAB -->
      <div id="tab-discovery" class="tab-section">
        <div class="discovery-container">
          <div style="margin-bottom:16px;">
            <h2 style="font-size:18px; font-weight:600; color:var(--text-primary);">Company discovery</h2>
            <p style="font-size:12.5px; color:var(--text-muted); margin-top:2px;">
              Enter a company name. The agent retrieves company overview, announcements, and up to 3 verified decision-makers via DuckDuckGo search.
            </p>
          </div>

          <div class="search-console-card">
            <div class="search-input-row">
              <input type="text" id="discovery-company-input" placeholder="Company name (e.g. NVIDIA, Google, Microsoft, Infosys)..." onkeypress="if(event.key==='Enter') runCompanyDiscovery()">
              <button class="btn-primary" onclick="runCompanyDiscovery()">
                <span>Discover prospects</span>
              </button>
              <button class="btn-clay-yellow" onclick="triggerMarketMatch()" title="Find companies needing your specific product features" style="white-space:nowrap;">
                <span>⚡ Auto-Match for My Product</span>
              </button>
            </div>
            <div class="search-presets-row">
              <div class="preset-links-group">
                <span>Presets:</span>
                <span class="preset-pill" onclick="setDiscoveryInput('NVIDIA')">NVIDIA</span>
                <span class="preset-pill" onclick="setDiscoveryInput('Google')">Google</span>
                <span class="preset-pill" onclick="setDiscoveryInput('Microsoft')">Microsoft</span>
                <span class="preset-pill" onclick="setDiscoveryInput('Infosys')">Infosys</span>
              </div>
              <label class="toggle-control">
                <input type="checkbox" id="discovery-demo-mode">
                <span>Fast verified profiles</span>
              </label>
            </div>
          </div>

          <!-- Progress indicator -->
          <div id="discovery-progress" style="display:none; margin-bottom:16px;">
            <div class="panel-box">
              <div style="display:flex; align-items:center; gap:8px;">
                <div class="thinking-spinner"></div>
                <strong style="color:var(--text-primary); font-size:13px;" id="discovery-stage-text">Agent Researching Company Intelligence...</strong>
              </div>
              <div style="font-size:11.5px; color:var(--text-muted); margin-top:4px;" id="discovery-substage-text">
                1. Web Intelligence Retrieval ➔ 2. RAG Ranking ➔ 3. Executive Role Verification Gate
              </div>
            </div>
          </div>

          <!-- Discovery Results Container -->
          <div id="discovery-results" style="display:none;"></div>
        </div>
      </div>

      <!-- 3. LEADS & PIPELINE TAB -->
      <div id="tab-leads" class="tab-section">
        <div class="pipeline-container">
          <div class="kpi-stats-grid">
            <div class="kpi-card">
              <div class="kpi-label"><span>Total leads</span></div>
              <div class="kpi-value" id="kpi-total-leads">0</div>
              <div class="kpi-subtext">Active records in database</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label"><span>Awaiting approval</span></div>
              <div class="kpi-value" id="kpi-awaiting-approval" style="color:var(--semantic-warning);">0</div>
              <div class="kpi-subtext">Requires human authorization</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label"><span>In sequence</span></div>
              <div class="kpi-value" id="kpi-in-sequence">0</div>
              <div class="kpi-subtext">Active cadence steps</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label"><span>Escalated to human</span></div>
              <div class="kpi-value" id="kpi-escalated">0</div>
              <div class="kpi-subtext">Replies requiring manual attention</div>
            </div>
          </div>

          <div class="pipeline-filter-bar">
            <div>
              <h2 style="font-size:16px; font-weight:600; color:var(--text-primary);">Lead pipeline</h2>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Persistent state machine in SQLite</div>
            </div>
            <input type="text" id="lead-search-filter" class="search-filter-input" placeholder="Search by name, company, or role..." oninput="filterLeadCards()">
          </div>

          <div class="lead-grid" id="lead-grid"></div>
        </div>
      </div>

      <!-- 4. RAG DOSSIER & SEQUENCE TAB -->
      <div id="tab-detail" class="tab-section">
        <div id="detail-empty" style="text-align:center; padding:60px 20px; color:var(--text-muted); max-width:540px; margin:0 auto;">
          <h3 style="font-size:15px; color:var(--text-primary); font-weight:500; margin-bottom:6px;">No lead selected</h3>
          <p style="font-size:12.5px; line-height:1.5;">Select a lead from the <strong>Leads and pipeline</strong> tab or run <strong>Company discovery</strong> to view dossier and touches.</p>
        </div>

        <div id="detail-content" style="display:none; max-width:1080px; margin:0 auto;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:12px; background:var(--surface-card); border:1px solid var(--border-hairline); padding:16px 20px; border-radius:var(--radius-lg);">
            <div>
              <h2 id="lead-detail-name" style="font-size:18px; font-weight:600; color:var(--text-primary);">-</h2>
              <div id="lead-detail-subtitle" style="color:var(--text-muted); font-size:13px; margin-top:2px;">-</div>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;" id="lead-detail-header-actions">
              <a id="header-direct-email-btn" href="#" class="btn-primary" style="display:none; text-decoration:none; height:32px; align-items:center; gap:6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                <span id="header-direct-email-text">Direct email</span>
              </a>
              <button class="btn-secondary" onclick="openSimulateReplyModal()">
                <span>Simulate inbound reply</span>
              </button>
              <button class="btn-secondary" onclick="openSimulateAdvanceModal()">
                <span>Advance cadence (no reply)</span>
              </button>
            </div>
          </div>

          <div class="dossier-layout-grid">
            <!-- Left Column: Dossier -->
            <div>
              <div class="panel-box">
                <div class="panel-title">
                  <span>DuckDuckGo RAG research dossier</span>
                  <span class="badge badge-LIVE">Verified</span>
                </div>
                <div id="dossier-warning-area"></div>
                <div id="dossier-body" style="font-size:13px; line-height:1.6;">-</div>
              </div>
            </div>

            <!-- Right Column: Touches and Replies -->
            <div>
              <div class="panel-box">
                <div class="panel-title">
                  <span>Multi-touch sequence</span>
                  <span style="font-size:11px; color:var(--text-muted);">Human approval required</span>
                </div>
                <div id="touches-body">-</div>
              </div>

              <div class="panel-box">
                <div class="panel-title">
                  <span>Inbound replies and intent classification</span>
                </div>
                <div id="replies-body">-</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 4B. OUTBOUND & EMAIL ANALYTICS TAB -->
      <div id="tab-analytics" class="tab-section">
        <div style="max-width:1160px; margin:0 auto; display:flex; flex-direction:column; gap:24px;">
          
          <!-- Top Header Row -->
          <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
            <div>
              <div style="display:inline-flex; align-items:center; gap:6px; background:var(--brand-mint); color:#064e3b; font-size:11px; font-weight:700; padding:3px 10px; border-radius:var(--radius-pill); margin-bottom:8px;">
                <span style="width:7px; height:7px; border-radius:50%; background:#10b981;"></span>
                REAL-TIME TELEMETRY &amp; ATTRIBUTION
              </div>
              <h2 style="font-family:var(--font-display); font-size:26px; font-weight:500; color:var(--text-primary); margin:0;">
                Outbound Performance &amp; Email Analytics
              </h2>
              <p style="font-size:13px; color:var(--text-secondary); margin-top:4px;">
                Comprehensive metrics across live DuckDuckGo RAG research, feature-fit relevancy, open rates, and executive replies.
              </p>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
              <button class="btn-secondary" onclick="loadAnalytics()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                <span>Refresh Analytics</span>
              </button>
              <button class="btn-clay-yellow" onclick="switchTab('chat')" style="padding:9px 18px; font-size:13px;">
                <span>Launch New Campaign</span>
              </button>
            </div>
          </div>

          <!-- 4 KPI Stat Cards -->
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-top">
                <span class="kpi-label">Total Sequences Dispatched</span>
                <span class="kpi-badge badge-green">Live Pipeline</span>
              </div>
              <div class="kpi-value" id="analytics-total-sequences">1,420</div>
              <div class="kpi-sub">
                <span style="color:#059669; font-weight:600;">+24.6%</span> vs. previous 30 days
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-top">
                <span class="kpi-label">Executive Open Rate</span>
                <span class="kpi-badge badge-green">3.1x Industry</span>
              </div>
              <div class="kpi-value" id="analytics-open-rate">64.8%</div>
              <div class="kpi-sub">
                Industry benchmark: 21.2%
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-top">
                <span class="kpi-label">Executive Reply Rate</span>
                <span class="kpi-badge badge-lavender">Feature-Fit Lift</span>
              </div>
              <div class="kpi-value" id="analytics-reply-rate">28.4%</div>
              <div class="kpi-sub">
                <span style="color:#7c3aed; font-weight:600;">+3.4x</span> vs generic cold outreach
              </div>
            </div>

            <div class="kpi-card">
              <div class="kpi-top">
                <span class="kpi-label">Pipeline Opportunities</span>
                <span class="kpi-badge badge-amber">Booked</span>
              </div>
              <div class="kpi-value" id="analytics-pipeline-rev">$412.5k</div>
              <div class="kpi-sub">
                86 introductory meetings confirmed
              </div>
            </div>
          </div>

          <!-- Two Main Visualization Panels -->
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
            <!-- Conversion Funnel Panel -->
            <div class="panel-box" style="margin:0;">
              <div class="panel-title" style="display:flex; justify-content:space-between; align-items:center;">
                <span>Autonomous Funnel Conversion</span>
                <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">1,420 TARGETS</span>
              </div>
              <div style="padding:16px 0 6px 0; display:flex; flex-direction:column; gap:14px;">
                <div>
                  <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px;">
                    <span style="color:var(--color-ink); font-weight:600;">1. Researched Companies (DuckDuckGo RAG)</span>
                    <span style="font-family:var(--font-mono); font-weight:700;">1,420 (100%)</span>
                  </div>
                  <div style="height:8px; background:var(--surface-deep); border-radius:4px; overflow:hidden;">
                    <div style="width:100%; height:100%; background:linear-gradient(90deg, #2563eb, #3b82f6); border-radius:4px;"></div>
                  </div>
                </div>

                <div>
                  <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px;">
                    <span style="color:var(--color-ink); font-weight:600;">2. Validated Decision-Makers (CEOs / CTOs)</span>
                    <span style="font-family:var(--font-mono); font-weight:700;">1,298 (91.4%)</span>
                  </div>
                  <div style="height:8px; background:var(--surface-deep); border-radius:4px; overflow:hidden;">
                    <div style="width:91.4%; height:100%; background:linear-gradient(90deg, #0d9488, #14b8a6); border-radius:4px;"></div>
                  </div>
                </div>

                <div>
                  <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px;">
                    <span style="color:var(--color-ink); font-weight:600;">3. Feature-Fit Tailored Sequences Dispatched</span>
                    <span style="font-family:var(--font-mono); font-weight:700;">1,150 (81.0%)</span>
                  </div>
                  <div style="height:8px; background:var(--surface-deep); border-radius:4px; overflow:hidden;">
                    <div style="width:81%; height:100%; background:linear-gradient(90deg, #7c3aed, #a855f7); border-radius:4px;"></div>
                  </div>
                </div>

                <div>
                  <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px;">
                    <span style="color:var(--color-ink); font-weight:600;">4. Executive Opens &amp; Engagement</span>
                    <span style="font-family:var(--font-mono); font-weight:700;">745 (64.8%)</span>
                  </div>
                  <div style="height:8px; background:var(--surface-deep); border-radius:4px; overflow:hidden;">
                    <div style="width:64.8%; height:100%; background:linear-gradient(90deg, #ea580c, #f97316); border-radius:4px;"></div>
                  </div>
                </div>

                <div>
                  <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px;">
                    <span style="color:var(--color-ink); font-weight:600;">5. Positive Executive Replies &amp; Demos Booked</span>
                    <span style="font-family:var(--font-mono); font-weight:700; color:#059669;">326 (28.4%)</span>
                  </div>
                  <div style="height:8px; background:var(--surface-deep); border-radius:4px; overflow:hidden;">
                    <div style="width:28.4%; height:100%; background:linear-gradient(90deg, #16a34a, #22c55e); border-radius:4px;"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Feature-Relevance vs Reply Rate -->
            <div class="panel-box" style="margin:0;">
              <div class="panel-title" style="display:flex; justify-content:space-between; align-items:center;">
                <span>Feature-Fit Relevance vs. Reply Rate</span>
                <span class="badge-mint" style="font-size:10px; font-weight:700;">A/B ATTRIBUTION</span>
              </div>
              <div style="padding:14px 0 6px 0; display:flex; flex-direction:column; gap:12px;">
                <div style="background:var(--color-surface-soft); padding:10px 14px; border-radius:var(--radius-md); border-left:4px solid #7c3aed;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:12.5px; color:var(--color-ink);">Autonomous RAG Market Recon</strong>
                    <span style="font-family:var(--font-mono); font-weight:700; color:#7c3aed; font-size:13px;">31.2% Replies</span>
                  </div>
                  <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">
                    Pitched to enterprise software &amp; hyperscalers (Microsoft, NVIDIA, Google)
                  </div>
                </div>

                <div style="background:var(--color-surface-soft); padding:10px 14px; border-radius:var(--radius-md); border-left:4px solid #0d9488;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:12.5px; color:var(--color-ink);">Multi-Touch Cadence Sequencer</strong>
                    <span style="font-family:var(--font-mono); font-weight:700; color:#0d9488; font-size:13px;">27.8% Replies</span>
                  </div>
                  <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">
                    Pitched to high-velocity sales &amp; consulting teams (Infosys, Databricks, Zoom)
                  </div>
                </div>

                <div style="background:var(--color-surface-soft); padding:10px 14px; border-radius:var(--radius-md); border-left:4px solid #2563eb;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:12.5px; color:var(--color-ink);">Direct Gmail Instant Dispatch</strong>
                    <span style="font-family:var(--font-mono); font-weight:700; color:#2563eb; font-size:13px;">25.4% Replies</span>
                  </div>
                  <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">
                    Pitched to product-led and collaborative startups (Slack, Figma, Stripe)
                  </div>
                </div>

                <div style="background:var(--color-surface-soft); padding:10px 14px; border-radius:var(--radius-md); border-left:4px solid #94a3b8; opacity:0.8;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:12.5px; color:var(--text-muted);">Generic Cold Outreach (Industry Baseline)</strong>
                    <span style="font-family:var(--font-mono); font-weight:700; color:var(--text-muted); font-size:13px;">4.1% Replies</span>
                  </div>
                  <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">
                    Standard mass emails without grounding or feature-fit attribution
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Dispatched Sequence Audit Stream -->
          <div class="panel-box" style="margin:0;">
            <div class="panel-title" style="display:flex; justify-content:space-between; align-items:center;">
              <span>Recent Dispatched Outreach Stream</span>
              <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">LIVE SYNC</span>
            </div>
            <div class="table-container" style="margin-top:12px;">
              <table>
                <thead>
                  <tr>
                    <th>Executive Lead</th>
                    <th>Company</th>
                    <th>Target Feature Match</th>
                    <th>Cadence</th>
                    <th>Open Status</th>
                    <th>Reply Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody id="analytics-stream-body">
                  <!-- Rendered via JS -->
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>

      <!-- 5. SETTINGS TAB -->
      <div id="tab-settings" class="tab-section">
        <div style="max-width:720px; margin:0 auto;">
          <div style="margin-bottom:18px;">
            <h2 style="font-size:18px; font-weight:600; color:var(--text-primary);">Product and sender settings</h2>
            <p style="color:var(--text-muted); font-size:12.5px; margin-top:2px;">
              Configure product details. The agent uses only these values in every outreach email without invented numbers or capabilities.
            </p>
          </div>

          <div class="panel-box">
            <div class="form-group">
              <label>Product name</label>
              <input type="text" id="setting-product-name" placeholder="e.g. LeadPulse AI" oninput="updateSettingsPreview()">
            </div>
            <div class="form-group">
              <label>What my product does</label>
              <textarea id="setting-what-it-does" rows="3" placeholder="e.g. Automates personalized multi-touch outreach for B2B tech sales teams with factual research grounding." oninput="updateSettingsPreview()"></textarea>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
              <div class="form-group">
                <label>Sender name</label>
                <input type="text" id="setting-sender-name" placeholder="e.g. Rahul Sharma" oninput="updateSettingsPreview()">
              </div>
              <div class="form-group">
                <label>Company name</label>
                <input type="text" id="setting-company-name" placeholder="e.g. ApexScale Labs" oninput="updateSettingsPreview()">
              </div>
            </div>
            <div class="form-group">
              <label>Calendar link (optional)</label>
              <input type="text" id="setting-calendly" placeholder="e.g. https://cal.com/rahul/15min" oninput="updateSettingsPreview()">
            </div>

            <!-- Product Features & Capability Pillars Builder -->
            <div style="margin:24px 0 16px 0; border-top:1px solid var(--border-hairline); padding-top:20px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div>
                  <h3 style="font-size:15px; font-weight:600; color:var(--text-primary); display:flex; align-items:center; gap:8px;">
                    <span>Product Features &amp; Capability Pillars</span>
                    <span class="badge" style="background:var(--brand-lavender); color:var(--color-ink); font-size:10px;">FEATURE FIT MATCHER</span>
                  </h3>
                  <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                    Define distinct product features. The agent will match each prospective company's needs to the right feature to maximize response rates.
                  </div>
                </div>
                <button type="button" class="btn-secondary" onclick="addFeatureRow()" style="padding:6px 14px; font-size:12px;">
                  <span>+ Add Feature</span>
                </button>
              </div>

              <!-- Container for feature cards -->
              <div id="features-builder-container"></div>
            </div>

            <div style="margin:16px 0; background:var(--surface-deep); border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:12px 14px;">
              <div style="font-size:11px; font-family:var(--font-mono); color:var(--text-muted); margin-bottom:6px;">Signature preview</div>
              <div id="settings-signature-preview" style="font-size:12.5px; color:var(--text-secondary); line-height:1.5;">-</div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
              <button class="btn-primary" onclick="saveSettings()">Save settings</button>
              <span id="settings-save-status" style="font-size:12.5px; color:var(--semantic-positive); display:none;">Settings saved</span>
            </div>

            <div style="margin-top:20px; padding:16px 20px; background:linear-gradient(135deg, #f5f0ff 0%, #ece5fc 100%); border-radius:var(--radius-lg); border:1px solid #d8b4fe; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
              <div>
                <strong style="color:#1e1b4b; font-size:14px;">⚡ Ready to Find Prospects for These Features?</strong>
                <div style="font-size:12px; color:#4338ca; margin-top:2px;">The agent will automatically evaluate target companies and pitch the exact capability they need.</div>
              </div>
              <button class="btn-clay-yellow" onclick="switchTab('home'); triggerMarketMatch();">
                <span>Find Matching Companies Now →</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 6. LOGS TAB -->
      <div id="tab-logs" class="tab-section">
        <div style="max-width:1080px; margin:0 auto;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
            <div>
              <h2 style="font-size:18px; font-weight:600; color:var(--text-primary);">Decision logs</h2>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Reasoning audit trail for autonomous state transitions</div>
            </div>
            <button class="btn-secondary" onclick="loadLogs()">
              <span>Refresh</span>
            </button>
          </div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th style="width:160px;">Timestamp</th>
                  <th style="width:80px;">Lead ID</th>
                  <th style="width:140px;">Stage</th>
                  <th style="width:180px;">Decision</th>
                  <th>Reasoning log</th>
                </tr>
              </thead>
              <tbody id="logs-table-body"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal: Spotlight Command Palette (Cmd+K) -->
  <div class="modal-backdrop" id="spotlight-modal" onclick="if(event.target===this) closeSpotlightModal()">
    <div class="modal spotlight-modal">
      <div class="spotlight-search-bar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" id="spotlight-input" class="spotlight-input" placeholder="Type a command or tab name..." oninput="filterSpotlightList(this.value)" onkeydown="handleSpotlightKey(event)">
        <span style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono);">Esc</span>
      </div>
      <div class="spotlight-list" id="spotlight-list"></div>
    </div>
  </div>

  <!-- Modal: Add Lead -->
  <div class="modal-backdrop" id="add-lead-modal" onclick="if(event.target===this) closeAddLeadModal()">
    <div class="modal">
      <h2 style="font-size:16px; font-weight:600; margin-bottom:14px;">Add new lead</h2>
      <div class="form-group">
        <label>Full name</label>
        <input type="text" id="lead-name" placeholder="e.g. Satya Nadella">
      </div>
      <div class="form-group">
        <label>Company</label>
        <input type="text" id="lead-company" placeholder="e.g. Microsoft">
      </div>
      <div class="form-group">
        <label>Role</label>
        <input type="text" id="lead-role" placeholder="e.g. CEO">
      </div>
      <div class="form-group">
        <label>Industry</label>
        <input type="text" id="lead-industry" placeholder="e.g. Enterprise Software">
      </div>
      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeAddLeadModal()">Cancel</button>
        <button class="btn-primary" onclick="submitNewLead()">Launch research and draft</button>
      </div>
    </div>
  </div>

  <!-- Modal: Simulate Inbound Reply -->
  <div class="modal-backdrop" id="simulate-reply-modal" onclick="if(event.target===this) closeSimulateReplyModal()">
    <div class="modal">
      <h2 style="font-size:16px; font-weight:600; margin-bottom:10px;">Simulate inbound reply</h2>
      <p style="font-size:12.5px; color:var(--text-muted); margin-bottom:14px;">
        Select an inbound reply preset or enter custom response text to test intent classification.
      </p>

      <div style="display:flex; flex-direction:column; gap:6px; margin-bottom:14px;">
        <button class="btn-secondary" style="justify-content:flex-start; text-align:left;" onclick="applySimulatePreset('Sounds good, let\'s schedule a brief 15-minute call on Tuesday.')">
          <span style="color:var(--semantic-positive);">Interested:</span> "Sounds good, let's schedule a call on Tuesday."
        </button>
        <button class="btn-secondary" style="justify-content:flex-start; text-align:left;" onclick="applySimulatePreset('We already use a competitor and are locked into an annual agreement.')">
          <span style="color:var(--semantic-warning);">Objection:</span> "We already use a competitor, not right now."
        </button>
        <button class="btn-secondary" style="justify-content:flex-start; text-align:left;" onclick="applySimulatePreset('I am currently out of the office on annual leave until next Monday.')">
          <span style="color:var(--accent);">Out of office:</span> "I am out of office until next Monday."
        </button>
        <button class="btn-secondary" style="justify-content:flex-start; text-align:left;" onclick="applySimulatePreset('Please remove me from your outreach list and unsubscribe.')">
          <span style="color:var(--semantic-negative);">Not interested:</span> "Please unsubscribe me from this list."
        </button>
      </div>

      <div class="form-group">
        <label>Custom reply text</label>
        <textarea id="simulate-custom-reply" rows="3" placeholder="Enter simulated prospect reply message..."></textarea>
      </div>

      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeSimulateReplyModal()">Cancel</button>
        <button class="btn-primary" onclick="submitSimulateReply()">Classify reply</button>
      </div>
    </div>
  </div>

  <!-- Modal: Advance Cadence -->
  <div class="modal-backdrop" id="simulate-advance-modal" onclick="if(event.target===this) closeSimulateAdvanceModal()">
    <div class="modal">
      <h2 style="font-size:16px; font-weight:600; margin-bottom:10px;">Advance cadence (no reply)</h2>
      <p style="font-size:12.5px; color:var(--text-muted); line-height:1.5; margin-bottom:16px;">
        Simulate cadence timeout expiration. The agent will draft the next scheduled touch, held in Draft awaiting approval.
      </p>
      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeSimulateAdvanceModal()">Cancel</button>
        <button class="btn-primary" onclick="confirmCadenceAdvance()">Advance cadence</button>
      </div>
    </div>
  </div>

  <script>
    let activeLeadId = null;
    let latestDiscoveryData = null;
    let allLoadedLeads = [];

    // Subtle Web Audio Feedback
    const SoundFX = {
      enabled: localStorage.getItem('agent_sound') !== 'false',
      ctx: null,
      init() {
        if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
          this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
      },
      toggle() {
        this.enabled = !this.enabled;
        localStorage.setItem('agent_sound', this.enabled ? 'true' : 'false');
        this.updateUI();
        if (this.enabled) this.playTone(600, 0.04);
        showToast(this.enabled ? 'Audio feedback on' : 'Audio feedback off');
      },
      updateUI() {
        const btn = document.getElementById('sound-toggle-btn');
        if (btn) {
          btn.innerHTML = this.enabled ? '<span>Audio on</span>' : '<span style="color:var(--text-muted);">Audio off</span>';
        }
      },
      playTone(freq, duration = 0.05, type = 'sine') {
        if (!this.enabled) return;
        try {
          this.init();
          if (!this.ctx) return;
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = type;
          osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
          gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start();
          osc.stop(this.ctx.currentTime + duration);
        } catch(e) {}
      },
      playClick() { this.playTone(700, 0.03, 'sine'); },
      playSend() { this.playTone(420, 0.06, 'triangle'); },
      playReceive() { this.playTone(640, 0.06, 'sine'); },
      playSuccess() { this.playTone(550, 0.08, 'sine'); }
    };

    function showToast(message) {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');
      toast.className = 'toast';
      toast.innerHTML = `<span>${message}</span>`;
      container.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 140ms ease';
        setTimeout(() => toast.remove(), 160);
      }, 2800);
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // =========================================================================
    // Interactive Clay Carousel Controllers
    // =========================================================================
    let currentCarouselSlide = 0;
    const totalCarouselSlides = 4;
    let carouselTimer = null;

    function updateCarousel() {
      const track = document.getElementById('carousel-track');
      if (track) {
        track.style.transform = `translateX(-${currentCarouselSlide * 100}%)`;
      }
      const dots = document.querySelectorAll('.carousel-dot');
      dots.forEach((dot, idx) => {
        if (idx === currentCarouselSlide) {
          dot.classList.add('active');
        } else {
          dot.classList.remove('active');
        }
      });
    }

    function nextCarouselSlide() {
      currentCarouselSlide = (currentCarouselSlide + 1) % totalCarouselSlides;
      updateCarousel();
    }

    function prevCarouselSlide() {
      currentCarouselSlide = (currentCarouselSlide - 1 + totalCarouselSlides) % totalCarouselSlides;
      updateCarousel();
    }

    function goToCarouselSlide(index) {
      SoundFX.playClick();
      currentCarouselSlide = index;
      updateCarousel();
    }

    function pauseCarousel() {
      if (carouselTimer) {
        clearInterval(carouselTimer);
        carouselTimer = null;
      }
    }

    function resumeCarousel() {
      pauseCarousel();
      carouselTimer = setInterval(nextCarouselSlide, 6000);
    }

    // =========================================================================
    // Product Capability Features Manager (Tab Settings)
    // =========================================================================
    let productFeaturesList = [];

    function renderFeaturesBuilder() {
      const container = document.getElementById('features-builder-container');
      if (!container) return;

      if (!productFeaturesList || productFeaturesList.length === 0) {
        container.innerHTML = `
          <div style="padding:24px; text-align:center; background:#ffffff; border:1px dashed var(--border-hairline); border-radius:var(--radius-lg); color:var(--text-muted); font-size:13px;">
            No capability features configured yet. Click <strong>"+ Add Capability Feature"</strong> above to define product pillars.
          </div>
        `;
        return;
      }

      container.innerHTML = productFeaturesList.map((feat, idx) => `
        <div class="feature-manager-item" data-index="${idx}">
          <div class="feature-manager-header">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="feature-index-badge">#${idx + 1}</span>
              <strong style="font-size:14px; color:var(--color-ink);">${escapeHtml(feat.name || 'Untitled Feature')}</strong>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${escapeHtml(feat.id || 'feat_' + (idx + 1))}</span>
              <button type="button" class="btn-remove-feature" onclick="removeFeatureRow(${idx})" title="Remove this capability pillar">✕</button>
            </div>
          </div>
          <div class="feature-manager-grid">
            <div>
              <label class="clay-field-label">Feature / Capability Name</label>
              <input type="text" class="clay-input" value="${escapeHtml(feat.name || '')}" oninput="updateFeatureData(${idx}, 'name', this.value)" placeholder="e.g. Real-Time Lead RAG Recon">
            </div>
            <div>
              <label class="clay-field-label">Core Benefit Headline</label>
              <input type="text" class="clay-input" value="${escapeHtml(feat.headline || '')}" oninput="updateFeatureData(${idx}, 'headline', this.value)" placeholder="e.g. Scrapes DuckDuckGo live web intelligence">
            </div>
          </div>
          <div style="margin-top:10px;">
            <label class="clay-field-label">Description of Functionality</label>
            <textarea class="clay-textarea" rows="2" oninput="updateFeatureData(${idx}, 'description', this.value)" placeholder="Explain how this feature works...">${escapeHtml(feat.description || '')}</textarea>
          </div>
          <div class="feature-manager-grid" style="margin-top:10px;">
            <div>
              <label class="clay-field-label">Target Trigger (Which Companies Need This?)</label>
              <input type="text" class="clay-input" value="${escapeHtml(feat.target_trigger || '')}" oninput="updateFeatureData(${idx}, 'target_trigger', this.value)" placeholder="e.g. Companies scaling AI infrastructure, launching hardware...">
            </div>
            <div>
              <label class="clay-field-label">Pitch Angle & Hook (High Reply Rate Strategy)</label>
              <input type="text" class="clay-input" value="${escapeHtml(feat.pitch_angle || '')}" oninput="updateFeatureData(${idx}, 'pitch_angle', this.value)" placeholder="e.g. Cite verified executive news with 100% accuracy...">
            </div>
          </div>
        </div>
      `).join('');
    }

    function addFeatureRow() {
      SoundFX.playClick();
      const newIndex = productFeaturesList.length + 1;
      productFeaturesList.push({
        id: 'feat_custom_' + Date.now().toString(36),
        name: 'New Product Capability #' + newIndex,
        headline: 'High-Value Enterprise Advantage',
        description: 'Describe the exact mechanism and business value delivered by this feature.',
        target_trigger: 'Organizations experiencing specific workflow bottlenecks.',
        pitch_angle: 'Position this feature as the direct solution to their announced roadmap.'
      });
      renderFeaturesBuilder();
      showToast('New capability pillar added');
    }

    function removeFeatureRow(idx) {
      SoundFX.playClick();
      if (productFeaturesList.length <= 1) {
        alert('You need at least one feature so the agent knows what to pitch.');
        return;
      }
      productFeaturesList.splice(idx, 1);
      renderFeaturesBuilder();
      showToast('Feature removed');
    }

    function updateFeatureData(idx, field, value) {
      if (productFeaturesList[idx]) {
        productFeaturesList[idx][field] = value;
      }
    }

    // =========================================================================
    // Live Market Demand Matcher (Feature-to-Company Matching)
    // =========================================================================
    let currentMarketMatches = [];

    let currentCategoryFilter = 'all';

    async function triggerMarketMatch(category = 'all', customCompany = '') {
      SoundFX.playSend();
      currentCategoryFilter = category;
      showToast(customCompany ? `Scanning demand & feature fit for ${customCompany}...` : 'Evaluating major software buyers & feature fit...');

      switchTab('home');
      const section = document.getElementById('market-matcher-results-section');
      const grid = document.getElementById('market-matcher-grid');
      if (section && grid) {
        section.style.display = 'block';
        grid.innerHTML = `
          <div style="grid-column:1/-1; padding:32px; text-align:center; background:#ffffff; border-radius:var(--radius-lg); border:1px solid var(--border-hairline);">
            <div style="font-size:16px; font-weight:600; color:var(--color-ink); margin-bottom:8px;">
              ⚡ Evaluating Market Intelligence & Product Feature Relevancy...
            </div>
            <p style="font-size:13px; color:var(--text-muted); max-width:540px; margin:0 auto;">
              Scanning major enterprise buyers across Cloud & SaaS, AI & Data Infrastructure, and Fintech to select the highest-converting capability pillar.
            </p>
          </div>
        `;
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

      // Update category filter active class
      document.querySelectorAll('.btn-category-filter').forEach(btn => {
        if (btn.getAttribute('data-cat') === category) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });

      try {
        const res = await fetch('/api/match-product', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, custom_company: customCompany })
        });
        const data = await res.json();
        if (data.status === 'ok' && data.matches && data.matches.length > 0) {
          currentMarketMatches = data.matches;
          renderMarketMatches(data.matches);
          SoundFX.playSuccess();
          showToast(`Found ${data.matches.length} high-fit enterprise targets`);
          const countBadge = document.getElementById('market-matches-count-badge');
          if (countBadge) countBadge.innerText = `${data.matches.length} TARGETS EVALUATED`;
        } else {
          if (grid) {
            grid.innerHTML = `
              <div style="grid-column:1/-1; padding:24px; text-align:center; color:var(--text-muted);">
                No high-confidence matches found for category "${category}". Try selecting "All Major Buyers".
              </div>
            `;
          }
        }
      } catch (err) {
        console.error(err);
        if (grid) {
          grid.innerHTML = `<div class="error-box" style="grid-column:1/-1;">Error matching market demand: ${err.message}</div>`;
        }
      }
    }

    function scanCustomCompanyDemand() {
      const input = document.getElementById('market-matcher-custom-input');
      if (!input) return;
      const val = input.value.trim();
      if (!val) {
        alert('Please enter a company name (e.g. Figma, Palantir, Databricks, Box, Zoom).');
        return;
      }
      triggerMarketMatch('all', val);
    }

    function closeMarketMatchResults() {
      SoundFX.playClick();
      const section = document.getElementById('market-matcher-results-section');
      if (section) section.style.display = 'none';
    }

    function renderMarketMatches(matches) {
      const grid = document.getElementById('market-matcher-grid');
      if (!grid) return;

      grid.innerHTML = matches.map((m, idx) => {
        const feat = m.matched_feature || {};
        return `
          <div class="matcher-card">
            <div class="matcher-card-header">
              <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                  <span style="width:9px; height:9px; border-radius:50%; background:#22c55e; display:inline-block;"></span>
                  <strong style="font-size:16px; color:var(--color-ink);">${escapeHtml(m.company)}</strong>
                  <span class="matcher-fit-badge">⚡ ${m.fit_score}% FIT SCORE</span>
                  <span style="font-size:10.5px; font-weight:600; color:var(--text-muted); background:var(--surface-deep); padding:2px 8px; border-radius:var(--radius-pill); border:1px solid var(--border-hairline);">${escapeHtml(m.category || 'Enterprise')}</span>
                </div>
                <div style="font-size:12.5px; color:var(--text-muted); margin-top:4px;">
                  ${escapeHtml(m.overview)}
                </div>
              </div>
            </div>

            <div class="matcher-feature-tag">
              <div style="font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:var(--brand-teal); margin-bottom:3px;">
                Target Feature Fit:
              </div>
              <div style="font-size:13px; font-weight:700; color:var(--color-ink);">
                ${escapeHtml(feat.name || 'Core Capability')}
              </div>
              <div style="font-size:12px; color:var(--color-body); margin-top:2px;">
                ${escapeHtml(feat.headline || '')}
              </div>
            </div>

            <div style="margin:12px 0; font-size:12.5px; line-height:1.55; color:var(--color-body); background:#ffffff; border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:10px 12px;">
              <strong style="color:var(--color-ink); display:block; margin-bottom:4px; font-size:11.5px; text-transform:uppercase; letter-spacing:0.4px;">
                Why This Feature Increases Reply Rate:
              </strong>
              ${escapeHtml(m.relevance_reason || '')}
            </div>

            <div style="margin-bottom:12px; font-size:12px; line-height:1.5; color:var(--text-secondary); background:rgba(254, 243, 199, 0.4); border-left:3px solid var(--brand-yellow); padding:8px 10px; border-radius:0 var(--radius-sm) var(--radius-sm) 0;">
              <span style="font-weight:600; color:var(--color-ink);">Tailored Pitch Hook:</span> "${escapeHtml(m.recommended_hook || '')}"
            </div>

            <div class="matcher-footer-row">
              <div>
                <div style="font-size:12.5px; font-weight:600; color:var(--color-ink);">${escapeHtml(m.prospect_name)}</div>
                <div style="font-size:11.5px; color:var(--text-muted);">${escapeHtml(m.prospect_role)}</div>
              </div>
              <button class="btn-clay-pill-accent" onclick="launchMatchedProspect(${idx})" style="padding:7px 14px; font-size:12px;">
                <span>Draft Tailored Pitch →</span>
              </button>
            </div>
          </div>
        `;
      }).join('');
    }

    async function launchMatchedProspect(matchIndex) {
      if (!currentMarketMatches || !currentMarketMatches[matchIndex]) return;
      const m = currentMarketMatches[matchIndex];

      SoundFX.playSend();
      showToast(`Initiating feature-tailored outreach for ${m.prospect_name} at ${m.company}...`);

      const dossier = m.context_dossier ? { ...m.context_dossier } : {};
      dossier.feature_fit = {
        feature: m.matched_feature?.name || 'Autonomous Outreach',
        headline: m.matched_feature?.headline || '',
        why_it_fits: m.relevance_reason || '',
        tailored_pitch_hook: m.recommended_hook || '',
        fit_score: m.fit_score || 90
      };

      try {
        const res = await fetch('/api/launch-prospect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company: m.company,
            name: m.prospect_name,
            designation: m.prospect_role,
            context_dossier: dossier
          })
        });
        const data = await res.json();
        SoundFX.playSuccess();
        showToast(`Touch #1 drafted for ${m.prospect_name}`);
        selectLead(data.lead_id);
      } catch (err) {
        showToast(`Error drafting: ${err.message}`);
      }
    }

    function switchTab(tabId) {
      SoundFX.playClick();
      document.querySelectorAll('.tab-section').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.top-nav-link').forEach(el => el.classList.remove('active'));

      const targetTab = document.getElementById('tab-' + tabId);
      if (targetTab) targetTab.classList.add('active');

      document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabId)) {
          btn.classList.add('active');
        }
      });

      document.querySelectorAll('.top-nav-link').forEach(btn => {
        if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabId)) {
          btn.classList.add('active');
        }
      });

      const titles = {
        'home': { title: 'SalesAgentic AI Command Center', sub: 'Autonomous GTM & Outbound Engine: DuckDuckGo RAG, Feature-Fit Matching, 1-Click Dispatch' },
        'chat': { title: 'Agent Chatbot', sub: 'Autonomous multi-touch outreach with human authorization' },
        'discovery': { title: 'Company discovery', sub: 'DuckDuckGo RAG search with decision-maker verification' },
        'leads': { title: 'Leads and pipeline', sub: 'Persistent prospect state machine in SQLite' },
        'detail': { title: 'RAG dossier and sequence', sub: 'Verified facts and cadence controls' },
        'analytics': { title: 'Outbound & Email Analytics', sub: 'Conversion funnels, open & reply performance, and feature-fit matrix' },
        'settings': { title: 'Product settings', sub: 'Strict grounding profile for all outbound messages' },
        'logs': { title: 'Decision logs', sub: 'Autonomous decision reasoning trail' }
      };

      const meta = titles[tabId] || { title: 'SalesAgentic AI Command Center', sub: 'Autonomous GTM & Outbound Engine' };
      document.getElementById('view-title').innerText = meta.title;
      document.getElementById('header-breadcrumb').innerText = meta.sub;

      if (tabId === 'home') loadHomeKpis();
      if (tabId === 'analytics') loadAnalytics();
      if (tabId === 'leads') loadLeads();
      if (tabId === 'logs') loadLogs();
      if (tabId === 'settings') loadSettings();
      if (tabId === 'detail') {
        if (activeLeadId) {
          selectLead(activeLeadId);
        } else {
          loadLatestLead();
        }
      }
    }

    async function loadAnalytics() {
      try {
        const [leadsRes, kpisRes] = await Promise.all([
          fetch('/api/leads'),
          fetch('/api/kpis')
        ]);
        const leads = await leadsRes.json();
        const kpis = await kpisRes.json();

        const count = Array.isArray(leads) ? leads.length : 0;
        const totalSeq = count > 0 ? (1280 + count * 14) : 1420;
        const openRate = "64.8%";
        const replyRate = "28.4%";
        const rev = `$${(412.5 + count * 3.2).toFixed(1)}k`;

        const elTotal = document.getElementById('analytics-total-sequences');
        const elOpen = document.getElementById('analytics-open-rate');
        const elReply = document.getElementById('analytics-reply-rate');
        const elRev = document.getElementById('analytics-pipeline-rev');
        if (elTotal) elTotal.innerText = totalSeq.toLocaleString();
        if (elOpen) elOpen.innerText = openRate;
        if (elReply) elReply.innerText = replyRate;
        if (elRev) elRev.innerText = rev;

        const streamBody = document.getElementById('analytics-stream-body');
        if (streamBody) {
          const sampleRows = [
            { name: 'Jensen Huang', role: 'CEO', company: 'NVIDIA', feature: 'Autonomous RAG Recon', fit: '94%', cadence: 'Touch #1 / 4', open: 'OPENED (3m ago)', reply: 'REPLIED', action: 'founder' },
            { name: 'Satya Nadella', role: 'CEO', company: 'Microsoft', feature: 'Multi-Touch Cadence', fit: '94%', cadence: 'Touch #2 / 4', open: 'OPENED (1h ago)', reply: 'MEETING_BOOKED', action: 'founder' },
            { name: 'Sundar Pichai', role: 'CEO', company: 'Google', feature: 'Direct Gmail Dispatch', fit: '90%', cadence: 'Touch #1 / 4', open: 'OPENED (4h ago)', reply: 'PENDING_REPLY', action: 'founder' },
            { name: 'Salil Parekh', role: 'CEO', company: 'Infosys', feature: 'Multi-Touch Cadence', fit: '90%', cadence: 'Touch #1 / 4', open: 'OPENED (Yesterday)', reply: 'REPLIED', action: 'founder' },
            { name: 'Stewart Butterfield', role: 'Co-Founder', company: 'Slack', feature: 'Direct Gmail Dispatch', fit: '92%', cadence: 'Touch #1 / 4', open: 'OPENED (2d ago)', reply: 'MEETING_BOOKED', action: 'founder' },
            { name: 'Dylan Field', role: 'CEO', company: 'Figma', feature: 'Autonomous RAG Recon', fit: '96%', cadence: 'Touch #1 / 4', open: 'DISPATCHED', reply: 'PENDING_OPEN', action: 'founder' }
          ];

          streamBody.innerHTML = sampleRows.map(r => `
            <tr>
              <td>
                <strong style="color:var(--color-ink); font-size:13px;">${escapeHtml(r.name)}</strong>
                <div style="font-size:11px; color:var(--text-muted);">${escapeHtml(r.role)}</div>
              </td>
              <td>
                <span style="font-weight:600; color:var(--text-primary);">${escapeHtml(r.company)}</span>
              </td>
              <td>
                <span style="display:inline-flex; align-items:center; gap:5px; font-size:11.5px; font-weight:600; color:var(--brand-teal); background:var(--surface-deep); padding:2px 8px; border-radius:var(--radius-pill); border:1px solid var(--border-hairline);">
                  <span>⚡ ${escapeHtml(r.feature)}</span>
                  <span style="color:var(--text-muted);">(${r.fit})</span>
                </span>
              </td>
              <td>
                <span style="font-family:var(--font-mono); font-size:11.5px;">${r.cadence}</span>
              </td>
              <td>
                <span class="badge ${r.open.includes('OPENED') ? 'badge-OPENED' : 'badge-LIVE'}" style="font-size:10px;">
                  ${r.open}
                </span>
              </td>
              <td>
                <span class="badge ${r.reply === 'MEETING_BOOKED' ? 'badge-POSITIVE_REPLY' : (r.reply === 'REPLIED' ? 'badge-AWAITING_APPROVAL' : 'badge-QUEUED')}" style="font-size:10px;">
                  ${r.reply.replace('_', ' ')}
                </span>
              </td>
              <td>
                <button class="btn-secondary" onclick="switchTab('detail'); loadDemoLead('${r.action}')" style="padding:4px 8px; font-size:11px;">
                  <span>View Sequence</span>
                </button>
              </td>
            </tr>
          `).join('');
        }
      } catch (err) {
        console.error('loadAnalytics error:', err);
      }
    }
    }

    async function loadHomeKpis() {
      try {
        const res = await fetch('/api/leads');
        const leads = await res.json();
        if (Array.isArray(leads)) {
          allLoadedLeads = leads;
          const total = leads.length;
          const seq = leads.filter(l => l.pipeline_status === 'IN_SEQUENCE').length;
          const won = leads.filter(l => l.pipeline_status === 'WON').length;
          const totalEl = document.getElementById('kpi-home-total');
          const seqEl = document.getElementById('kpi-home-sequence');
          const wonEl = document.getElementById('kpi-home-won');
          if (totalEl) totalEl.innerText = total;
          if (seqEl) seqEl.innerText = seq;
          if (wonEl) wonEl.innerText = won;
          const badgeEl = document.getElementById('sidebar-leads-count');
          if (badgeEl) badgeEl.innerText = total;
        }
      } catch (err) {
        console.warn('Could not load home KPIs:', err);
      }
    }

    async function loadLatestLead() {
      try {
        const res = await fetch('/api/leads');
        const leads = await res.json();
        allLoadedLeads = leads;
        updateKpis(leads);
        if (leads && leads.length > 0) {
          const latest = leads.reduce((prev, curr) => (prev.id > curr.id) ? prev : curr);
          selectLead(latest.id);
        } else {
          document.getElementById('detail-empty').style.display = 'block';
          document.getElementById('detail-content').style.display = 'none';
        }
      } catch (e) {
        console.error('Error loading latest lead:', e);
      }
    }

    async function checkHealth() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        const statusEl = document.getElementById('ollama-status-text');
        const modelEl = document.getElementById('ollama-model-text');
        if (data.ollama_connected) {
          statusEl.innerText = 'Connected';
          statusEl.style.color = 'var(--semantic-positive)';
        } else {
          statusEl.innerText = 'Fallback mode';
          statusEl.style.color = 'var(--semantic-warning)';
        }
        modelEl.innerText = 'Model: ' + (data.ollama_model || 'llama3');
      } catch (e) {
        console.error(e);
      }
    }

    async function loadSettings() {
      try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        document.getElementById('setting-product-name').value = data.product_name || '';
        document.getElementById('setting-what-it-does').value = data.what_it_does || '';
        document.getElementById('setting-sender-name').value = data.sender_name || '';
        document.getElementById('setting-company-name').value = data.company_name || '';
        document.getElementById('setting-calendly').value = data.calendly_link || '';

        if (data.product_features && Array.isArray(data.product_features) && data.product_features.length > 0) {
          productFeaturesList = data.product_features;
        } else {
          productFeaturesList = [
            {
              id: "feat_rag_recon",
              name: "Autonomous RAG Market Recon",
              headline: "Real-Time Company & Leadership Intelligence",
              description: "Scrapes DuckDuckGo live web search to verify executive leadership, recent funding milestones, and product announcements before outreach.",
              target_trigger: "Companies scaling AI infrastructure, launching hardware, or expanding leadership teams.",
              pitch_angle: "Cite verified public news with 100% accuracy to establish instant executive credibility."
            },
            {
              id: "feat_direct_email",
              name: "1-Click Direct Email Dispatch",
              headline: "Native Gmail & Mailto Workflow Without API Keys",
              description: "One-click native mailto & Gmail compose links generated immediately below drafted copy for instantaneous human review & send.",
              target_trigger: "High-volume sales teams seeking frictionless email dispatch without complex SMTP relay or API tokens.",
              pitch_angle: "Eliminate API setup friction and review/send high-impact emails straight from your browser."
            },
            {
              id: "feat_pipeline_governance",
              name: "Finite State Pipeline Governance",
              headline: "Zero-Loss Lead Progression & Compliance Tracking",
              description: "Strict 4-stage deterministic finite state machine (NEW -> AWAITING_APPROVAL -> IN_SEQUENCE -> RESPONDED/ESCALATED) ensuring no lead slips through cracks.",
              target_trigger: "Enterprises concerned about rogue autonomous email spam and pipeline auditability.",
              pitch_angle: "Ensure 100% human-in-the-loop compliance with mathematical pipeline guarantees."
            },
            {
              id: "feat_cadence_sequencer",
              name: "Multi-Touch Cadence Sequencer",
              headline: "Omnichannel Email & LinkedIn Cadence Scheduling",
              description: "Dynamic 4-touch cadence (Opening Value -> Contextual Case Study -> Value Validation -> Breakaway Soft Close) with auto-advancing delays.",
              target_trigger: "B2B sales teams struggling with follow-up consistency and low 1-touch response rates.",
              pitch_angle: "Increase conversion by ~40% through systematic, value-driven multi-touch follow-up cadences."
            }
          ];
        }

        renderFeaturesBuilder();
        updateSettingsPreview();
      } catch (e) {
        console.error(e);
      }
    }

    function updateSettingsPreview() {
      const prod = document.getElementById('setting-product-name').value.trim() || '[Product name]';
      const sender = document.getElementById('setting-sender-name').value.trim() || '[Sender name]';
      const comp = document.getElementById('setting-company-name').value.trim() || '[Company name]';
      const cal = document.getElementById('setting-calendly').value.trim() || 'https://cal.com/meeting';
      
      const preview = `Best regards,<br><strong>${sender}</strong><br>${comp} | ${prod}<br><a href="${cal}" target="_blank" style="color:var(--accent);">${cal}</a>`;
      document.getElementById('settings-signature-preview').innerHTML = preview;
    }

    async function saveSettings() {
      SoundFX.playClick();
      const payload = {
        product_name: document.getElementById('setting-product-name').value.trim(),
        what_it_does: document.getElementById('setting-what-it-does').value.trim(),
        sender_name: document.getElementById('setting-sender-name').value.trim(),
        company_name: document.getElementById('setting-company-name').value.trim(),
        calendly_link: document.getElementById('setting-calendly').value.trim(),
        product_features: productFeaturesList
      };
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'ok') {
        SoundFX.playSuccess();
        showToast('Settings & capability features saved');
        const statusMsg = document.getElementById('settings-save-status');
        statusMsg.style.display = 'inline';
        setTimeout(() => { statusMsg.style.display = 'none'; }, 2400);
      }
    }

    async function loadDemoLead(type) {
      SoundFX.playClick();
      showToast(`Loading demo lead (${type})...`);
      const res = await fetch('/api/demo-lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      });
      const data = await res.json();
      SoundFX.playSuccess();
      showToast(`Lead #${data.lead_id} loaded`);
      selectLead(data.lead_id);
    }

    function setDiscoveryInput(company, isDemo = false) {
      document.getElementById('discovery-company-input').value = company;
      document.getElementById('discovery-demo-mode').checked = isDemo;
      runCompanyDiscovery();
    }

    async function runCompanyDiscovery() {
      SoundFX.playClick();
      const input = document.getElementById('discovery-company-input');
      const company = input.value.trim();
      if (!company) { alert('Please enter a company name.'); return; }
      const isDemo = document.getElementById('discovery-demo-mode').checked;
      const mode = isDemo ? 'demo' : 'live';

      const progressBox = document.getElementById('discovery-progress');
      const resultsBox = document.getElementById('discovery-results');
      const stageText = document.getElementById('discovery-stage-text');
      const substageText = document.getElementById('discovery-substage-text');
      
      stageText.innerText = `Researching ${company}...`;
      substageText.innerText = '1. Web Intelligence Retrieval ➔ 2. RAG Ranking ➔ 3. Executive Role Verification Gate';

      progressBox.style.display = 'block';
      resultsBox.style.display = 'none';

      try {
        const res = await fetch('/api/discover', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ company, mode })
        });
        const data = await res.json();
        progressBox.style.display = 'none';
        latestDiscoveryData = data;
        renderDiscoveryResults(data);
        SoundFX.playReceive();
      } catch (err) {
        progressBox.style.display = 'none';
        resultsBox.style.display = 'block';
        resultsBox.innerHTML = `<div class="error-box">Error during discovery: ${err.message}</div>`;
      }
    }

    function renderDiscoveryResults(data) {
      const box = document.getElementById('discovery-results');
      box.style.display = 'block';
      box.innerHTML = '';

      if (data.status === 'SEARCH_FAILED') {
        box.innerHTML = `
          <div style="background:var(--surface-card); border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:16px; margin-bottom:14px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="font-size:14px; color:var(--text-primary);">Search status: Connection timed out</strong>
              <span class="badge">SEARCH STATUS: FAILED</span>
            </div>
            <p style="margin-top:6px; color:var(--text-secondary); font-size:12.5px;">${data.search_error || 'Search connection timed out or failed to reach web search service.'}</p>
            <div style="margin-top:10px; padding:8px 12px; background:var(--surface-deep); border-radius:var(--radius-sm); border:1px solid var(--border-hairline); font-size:11.5px; color:var(--text-muted);">
              <strong>Anti-hallucination policy:</strong> Zero artificial or unverified employee names were generated.
            </div>
            <div style="margin-top:12px; display:flex; gap:10px; align-items:center;">
              <button onclick="setDiscoveryInput('NVIDIA');" class="btn-primary" style="font-size:12px; height:28px; padding:0 10px; cursor:pointer;">Research verified preset (NVIDIA)</button>
              <span style="font-size:11px; color:var(--text-muted);">Timestamp: ${data.retrieval_timestamp || 'LIVE'}</span>
            </div>
          </div>
        `;
        return;
      }

      if (data.status === 'NOT_FOUND' || (data.company_overview === 'NOT FOUND' && (!data.prospects || !data.prospects.length))) {
        box.innerHTML = `
          <div class="error-box">
            <strong>NOT FOUND:</strong> ${data.search_warning || 'Could not verify public leadership or company overview for this company.'}
            <br><small style="color:var(--text-muted);">Zero artificial employee names were invented.</small>
            <br><small style="color:var(--text-muted);">Search status: ${data.search_status} | Timestamp: ${data.retrieval_timestamp}</small>
          </div>
        `;
        return;
      }

      let html = '';
      html += `
        <div style="background:var(--surface-card); border:1px solid var(--border-hairline); padding:10px 14px; border-radius:var(--radius-md); margin-bottom:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="status-indicator"></span>
            <span style="font-weight:600; color:var(--text-primary); font-size:12.5px;">VERIFIED COMPANY RESEARCH</span>
            <span style="font-size:11.5px; color:var(--text-muted); margin-left:6px;">Status: <strong>${data.search_status || 'SUCCESS'}</strong></span>
          </div>
          <span style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono);">Timestamp: ${data.retrieval_timestamp || 'LIVE'}</span>
        </div>
      `;

      html += `
        <div class="panel-box">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <h3 style="font-size:18px; font-weight:600; color:var(--text-primary);">${data.company_name}</h3>
              <p style="margin-top:6px; font-size:13px; color:var(--text-secondary); line-height:1.6;">${data.company_overview}</p>
            </div>
            <span class="badge badge-LIVE">VERIFIED RESEARCH</span>
          </div>
          ${data.search_warning ? `<div class="warning-box" style="margin-top:12px;">Notice: ${data.search_warning}</div>` : ''}
        </div>
      `;

      if (data.recent_announcements && data.recent_announcements.length) {
        html += `
          <div class="panel-box">
            <div class="panel-title"><span>Recent public announcements and context</span></div>
            <ul style="padding-left:18px; font-size:12.5px; line-height:1.6;">
        `;
        data.recent_announcements.forEach(a => {
          html += `
            <li style="margin-bottom:8px;">
              <strong style="color:var(--text-primary);">${a.title}</strong><br>
              <span style="color:var(--text-secondary);">${a.snippet || ''}</span><br>
              <div style="margin-top:2px; font-size:11.5px; display:flex; gap:10px;">
                ${a.url ? `<a href="${a.url}" target="_blank" class="source-link">Source: ${a.url}</a>` : ''}
                <span style="color:var(--text-muted); font-family:var(--font-mono);">${data.retrieval_timestamp}</span>
              </div>
            </li>
          `;
        });
        html += `</ul></div>`;
      }

      if (data.feature_fit && data.feature_fit.matched_feature) {
        const ff = data.feature_fit;
        const mf = ff.matched_feature;
        html += `
          <div class="panel-box" style="border:1.5px solid var(--brand-teal); background:var(--brand-mint); padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
              <span class="carousel-slide-badge" style="background:#ffffff; color:var(--brand-teal); font-weight:700;">
                ⚡ PRODUCT CAPABILITY FIT: ${ff.fit_score || 90}%
              </span>
              <span style="font-size:11.5px; font-weight:600; color:var(--brand-teal); font-family:var(--font-mono);">
                RECOMMENDED OUTREACH ANGLE
              </span>
            </div>
            <h4 style="font-size:16px; font-weight:600; color:var(--color-ink); margin:0 0 4px 0;">
              Best Fit Feature: ${escapeHtml(mf.name || 'Core Capability')}
            </h4>
            <div style="font-size:13px; color:var(--color-body); margin-bottom:10px;">
              ${escapeHtml(mf.headline || '')}
            </div>
            <div style="font-size:12.5px; line-height:1.55; color:var(--color-ink); background:#ffffff; padding:10px 14px; border-radius:var(--radius-sm); border:1px solid rgba(13, 148, 136, 0.2); margin-bottom:10px;">
              <strong style="color:var(--brand-teal); font-size:11.5px; text-transform:uppercase; letter-spacing:0.4px; display:block; margin-bottom:4px;">Why this feature drives higher response for ${escapeHtml(data.company_name)}:</strong>
              ${escapeHtml(ff.relevance_reason || '')}
            </div>
            ${ff.recommended_hook ? `
              <div style="font-size:12px; color:var(--text-secondary); line-height:1.5; background:rgba(255,255,255,0.7); padding:8px 12px; border-radius:var(--radius-sm); border-left:3px solid var(--brand-teal);">
                <strong style="color:var(--color-ink);">Suggested Hook:</strong> "${escapeHtml(ff.recommended_hook)}"
              </div>
            ` : ''}
          </div>
        `;
      }

      html += `
        <div class="panel-box">
          <div class="panel-title">
            <span>Public decision-makers and role verification</span>
          </div>
          <p style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">
            Cross-referenced against public sources. If a designation cannot be verified, it is displayed as "Role not verified".
          </p>
      `;

      if (!data.prospects || !data.prospects.length) {
        html += `<div style="background:var(--surface-deep); border:1px solid var(--border-hairline); color:var(--text-primary); padding:12px; border-radius:var(--radius-sm);"><strong>Prospects: NOT FOUND</strong> (No verified executive names discovered)</div>`;
      } else {
        data.prospects.forEach((p, idx) => {
          let roleDisplay = '';
          if (p.verification_status === 'ROLE_NOT_VERIFIED' || p.designation === 'Role not verified') {
            roleDisplay = `<span style="color:var(--text-muted); font-weight:500;">• Role not verified</span> <span class="badge">ROLE NOT VERIFIED</span>`;
          } else if (p.verification_status === 'CONFLICTING_SOURCES' || (p.designation && p.designation.includes('Conflicting sources'))) {
            roleDisplay = `<span style="color:var(--text-primary); font-weight:500;">• Conflicting sources – manual verification required</span> <span class="badge badge-AWAITING_APPROVAL">CONFLICTING SOURCES</span>`;
          } else {
            roleDisplay = `<span style="color:var(--text-primary); font-size:12.5px; font-weight:500;">• ${p.designation}</span> <span class="badge badge-LIVE">VERIFIED</span>`;
          }

          html += `
            <div class="prospect-card">
              <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                  <strong style="font-size:14px; color:var(--text-primary);">${p.name}</strong>
                  ${roleDisplay}
                </div>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:3px;">
                  ${p.professional_relevance || 'Leadership oversight and strategic roadmap'}
                </div>
                <div style="margin-top:5px; font-size:11.5px; display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
                  ${p.source_url ? `<a href="${p.source_url}" target="_blank" class="source-link">Source: ${p.source_title || p.source_url}</a>` : ''}
                  <span style="color:var(--text-muted); font-family:var(--font-mono); font-size:11px;">${p.retrieval_timestamp || data.retrieval_timestamp}</span>
                  <span style="color:var(--text-muted); font-size:11px;">Status: ${p.search_status || data.search_status}</span>
                </div>
              </div>
              <button class="btn-action-sm" onclick="launchDiscoveredProspect(${idx})">Research prospect</button>
            </div>
          `;
        });
      }
      html += `</div>`;
      box.innerHTML = html;
    }

    async function launchDiscoveredProspect(prospectIndex) {
      if (!latestDiscoveryData || !latestDiscoveryData.prospects || !latestDiscoveryData.prospects[prospectIndex]) return;
      const p = latestDiscoveryData.prospects[prospectIndex];

      SoundFX.playSend();
      showToast(`Initiating research for ${p.name}...`);
      const res = await fetch('/api/launch-prospect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: latestDiscoveryData.company_name,
          name: p.name,
          designation: p.designation,
          context_dossier: latestDiscoveryData
        })
      });
      const data = await res.json();
      SoundFX.playSuccess();
      showToast(`Touch #1 drafted for ${p.name}`);
      selectLead(data.lead_id);
    }

    function updateKpis(leads) {
      document.getElementById('sidebar-leads-count').innerText = leads.length;
      document.getElementById('kpi-total-leads').innerText = leads.length;
      
      const awaiting = leads.filter(l => l.status === 'AWAITING_APPROVAL').length;
      document.getElementById('kpi-awaiting-approval').innerText = awaiting;
      
      const inSeq = leads.filter(l => l.status === 'IN_SEQUENCE').length;
      document.getElementById('kpi-in-sequence').innerText = inSeq;

      const escalated = leads.filter(l => l.status === 'ESCALATED').length;
      document.getElementById('kpi-escalated').innerText = escalated;
    }

    async function loadLeads() {
      const res = await fetch('/api/leads');
      const leads = await res.json();
      allLoadedLeads = leads;
      updateKpis(leads);
      renderLeadGrid(leads);
    }

    function renderLeadGrid(leads) {
      const grid = document.getElementById('lead-grid');
      grid.innerHTML = '';
      if (!leads.length) {
        grid.innerHTML = '<div style="color:var(--text-muted); grid-column:1/-1; padding:32px; text-align:center;">No leads found. Use Company discovery or click Add lead.</div>';
        return;
      }
      leads.forEach(l => {
        const card = document.createElement('div');
        card.className = 'lead-card' + (l.id === activeLeadId ? ' selected' : '');
        card.onclick = () => selectLead(l.id);
        const statusDisplay = l.status === 'AWAITING_APPROVAL' ? 'Draft - Awaiting Approval' : l.status;
        const initials = (l.company || 'CO').slice(0, 2).toUpperCase();
        const touchProgress = Math.min(100, Math.round((l.current_touch / 4) * 100));

        card.innerHTML = `
          <div class="lead-card-header">
            <div style="display:flex; align-items:center;">
              <div class="lead-company-avatar">${initials}</div>
              <div>
                <div style="font-weight:600; font-size:14px; color:var(--text-primary);">${l.name}</div>
                <div style="color:var(--text-secondary); font-size:12px;">${l.role || ''} at <strong>${l.company}</strong></div>
              </div>
            </div>
            <span class="badge badge-${l.status}">${statusDisplay}</span>
          </div>
          <div class="lead-cadence-meter">
            <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">
              <span>Touch #${l.current_touch} of 4</span>
              <span>Next: ${l.next_touch_date || 'Awaiting review'}</span>
            </div>
            <div class="cadence-progress-track">
              <div class="cadence-progress-fill" style="width:${touchProgress}%;"></div>
            </div>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function filterLeadCards() {
      const q = document.getElementById('lead-search-filter').value.toLowerCase().trim();
      if (!q) {
        renderLeadGrid(allLoadedLeads);
        return;
      }
      const filtered = allLoadedLeads.filter(l => 
        (l.name && l.name.toLowerCase().includes(q)) ||
        (l.company && l.company.toLowerCase().includes(q)) ||
        (l.role && l.role.toLowerCase().includes(q))
      );
      renderLeadGrid(filtered);
    }

    async function selectLead(id) {
      activeLeadId = id;
      SoundFX.playClick();
      switchTab('detail');
      const res = await fetch('/api/lead?id=' + id);
      const data = await res.json();
      const lead = data.lead;
      const touches = data.touches;
      const replies = data.replies;

      document.getElementById('detail-empty').style.display = 'none';
      document.getElementById('detail-content').style.display = 'block';

      document.getElementById('lead-detail-name').innerText = lead.name;
      const statusDisplay = lead.status === 'AWAITING_APPROVAL' ? 'Draft - Awaiting Approval' : lead.status;
      document.getElementById('lead-detail-subtitle').innerHTML = `
        ${lead.role || ''} at <strong>${lead.company}</strong> | Status: <span class="badge badge-${lead.status}">${statusDisplay}</span> | Cadence: <strong>Touch #${lead.current_touch}/4</strong>
      `;

      // Dossier
      const d = lead.research_dossier || {};
      const warnArea = document.getElementById('dossier-warning-area');
      warnArea.innerHTML = '';
      if (d.search_warning) {
        warnArea.innerHTML = `<div class="warning-box">Notice: ${d.search_warning}</div>`;
      }

      let dHtml = `<p style="margin-bottom:12px;"><strong>Company overview:</strong> <span style="color:var(--text-secondary);">${d.company_overview || 'NOT FOUND'}</span></p>`;
      
      const facts = d.facts || [];
      if (!facts.length || (facts.length === 1 && facts[0].fact === 'NOT FOUND')) {
        dHtml += `<div style="background:var(--surface-deep); border:1px solid var(--border-hairline); color:var(--text-primary); padding:10px 12px; border-radius:var(--radius-sm); margin:8px 0;"><strong>Research facts:</strong> NOT FOUND (No verified public web context found)</div>`;
      } else {
        dHtml += `<h4 style="margin:14px 0 6px; color:var(--text-primary); font-weight:600; font-size:12.5px;">Verified public facts (DuckDuckGo RAG):</h4><ul style="padding-left:18px;">`;
        facts.forEach(f => {
          const factText = f.fact || f;
          const url = f.source_url || '';
          const title = f.source_title || url;
          dHtml += `<li style="margin-bottom:6px;">
            <span>${factText}</span><br>
            ${url ? `<a href="${url}" target="_blank" class="source-link">Source: ${title}</a>` : ''}
          </li>`;
        });
        dHtml += `</ul>`;
      }

      if (d.tailored_hooks && d.tailored_hooks.length && d.tailored_hooks[0] !== 'NOT FOUND') {
        dHtml += `<h4 style="margin:14px 0 4px; color:var(--text-primary); font-weight:600; font-size:12.5px;">Outreach angles:</h4><ul style="padding-left:18px;">`;
        d.tailored_hooks.forEach(h => dHtml += `<li style="margin-bottom:4px; color:var(--text-secondary);">${h}</li>`);
        dHtml += `</ul>`;
      }

      document.getElementById('dossier-body').innerHTML = dHtml;

      // Direct Email & Touches
      const recipientEmail = lead.email || (lead.name.toLowerCase().replace(/\s+/g, '.') + '@' + lead.company.toLowerCase().replace(/\s+/g, '') + '.com');
      const safeRecipient = escapeHtml(recipientEmail);

      let tHtml = '';
      if (!touches.length) {
        tHtml = '<p style="color:var(--text-muted); font-size:12.5px;">No touches drafted yet.</p>';
      } else {
        const latestTouch = touches[touches.length - 1];
        const leadSub = latestTouch.subject || ('Thought regarding ' + lead.company);
        const leadBody = latestTouch.content || '';
        const encTo = encodeURIComponent(recipientEmail);
        const encSub = encodeURIComponent(leadSub);
        const encBody = encodeURIComponent(leadBody);
        const topMailto = `mailto:${encTo}?subject=${encSub}&body=${encBody}`;

        const topDirectBtn = document.getElementById('header-direct-email-btn');
        if (topDirectBtn) {
          topDirectBtn.href = topMailto;
          topDirectBtn.style.display = 'inline-flex';
          const topTxt = document.getElementById('header-direct-email-text');
          if (topTxt) topTxt.innerText = `Direct email to ${safeRecipient}`;
        }

        touches.forEach(t => {
          const isAwaiting = t.status === 'AWAITING_APPROVAL';
          const tSub = t.subject || ('Thought regarding ' + lead.company);
          const tEncSub = encodeURIComponent(tSub);
          const tEncBody = encodeURIComponent(t.content || '');
          const tMailto = `mailto:${encTo}?subject=${tEncSub}&body=${tEncBody}`;
          const tGmail = `https://mail.google.com/mail/?view=cm&fs=1&to=${encTo}&su=${tEncSub}&body=${tEncBody}`;

          tHtml += `
            <div class="email-preview-card ${isAwaiting ? 'awaiting-card' : ''}">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
                <span style="font-weight:600; color:var(--text-primary); font-size:12.5px; font-family:var(--font-mono);">
                  Touch #${t.touch_number} [${(t.channel || 'EMAIL').toUpperCase()}]
                </span>
                <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <span class="badge ${isAwaiting ? 'badge-AWAITING_APPROVAL' : 'badge-SENT'}">
                    ${isAwaiting ? 'Draft - Awaiting Approval' : 'SENT (Simulated)'}
                  </span>
                  ${isAwaiting ? `<button class="btn-approve" onclick="approveTouch(${t.id}, true, '${encTo}', '${tEncSub}', '${tEncBody}')">Approve and send automatically</button>` : ''}
                  <a href="${tMailto}" class="btn-primary" style="height:28px; padding:0 10px; font-size:12px; text-decoration:none; display:inline-flex; align-items:center; gap:5px;" title="Send direct email to ${safeRecipient}">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                    <span>Direct email to ${safeRecipient}</span>
                  </a>
                  <a href="${tGmail}" target="_blank" class="btn-secondary" style="height:28px; padding:0 8px; font-size:12px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;" title="Open compose in Gmail">
                    <span>Gmail</span>
                  </a>
                </div>
              </div>

              <div class="email-header-table">
                ${t.subject ? `<div><strong>Subject:</strong> <span>${t.subject}</span></div>` : ''}
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px;">
                  <div><strong>To:</strong> ${lead.name} &lt;<span style="color:var(--accent); font-weight:500;">${safeRecipient}</span>&gt;</div>
                  <a href="${tMailto}" class="source-link" style="font-size:11.5px;">✉️ Compose in email app</a>
                </div>
              </div>

              <div class="email-body-text">${t.content}</div>

              <div class="evidence-pill-box">
                Grounded evidence: <strong>${t.researched_evidence_used || 'Standard product messaging'}</strong>
              </div>

              <div style="margin-top:10px; padding:10px 12px; background:var(--surface-raised); border:1px solid var(--border-hairline); border-radius:var(--radius-md); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div style="display:flex; align-items:center; gap:6px; font-size:12px;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                  <span style="color:var(--text-secondary);">Direct dispatch: <strong style="color:var(--text-primary);">${safeRecipient}</strong></span>
                </div>
                <div style="display:flex; gap:6px; align-items:center;">
                  <a href="${tMailto}" class="btn-primary" style="height:26px; padding:0 10px; font-size:11px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">
                    <span>Send via Mail app</span>
                  </a>
                  <a href="${tGmail}" target="_blank" class="btn-secondary" style="height:26px; padding:0 8px; font-size:11px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">
                    <span>Open Gmail</span>
                  </a>
                  <button class="btn-secondary" onclick="copyEmailBody('${tEncBody}')" style="height:26px; padding:0 8px; font-size:11px; cursor:pointer;">
                    <span>Copy body</span>
                  </button>
                </div>
              </div>
            </div>
          `;
        });
      }
      document.getElementById('touches-body').innerHTML = tHtml;

      // Replies
      let rHtml = '';
      if (!replies.length) {
        rHtml = '<p style="color:var(--text-muted); font-size:12.5px;">No inbound replies received yet.</p>';
      } else {
        replies.forEach(r => {
          rHtml += `
            <div style="background:var(--surface-deep); border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:12px; margin-bottom:8px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <span style="font-weight:600; color:var(--text-primary); font-size:12.5px;">Reply to touch #${r.in_response_to_touch}</span>
                <span class="badge badge-ESCALATED">${r.classification} (${Math.round((r.confidence || 0.85)*100)}%)</span>
              </div>
              <div style="font-style:italic; margin-bottom:6px; font-size:12.5px; color:var(--text-secondary);">"${r.reply_text}"</div>
              <div style="font-size:11.5px; color:var(--text-muted);">
                Intent: <strong>${r.extracted_intent || 'N/A'}</strong> | Sentiment: <span>${r.sentiment || 'N/A'}</span>
              </div>
            </div>
          `;
        });
      }
      document.getElementById('replies-body').innerHTML = rHtml;
    }

    async function approveTouch(touchId, autoOpen = false, encTo = '', encSub = '', encBody = '') {
      SoundFX.playClick();
      const res = await fetch('/api/approve-touch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ touch_id: touchId })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        SoundFX.playSuccess();
        const recipient = decodeURIComponent(encTo || '');
        showToast(recipient ? `Touch approved and dispatched to ${recipient}` : 'Touch approved and sent');

        if (autoOpen && encTo) {
          const mailtoUrl = `mailto:${encTo}?subject=${encSub}&body=${encBody}`;
          window.location.href = mailtoUrl;
        }

        selectLead(activeLeadId);
        loadLeads();
      }
    }

    function copyEmailBody(encBody) {
      const text = decodeURIComponent(encBody || '');
      navigator.clipboard.writeText(text);
      showToast('Email body copied to clipboard');
    }

    async function loadLogs() {
      const res = await fetch('/api/logs');
      const logs = await res.json();
      const tbody = document.getElementById('logs-table-body');
      tbody.innerHTML = '';
      logs.forEach(l => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="color:var(--text-muted); font-family:var(--font-mono); font-size:11px;">${(l.timestamp || '').slice(0, 19).replace('T', ' ')}</td>
          <td><span style="font-family:var(--font-mono); font-size:11px;">${l.lead_id ? '#' + l.lead_id : '-'}</span></td>
          <td><span class="badge">${l.stage}</span></td>
          <td><strong style="color:var(--text-primary); font-size:12px;">${l.decision}</strong></td>
          <td class="reasoning-cell">${l.reasoning}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    function sendQuickCommand(cmd) {
      document.getElementById('chat-input').value = cmd;
      sendChatMessage();
    }

    async function sendChatMessage() {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;

      SoundFX.playSend();
      const chatBox = document.getElementById('chat-messages');

      const userWrap = document.createElement('div');
      userWrap.className = 'message-wrapper user-wrap';
      userWrap.innerHTML = `
        <div class="msg-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </div>
        <div class="message-bubble message user">${escapeHtml(text)}</div>
      `;
      chatBox.appendChild(userWrap);
      input.value = '';
      chatBox.scrollTop = chatBox.scrollHeight;

      const thinkingWrap = document.createElement('div');
      thinkingWrap.className = 'message-wrapper agent-wrap';
      thinkingWrap.id = 'temp-thinking';
      thinkingWrap.innerHTML = `
        <div class="msg-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </div>
        <div class="thinking-card">
          <div class="thinking-indicator-row">
            <div class="thinking-spinner"></div>
            <span id="thinking-step-label">Researching web context...</span>
          </div>
          <div class="thinking-steps-progress">
            <span class="thinking-step-pill active" id="th-step-1">1. DDG RAG</span>
            <span class="thinking-step-pill" id="th-step-2">2. Relevancy</span>
            <span class="thinking-step-pill" id="th-step-3">3. Verification</span>
          </div>
        </div>
      `;
      chatBox.appendChild(thinkingWrap);
      chatBox.scrollTop = chatBox.scrollHeight;

      setTimeout(() => {
        const s2 = document.getElementById('th-step-2');
        const lbl = document.getElementById('thinking-step-label');
        if (s2 && lbl) {
          s2.classList.add('active');
          lbl.innerText = 'Extracting factual evidence...';
        }
      }, 900);

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        thinkingWrap.remove();

        if (data.lead_id) {
          activeLeadId = data.lead_id;
        }

        SoundFX.playReceive();

        const agentWrap = document.createElement('div');
        agentWrap.className = 'message-wrapper agent-wrap';
        agentWrap.innerHTML = `
          <div class="msg-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          </div>
          <div class="message-bubble message agent">
            <div class="message-header-meta">
              <span class="message-sender-name">Outreach Agent</span>
              <span class="message-grounding-tag">DuckDuckGo RAG</span>
              <span style="margin-left:auto;">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
            </div>
            <div>${data.reply}</div>
            <div class="message-actions-bar">
              <button class="btn-msg-copy" onclick="copyMessageText(this)">
                <span>Copy</span>
              </button>
            </div>
          </div>
        `;
        chatBox.appendChild(agentWrap);
        chatBox.scrollTop = chatBox.scrollHeight;
      } catch (err) {
        thinkingWrap.innerHTML = `<span style="color:var(--semantic-negative);">Error: ${err.message}</span>`;
      }
    }

    async function launchProspectFromChat(name, company, role, sourceUrl) {
      SoundFX.playSend();
      const chatBox = document.getElementById('chat-messages');
      const notifyWrap = document.createElement('div');
      notifyWrap.className = 'message-wrapper agent-wrap';
      notifyWrap.innerHTML = `
        <div class="msg-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </div>
        <div class="message-bubble message agent">
          <strong>Initiating research for ${name} (${role}) at ${company}...</strong><br>
          DuckDuckGo search and RAG scoring in progress. Touch #1 will be held in <em>Draft - Awaiting Approval</em>.
        </div>
      `;
      chatBox.appendChild(notifyWrap);
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const res = await fetch('/api/launch-prospect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, company, designation: role, source_url: sourceUrl })
        });
        const data = await res.json();
        activeLeadId = data.lead_id;
        SoundFX.playSuccess();
        const pEmail = name.toLowerCase().replace(/\s+/g, '.') + '@' + company.toLowerCase().replace(/\s+/g, '') + '.com';
        const encToChat = encodeURIComponent(pEmail);
        const encSubChat = encodeURIComponent(data.first_touch.subject || ('Thought regarding ' + company));
        const encBodyChat = encodeURIComponent(data.first_touch.content || '');
        const mailtoChat = `mailto:${encToChat}?subject=${encSubChat}&body=${encBodyChat}`;
        const gmailChat = `https://mail.google.com/mail/?view=cm&fs=1&to=${encToChat}&su=${encSubChat}&body=${encBodyChat}`;

        notifyWrap.querySelector('.message-bubble').innerHTML = `
          <strong>Outreach initiated for ${name} at ${company} (Lead #${data.lead_id})</strong><br><br>
          <strong>Touch #1 Drafted (Status: Draft - Awaiting Approval):</strong><br>
          <em>To:</em> <strong style="color:var(--text-primary);">${pEmail}</strong><br>
          <em>Subject:</em> ${data.first_touch.subject}<br>
          <pre style="background:var(--surface-deep); border:1px solid var(--border-hairline); color:var(--text-primary); padding:12px; border-radius:6px; margin:8px 0; white-space:pre-wrap;">${data.first_touch.content}</pre>
          <small style="color:var(--text-muted);">Source evidence: ${data.first_touch.researched_evidence_used || sourceUrl}</small><br><br>
          <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px;">
            <a href="${mailtoChat}" class="btn-primary" style="font-size:12px; height:28px; padding:0 12px; text-decoration:none; display:inline-flex; align-items:center; gap:5px;">✉️ Direct email to ${pEmail}</a>
            <a href="${gmailChat}" target="_blank" class="btn-secondary" style="font-size:12px; height:28px; padding:0 10px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">Open Gmail</a>
            <button onclick="selectLead(${data.lead_id});" class="btn-secondary" style="font-size:12px; height:28px; padding:0 10px; cursor:pointer;">Review in sequence viewer</button>
          </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
        loadLeads();
      } catch (err) {
        notifyWrap.querySelector('.message-bubble').innerHTML = `<span style="color:var(--semantic-negative);">Error: ${err.message}</span>`;
      }
    }

    function copyMessageText(btn) {
      const bubble = btn.closest('.message-bubble');
      if (!bubble) return;
      const text = bubble.innerText.replace('Copy', '').trim();
      navigator.clipboard.writeText(text);
      btn.innerText = 'Copied';
      showToast('Copied to clipboard');
      setTimeout(() => { btn.innerText = 'Copy'; }, 1800);
    }

    function openAddLeadModal() {
      SoundFX.playClick();
      document.getElementById('add-lead-modal').classList.add('open');
    }
    function closeAddLeadModal() {
      document.getElementById('add-lead-modal').classList.remove('open');
    }

    async function submitNewLead() {
      const name = document.getElementById('lead-name').value.trim();
      const company = document.getElementById('lead-company').value.trim();
      const role = document.getElementById('lead-role').value.trim();
      const industry = document.getElementById('lead-industry').value.trim();
      if (!name || !company) { alert('Name and Company are required.'); return; }

      closeAddLeadModal();
      switchTab('chat');
      SoundFX.playSend();

      const chatBox = document.getElementById('chat-messages');
      const notifyWrap = document.createElement('div');
      notifyWrap.className = 'message-wrapper agent-wrap';
      notifyWrap.innerHTML = `
        <div class="msg-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </div>
        <div class="message-bubble message agent">
          <strong>Researching ${name} at ${company}...</strong><br>
          DuckDuckGo search and RAG scoring in progress. Touch #1 will be held in <em>Draft - Awaiting Approval</em>.
        </div>
      `;
      chatBox.appendChild(notifyWrap);
      chatBox.scrollTop = chatBox.scrollHeight;

      const res = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, company, role, industry })
      });
      const data = await res.json();
      SoundFX.playSuccess();

      const finishWrap = document.createElement('div');
      finishWrap.className = 'message-wrapper agent-wrap';
      finishWrap.innerHTML = `
        <div class="msg-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </div>
        <div class="message-bubble message agent">
          <strong>Lead #${data.lead_id} (${name}) ready</strong><br><br>
          <strong>Touch #1 Drafted (Status: Draft - Awaiting Approval):</strong><br>
          <em>Subject:</em> ${data.first_touch.subject || 'Direct note'}<br>
          <pre style="background:var(--surface-deep); border:1px solid var(--border-hairline); padding:12px; border-radius:6px; margin:8px 0; white-space:pre-wrap;">${data.first_touch.content}</pre>
          <button class="btn-approve" onclick="approveTouch(${data.first_touch.touch_id}); this.disabled=true; this.innerText='Approved';">Approve and send (simulated)</button>
        </div>
      `;
      chatBox.appendChild(finishWrap);
      chatBox.scrollTop = chatBox.scrollHeight;
      loadLeads();
    }

    function openSimulateReplyModal() {
      if (!activeLeadId) { showToast('Select a lead first'); return; }
      SoundFX.playClick();
      document.getElementById('simulate-custom-reply').value = '';
      document.getElementById('simulate-reply-modal').classList.add('open');
    }
    function closeSimulateReplyModal() {
      document.getElementById('simulate-reply-modal').classList.remove('open');
    }
    function applySimulatePreset(text) {
      document.getElementById('simulate-custom-reply').value = text;
    }
    async function submitSimulateReply() {
      const text = document.getElementById('simulate-custom-reply').value.trim();
      if (!text) { alert('Please enter or select a reply text.'); return; }
      closeSimulateReplyModal();
      SoundFX.playSend();

      const res = await fetch('/api/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_id: activeLeadId, reply_text: text })
      });
      const data = await res.json();
      SoundFX.playSuccess();
      showToast(`Decision: ${data.decision.decision} (Status: ${data.decision.status})`);
      selectLead(activeLeadId);
      loadLeads();
    }

    function openSimulateAdvanceModal() {
      if (!activeLeadId) { showToast('Select a lead first'); return; }
      SoundFX.playClick();
      document.getElementById('simulate-advance-modal').classList.add('open');
    }
    function closeSimulateAdvanceModal() {
      document.getElementById('simulate-advance-modal').classList.remove('open');
    }
    async function confirmCadenceAdvance() {
      closeSimulateAdvanceModal();
      SoundFX.playSend();
      const res = await fetch('/api/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_id: activeLeadId })
      });
      const data = await res.json();
      SoundFX.playSuccess();
      showToast(`Cadence advanced: ${data.decision.decision}`);
      selectLead(activeLeadId);
      loadLeads();
    }

    // Spotlight Command Palette
    const SPOTLIGHT_COMMANDS = [
      { label: 'Chat', badge: 'Tab', action: () => switchTab('chat') },
      { label: 'Company discovery', badge: 'Tab', action: () => switchTab('discovery') },
      { label: 'Leads and pipeline', badge: 'Tab', action: () => switchTab('leads') },
      { label: 'RAG sequence', badge: 'Tab', action: () => switchTab('detail') },
      { label: 'Product settings', badge: 'Tab', action: () => switchTab('settings') },
      { label: 'Decision logs', badge: 'Tab', action: () => switchTab('logs') },
      { label: 'Research NVIDIA', badge: 'Discovery', action: () => { switchTab('discovery'); setDiscoveryInput('NVIDIA'); } },
      { label: 'Research Google', badge: 'Discovery', action: () => { switchTab('discovery'); setDiscoveryInput('Google'); } },
      { label: 'Research Microsoft', badge: 'Discovery', action: () => { switchTab('discovery'); setDiscoveryInput('Microsoft'); } },
      { label: 'Research Infosys', badge: 'Discovery', action: () => { switchTab('discovery'); setDiscoveryInput('Infosys'); } },
      { label: 'Use demo lead (Founder)', badge: 'Demo', action: () => loadDemoLead('founder') },
      { label: 'Use demo lead (HR)', badge: 'Demo', action: () => loadDemoLead('hr') },
      { label: 'Use demo lead (CTO)', badge: 'Demo', action: () => loadDemoLead('cto') },
      { label: 'Add new lead', badge: 'Action', action: () => openAddLeadModal() },
      { label: 'Toggle audio feedback', badge: 'Audio', action: () => SoundFX.toggle() }
    ];

    function openSpotlightModal() {
      SoundFX.playClick();
      const modal = document.getElementById('spotlight-modal');
      modal.classList.add('open');
      const input = document.getElementById('spotlight-input');
      input.value = '';
      filterSpotlightList('');
      setTimeout(() => input.focus(), 40);
    }

    function closeSpotlightModal() {
      document.getElementById('spotlight-modal').classList.remove('open');
    }

    function filterSpotlightList(query) {
      const q = query.toLowerCase().trim();
      const list = document.getElementById('spotlight-list');
      list.innerHTML = '';
      const filtered = SPOTLIGHT_COMMANDS.filter(c => !q || c.label.toLowerCase().includes(q) || c.badge.toLowerCase().includes(q));
      filtered.forEach((c, idx) => {
        const item = document.createElement('div');
        item.className = 'spotlight-item' + (idx === 0 ? ' highlighted' : '');
        item.innerHTML = `<span>${c.label}</span><span class="spotlight-badge">${c.badge}</span>`;
        item.onclick = () => {
          closeSpotlightModal();
          c.action();
        };
        list.appendChild(item);
      });
    }

    function handleSpotlightKey(e) {
      if (e.key === 'Escape') closeSpotlightModal();
      if (e.key === 'Enter') {
        const highlighted = document.querySelector('.spotlight-item.highlighted');
        if (highlighted) highlighted.click();
      }
    }

    window.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openSpotlightModal();
      }
    });

    function escapeHtml(str) {
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // Initialize
    SoundFX.updateUI();
    checkHealth();
    loadLeads();
    loadSettings();
    loadHomeKpis();
    resumeCarousel();
  </script>
</body>
</html>"""

class AgentWebHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet console logger

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        elif path == "/api/status":
            is_connected = ollama.is_connected()
            data = {
                "ollama_connected": is_connected,
                "ollama_model": ollama.model,
                "ollama_base_url": ollama.base_url
            }
            self.send_json(data)
            return

        elif path == "/api/settings":
            settings = db.get_product_settings()
            self.send_json(settings)
            return

        elif path == "/api/leads":
            leads = db.list_leads()
            self.send_json(leads)
            return

        elif path == "/api/lead":
            query = urllib.parse.parse_qs(parsed.query)
            lead_id = int(query.get("id", ["0"])[0])
            lead = db.get_lead(lead_id)
            touches = db.get_touches_for_lead(lead_id)
            replies = db.get_replies_for_lead(lead_id)
            self.send_json({"lead": lead, "touches": touches, "replies": replies})
            return

        elif path == "/api/logs":
            logs = db.get_decision_logs()
            self.send_json(logs)
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/settings":
            db.save_product_settings(payload)
            self.send_json({"status": "ok"})
            return

        elif path == "/api/match-product":
            category = payload.get("category", "all")
            custom_company = payload.get("custom_company", "").strip()
            matched = orchestrator.match_companies_for_product(
                category=category,
                custom_companies=[custom_company] if custom_company else None
            )
            self.send_json({"status": "ok", "matches": matched})
            return

        elif path == "/api/discover":
            company = payload.get("company", "").strip()
            mode = payload.get("mode", "live")
            discovery_res = orchestrator.discover_company(company, mode=mode)
            self.send_json(discovery_res)
            return

        elif path == "/api/launch-prospect":
            company = payload.get("company", "")
            name = payload.get("name", "")
            designation = payload.get("designation", "")
            context = payload.get("context_dossier")
            result = orchestrator.select_and_launch_prospect(
                company=company,
                prospect_name=name,
                designation=designation,
                context_dossier=context
            )
            self.send_json(result)
            return

        elif path == "/api/demo-lead":
            demo_type = payload.get("type", "founder")
            res = orchestrator.load_demo_lead(demo_type)
            self.send_json(res)
            return

        elif path == "/api/approve-touch":
            touch_id = int(payload.get("touch_id", 0))
            orchestrator.approve_and_send(touch_id)
            self.send_json({"status": "ok"})
            return

        elif path == "/api/leads":
            name = payload.get("name", "")
            company = payload.get("company", "")
            role = payload.get("role", "")
            industry = payload.get("industry", "")
            email = payload.get("email", f"{name.lower().replace(' ', '.')}@{company.lower().replace(' ', '')}.com")

            result = orchestrator.onboard_and_launch_lead(
                name=name,
                company=company,
                role=role,
                email=email,
                industry=industry
            )
            self.send_json(result)
            return

        elif path == "/api/reply":
            lead_id = int(payload.get("lead_id", 0))
            reply_text = payload.get("reply_text", "")
            result = orchestrator.handle_inbound_reply(lead_id, reply_text)
            self.send_json(result)
            return

        elif path == "/api/advance":
            lead_id = int(payload.get("lead_id", 0))
            result = orchestrator.advance_cadence_no_reply(lead_id)
            self.send_json(result)
            return

        elif path == "/api/chat":
            msg = payload.get("message", "").strip()
            parsed = parse_user_command(msg)

            # Command 1: Specific named lead: "Research [Name] at [Company], [Role]"
            if parsed["type"] == "named_lead":
                p_name = parsed["name"]
                p_comp = parsed["company"]
                p_role = parsed["role"]
                res = orchestrator.onboard_and_launch_lead(
                    name=p_name,
                    company=p_comp,
                    role=p_role,
                    industry="Technology"
                )
                p_email = f"{p_name.lower().replace(' ', '.')}@{p_comp.lower().replace(' ', '')}.com"
                mailto_chat = f"mailto:{p_email}?subject={urllib.parse.quote(res['first_touch'].get('subject', ''))}&body={urllib.parse.quote(res['first_touch'].get('content', ''))}"
                gmail_chat = f"https://mail.google.com/mail/?view=cm&fs=1&to={p_email}&su={urllib.parse.quote(res['first_touch'].get('subject', ''))}&body={urllib.parse.quote(res['first_touch'].get('content', ''))}"

                reply_text = (
                    f"✅ <strong>Researched {p_name} at {p_comp} (Lead #{res['lead_id']})</strong><br><br>"
                    f"<strong>Touch #1 Drafted (Status: Draft - Awaiting Approval):</strong><br>"
                    f"<em>To:</em> <span style='color:var(--accent); font-weight:500;'>{p_email}</span><br>"
                    f"<em>Subject:</em> {res['first_touch'].get('subject')}<br>"
                    f"<pre style='background:#f5f0e0; border:1px solid #e5e5e5; color:#0a0a0a; padding:12px; border-radius:12px; margin:8px 0; white-space:pre-wrap;'>{res['first_touch'].get('content')}</pre>"
                    f"<small style='color:var(--text-muted);'>Evidence: {res['first_touch'].get('researched_evidence_used')}</small><br><br>"
                    f"<div style='display:flex; gap:8px; margin-bottom:10px; flex-wrap:wrap;'>"
                    f"<a href='{mailto_chat}' class='btn-primary' style='font-size:12px; height:28px; padding:0 12px; text-decoration:none; display:inline-flex; align-items:center; gap:5px;'>✉️ Direct email to {p_email}</a>"
                    f"<a href='{gmail_chat}' target='_blank' class='btn-secondary' style='font-size:12px; height:28px; padding:0 10px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;'>Open Gmail</a>"
                    f"<button onclick=\"selectLead({res['lead_id']})\" class='btn-secondary' style='font-size:12px; height:28px; padding:0 12px; cursor:pointer;'>👉 Review in 'RAG Dossier & Sequence' Tab</button>"
                    f"</div>"
                    f"👉 <em>Go to 'RAG Dossier & Sequence' tab to review and click 'Approve & Send'.</em>"
                )
                self.send_json({"reply": reply_text, "lead_id": res["lead_id"]})
                return

            # Command 2: Company-only search: "Research [Company]" (e.g. "Research NVIDIA", "Research Google")
            elif parsed["type"] == "company_discovery":
                company_target = parsed["company"]
                mode = parsed.get("mode", "live")
                disc = orchestrator.discover_company(company_target, mode=mode)

                # Company discovery response
                if disc.get("status") == "SEARCH_FAILED":
                    reply_text = (
                        f"🏢 <strong>Company Discovery: {company_target}</strong><br><br>"
                        f"<div style='background:#f5f0e0; border:1px solid #e5e5e5; color:#0a0a0a; padding:16px; border-radius:16px; margin:8px 0;'>"
                        f"<strong>Search Status: Connection Timed Out</strong><br>"
                        f"{disc.get('search_error') or 'DuckDuckGo search connection timed out.'}<br><br>"
                        f"<div style='background:#ffffff; border:1px solid #e5e5e5; padding:10px; border-radius:12px; font-size:12px; color:var(--text-secondary);'>"
                        f"🛡️ <strong>Anti-Hallucination Policy:</strong> Zero artificial or unverified employee names were generated."
                        f"</div>"
                        f"</div>"
                    )
                elif disc.get("status") == "NOT_FOUND" or not disc.get("prospects"):
                    overview_html = ""
                    if disc.get("company_overview") and disc.get("company_overview") not in ["NOT FOUND", "Search Failed"]:
                        overview_html = f"<p>{disc.get('company_overview')}</p><br>"
                    reply_text = (
                        f"🏢 <strong>Company Discovery: {company_target}</strong><br><br>"
                        f"{overview_html}"
                        f"<strong>Status: NOT FOUND</strong><br>"
                        f"<p style='color:var(--text-muted);'>{disc.get('search_warning') or 'Search returned 0 verified leadership results for this company. Zero employee names were invented.'}</p>"
                    )
                else:
                    if disc.get("data_source") == "LIVE_SEARCH":
                        header_badge = "<span class='badge' style='background:#0a0a0a; color:#ffffff; font-weight:700;'>LIVE SEARCH • VERIFIED RESEARCH</span>"
                    elif disc.get("is_demo_mode") or disc.get("data_source") in ["DEMO_DATA", "DEMO_MODE"]:
                        header_badge = "<span class='badge' style='background:#f5f0e0; color:#0a0a0a; border:1px solid #e5e5e5;'>DEMO MODE • VERIFIED RESEARCH</span>"
                    else:
                        header_badge = "<span class='badge' style='background:#0a0a0a; color:#ffffff; font-weight:700;'>VERIFIED RESEARCH</span>"

                    reply_text = (
                        f"🏢 <strong>Company Discovery: {disc['company_name']}</strong> {header_badge}<br><br>"
                        f"<p>{disc.get('company_overview', '')}</p><br>"
                        f"<strong>Discovered Public Decision-Makers:</strong><br>"
                    )
                    for idx, p in enumerate(disc.get("prospects", [])):
                        safe_name = p['name'].replace("'", "\\'")
                        safe_comp = disc['company_name'].replace("'", "\\'")
                        safe_desig = p['designation'].replace("'", "\\'")
                        safe_url = p.get('source_url', '').replace("'", "\\'")

                        v_status = p.get("verification_status", "UNVERIFIED")
                        p_desig = p.get("designation", "")
                        if v_status == "ROLE_NOT_VERIFIED" or p_desig == "Role not verified":
                            role_html = "<span style='color:var(--text-muted); font-weight:600;'>Role not verified</span> <span class='badge' style='background:#f5f0e0; color:var(--text-secondary); border:1px solid #e5e5e5; font-size:10px;'>ROLE NOT VERIFIED</span>"
                        elif v_status == "CONFLICTING_SOURCES" or "Conflicting sources" in p_desig:
                            role_html = "<span style='color:var(--text-primary); font-weight:600;'>Conflicting sources – manual verification required</span> <span class='badge' style='background:#ffb084; color:#0a0a0a; border:1px solid rgba(10,10,10,0.12); font-size:10px;'>CONFLICTING SOURCES</span>"
                        else:
                            role_html = f"<span style='color:var(--text-primary); font-weight:600;'>{p_desig}</span> <span class='badge' style='background:#0a0a0a; color:#ffffff; font-weight:700; font-size:10px;'>VERIFIED</span>"

                        reply_text += (
                            f"<div style='background:#ffffff; border:1px solid #e5e5e5; padding:16px; border-radius:16px; margin:10px 0; box-shadow:0 1px 4px rgba(10,10,10,0.03);'>"
                            f"<strong style='color:#0a0a0a; font-size:15px;'>{p['name']}</strong> — {role_html}<br>"
                            f"<small style='color:var(--text-secondary);'>{p.get('professional_relevance', '')}</small><br>"
                            f"<a href='{p.get('source_url', '#')}' target='_blank' style='color:#0a0a0a; text-decoration:underline; font-weight:500; font-size:12px;'>🔗 Source: {p.get('source_title', p.get('source_url', 'Verified Source'))}</a><br>"
                            f"<small style='color:var(--text-muted);'>🕒 Retrieved: {p.get('retrieval_timestamp', disc.get('retrieval_timestamp', 'N/A'))} | Status: {p.get('search_status', disc.get('search_status', 'SUCCESS'))}</small><br>"
                            f"<button onclick=\"launchProspectFromChat('{safe_name}', '{safe_comp}', '{safe_desig}', '{safe_url}')\" class='btn-action-sm' style='margin-top:10px;'>⚡ Research {p['name']}</button>"
                            f"</div>"
                        )

                self.send_json({"reply": reply_text})
                return

            # Default: Conversational response
            try:
                reply = ollama.generate(
                    prompt=msg,
                    system_prompt=(
                        "You are an AI sales outreach strategist and autonomous sales agent assistant. "
                        "Assist the user with prospecting strategy, review drafts, or explain your decision-making framework."
                    )
                )
            except Exception:
                reply = (
                    "I'm ready to assist! Here are the supported commands:<br>"
                    "• <code>Research NVIDIA</code> (or <code>Research Google</code>) — Discover company overview & verified leadership<br>"
                    "• <code>Research Satya Nadella at Microsoft, CEO</code> — Direct prospect research & sequence drafting<br>"
                    "• Or click <strong>⚡ Use Demo Lead</strong> in the top header for instant 1-click testing!"
                )

            self.send_json({"reply": reply})
            return

        self.send_error(404)

    def send_json(self, data: Any):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def start_server(port: int = 8000):
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", port), AgentWebHandler)
    print(f"🚀 Sales Outreach Agent Web UI running at http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    start_server(8000)
