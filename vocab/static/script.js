let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let stopRecordingTimeout;

function setupMediaRecorder(stream) {
    mediaRecorder = new MediaRecorder(stream);
    isRecording = true;
    
    mediaRecorder.addEventListener("dataavailable", event => {
        audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", handleRecordingStop);
    mediaRecorder.start();

    // Set to automatically stop recording after 15 seconds
    stopRecordingTimeout = setTimeout(() => {
        if (isRecording) {
            stopRecording();
        }
    }, 15000); // 15000 milliseconds = 15 seconds
}

function stopRecording() {
    if (isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        clearTimeout(stopRecordingTimeout);
    }
}

function handleRecordingStop() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const audioUrl = URL.createObjectURL(audioBlob);
    document.getElementById("audioPlayback").src = audioUrl;

    const formData = new FormData();
    formData.append("audio_data", audioBlob, "recorded_audio.wav");

    // Assuming there's a hidden input with id 'targetWord' that holds the target word
    const targetWord = document.getElementById('targetWord').value;
    formData.append('target_word', targetWord); // Append target word to FormData

    fetch("/study/process_audio", {
        method: "POST",
        body: formData
    })
    .then(response => response.json()) // Assuming the server sends back JSON now
    .then(data => {
        if (data.redirect) {
            window.location.href = data.redirect; // Redirects the browser to the new URL
        } else {
            console.error('No redirect URL provided.');
        }
    })
    .catch(error => console.error("Error:", error));    

    audioChunks = []; // Reset chunks for the next recording
}

document.addEventListener('DOMContentLoaded', function () {
    const flipCard = document.querySelector('.flip-card');
    flipCard.addEventListener('click', function() {
        flipCard.classList.toggle('flipped');
        if (isRecording) {
            stopRecording();  // This will also trigger the file upload now
        }
    });

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(setupMediaRecorder)
        .catch(error => console.error("Error accessing media devices:", error));
});