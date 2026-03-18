(function() {
  const voiceBtn = document.getElementById('voice-btn');
  const promptInput = document.getElementById('prompt-input');
  
  if (!voiceBtn || !promptInput) return;

  // Check for browser support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    voiceBtn.style.display = 'none';
    console.warn('Speech recognition not supported in this browser');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  let isRecording = false;

  voiceBtn.addEventListener('click', function() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  function startRecording() {
    try {
      recognition.start();
      isRecording = true;
      voiceBtn.classList.add('recording');
      voiceBtn.title = 'Stop recording';
    } catch (err) {
      console.error('Failed to start recording:', err);
      alert('Failed to start voice input. Please check microphone permissions.');
    }
  }

  function stopRecording() {
    recognition.stop();
    isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceBtn.title = 'Voice input';
  }

  recognition.onresult = function(event) {
    let transcript = '';
    
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    
    // Update input with transcribed text
    promptInput.value = transcript;
    
    // If final result, stop recording
    if (event.results[event.results.length - 1].isFinal) {
      stopRecording();
      promptInput.focus();
    }
  };

  recognition.onerror = function(event) {
    console.error('Speech recognition error:', event.error);
    stopRecording();
    
    if (event.error === 'no-speech') {
      alert('No speech detected. Please try again.');
    } else if (event.error === 'not-allowed') {
      alert('Microphone access denied. Please allow microphone access in your browser settings.');
    } else {
      alert('Voice input error: ' + event.error);
    }
  };

  recognition.onend = function() {
    stopRecording();
  };
})();
