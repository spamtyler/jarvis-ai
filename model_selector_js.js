// Load saved model preference
function loadModelPreference() {
    const savedModel = localStorage.getItem('jarvis_model') || 'llama3.1';
    document.getElementById('model-select').value = savedModel;
}

// Save model preference
function saveModelPreference() {
    const model = document.getElementById('model-select').value;
    localStorage.setItem('jarvis_model', model);
    console.log('Model changed to:', model);
}

// Get current model
function getCurrentModel() {
    return document.getElementById('model-select').value;
}

// Load preference on startup
loadModelPreference();

// MODIFIED: Update send function to include model
async function send() {
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, 'user');
    input.value = '';

    orb.classList.add('active');

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: msg,
                model: getCurrentModel()  // Include selected model
            })
        });
        const data = await await response.json();
        addMessage(data.response, 'jarvis');
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'jarvis');
    } finally {
        orb.classList.remove('active');
    }
}
