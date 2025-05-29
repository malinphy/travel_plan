// Get references to the HTML elements
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const chatBox = document.getElementById('chat-box');

// Add an event listener to the send button
sendButton.addEventListener('click', function() {
    // Get the value from the input field
    const message = userInput.value;

    // Check if the message is not empty
    if (message.trim() !== '') {
        // Create a new div for the user's message
        const userMessageElement = document.createElement('div');
        userMessageElement.textContent = `User: ${message}`;
        userMessageElement.style.marginBottom = '10px'; // Add some spacing

        // Append the user's message to the chat box
        chatBox.appendChild(userMessageElement);

        // Scroll to the bottom of the chat box
        chatBox.scrollTop = chatBox.scrollHeight;

        // Send the message to the FastAPI backend
        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.response) {
                // Display the LLM's response
                const llmResponse = data.response; // Assuming the response key is 'response' from the backend
                const llmMessageElement = document.createElement('div');
                llmMessageElement.textContent = `LLM: ${llmResponse}`;
                llmMessageElement.style.marginBottom = '10px'; // Add some spacing
                llmMessageElement.style.color = 'blue'; // Optional: style LLM responses differently

                chatBox.appendChild(llmMessageElement);
            }
            // Scroll to the bottom of the chat box after adding any new message
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error('Error fetching LLM response:', error);
            const errorMessageElement = document.createElement('div');
            errorMessageElement.textContent = 'LLM: Error fetching response.';
            errorMessageElement.style.marginBottom = '10px';
            errorMessageElement.style.color = 'red';
            chatBox.appendChild(errorMessageElement);
            chatBox.scrollTop = chatBox.scrollHeight;
        });

        userInput.value = ''; // Clear the input field
    }
});