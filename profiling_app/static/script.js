const actionButton = document.getElementById('action-button');
const messageInput = document.getElementById('message-input');
const messageList = document.getElementById('message-list');
const toast = document.getElementById('toast');
let mediaRecorder;
let audioChunks = [];

// Function to set microphone icon
function setMicIcon() {
    actionButton.innerHTML = "<i style='font-size:20px' class='fas fa-microphone'></i>";
}

// Function to set send text
function setSendText() {
    actionButton.innerHTML = "Send";
}

actionButton.addEventListener('mousedown', function() {
    // Only start recording if input is empty
    if (messageInput.value.trim() === "") {
        startVoiceRecording(); // Start voice recording if input is empty
        setMicIcon(); // Indicate listening
    }
});

actionButton.addEventListener('mouseup', function() {
    if (messageInput.value.trim() === "") {
        stopVoiceRecording(); // Stop recording and send the audio
        setMicIcon(); // Reset button text
    }
});
actionButton.addEventListener('mouseleave', function() {
    if (messageInput.value.trim() === "") {
        stopVoiceRecording(); // Stop recording if mouse leaves button
        setMicIcon(); // Reset button text

    }
});


messageInput.addEventListener('input', function() {
    if (messageInput.value.trim() === "") {
        setMicIcon(); // Change button to voice icon if input is empty
    } else {
        setSendText(); // Change button to send if there's text
    }
});

// Unified click event to handle sending messages and starting voice recording
actionButton.addEventListener('click', async function() {
    if (messageInput.value.trim() !== "") {
        await sendMessage(messageInput.value); // Wait for message to be sent
        messageInput.value = ""; // Clear input after sending
        setMicIcon(); // Reset to mic icon
    }
});

messageInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter' && messageInput.value.trim() !== "") {
        sendMessage(messageInput.value);
        messageInput.value = ""; // Clear input after sending
        setMicIcon(); // Reset to mic icon
    }
});

function showToast(message) {
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000); // Hide after 3 seconds
}

async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'audio.wav');

            const response = await fetch('/process-audio', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.transcription) {
                await sendMessage(data.transcription); // Send transcription as user input
            } else {
                showToast("An error occurred");
            }
        };

        mediaRecorder.onerror = function(event) {
            console.error('Error occurred in recording: ' + event.error);
            showToast("Couldn't understand, please try again.");
        };
    } catch (err) {
        console.error('Error accessing microphone: ' + err);
        showToast("Couldn't access microphone.");
    }
}

function stopVoiceRecording() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        audioChunks = []; // Clear the audio chunks
    }
}

async function sendMessage(message) {
    const userMessage = document.createElement('div');
    userMessage.className = 'message';
    userMessage.textContent = message;
    messageList.appendChild(userMessage);
    messageList.scrollTop = messageList.scrollHeight; // Scroll to bottom

    // Show loading animation in the message list
    const loadingContainer = document.createElement('div');
    loadingContainer.className = 'loading-animation';
    loadingContainer.innerHTML = `
        <div class="loading-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>`;
    messageList.appendChild(loadingContainer);
    messageList.scrollTop = messageList.scrollHeight; // Scroll to bottom

    // Simulate bot response delay
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for 2 seconds
    messageList.removeChild(loadingContainer); // Remove loading animation
    displayBotMessage("This is a bot response to: " + message); // Simulate bot response
}

function displayBotMessage(response) {
    const botMessage = document.createElement('div');
    botMessage.className = 'bot-message';
    botMessage.textContent = response;
    messageList.appendChild(botMessage);
    messageList.scrollTop = messageList.scrollHeight; // Scroll to bottom
}
