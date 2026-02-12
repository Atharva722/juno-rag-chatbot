document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const fileUpload = document.getElementById('file-upload');
    const documentList = document.getElementById('document-list');
    const modelSelect = document.getElementById('model-select');

    const API_URL = 'http://localhost:5001';
    let sessionId = null;

    // --- Helper Functions ---

    const addMessage = (role, content) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'mb-4', 'flex');

        const iconDiv = document.createElement('div');
        iconDiv.classList.add('w-10', 'h-10', 'rounded-full', 'flex', 'items-center', 'justify-center', 'mr-3', 'flex-shrink-0');
        
        const textDiv = document.createElement('div');
        textDiv.classList.add('p-3', 'rounded-lg', 'max-w-md');

        if (role === 'user') {
            messageDiv.classList.add('justify-end');
            iconDiv.classList.add('bg-blue-500');
            iconDiv.innerHTML = '<i class="fas fa-user"></i>';
            textDiv.classList.add('bg-blue-500', 'text-white');
            messageDiv.appendChild(textDiv);
            messageDiv.appendChild(iconDiv);
        } else {
            messageDiv.classList.add('justify-start');
            iconDiv.classList.add('bg-gray-700');
            iconDiv.innerHTML = '<i class="fas fa-robot"></i>';
            textDiv.classList.add('bg-gray-700', 'text-white');
            messageDiv.appendChild(iconDiv);
            messageDiv.appendChild(textDiv);
        }

        textDiv.innerText = content;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // --- API Calls ---

    const fetchDocuments = async () => {
        try {
            const response = await fetch(`${API_URL}/list-docs`);
            if (!response.ok) throw new Error('Failed to fetch documents.');
            
            const docs = await response.json();
            documentList.innerHTML = ''; // Clear list

            if (docs.length === 0) {
                documentList.innerHTML = '<p class="text-gray-500 text-sm">No documents uploaded.</p>';
            } else {
                docs.forEach(doc => {
                    const docElement = document.createElement('div');
                    docElement.className = 'bg-gray-700 p-2 rounded-lg flex justify-between items-center text-sm';
                    docElement.innerHTML = `
                        <span class="truncate pr-2">${doc.filename}</span>
                        <button class="text-red-500 hover:text-red-400 delete-btn flex-shrink-0" data-id="${doc.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    `;
                    documentList.appendChild(docElement);
                });
            }
        } catch (error) {
            console.error(error);
            documentList.innerHTML = '<p class="text-red-500 text-sm">Error loading documents.</p>';
        }
    };

    // --- Event Listeners ---

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question) return;

        addMessage('user', question);
        chatInput.value = '';

        // Add a temporary "thinking" message from the assistant
        addMessage('assistant', 'Thinking...');

        try {
            // FIX: The endpoint must be '/chat' to match main.py
            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId,
                    model: modelSelect.value
                })
            });

            // Remove the "thinking" message
            chatBox.removeChild(chatBox.lastChild);

            if (!response.ok) throw new Error('API request failed.');

            const data = await response.json();
            sessionId = data.session_id;
            addMessage('assistant', data.answer);
        } catch (error) {
            console.error(error);
            // Remove the "thinking" message and show an error instead
            if (chatBox.lastChild.innerText.includes('Thinking...')) {
                 chatBox.removeChild(chatBox.lastChild);
            }
            addMessage('assistant', 'Sorry, something went wrong. Please check the terminal for errors.');
        }
    });

    fileUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        // Optional: Show a temporary "uploading" message
        const uploadingMessage = document.createElement('p');
        uploadingMessage.className = 'text-blue-400 text-sm';
        uploadingMessage.innerText = `Uploading ${file.name}...`;
        documentList.prepend(uploadingMessage);

        try {
            const response = await fetch(`${API_URL}/upload-doc`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                 const errorData = await response.json();
                 throw new Error(errorData.detail || 'File upload failed.');
            }
            
            // Success, now refresh the list
            fetchDocuments();
        } catch (error) {
            console.error(error);
            alert(`Error uploading file: ${error.message}`);
            // On error, remove the "uploading" message and refresh to show the current state
            fetchDocuments();
        }
    });

    documentList.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            const button = e.target.closest('.delete-btn');
            const fileId = button.dataset.id;
            
            if (confirm('Are you sure you want to delete this document?')) {
                try {
                    const response = await fetch(`${API_URL}/delete-doc`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ file_id: parseInt(fileId) })
                    });
                    if (!response.ok) throw new Error('Failed to delete document.');
                    
                    fetchDocuments(); // Refresh the list on success
                } catch (error) {
                    console.error(error);
                    alert('Error deleting document.');
                }
            }
        }
    });

    // Initial load
    fetchDocuments();
});
