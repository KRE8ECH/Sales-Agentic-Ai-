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
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-red: #ef4444;
      --accent-purple: #a855f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    /* Sidebar */
    .sidebar {
      width: 280px;
      background-color: #0b1120;
      border-right: 1px solid var(--card-border);
      display: flex;
      flex-direction: column;
      padding: 20px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
    }
    .brand-icon {
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }
    .brand h2 { font-size: 16px; font-weight: 700; color: #fff; line-height: 1.2; }
    .brand span { font-size: 11px; color: var(--primary); font-weight: 500; }
    
    .nav-tabs {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1;
    }
    .nav-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 8px;
      background: transparent;
      color: var(--text-muted);
      border: none;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      text-align: left;
      transition: all 0.2s;
    }
    .nav-btn:hover { background: #1e293b; color: #fff; }
    .nav-btn.active { background: #1e293b; color: var(--primary); font-weight: 600; border-left: 3px solid var(--primary); }

    .ollama-status-box {
      background: #1e293b;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 14px;
      font-size: 12px;
    }
    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-green);
      margin-right: 6px;
    }

    /* Main Area */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .top-header {
      height: 65px;
      border-bottom: 1px solid var(--card-border);
      background: #0f172a;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
    }
    .top-header h1 { font-size: 18px; font-weight: 600; }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .btn-primary {
      background: linear-gradient(135deg, #38bdf8, #0284c7);
      color: #fff;
      border: none;
      padding: 8px 18px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: opacity 0.2s;
    }
    .btn-primary:hover { opacity: 0.9; }

    .btn-demo {
      background: #1e293b;
      color: #38bdf8;
      border: 1px solid #38bdf8;
      padding: 8px 14px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn-demo:hover { background: rgba(56, 189, 248, 0.15); }

    .btn-approve {
      background: linear-gradient(135deg, #10b981, #059669);
      color: #fff;
      border: none;
      padding: 7px 14px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 12px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: opacity 0.2s;
    }
    .btn-approve:hover { opacity: 0.9; }

    .content-viewport {
      flex: 1;
      overflow-y: auto;
      padding: 24px 28px;
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
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .message {
      max-width: 80%;
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
    }
    .message.agent {
      background: #0b1120;
      border: 1px solid var(--card-border);
      align-self: flex-start;
      border-top-left-radius: 2px;
    }
    .message.user {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff;
      align-self: flex-end;
      border-top-right-radius: 2px;
    }
    .chat-input-bar {
      padding: 16px 20px;
      background: #0f172a;
      border-top: 1px solid var(--card-border);
      display: flex;
      gap: 12px;
    }
    .chat-input {
      flex: 1;
      background: #1e293b;
      border: 1px solid var(--card-border);
      color: #fff;
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 14px;
      outline: none;
    }
    .chat-input:focus { border-color: var(--primary); }

    /* Grid & Cards */
    .lead-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 18px;
      margin-top: 18px;
    }
    .lead-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .lead-card:hover {
      border-color: var(--primary);
      transform: translateY(-2px);
    }
    .lead-card.selected {
      border-color: var(--primary);
      box-shadow: 0 0 0 1px var(--primary);
    }
    .badge {
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-NEW { background: #334155; color: #cbd5e1; }
    .badge-AWAITING_APPROVAL { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-IN_SEQUENCE { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
    .badge-ESCALATED { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .badge-PAUSED { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .badge-STOPPED { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .badge-COMPLETED { background: #1e293b; color: #94a3b8; }
    .badge-SENT { background: rgba(16, 185, 129, 0.2); color: #34d399; }

    /* Modal */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.7);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      background: #1e293b;
      border: 1px solid var(--card-border);
      width: 520px;
      border-radius: 12px;
      padding: 24px;
    }
    .modal h2 { margin-bottom: 16px; font-size: 18px; }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    .form-group input, .form-group textarea {
      width: 100%;
      background: #0f172a;
      border: 1px solid var(--card-border);
      color: #fff;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 14px;
      font-family: inherit;
    }
    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 20px;
    }
    .btn-secondary {
      background: #334155;
      color: #fff;
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
    }

    /* Decision Log Table */
    .table-container {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      overflow: hidden;
      margin-top: 18px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th {
      background: #0b1120;
      text-align: left;
      padding: 14px 18px;
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--card-border);
    }
    td { padding: 14px 18px; border-bottom: 1px solid var(--card-border); }
    tr:last-child td { border-bottom: none; }
    .reasoning-cell { color: #cbd5e1; line-height: 1.4; }

    /* Dossier & Sequence Viewer */
    .panel-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
    }
    .panel-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .warning-box {
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid var(--accent-amber);
      color: #fbbf24;
      padding: 12px 16px;
      border-radius: 8px;
      margin-bottom: 16px;
      font-size: 13px;
    }

    .source-link {
      color: var(--primary);
      text-decoration: underline;
      font-size: 12px;
      display: inline-block;
      margin-top: 3px;
    }

    .dropdown {
      position: relative;
      display: inline-block;
    }
    .dropdown-content {
      display: none;
      position: absolute;
      right: 0;
      background-color: #1e293b;
      min-width: 260px;
      box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.5);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      z-index: 10;
      overflow: hidden;
    }
    .dropdown-content a {
      color: #f8fafc;
      padding: 12px 16px;
      text-decoration: none;
      display: block;
      font-size: 13px;
      cursor: pointer;
    }
    .dropdown-content a:hover { background-color: #0f172a; color: var(--primary); }
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
                <strong>What I do:</strong><br>
                1. 🔍 Research each lead via <strong>DuckDuckGo</strong> and build an evidence dossier with clickable source links.<br>
                2. ✍️ Draft personalized emails strictly using your <strong>My Product Settings</strong> (no invented stats!).<br>
                3. 🛡️ Keep every drafted touch as <strong>"Draft - Awaiting Approval"</strong> until you click <em>Approve & Send</em>.<br>
                4. ⚡ You can click <strong>"Use Demo Lead"</strong> above for instant offline testing!
              </div>
            </div>
            <div class="chat-input-bar">
              <input type="text" id="chat-input" class="chat-input" placeholder="Type a message or instruction (e.g. 'Research Satya Nadella at Microsoft')..." onkeypress="if(event.key==='Enter') sendChatMessage()">
              <button class="btn-primary" onclick="sendChatMessage()">Send</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. LEADS TAB -->
      <div id="tab-leads" class="tab-section">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h2 style="font-size:16px;">Active Lead State Machine</h2>
          <span style="font-size:12px; color:var(--text-muted);">Stored persistently in SQLite</span>
        </div>
        <div class="lead-grid" id="lead-grid">
          <!-- Lead Cards populated dynamically -->
        </div>
      </div>

      <!-- 3. RAG DOSSIER & SEQUENCE TAB -->
      <div id="tab-detail" class="tab-section">
        <div id="detail-empty" style="text-align:center; padding:50px; color:var(--text-muted);">
          Select a lead from the <strong>Leads & Pipeline</strong> tab or click <strong>⚡ Use Demo Lead</strong> above to inspect its RAG Research Dossier and Outreach Sequence.
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

      <!-- 4. SETTINGS TAB -->
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

      <!-- 5. LOGS TAB -->
      <div id="tab-logs" class="tab-section">
        <h2 style="font-size:16px; margin-bottom:12px;">Visible Decision & Reasoning Audit Logs</h2>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th style="width:160px;">Timestamp</th>
                <th style="width:80px;">Lead ID</th>
                <th style="width:140px;">Pipeline Stage</th>
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

    function switchTab(tabId) {
      document.querySelectorAll('.tab-section').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');

      const titles = {
        'chat': 'Agent Chatbot & Command Center',
        'leads': 'Leads & Pipeline State Machine',
        'detail': 'RAG Research Dossier & Sequence',
        'settings': 'My Product & Sender Settings',
        'logs': 'Agent Decision Logs & Audit Trail'
      };
      document.getElementById('view-title').innerText = titles[tabId] || 'Outreach Agent';

      if (tabId === 'leads') loadLeads();
      if (tabId === 'logs') loadLogs();
      if (tabId === 'settings') loadSettings();
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

    async function loadLeads() {
      const res = await fetch('/api/leads');
      const leads = await res.json();
      const grid = document.getElementById('lead-grid');
      grid.innerHTML = '';
      if (!leads.length) {
        grid.innerHTML = '<div style="color:var(--text-muted); grid-column:1/-1;">No leads yet. Click "+ Add New Lead" or "⚡ Use Demo Lead" above!</div>';
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
      
      // Facts with clickable URLs
      const facts = d.facts || [];
      if (!facts.length || (facts.length === 1 && facts[0].fact === 'NOT FOUND')) {
        dHtml += `<div style="background:#0b1120; border:1px solid #ef4444; color:#f87171; padding:10px 14px; border-radius:6px; margin:8px 0;"><strong>Research Facts:</strong> NOT FOUND (No verified public web context found)</div>`;
      } else {
        dHtml += `<h4 style="margin:14px 0 8px; color:#38bdf8;">Verified Public Facts (DuckDuckGo RAG):</h4><ul style="padding-left:18px;">`;
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
        dHtml += `<h4 style="margin:14px 0 6px; color:#38bdf8;">Tailored Outreach Angles:</h4><ul style="padding-left:18px;">`;
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
            <div style="background:#0b1120; border:1px solid ${isAwaiting ? '#f59e0b' : 'var(--card-border)'}; border-radius:8px; padding:16px; margin-bottom:14px;">
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
              <div style="white-space:pre-wrap; font-size:13px; color:#cbd5e1; background:#1e293b; padding:12px; border-radius:6px; line-height:1.5;">${t.content}</div>
              <div style="font-size:11px; color:var(--text-muted); margin-top:8px;">
                Evidence used: <span style="color:#fbbf24;">${t.researched_evidence_used || 'Standard product messaging'}</span>
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
            <div style="background:#0b1120; border:1px solid var(--card-border); border-radius:8px; padding:14px; margin-bottom:10px;">
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
          <td>#${l.lead_id}</td>
          <td><span style="color:var(--primary); font-weight:600;">${l.stage}</span></td>
          <td><strong style="color:#fbbf24;">${l.decision}</strong></td>
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

        const agentMsg = document.createElement('div');
        agentMsg.className = 'message agent';
        agentMsg.innerHTML = data.reply.replace(/\\n/g, '<br>');
        chatBox.appendChild(agentMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
      } catch (err) {
        thinkingMsg.innerText = 'Error processing request: ' + err.message;
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
            if msg.lower().startswith("research") or msg.lower().startswith("prospect") or msg.lower().startswith("add lead"):
                import re
                m = re.search(r"(?:research|prospect|add lead)\s+([A-Za-z\s]+?)\s+at\s+([A-Za-z0-9\s]+?)(?:,\s*([A-Za-z0-9\s]+))?$", msg, re.IGNORECASE)
                if m:
                    p_name = m.group(1).strip()
                    p_comp = m.group(2).strip()
                    p_role = m.group(3).strip() if m.group(3) else "Executive"
                    res = orchestrator.onboard_and_launch_lead(
                        name=p_name,
                        company=p_comp,
                        role=p_role,
                        industry="Technology"
                    )
                    reply_text = (
                        f"✅ Researched and onboarded **{p_name}** at **{p_comp}** (Lead #{res['lead_id']})!\n\n"
                        f"**Touch #1 Drafted (Awaiting Approval):**\n"
                        f"Subject: {res['first_touch'].get('subject')}\n\n"
                        f"{res['first_touch'].get('content')}\n\n"
                        f"*Evidence Grounded:* {res['first_touch'].get('researched_evidence_used')}\n\n"
                        f"👉 *Click 'Approve & Send (simulated)' on the sequence viewer to approve dispatch.*"
                    )
                    self.send_json({"reply": reply_text})
                    return

            try:
                reply = ollama.generate(
                    prompt=msg,
                    system_prompt=(
                        "You are an AI sales outreach strategist and autonomous sales agent assistant. "
                        "Assist the user with prospecting strategy, review drafts, or explain your decision-making framework."
                    )
                )
            except Exception:
                reply = "I'm ready to assist! You can tell me 'Research [Name] at [Company], [Role]' or use the '⚡ Use Demo Lead' button."

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
    server = socketserver.TCPServer(("", port), AgentWebHandler)
    print(f"🚀 Sales Outreach Agent Web UI running at http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    start_server(8000)
