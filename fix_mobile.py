#!/usr/bin/env python3
"""Fix mobile HTML to add model selector"""

# Read original  
with open('mobile_index.html', 'r') as f:
    content = f.read()

# Insert CSS styles after .status-indicator style block
css_insert = '''
        /* Model Selector */
        .model-selector {
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: var(--font-mono);
            font-size: 11px;
        }

        .model-selector select {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 243, 255, 0.3);
            color: var(--accent-color);
            padding: 4px 8px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 10px;
            cursor: pointer;
            transition: all 0.2s;
            backdrop-filter: blur(5px);
        }

        .model-selector select:hover {
            border-color: var(--accent-color);
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
        }

        .model-selector select option {
            background: #1a1a1a;
            color: var(--accent-color);
        }

        .model-label {
            color: var(--text-secondary);
            font-size: 9px;
            text-transform: uppercase;
        }
'''

# Insert CSS before </style>
content = content.replace('</style>', css_insert + '\n    </style>')

# Replace header HTML
old_header = '''    <header>
        <div class="brand">JARVIS</div>
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span>ONLINE</span>
        </div>
    </header>'''

new_header = '''    <header>
        <div class="brand">JARVIS</div>
        <div class="model-selector">
            <span class="model-label">Model</span>
            <select id="model-select" onchange="saveModelPreference()">
                <option value="phi3">Phi-3 (Fast)</option>
                <option value="llama3.1" selected>Llama 3.1 (Default)</option>
                <option value="qwen2.5">Qwen 2.5</option>
                <option value="mistral">Mistral</option>
            </select>
        </div>
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span>ONLINE</span>
        </div>
    </header>'''

content = content.replace(old_header, new_header)

# Add JavaScript functions after recognition setup
js_insert = '''
        // Model Selection
        function loadModelPreference() {
            const savedModel = localStorage.getItem('jarvis_model') || 'llama3.1';
            document.getElementById('model-select').value = savedModel;
        }

        function saveModelPreference() {
            const model = document.getElementById('model-select').value;
            localStorage.setItem('jarvis_model', model);
            console.log('Model changed to:', model);
        }

        function getCurrentModel() {
            return document.getElementById('model-select').value;
        }

        loadModelPreference();

'''

# Find and insert after voice recognition setup
content = content.replace('// Setup Voice Recognition', js_insert + '        // Setup Voice Recognition')

# Update send function to include model
old_send = "body: JSON.stringify({ message: msg })"
new_send = "body: JSON.stringify({ message: msg, model: getCurrentModel() })"
content = content.replace(old_send, new_send)

# Write updated file
with open('mobile_index_final.html', 'w') as f:
    f.write(content)

print("Updated mobile HTML with model selector!")
