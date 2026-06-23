document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropArea = document.getElementById('drop-area');
    const fileElem = document.getElementById('fileElem');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    
    const recordBtn = document.getElementById('record-btn');
    const timeDisplay = document.getElementById('time-display');
    const recordUiDefault = document.getElementById('record-ui-default');
    
    const transcribeBtn = document.getElementById('transcribe-btn');
    const loading = document.getElementById('loading');
    const resultSection = document.getElementById('result-section');
    const transcriptText = document.getElementById('transcript-text');
    const downloadBtn = document.getElementById('download-btn');
    
    const stars = document.querySelectorAll('.stars i');
    const ratingThanks = document.getElementById('rating-thanks');

    // Canvas Visualizer
    const canvas = document.getElementById('visualizer');
    const canvasCtx = canvas.getContext('2d');
    
    let currentFile = null;
    let mediaRecorder = null;
    let audioChunks = [];
    let recordInterval = null;
    let startTime = null;

    // Audio Context & Analyser
    let audioCtx;
    let analyser;
    let source;
    let animationId;

    // Adjust canvas resolution
    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // File Upload Handling
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
    });

    dropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileElem.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            currentFile = files[0];
            updateFileUI();
        }
    }

    function updateFileUI() {
        if (currentFile) {
            dropArea.classList.add('hidden');
            fileInfo.classList.remove('hidden');
            fileName.textContent = currentFile.name;
            transcribeBtn.disabled = false;
            
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                stopRecording();
            }
        } else {
            dropArea.classList.remove('hidden');
            fileInfo.classList.add('hidden');
            transcribeBtn.disabled = true;
        }
    }

    removeFileBtn.addEventListener('click', () => {
        currentFile = null;
        fileElem.value = '';
        updateFileUI();
    });

    // Recording Handling
    recordBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            stopRecording();
        } else {
            await startRecording();
        }
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Setup Visualizer
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            source = audioCtx.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 2048;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            function draw() {
                resizeCanvas();
                animationId = requestAnimationFrame(draw);
                analyser.getByteTimeDomainData(dataArray);

                canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
                canvasCtx.lineWidth = 2;
                canvasCtx.strokeStyle = '#d4ff00'; // Neon accent
                canvasCtx.beginPath();

                const sliceWidth = canvas.width * 1.0 / bufferLength;
                let x = 0;

                for (let i = 0; i < bufferLength; i++) {
                    const v = dataArray[i] / 128.0;
                    const y = v * canvas.height / 2;

                    if (i === 0) {
                        canvasCtx.moveTo(x, y);
                    } else {
                        canvasCtx.lineTo(x, y);
                    }
                    x += sliceWidth;
                }
                canvasCtx.lineTo(canvas.width, canvas.height / 2);
                canvasCtx.stroke();
            }
            draw();

            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                currentFile = new File([audioBlob], `recording_${new Date().getTime()}.wav`, { type: 'audio/wav' });
                updateFileUI();
                
                stream.getTracks().forEach(track => track.stop());
                if (audioCtx.state !== 'closed') {
                    audioCtx.close();
                }
                cancelAnimationFrame(animationId);
                canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
            });

            mediaRecorder.start();
            
            // UI Updates
            recordBtn.classList.add('recording');
            recordUiDefault.classList.add('hidden');
            timeDisplay.classList.add('active');
            
            // Timer
            startTime = Date.now();
            recordInterval = setInterval(updateTimer, 1000);
            
            if (currentFile) {
                currentFile = null;
                updateFileUI();
            }
            transcribeBtn.disabled = true;

        } catch (err) {
            console.error("Error accessing mic:", err);
            alert("Could not access microphone.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            clearInterval(recordInterval);
            
            recordBtn.classList.remove('recording');
            recordUiDefault.classList.remove('hidden');
            timeDisplay.classList.remove('active');
            timeDisplay.textContent = '00:00';
        }
    }

    function updateTimer() {
        const diff = new Date(Date.now() - startTime);
        const mins = diff.getMinutes().toString().padStart(2, '0');
        const secs = diff.getSeconds().toString().padStart(2, '0');
        timeDisplay.textContent = `${mins}:${secs}`;
    }

    // Transcription Handling
    transcribeBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        const originalBtnText = transcribeBtn.innerHTML;
        transcribeBtn.disabled = true;
        transcribeBtn.innerHTML = 'PROCESSING... <i class="fa-solid fa-spinner fa-spin"></i>';
        
        loading.classList.remove('hidden');
        resultSection.classList.add('hidden');
        resetRating();

        const formData = new FormData();
        formData.append('audio', currentFile);
        formData.append('model_path', document.getElementById('model-path').value);

        try {
            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                transcriptText.textContent = data.text;
                resultSection.classList.remove('hidden');
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred during transcription.');
        } finally {
            loading.classList.add('hidden');
            transcribeBtn.disabled = false;
            transcribeBtn.innerHTML = originalBtnText;
        }
    });

    // Download Handling
    downloadBtn.addEventListener('click', () => {
        const text = transcriptText.textContent;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cs_whisper_transcript_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Rating Handling
    stars.forEach(star => {
        star.addEventListener('mouseover', function() {
            const value = this.getAttribute('data-value');
            highlightStars(value);
        });

        star.addEventListener('mouseout', function() {
            const activeStar = document.querySelector('.stars i.active');
            if (activeStar) {
                highlightStars(activeStar.getAttribute('data-value'));
            } else {
                highlightStars(0);
            }
        });

        star.addEventListener('click', async function() {
            const value = this.getAttribute('data-value');
            stars.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
            highlightStars(value);
            
            try {
                await fetch('/rate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        rating: value,
                        transcript: transcriptText.textContent
                    })
                });
                ratingThanks.classList.remove('hidden');
            } catch (err) {
                console.error('Failed to submit rating', err);
            }
        });
    });

    function highlightStars(value) {
        stars.forEach(star => {
            if (star.getAttribute('data-value') <= value) {
                star.style.color = 'var(--accent)';
            } else {
                star.style.color = '';
            }
        });
    }

    function resetRating() {
        stars.forEach(s => {
            s.classList.remove('active');
            s.style.color = '';
        });
        ratingThanks.classList.add('hidden');
    }
});
