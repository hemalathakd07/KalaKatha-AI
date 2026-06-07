document.addEventListener('DOMContentLoaded', () => {
    let storyId = "";
    try {
        storyId = JSON.parse(document.getElementById('storyIdData').textContent);
    } catch(e) {
        console.warn("Story ID not found in page data");
    }

    const listenBtn = document.getElementById('listenBtn');
    const videoBtn = document.getElementById('videoBtn');
    const storyAudioPlayer = document.getElementById('storyAudioPlayer');
    const audioPlayerTracks = document.getElementById('audioPlayerTracks');
    const storyVideoPlayer = document.getElementById('storyVideoPlayer');
    const storyVideoElement = document.getElementById('storyVideoElement');

    // Recorder Elements
    const startRecordBtn = document.getElementById('startRecordBtn');
    const stopRecordBtn = document.getElementById('stopRecordBtn');
    const recordStatus = document.getElementById('recordStatus');
    const recordingWave = document.getElementById('recordingWave');
    const audioUpload = document.getElementById('audioUpload');

    // Helper to toggle loading state
    const toggleLoading = (btn, isLoading, text) => {
        btn.disabled = isLoading;
        btn.querySelector('.btn-text').textContent = text;
        const loader = btn.querySelector('.spinner') || btn.querySelector('.btn-loader');
        if (loader) loader.classList.toggle('hidden', !isLoading);
    };

    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add("fade-in");
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Init animations
    document.querySelectorAll(".story-paragraph, .gallery-item, .image-placeholder").forEach(el => {
        observer.observe(el);
    });

    // Handle Story Form Submission
    const form = document.getElementById("storyForm");
    const generateBtn = document.getElementById("generateBtn");
    if (form && generateBtn) {
        form.addEventListener("submit", () => {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<span class="btn-loader spinner"></span> <span>Generating Story...</span>';
        });
    }

    // --- Recording Logic ---
    let mediaRecorder;
    let audioChunks = [];

    if (startRecordBtn && stopRecordBtn) {
        startRecordBtn.addEventListener('click', async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    await uploadAudio(audioBlob);
                };

                mediaRecorder.start();
                startRecordBtn.classList.add('hidden');
                stopRecordBtn.classList.remove('hidden');
                recordingWave.classList.remove('hidden');
                recordStatus.textContent = "Recording... Speak clearly.";
                recordStatus.style.color = "#ff4d4d";
            } catch (err) {
                console.error("Mic error:", err);
                alert("Microphone access denied. Please check browser permissions.");
            }
        });

        stopRecordBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                stopRecordBtn.disabled = true;
                stopRecordBtn.textContent = "Processing Audio...";
                recordingWave.classList.add('hidden');
            }
        });
    }

    // Handle direct file upload
    if (audioUpload) {
        audioUpload.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                recordStatus.textContent = "Uploading file...";
                await uploadAudio(file);
            }
        });
    }

    async function uploadAudio(audioFile) {
        const formData = new FormData();
        formData.append('audio', audioFile);
        
        // Get current language and theme from the story form
        const language = document.getElementById('language')?.value || 'English';
        const themeEl = document.querySelector('input[name="theme"]:checked');
        const theme = themeEl ? themeEl.value : 'Folk Tale';

        formData.append('language', language);
        formData.append('theme', theme);

        recordStatus.textContent = "Weaving a story from your voice... This takes a moment.";

        try {
            const response = await fetch('/upload-audio', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                resetRecorderUI(data.error || "Generation failed.");
            }
        } catch (err) {
            console.error("Upload failed:", err);
            resetRecorderUI("Server error. Check your connection.");
        }
    }

    function resetRecorderUI(errorMsg) {
        alert("Error: " + errorMsg);
        startRecordBtn.classList.remove('hidden');
        stopRecordBtn.classList.add('hidden');
        stopRecordBtn.disabled = false;
        stopRecordBtn.innerHTML = '<span class="btn-icon">⏹️</span> Stop & Process';
        recordingWave.classList.add('hidden');
        recordStatus.textContent = "Ready to try again.";
        recordStatus.style.color = "inherit";
        if(audioUpload) audioUpload.value = "";
    }

    // Handle Narration Generation
    if (listenBtn) {
        listenBtn.addEventListener('click', async () => {
            toggleLoading(listenBtn, true, 'Generating Narration...');
            
            try {
                const response = await fetch(`/story/${storyId}/narrate`);
                const data = await response.json();
                
                if (response.ok) {
                    audioPlayerTracks.innerHTML = '';
                    data.audio_urls.forEach(url => {
                        const audio = document.createElement('audio');
                        audio.controls = true;
                        audio.className = 'story-audio-element';
                        audio.src = url;
                        audioPlayerTracks.appendChild(audio);
                    });
                    storyAudioPlayer.classList.remove('hidden');
                    toggleLoading(listenBtn, false, 'Listen to Story');
                } else {
                    alert('Error: ' + data.error);
                    toggleLoading(listenBtn, false, 'Try Narration Again');
                }
            } catch (err) {
                console.error(err);
                toggleLoading(listenBtn, false, 'Narration Failed');
            }
        });
    }

    // Handle Video Generation
    if (videoBtn) {
        videoBtn.addEventListener('click', async () => {
            toggleLoading(videoBtn, true, 'Crafting Video (may take a minute)...');
            
            try {
                const response = await fetch(`/story/${storyId}/video`);
                const data = await response.json();
                
                if (response.ok) {
                    // Update video source and show player
                    storyVideoElement.innerHTML = `<source src="${data.video_url}" type="video/mp4">`;
                    storyVideoElement.load();
                    storyVideoPlayer.classList.remove('hidden');
                    
                    // Scroll smoothly to video
                    storyVideoPlayer.scrollIntoView({ behavior: 'smooth' });
                    
                    // Update button
                    videoBtn.classList.replace('btn-secondary', 'btn-primary');
                    toggleLoading(videoBtn, false, 'Watch Video');
                } else {
                    alert('Note: ' + data.error);
                    toggleLoading(videoBtn, false, 'Generate Video');
                }
            } catch (err) {
                console.error(err);
                alert('Video generation failed. Please check if FFmpeg is installed.');
                toggleLoading(videoBtn, false, 'Generation Failed');
            }
        });
    }
});