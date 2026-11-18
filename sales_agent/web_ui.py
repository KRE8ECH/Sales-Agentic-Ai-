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
  <title>Sales Agentic AI - Multi-Touch Outreach</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #000000;
      --card-bg: #0a0a0a;
      --card-border: #262626;
      --card-border-hover: #525252;
      --primary: #ffffff;
      --primary-hover: #e5e5e5;
      --text: #fafafa;
      --text-muted: #a1a1aa;
      --text-subtle: #71717a;
      --surface-1: #0a0a0a;
      --surface-2: #121214;
      --surface-3: #18181b;
      --accent-white: #ffffff;
      --accent-black: #000000;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      height: 100vh;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Custom Minimal Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #000000; }
    ::-webkit-scrollbar-thumb { background: #262626; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #525252; }

    /* Sidebar */
    .sidebar {
      width: 280px;
      background-color: #000000;
      border-right: 1px solid var(--card-border);
      display: flex;
      flex-direction: column;
      padding: 24px 20px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 28px;
    }
    .brand-icon {
      width: 36px;
      height: 36px;
      background: #ffffff;
      color: #000000;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 700;
      border: 1px solid #ffffff;
    }
    .brand h2 { font-size: 16px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px; line-height: 1.2; }
    .brand span { font-size: 11px; color: var(--text-muted); font-weight: 500; }
    
    .nav-tabs {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .nav-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-radius: 6px;
      background: transparent;
      color: var(--text-muted);
      border: 1px solid transparent;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      text-align: left;
      transition: all 0.15s ease;
    }
    .nav-btn:hover { background: #121214; color: #ffffff; border-color: #262626; }
    .nav-btn.active {
      background: #18181b;
      color: #ffffff;
      font-weight: 600;
      border: 1px solid #3f3f46;
      border-left: 3px solid #ffffff;
    }

    .ollama-status-box {
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px;
      font-size: 12px;
    }
    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #ffffff;
      box-shadow: 0 0 6px rgba(255, 255, 255, 0.6);
      margin-right: 8px;
    }

    /* Main Area */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: #000000;
    }
    .top-header {
      height: 65px;
      border-bottom: 1px solid var(--card-border);
      background: #000000;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
    }
    .top-header h1 { font-size: 16px; font-weight: 600; color: #ffffff; letter-spacing: -0.2px; }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .btn-primary {
      background: #ffffff;
      color: #000000;
      border: 1px solid #ffffff;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
    }
    .btn-primary:hover {
      background: #e5e5e5;
      border-color: #e5e5e5;
    }

    .btn-demo {
      background: #0a0a0a;
      color: #fafafa;
      border: 1px solid var(--card-border);
      padding: 8px 14px;
      border-radius: 6px;
      font-weight: 500;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn-demo:hover {
      background: #18181b;
      border-color: #ffffff;
      color: #ffffff;
    }

    .btn-approve {
      background: #ffffff;
      color: #000000;
      border: 1px solid #ffffff;
      padding: 6px 14px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 12px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn-approve:hover { background: #e5e5e5; }

    .btn-action-sm {
      background: #ffffff;
      color: #000000;
      border: 1px solid #ffffff;
      padding: 6px 12px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 12px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s ease;
    }
    .btn-action-sm:hover { background: #e5e5e5; }

    .content-viewport {
      flex: 1;
      overflow-y: auto;
      padding: 24px 28px;
      background: #000000;
    }

    /* Tab Sections */
    .tab-section { display: none; }
    .tab-section.active { display: block; }

    /* Chat Tab */
    .chat-layout {
      display: flex;
      gap: 20px;
      height: calc(100vh - 120px);
    }
    .chat-container {
      flex: 1;
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .chat-messages {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .message {
      max-width: 80%;
      padding: 14px 18px;
      border-radius: 10px;
      font-size: 14px;
      line-height: 1.6;
    }
    .message.agent {
      background: #121214;
      border: 1px solid var(--card-border);
      color: #fafafa;
      align-self: flex-start;
      border-top-left-radius: 2px;
    }
    .message.user {
      background: #ffffff;
      color: #000000;
      font-weight: 500;
      align-self: flex-end;
      border-top-right-radius: 2px;
      border: 1px solid #ffffff;
    }
    .chat-input-bar {
      padding: 16px 20px;
      background: #000000;
      border-top: 1px solid var(--card-border);
      display: flex;
      gap: 12px;
    }
    .chat-input {
      flex: 1;
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      color: #ffffff;
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s ease;
    }
    .chat-input:focus { border-color: #ffffff; }

    /* Grid & Cards */
    .lead-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
      margin-top: 18px;
    }
    .lead-card {
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .lead-card:hover {
      border-color: #525252;
      transform: translateY(-1px);
    }
    .lead-card.selected {
      border-color: #ffffff;
      background: #121214;
    }

    /* Badges */
    .badge {
      font-size: 10px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border: 1px solid #3f3f46;
      background: #18181b;
      color: #ffffff;
      display: inline-block;
    }
    .badge-NEW { background: #18181b; color: #a1a1aa; border-color: #27272a; }
    .badge-AWAITING_APPROVAL { background: #18181b; color: #ffffff; border-color: #71717a; }
    .badge-IN_SEQUENCE { background: #18181b; color: #ffffff; border-color: #52525b; }
    .badge-ESCALATED { background: #ffffff; color: #000000; border-color: #ffffff; }
    .badge-PAUSED { background: #18181b; color: #d4d4d8; border-color: #52525b; }
    .badge-STOPPED { background: #0a0a0a; color: #71717a; border-color: #262626; }
    .badge-COMPLETED { background: #18181b; color: #a1a1aa; border-color: #27272a; }
    .badge-SENT { background: #18181b; color: #ffffff; border-color: #52525b; }
    .badge-LIVE { background: #ffffff; color: #000000; border-color: #ffffff; }
    .badge-DEMO { background: #18181b; color: #ffffff; border-color: #52525b; }

    /* Modal */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.85);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
      backdrop-filter: blur(4px);
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      width: 520px;
      border-radius: 10px;
      padding: 24px;
      color: #ffffff;
    }
    .modal h2 { margin-bottom: 16px; font-size: 17px; font-weight: 600; }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    .form-group input, .form-group textarea {
      width: 100%;
      background: #121214;
      border: 1px solid var(--card-border);
      color: #ffffff;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.15s ease;
    }
    .form-group input:focus, .form-group textarea:focus { border-color: #ffffff; }
    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 20px;
    }
    .btn-secondary {
      background: #18181b;
      color: #ffffff;
      border: 1px solid var(--card-border);
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.15s ease;
    }
    .btn-secondary:hover { background: #27272a; border-color: #525252; }

    /* Decision Log Table */
    .table-container {
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      overflow: hidden;
      margin-top: 18px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th {
      background: #000000;
      text-align: left;
      padding: 12px 18px;
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--card-border);
      font-size: 12px;
      letter-spacing: 0.3px;
    }
    td { padding: 14px 18px; border-bottom: 1px solid var(--card-border); }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #121214; }
    .reasoning-cell { color: #d4d4d8; line-height: 1.5; font-size: 13px; }

    /* Dossier & Sequence Viewer */
    .panel-box {
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
    }
    .panel-title {
      font-size: 14px;
      font-weight: 600;
      color: #ffffff;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      letter-spacing: -0.2px;
    }

    .warning-box {
      background: #121214;
      border: 1px solid #525252;
      color: #ffffff;
      padding: 12px 16px;
      border-radius: 6px;
      margin-bottom: 16px;
      font-size: 13px;
    }

    .error-box {
      background: #121214;
      border: 1px solid #71717a;
      color: #ffffff;
      padding: 12px 16px;
      border-radius: 6px;
      margin-bottom: 16px;
      font-size: 13px;
    }

    .source-link {
      color: #ffffff;
      text-decoration: underline;
      text-underline-offset: 3px;
      font-size: 12px;
      display: inline-block;
      margin-top: 3px;
    }
    .source-link:hover { color: #d4d4d8; }

    /* Prospect Card in Discovery */
    .prospect-card {
      background: #121214;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.15s ease;
    }
    .prospect-card:hover {
      border-color: #525252;
      background: #18181b;
    }

    .dropdown {
      position: relative;
      display: inline-block;
    }
    .dropdown-content {
      display: none;
      position: absolute;
      right: 0;
      background-color: #0a0a0a;
      min-width: 260px;
      box-shadow: 0px 12px 32px rgba(0,0,0,0.9);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      z-index: 10;
      overflow: hidden;
    }
    .dropdown-content a {
      color: #fafafa;
      padding: 12px 16px;
      text-decoration: none;
      display: block;
      font-size: 13px;
      cursor: pointer;
      border-bottom: 1px solid #18181b;
    }
    .dropdown-content a:last-child { border-bottom: none; }
    .dropdown-content a:hover { background-color: #18181b; color: #ffffff; }
    .dropdown:hover .dropdown-content { display: block; }
  </style>
</head>
<body>
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="brand">
      <div class="brand-icon">🚀</div>
      <div>
        <h2>SalesAgentic.AI</h2>
        <span>Personalized Outreach Agent</span>
      </div>
    </div>

    <div class="nav-tabs">
      <button class="nav-btn active" onclick="switchTab('chat')">💬 Agent Chatbot</button>
      <button class="nav-btn" onclick="switchTab('discovery')">🏢 Company Discovery</button>
      <button class="nav-btn" onclick="switchTab('leads')">👥 Leads & Pipeline</button>
      <button class="nav-btn" onclick="switchTab('detail')">🔍 RAG Dossier & Sequence</button>
      <button class="nav-btn" onclick="switchTab('settings')">⚙️ My Product Settings</button>
      <button class="nav-btn" onclick="switchTab('logs')">📜 Agent Decision Logs</button>
    </div>

    <div class="ollama-status-box">
      <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
        <span style="font-weight:600;"><span class="status-dot"></span>Local Ollama</span>
        <span style="color:var(--primary);" id="ollama-status-text">Checking...</span>
      </div>
      <div style="color:var(--text-muted); font-size:11px;" id="ollama-model-text">Model: llama3</div>
      <div style="color:var(--text-muted); font-size:11px; margin-top:4px;">Search: DuckDuckGo RAG</div>
    </div>
  </div>

  <!-- Main Viewport -->
  <div class="main-content">
    <div class="top-header">
      <h1 id="view-title">Agent Chatbot & Command Center</h1>
      <div class="header-actions">
        <!-- Demo Lead Dropdown -->
        <div class="dropdown">
          <button class="btn-demo">⚡ Use Demo Lead ▾</button>
          <div class="dropdown-content">
            <a onclick="loadDemoLead('founder')">🚀 <strong>Startup Founder</strong><br><small style="color:var(--text-muted)">Alex Rivera @ KiteFlow AI</small></a>
            <a onclick="loadDemoLead('hr')">👥 <strong>HR Head</strong><br><small style="color:var(--text-muted)">Maya Patel @ Lumina Health</small></a>
            <a onclick="loadDemoLead('cto')">💻 <strong>Chief Tech Officer</strong><br><small style="color:var(--text-muted)">Marcus Sterling @ Apex Payments</small></a>
          </div>
        </div>
        <button class="btn-primary" onclick="openAddLeadModal()">+ Add New Lead</button>
      </div>
    </div>

    <div class="content-viewport">
      <!-- 1. CHAT TAB -->
      <div id="tab-chat" class="tab-section active">
        <div class="chat-layout">
          <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
              <div class="message agent">
                👋 Hello! I am your <strong>Personalized Multi-Touch Sales Outreach Agent</strong>.<br><br>
                <strong>What I can do:</strong><br>
                1. 🏢 <strong>Company Discovery:</strong> Type <code>Research NVIDIA</code>, <code>Research Infosys</code>, or <code>Research Microsoft</code> to discover company overview & key decision-makers automatically.<br>
                2. 👤 <strong>Named Lead Outreach:</strong> Type <code>Research Satya Nadella at Microsoft, CEO</code> to launch direct outreach.<br>
                3. 🛡️ <strong>Human Approval:</strong> All touches are held in <em>Draft - Awaiting Approval</em>. No emails sent automatically!<br>
                4. ⚡ <strong>Sample Leads:</strong> Click <em>Use Demo Lead</em> in the top header for instant 1-click testing!
              </div>
            </div>
            <div class="chat-input-bar">
              <input type="text" id="chat-input" class="chat-input" placeholder="Enter company (e.g. 'Research NVIDIA') or lead ('Research Jensen Huang at NVIDIA, CEO')..." onkeypress="if(event.key==='Enter') sendChatMessage()">
              <button class="btn-primary" onclick="sendChatMessage()">Send</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. COMPANY DISCOVERY TAB -->
      <div id="tab-discovery" class="tab-section">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <div>
            <h2 style="font-size:18px; font-weight:700;">🏢 AI-Powered Company & Prospect Discovery</h2>
            <div style="font-size:13px; color:var(--text-muted); margin-top:4px;">
              Enter a company name only. The agent uses DuckDuckGo RAG to retrieve overview, recent announcements, and identify up to 3 verifiable decision-makers.
            </div>
          </div>
        </div>

        <div class="panel-box" style="margin-bottom:20px;">
          <div style="display:flex; gap:12px;">
            <input type="text" id="discovery-company-input" class="chat-input" placeholder="Enter company name (e.g. NVIDIA, Google, Microsoft, Infosys)..." onkeypress="if(event.key==='Enter') runCompanyDiscovery()">
            <button class="btn-primary" onclick="runCompanyDiscovery()">🔍 Discover Prospects</button>
          </div>
          <div style="margin-top:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div style="font-size:12px; color:var(--text-muted); display:flex; gap:12px; align-items:center;">
              <span>Quick Presets:</span>
              <a href="javascript:void(0)" onclick="setDiscoveryInput('NVIDIA')" style="color:var(--primary)">NVIDIA</a>
              <a href="javascript:void(0)" onclick="setDiscoveryInput('Google')" style="color:var(--primary)">Google</a>
              <a href="javascript:void(0)" onclick="setDiscoveryInput('Microsoft')" style="color:var(--primary)">Microsoft</a>
              <a href="javascript:void(0)" onclick="setDiscoveryInput('Infosys')" style="color:var(--primary)">Infosys</a>
            </div>
            <label style="font-size:12px; color:#ffffff; display:flex; align-items:center; gap:6px; cursor:pointer; background:#121214; border:1px solid #262626; padding:6px 12px; border-radius:6px;">
              <input type="checkbox" id="discovery-demo-mode"> <strong>⚡ Fast Verified Profiles</strong>
            </label>
          </div>
        </div>

        <!-- Discovery Progress / Stages indicator -->
        <div id="discovery-progress" style="display:none; margin-bottom:20px;">
          <div class="panel-box" style="border-color:var(--primary);">
            <div style="display:flex; align-items:center; gap:10px;">
              <div class="status-dot"></div>
              <strong style="color:var(--primary);" id="discovery-stage-text">Agent Researching Company via DuckDuckGo...</strong>
            </div>
            <div style="font-size:12px; color:var(--text-muted); margin-top:6px;" id="discovery-substage-text">
              1. Querying DuckDuckGo -> 2. Python RAG Ranking -> 3. Verifying Decision-Maker Roles
            </div>
          </div>
        </div>

        <!-- Discovery Results Container -->
        <div id="discovery-results" style="display:none;">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- 3. LEADS TAB -->
      <div id="tab-leads" class="tab-section">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h2 style="font-size:16px;">Active Lead State Machine</h2>
          <span style="font-size:12px; color:var(--text-muted);">Stored persistently in SQLite</span>
        </div>
        <div class="lead-grid" id="lead-grid">
          <!-- Lead Cards populated dynamically -->
        </div>
      </div>

      <!-- 4. RAG DOSSIER & SEQUENCE TAB -->
      <div id="tab-detail" class="tab-section">
        <div id="detail-empty" style="text-align:center; padding:50px; color:var(--text-muted);">
          Select a lead from the <strong>Leads & Pipeline</strong> tab or use <strong>Company Discovery</strong> to inspect its RAG Research Dossier and Outreach Sequence.
        </div>
        <div id="detail-content" style="display:none;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <div>
              <h2 id="lead-detail-name" style="font-size:22px; font-weight:700;">-</h2>
              <div id="lead-detail-subtitle" style="color:var(--text-muted); font-size:14px;">-</div>
            </div>
            <div style="display:flex; gap:10px;">
              <button class="btn-secondary" onclick="simulateReplyPrompt()">💬 Simulate Inbound Reply</button>
              <button class="btn-secondary" onclick="simulateCadenceAdvance()">⏩ Advance Cadence (No Reply)</button>
            </div>
          </div>

          <!-- RAG Dossier Box -->
          <div class="panel-box">
            <div class="panel-title">🔍 DuckDuckGo RAG Research Dossier</div>
            <div id="dossier-warning-area"></div>
            <div id="dossier-body" style="font-size:14px; line-height:1.6;">-</div>
          </div>

          <!-- Sequence Touches Box -->
          <div class="panel-box">
            <div class="panel-title">✉️ Multi-Touch Sequence (Human Approval Required)</div>
            <div id="touches-body">-</div>
          </div>

          <!-- Inbound Replies & Classifications -->
          <div class="panel-box">
            <div class="panel-title">📥 Inbound Replies & Intent Classification</div>
            <div id="replies-body">-</div>
          </div>
        </div>
      </div>

      <!-- 5. SETTINGS TAB -->
      <div id="tab-settings" class="tab-section">
        <h2 style="font-size:16px; margin-bottom:16px;">⚙️ My Product & Sender Settings</h2>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:20px;">
          Configure your product details below. The agent will use <strong>ONLY</strong> these values in every outreach email. Invented company names, fake stats, or hardcoded personas are strictly forbidden.
        </p>

        <div class="panel-box" style="max-width:650px;">
          <div class="form-group">
            <label>Product Name</label>
            <input type="text" id="setting-product-name" placeholder="e.g. LeadPulse AI">
          </div>
          <div class="form-group">
            <label>What My Product Does (Capabilities)</label>
            <textarea id="setting-what-it-does" rows="3" placeholder="e.g. Automates personalized multi-touch outreach for B2B tech sales teams with factual research grounding."></textarea>
          </div>
          <div class="form-group">
            <label>My Name (Sender Name)</label>
            <input type="text" id="setting-sender-name" placeholder="e.g. Rahul Sharma">
          </div>
          <div class="form-group">
            <label>My Company Name</label>
            <input type="text" id="setting-company-name" placeholder="e.g. ApexScale Labs">
          </div>
          <div class="form-group">
            <label>Calendar / Meeting Link (Optional)</label>
            <input type="text" id="setting-calendly" placeholder="e.g. https://cal.com/rahul/15min">
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
            <button class="btn-primary" onclick="saveSettings()">Save Product Settings</button>
            <span id="settings-save-status" style="font-size:13px; color:var(--accent-green); display:none;">✔ Settings saved successfully!</span>
          </div>
        </div>
      </div>

      <!-- 6. LOGS TAB -->
      <div id="tab-logs" class="tab-section">
        <h2 style="font-size:16px; margin-bottom:12px;">Visible Decision & Reasoning Audit Logs</h2>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th style="width:160px;">Timestamp</th>
                <th style="width:80px;">Lead ID</th>
                <th style="width:160px;">Pipeline Stage</th>
                <th style="width:220px;">Decision</th>
                <th>Reasoning & Autonomous Thought Log</th>
              </tr>
            </thead>
            <tbody id="logs-table-body">
              <!-- Logs populated dynamically -->
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal: Add Lead -->
  <div class="modal-backdrop" id="add-lead-modal">
    <div class="modal">
      <h2>Prospect New Lead</h2>
      <div class="form-group">
        <label>Full Name</label>
        <input type="text" id="lead-name" placeholder="e.g. Satya Nadella">
      </div>
      <div class="form-group">
        <label>Company</label>
        <input type="text" id="lead-company" placeholder="e.g. Microsoft">
      </div>
      <div class="form-group">
        <label>Role / Job Title</label>
        <input type="text" id="lead-role" placeholder="e.g. CEO">
      </div>
      <div class="form-group">
        <label>Industry</label>
        <input type="text" id="lead-industry" placeholder="e.g. Enterprise Cloud & AI">
      </div>
      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeAddLeadModal()">Cancel</button>
        <button class="btn-primary" onclick="submitNewLead()">Launch Research & Draft</button>
      </div>
    </div>
  </div>

  <script>
    let activeLeadId = null;
    let latestDiscoveryData = null;

    function switchTab(tabId) {
      document.querySelectorAll('.tab-section').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');

      const titles = {
        'chat': 'Agent Chatbot & Command Center',
        'discovery': 'AI Company & Prospect Discovery',
        'leads': 'Leads & Pipeline State Machine',
        'detail': 'RAG Research Dossier & Sequence',
        'settings': 'My Product & Sender Settings',
        'logs': 'Agent Decision Logs & Audit Trail'
      };
      document.getElementById('view-title').innerText = titles[tabId] || 'Outreach Agent';

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

    async function loadLatestLead() {
      try {
        const res = await fetch('/api/leads');
        const leads = await res.json();
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

    function setDiscoveryInput(comp) {
      document.getElementById('discovery-company-input').value = comp;
      runCompanyDiscovery();
    }

    async function checkHealth() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        const statusEl = document.getElementById('ollama-status-text');
        const modelEl = document.getElementById('ollama-model-text');
        if (data.ollama_connected) {
          statusEl.innerText = 'Connected';
          statusEl.style.color = 'var(--accent-green)';
        } else {
          statusEl.innerText = 'Offline (Fallback Mode)';
          statusEl.style.color = 'var(--accent-amber)';
        }
        modelEl.innerText = 'Model: ' + data.ollama_model;
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
      } catch (e) {
        console.error(e);
      }
    }

    async function saveSettings() {
      const payload = {
        product_name: document.getElementById('setting-product-name').value.trim(),
        what_it_does: document.getElementById('setting-what-it-does').value.trim(),
        sender_name: document.getElementById('setting-sender-name').value.trim(),
        company_name: document.getElementById('setting-company-name').value.trim(),
        calendly_link: document.getElementById('setting-calendly').value.trim()
      };
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'ok') {
        const statusMsg = document.getElementById('settings-save-status');
        statusMsg.style.display = 'inline';
        setTimeout(() => { statusMsg.style.display = 'none'; }, 3000);
      }
    }

    async function loadDemoLead(type) {
      const res = await fetch('/api/demo-lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      });
      const data = await res.json();
      selectLead(data.lead_id);
    }

    function setDiscoveryInput(company, isDemo = false) {
      document.getElementById('discovery-company-input').value = company;
      document.getElementById('discovery-demo-mode').checked = isDemo;
      runCompanyDiscovery();
    }

    async function runCompanyDiscovery() {
      const input = document.getElementById('discovery-company-input');
      const company = input.value.trim();
      if (!company) { alert('Please enter a company name.'); return; }
      const isDemo = document.getElementById('discovery-demo-mode').checked;
      const mode = isDemo ? 'demo' : 'live';

      const progressBox = document.getElementById('discovery-progress');
      const resultsBox = document.getElementById('discovery-results');
      const stageText = document.getElementById('discovery-stage-text');
      const substageText = document.getElementById('discovery-substage-text');
      
      stageText.innerText = 'Agent Researching Company Intelligence...';
      substageText.innerText = '1. Gathering Web Intelligence -> 2. Verifying Current Designations -> 3. Anti-Hallucination Gate';

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

      // Scenario 1: Live Search Failed
      if (data.status === 'SEARCH_FAILED') {
        box.innerHTML = `
          <div style="background:#121214; border:1px solid #525252; border-radius:8px; padding:16px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="font-size:15px; color:#ffffff;">Search Status: Connection Timed Out</strong>
              <span class="badge" style="background:#18181b; color:#ffffff; border:1px solid #525252;">SEARCH STATUS: FAILED</span>
            </div>
            <p style="margin-top:8px; color:#a1a1aa; font-size:13px;">${data.search_error || 'Search connection timed out or failed to reach web search service.'}</p>
            <div style="margin-top:10px; padding:10px; background:#000000; border-radius:6px; border:1px solid #262626; font-size:12px; color:#a1a1aa;">
              🛡️ <strong>Anti-Hallucination Policy:</strong> Zero artificial or unverified employee names were generated.
            </div>
            <div style="margin-top:12px; display:flex; gap:12px; align-items:center;">
              <button onclick="setDiscoveryInput('NVIDIA');" class="btn-primary" style="font-size:12px; padding:6px 12px; cursor:pointer;">🔍 Research Verified Preset (NVIDIA)</button>
              <span style="font-size:11px; color:#71717a;">Timestamp: ${data.retrieval_timestamp || 'LIVE'}</span>
            </div>
          </div>
        `;
        return;
      }

      // Scenario 2: Not Found
      if (data.status === 'NOT_FOUND' || (data.company_overview === 'NOT FOUND' && (!data.prospects || !data.prospects.length))) {
        box.innerHTML = `
          <div class="error-box">
            <strong>NOT FOUND:</strong> ${data.search_warning || 'Could not verify public leadership or company overview for this company.'}
            <br><small style="color:#a1a1aa;">Zero artificial employee names were invented.</small>
            <br><small style="color:#71717a;">Search Status: ${data.search_status} | Timestamp: ${data.retrieval_timestamp}</small>
          </div>
        `;
        return;
      }

      let html = '';
      html += `
        <div style="background:#0a0a0a; border:1px solid #262626; color:#ffffff; padding:12px 16px; border-radius:8px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <span style="font-weight:700; color:#ffffff; letter-spacing:0.5px;">● VERIFIED COMPANY RESEARCH</span>
            <span style="font-size:11px; color:#a1a1aa; margin-left:12px;">Status: <strong>${data.search_status || 'SUCCESS'}</strong></span>
          </div>
          <span style="font-size:11px; color:#a1a1aa;">🕒 Retrieved: ${data.retrieval_timestamp || 'LIVE'}</span>
        </div>
      `;

      const badgeClass = 'badge-LIVE';
      const badgeText = 'VERIFIED RESEARCH';

      html += `
        <div class="panel-box">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <h3 style="font-size:20px; font-weight:700; color:#ffffff; letter-spacing:-0.3px;">${data.company_name}</h3>
              <p style="margin-top:6px; font-size:14px; color:#d4d4d8; line-height:1.5;">${data.company_overview}</p>
            </div>
            <span class="badge ${badgeClass}">${badgeText}</span>
          </div>
          ${data.search_warning ? `<div class="warning-box" style="margin-top:12px;">⚠️ ${data.search_warning}</div>` : ''}
        </div>
      `;

      // Business Activities & Announcements
      if (data.recent_announcements && data.recent_announcements.length) {
        html += `
          <div class="panel-box">
            <div class="panel-title">📰 Recent Public Announcements & Context</div>
            <ul style="padding-left:18px; font-size:13px; line-height:1.6;">
        `;
        data.recent_announcements.forEach(a => {
          html += `
            <li style="margin-bottom:8px;">
              <strong style="color:#ffffff;">${a.title}</strong><br>
              <span style="color:#a1a1aa;">${a.snippet || ''}</span><br>
              <div style="margin-top:2px; font-size:11px; display:flex; gap:12px;">
                ${a.url ? `<a href="${a.url}" target="_blank" class="source-link">🔗 Source: ${a.url}</a>` : ''}
                <span style="color:#71717a;">🕒 ${data.retrieval_timestamp}</span>
              </div>
            </li>
          `;
        });
        html += `</ul></div>`;
      }

      // Discovered Prospects Section
      html += `
        <div class="panel-box">
          <div class="panel-title">👥 Public Decision-Makers & Designation Verification (Up to 3)</div>
          <p style="font-size:12px; color:var(--text-muted); margin-bottom:14px;">Every prospect is cross-checked against public sources. If their designation cannot be verified, it is explicitly shown as "Role not verified".</p>
      `;

      if (!data.prospects || !data.prospects.length) {
        html += `<div style="background:#121214; border:1px solid #525252; color:#ffffff; padding:12px; border-radius:8px;"><strong>Prospects: NOT FOUND</strong> (No verified executive names discovered in public snippets)</div>`;
      } else {
        data.prospects.forEach((p, idx) => {
          let roleDisplay = '';
          if (p.verification_status === 'ROLE_NOT_VERIFIED' || p.designation === 'Role not verified') {
            roleDisplay = `<span style="color:#a1a1aa; font-weight:600;">• Role not verified</span> <span class="badge" style="background:#18181b; color:#a1a1aa; border:1px solid #3f3f46; font-size:10px;">ROLE NOT VERIFIED</span>`;
          } else if (p.verification_status === 'CONFLICTING_SOURCES' || (p.designation && p.designation.includes('Conflicting sources'))) {
            roleDisplay = `<span style="color:#ffffff; font-weight:600;">• Conflicting sources – manual verification required</span> <span class="badge" style="background:#18181b; color:#ffffff; border:1px solid #52525b; font-size:10px;">CONFLICTING SOURCES</span>`;
          } else {
            roleDisplay = `<span style="color:#ffffff; font-size:13px; font-weight:600;">• ${p.designation}</span> <span class="badge" style="background:#ffffff; color:#000000; font-weight:700; font-size:10px;">VERIFIED</span>`;
          }

          html += `
            <div class="prospect-card">
              <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <strong style="font-size:15px; color:#ffffff;">${p.name}</strong>
                  ${roleDisplay}
                </div>
                <div style="font-size:12px; color:#a1a1aa; margin-top:4px;">
                  ${p.professional_relevance || 'Leadership oversight and strategic roadmap'}
                </div>
                <div style="margin-top:6px; font-size:12px; display:flex; flex-wrap:wrap; gap:12px; align-items:center;">
                  ${p.source_url ? `<a href="${p.source_url}" target="_blank" class="source-link">🔗 Source: ${p.source_title || p.source_url}</a>` : ''}
                  <span style="color:#71717a; font-size:11px;">🕒 ${p.retrieval_timestamp || data.retrieval_timestamp}</span>
                  <span style="color:#a1a1aa; font-size:11px;">Status: ${p.search_status || data.search_status}</span>
                </div>
              </div>
              <button class="btn-action-sm" onclick="launchDiscoveredProspect(${idx})">⚡ Research Prospect</button>
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
      selectLead(data.lead_id);
    }

    async function loadLeads() {
      const res = await fetch('/api/leads');
      const leads = await res.json();
      const grid = document.getElementById('lead-grid');
      grid.innerHTML = '';
      if (!leads.length) {
        grid.innerHTML = '<div style="color:var(--text-muted); grid-column:1/-1;">No leads yet. Use <strong>Company Discovery</strong> or click "+ Add New Lead" above!</div>';
        return;
      }
      leads.forEach(l => {
        const card = document.createElement('div');
        card.className = 'lead-card' + (l.id === activeLeadId ? ' selected' : '');
        card.onclick = () => selectLead(l.id);
        const statusDisplay = l.status === 'AWAITING_APPROVAL' ? 'Draft - Awaiting Approval' : l.status;
        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
            <div>
              <div style="font-weight:700; font-size:16px;">${l.name}</div>
              <div style="color:var(--text-muted); font-size:13px;">${l.role || ''} at <strong style="color:#fff;">${l.company}</strong></div>
            </div>
            <span class="badge badge-${l.status}">${statusDisplay}</span>
          </div>
          <div style="font-size:12px; color:var(--text-muted); display:flex; justify-content:space-between;">
            <span>Current Touch: <strong>#${l.current_touch}/4</strong></span>
            <span>Next: ${l.next_touch_date || 'Awaiting Review'}</span>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    async function selectLead(id) {
      activeLeadId = id;
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
        ${lead.role || ''} at <strong>${lead.company}</strong> | Status: <span class="badge badge-${lead.status}">${statusDisplay}</span> | Touch #${lead.current_touch}/4
      `;

      // Dossier
      const d = lead.research_dossier || {};
      const warnArea = document.getElementById('dossier-warning-area');
      warnArea.innerHTML = '';
      if (d.search_warning) {
        warnArea.innerHTML = `<div class="warning-box">⚠️ ${d.search_warning}</div>`;
      }

      let dHtml = `<p style="margin-bottom:12px;"><strong>Company Overview:</strong> ${d.company_overview || 'NOT FOUND'}</p>`;
      
      const facts = d.facts || [];
      if (!facts.length || (facts.length === 1 && facts[0].fact === 'NOT FOUND')) {
        dHtml += `<div style="background:#121214; border:1px solid #525252; color:#ffffff; padding:10px 14px; border-radius:6px; margin:8px 0;"><strong>Research Facts:</strong> NOT FOUND (No verified public web context found)</div>`;
      } else {
        dHtml += `<h4 style="margin:14px 0 8px; color:#ffffff; font-weight:600;">Verified Public Facts (DuckDuckGo RAG):</h4><ul style="padding-left:18px;">`;
        facts.forEach(f => {
          const factText = f.fact || f;
          const url = f.source_url || '';
          const title = f.source_title || url;
          dHtml += `<li style="margin-bottom:8px;">
            <span>${factText}</span><br>
            ${url ? `<a href="${url}" target="_blank" class="source-link">🔗 Source: ${title}</a>` : ''}
          </li>`;
        });
        dHtml += `</ul>`;
      }

      if (d.tailored_hooks && d.tailored_hooks.length && d.tailored_hooks[0] !== 'NOT FOUND') {
        dHtml += `<h4 style="margin:14px 0 6px; color:#ffffff; font-weight:600;">Tailored Outreach Angles:</h4><ul style="padding-left:18px;">`;
        d.tailored_hooks.forEach(h => dHtml += `<li>${h}</li>`);
        dHtml += `</ul>`;
      }

      document.getElementById('dossier-body').innerHTML = dHtml;

      // Touches
      let tHtml = '';
      if (!touches.length) {
        tHtml = '<p style="color:var(--text-muted);">No touches drafted yet.</p>';
      } else {
        touches.forEach(t => {
          const isAwaiting = t.status === 'AWAITING_APPROVAL';
          tHtml += `
            <div style="background:#0a0a0a; border:1px solid ${isAwaiting ? '#ffffff' : 'var(--card-border)'}; border-radius:8px; padding:16px; margin-bottom:14px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-weight:700; color:var(--primary);">Touch #${t.touch_number} [${t.channel.toUpperCase()}]</span>
                <div style="display:flex; align-items:center; gap:10px;">
                  <span class="badge ${isAwaiting ? 'badge-AWAITING_APPROVAL' : 'badge-SENT'}">
                    ${isAwaiting ? 'Draft - Awaiting Approval' : 'SENT (Simulated)'}
                  </span>
                  ${isAwaiting ? `<button class="btn-approve" onclick="approveTouch(${t.id})">✔ Approve & Send (simulated)</button>` : ''}
                </div>
              </div>
              ${t.subject ? `<div style="font-weight:600; margin-bottom:8px;">Subject: ${t.subject}</div>` : ''}
              <div style="white-space:pre-wrap; font-size:13px; color:#ededed; background:#121214; border:1px solid #262626; padding:12px; border-radius:6px; line-height:1.5;">${t.content}</div>
              <div style="font-size:11px; color:var(--text-muted); margin-top:8px;">
                Evidence used: <span style="color:#ffffff; font-weight:600;">${t.researched_evidence_used || 'Standard product messaging'}</span>
              </div>
            </div>
          `;
        });
      }
      document.getElementById('touches-body').innerHTML = tHtml;

      // Replies
      let rHtml = '';
      if (!replies.length) {
        rHtml = '<p style="color:var(--text-muted);">No inbound replies received yet.</p>';
      } else {
        replies.forEach(r => {
          rHtml += `
            <div style="background:#0a0a0a; border:1px solid var(--card-border); border-radius:8px; padding:14px; margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-weight:700;">Inbound Reply to Touch #${r.in_response_to_touch}</span>
                <span class="badge badge-ESCALATED">${r.classification} (${Math.round((r.confidence || 0.85)*100)}%)</span>
              </div>
              <div style="font-style:italic; margin-bottom:8px; font-size:13px;">"${r.reply_text}"</div>
              <div style="font-size:12px; color:var(--text-muted);">Intent: <strong>${r.extracted_intent || 'N/A'}</strong> | Sentiment: ${r.sentiment || 'N/A'}</div>
            </div>
          `;
        });
      }
      document.getElementById('replies-body').innerHTML = rHtml;
    }

    async function approveTouch(touchId) {
      const res = await fetch('/api/approve-touch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ touch_id: touchId })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        selectLead(activeLeadId);
      }
    }

    async function loadLogs() {
      const res = await fetch('/api/logs');
      const logs = await res.json();
      const tbody = document.getElementById('logs-table-body');
      tbody.innerHTML = '';
      logs.forEach(l => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="color:var(--text-muted);">${(l.timestamp || '').slice(0, 19).replace('T', ' ')}</td>
          <td>${l.lead_id ? '#' + l.lead_id : '-'}</td>
          <td><span style="color:#ffffff; font-weight:600;">${l.stage}</span></td>
          <td><strong style="color:#ffffff;">${l.decision}</strong></td>
          <td class="reasoning-cell">${l.reasoning}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    async function sendChatMessage() {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;

      const chatBox = document.getElementById('chat-messages');
      const userMsg = document.createElement('div');
      userMsg.className = 'message user';
      userMsg.innerText = text;
      chatBox.appendChild(userMsg);
      input.value = '';
      chatBox.scrollTop = chatBox.scrollHeight;

      const thinkingMsg = document.createElement('div');
      thinkingMsg.className = 'message agent';
      thinkingMsg.id = 'temp-thinking';
      thinkingMsg.innerText = '⚙️ Agent reasoning and researching...';
      chatBox.appendChild(thinkingMsg);
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        thinkingMsg.remove();
        if (data.lead_id) {
          activeLeadId = data.lead_id;
        }

        const agentMsg = document.createElement('div');
        agentMsg.className = 'message agent';
        agentMsg.innerHTML = data.reply;
        chatBox.appendChild(agentMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
      } catch (err) {
        thinkingMsg.innerText = 'Error processing request: ' + err.message;
      }
    }

    async function launchProspectFromChat(name, company, role, sourceUrl) {
      const chatBox = document.getElementById('chat-messages');
      const notify = document.createElement('div');
      notify.className = 'message agent';
      notify.innerHTML = `⚙️ <strong>Launching outreach pipeline for ${name} (${role}) at ${company}...</strong><br>DuckDuckGo search + RAG scoring in progress. Touch #1 will be drafted in <em>Draft - Awaiting Approval</em> status.`;
      chatBox.appendChild(notify);
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const res = await fetch('/api/launch-prospect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, company, designation: role, source_url: sourceUrl })
        });
        const data = await res.json();
        activeLeadId = data.lead_id;
        notify.innerHTML = `
          ✅ <strong>Outreach Initiated for ${name} at ${company} (Lead #${data.lead_id})</strong><br><br>
          <strong>Touch #1 Drafted (Status: Draft - Awaiting Approval):</strong><br>
          <em>Subject:</em> ${data.first_touch.subject}<br>
          <pre style="background:#121214; border:1px solid #262626; color:#ededed; padding:12px; border-radius:6px; margin:8px 0; white-space:pre-wrap;">${data.first_touch.content}</pre>
          <small style="color:var(--text-muted);">Source Evidence: ${data.first_touch.researched_evidence_used || sourceUrl}</small><br><br>
          <button onclick="selectLead(${data.lead_id});" class="btn-primary" style="font-size:11px; padding:6px 12px; cursor:pointer;">👉 Review & Approve in Sequence Viewer</button>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
        loadLeads();
      } catch (err) {
        notify.innerHTML = `<span style="color:#f87171;">Error launching prospect: ${err.message}</span>`;
      }
    }

    function openAddLeadModal() { document.getElementById('add-lead-modal').classList.add('open'); }
    function closeAddLeadModal() { document.getElementById('add-lead-modal').classList.remove('open'); }

    async function submitNewLead() {
      const name = document.getElementById('lead-name').value.trim();
      const company = document.getElementById('lead-company').value.trim();
      const role = document.getElementById('lead-role').value.trim();
      const industry = document.getElementById('lead-industry').value.trim();
      if (!name || !company) { alert('Name and Company are required.'); return; }

      closeAddLeadModal();
      switchTab('chat');
      const chatBox = document.getElementById('chat-messages');
      const notify = document.createElement('div');
      notify.className = 'message agent';
      notify.innerHTML = `🚀 <strong>Researching ${name} at ${company}...</strong><br>DuckDuckGo search + RAG scoring in progress. Touch #1 will be drafted in <em>Draft - Awaiting Approval</em> status.`;
      chatBox.appendChild(notify);
      chatBox.scrollTop = chatBox.scrollHeight;

      const res = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, company, role, industry })
      });
      const data = await res.json();

      const finishMsg = document.createElement('div');
      finishMsg.className = 'message agent';
      finishMsg.innerHTML = `
        ✅ <strong>Lead #${data.lead_id} (${name}) Ready!</strong><br><br>
        <strong>Touch #1 Drafted (Status: Draft - Awaiting Approval):</strong><br>
        <em>Subject:</em> ${data.first_touch.subject || 'Direct Note'}<br>
        <pre style="background:#1e293b; padding:10px; border-radius:6px; margin:8px 0; white-space:pre-wrap;">${data.first_touch.content}</pre>
        <button class="btn-approve" onclick="approveTouch(${data.first_touch.touch_id}); this.disabled=true; this.innerText='Approved & Sent';">✔ Approve & Send (simulated)</button>
      `;
      chatBox.appendChild(finishMsg);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function simulateReplyPrompt() {
      if (!activeLeadId) return;
      const text = prompt("Enter simulated reply from prospect:\\n\\nExamples:\\n- 'Sounds good, let's schedule a call on Tuesday' (INTERESTED)\\n- 'We already use competitor, not right now' (OBJECTION)\\n- 'I am out of office until next Monday' (OUT_OF_OFFICE)\\n- 'Please unsubscribe me' (NOT_INTERESTED)");
      if (!text) return;

      const res = await fetch('/api/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_id: activeLeadId, reply_text: text })
      });
      const data = await res.json();
      alert(`Agent Decision: ${data.decision.decision}\\nNew Lead Status: ${data.decision.status}\\n\\nReasoning: ${data.decision.reasoning}`);
      selectLead(activeLeadId);
    }

    async function simulateCadenceAdvance() {
      if (!activeLeadId) return;
      if (!confirm("Simulate no-reply cadence timeout? The agent will draft the next scheduled touch.")) return;
      const res = await fetch('/api/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_id: activeLeadId })
      });
      const data = await res.json();
      alert(`Decision: ${data.decision.decision}\\nNew Status: ${data.decision.status}\\n\\nReasoning: ${data.decision.reasoning}`);
      selectLead(activeLeadId);
    }

    // Init
    checkHealth();
    loadLeads();
    loadSettings();
  </script>
</body>
</html>
"""

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
                reply_text = (
                    f"✅ <strong>Researched {p_name} at {p_comp} (Lead #{res['lead_id']})</strong><br><br>"
                    f"<strong>Touch #1 Drafted (Status: Draft - Awaiting Approval):</strong><br>"
                    f"<em>Subject:</em> {res['first_touch'].get('subject')}<br>"
                    f"<pre style='background:#121214; border:1px solid #262626; color:#ededed; padding:12px; border-radius:6px; margin:8px 0; white-space:pre-wrap;'>{res['first_touch'].get('content')}</pre>"
                    f"<small style='color:var(--text-muted);'>Evidence: {res['first_touch'].get('researched_evidence_used')}</small><br><br>"
                    f"<button onclick=\"selectLead({res['lead_id']})\" class='btn-primary' style='font-size:12px; padding:6px 14px; cursor:pointer; margin-bottom:8px;'>👉 Review in 'RAG Dossier & Sequence' Tab</button><br>"
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
                        f"<div style='background:#121214; border:1px solid #525252; color:#ffffff; padding:14px; border-radius:6px; margin:8px 0;'>"
                        f"<strong>Search Status: Connection Timed Out</strong><br>"
                        f"{disc.get('search_error') or 'DuckDuckGo search connection timed out.'}<br><br>"
                        f"<div style='background:#000000; border:1px solid #262626; padding:8px; border-radius:4px; font-size:12px; color:#a1a1aa;'>"
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
                        f"<p style='color:#a1a1aa;'>{disc.get('search_warning') or 'Search returned 0 verified leadership results for this company. Zero employee names were invented.'}</p>"
                    )
                else:
                    if disc.get("data_source") == "LIVE_SEARCH":
                        header_badge = "<span class='badge' style='background:#ffffff; color:#000000; font-weight:700;'>LIVE SEARCH • VERIFIED RESEARCH</span>"
                    elif disc.get("is_demo_mode") or disc.get("data_source") in ["DEMO_DATA", "DEMO_MODE"]:
                        header_badge = "<span class='badge' style='background:#18181b; color:#ffffff; border:1px solid #52525b;'>DEMO MODE • VERIFIED RESEARCH</span>"
                    else:
                        header_badge = "<span class='badge' style='background:#ffffff; color:#000000; font-weight:700;'>VERIFIED RESEARCH</span>"

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
                            role_html = "<span style='color:#a1a1aa; font-weight:600;'>Role not verified</span> <span class='badge' style='background:#18181b; color:#a1a1aa; border:1px solid #333; font-size:10px;'>ROLE NOT VERIFIED</span>"
                        elif v_status == "CONFLICTING_SOURCES" or "Conflicting sources" in p_desig:
                            role_html = "<span style='color:#ffffff; font-weight:600;'>Conflicting sources – manual verification required</span> <span class='badge' style='background:#18181b; color:#ffffff; border:1px solid #52525b; font-size:10px;'>CONFLICTING SOURCES</span>"
                        else:
                            role_html = f"<span style='color:#ffffff; font-weight:600;'>{p_desig}</span> <span class='badge' style='background:#ffffff; color:#000000; font-weight:700; font-size:10px;'>VERIFIED</span>"

                        reply_text += (
                            f"<div style='background:#0a0a0a; border:1px solid #262626; padding:14px; border-radius:6px; margin:8px 0;'>"
                            f"<strong style='color:#ffffff; font-size:15px;'>{p['name']}</strong> — {role_html}<br>"
                            f"<small style='color:#a1a1aa;'>{p.get('professional_relevance', '')}</small><br>"
                            f"<a href='{p.get('source_url', '#')}' target='_blank' style='color:#ffffff; text-decoration:underline; font-size:12px;'>🔗 Source: {p.get('source_title', p.get('source_url', 'Verified Source'))}</a><br>"
                            f"<small style='color:#71717a;'>🕒 Retrieved: {p.get('retrieval_timestamp', disc.get('retrieval_timestamp', 'N/A'))} | Status: {p.get('search_status', disc.get('search_status', 'SUCCESS'))}</small><br>"
                            f"<button onclick=\"launchProspectFromChat('{safe_name}', '{safe_comp}', '{safe_desig}', '{safe_url}')\" class='btn-action-sm' style='margin-top:8px;'>⚡ Research {p['name']}</button>"
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
