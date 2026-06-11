document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('storyForm');
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

    // Result Elements
    const resultsSection = document.getElementById('resultsSection');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingStatus = document.getElementById('loadingStatus');
    const resTitle = document.getElementById('resTitle');
    const resContent = document.getElementById('resContent');
    const resTheme = document.getElementById('resTheme');
    const resLang = document.getElementById('resLang');
    const resImages = document.getElementById('resImages');
    const audioTracks = document.getElementById('audioTracks');
    const resVideoContainer = document.getElementById('resVideoContainer');
    const resVideoPlayer = document.getElementById('resVideoPlayer');

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

    // Gallery image loading / error states
    document.querySelectorAll(".gallery-item").forEach((item) => {
        const frame = item.querySelector(".gallery-image-frame");
        const img = item.querySelector(".story-illustration");
        const loader = item.querySelector(".gallery-loader");
        const errorBox = item.querySelector(".gallery-error");
        const retryBtn = item.querySelector(".gallery-retry-btn");

        if (!img || !frame) return;

        const showLoaded = () => {
            if (loader) loader.classList.add("hidden");
            if (errorBox) errorBox.classList.add("hidden");
            img.classList.remove("is-loading");
            img.classList.add("is-loaded");
        };

        const showError = () => {
            if (loader) loader.classList.add("hidden");
            if (errorBox) errorBox.classList.remove("hidden");
            img.classList.remove("is-loaded");
            img.classList.add("is-loading");
        };

        img.classList.add("is-loading");

        if (img.complete && img.naturalWidth > 0) {
            showLoaded();
        } else {
            img.addEventListener("load", showLoaded);
            img.addEventListener("error", showError);
        }

        if (retryBtn) {
            retryBtn.addEventListener("click", () => {
                if (loader) loader.classList.remove("hidden");
                if (errorBox) errorBox.classList.add("hidden");
                img.classList.add("is-loading");
                img.classList.remove("is-loaded");
                const baseSrc = item.dataset.imageUrl || img.getAttribute("src");
                img.src = `${baseSrc.split("?")[0]}?t=${Date.now()}`;
            });
        }
    });

    // Handle Story Form Submission
    if (storyForm) {
        storyForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            console.log("[DEBUG] Story generation started via AJAX");

            // UI State: Loading
            loadingOverlay.classList.remove('hidden');
            resultsSection.classList.add('hidden');
            loadingStatus.textContent = "Weaving your cultural tale...";

            const formData = new FormData(storyForm);
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `Server Error: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    console.log("[DEBUG] Generation successful:", data.story.id);
                    renderStoryResults(data.story);
                } else {
                    throw new Error(data.error || "Failed to generate story.");
                }
            } catch (error) {
                console.error("[ERROR] Fetch failed:", error);
                alert("Generation Error: " + error.message);
            } finally {
                loadingOverlay.classList.add('hidden');
            }
        });
    }

    function renderStoryResults(story) {
        console.log("[DEBUG] Starting frontend render for story:", story.id);
        
        // 1. Text Content
        resTitle.textContent = story.title;
        resTheme.textContent = story.theme;
        resLang.textContent = story.language;

        // Format content paragraphs
        resContent.innerHTML = story.content
            .split('\n\n')
            .map(para => `<p class="story-paragraph">${para.replace(/\n/g, '<br>')}</p>`)
            .join('');
        console.log("[DEBUG] Story text rendered.");

        // 2. Images
        resImages.innerHTML = '';
        if (story.images && story.images.length > 0) {
            story.images.forEach((url, index) => {
                const div = document.createElement('div');
                div.className = 'gallery-item';
                div.innerHTML = `
                    <div class="gallery-image-frame">
                        <img src="${url}" alt="Scene ${index + 1}" class="story-illustration is-loaded">
                    </div>
                `;
                resImages.appendChild(div);
            });
            console.log(`[DEBUG] ${story.images.length} images rendered.`);
        } else {
            resImages.innerHTML = '<p class="status-note">Illustrations could not be generated at this time.</p>';
        }

        // 3. Audio
        audioTracks.innerHTML = '';
        if (story.audio && story.audio.length > 0) {
            story.audio.forEach(url => {
                const audio = document.createElement('audio');
                audio.controls = true;
                audio.src = url;
                audio.className = 'res-audio-control';
                audioTracks.appendChild(audio);
            });
            console.log("[DEBUG] Audio players rendered.");
        } else {
            audioTracks.innerHTML = '<p class="status-note">Narration currently unavailable (connection error).</p>';
        }

        // 4. Video
        if (story.video) {
            resVideoPlayer.src = story.video;
            resVideoPlayer.load();
            resVideoContainer.classList.remove('hidden');
            console.log("[DEBUG] Video player rendered.");
        } else {
            resVideoContainer.classList.remove('hidden');
            resVideoContainer.innerHTML = '<div class="video-placeholder"><p>🎥 Video generation skipped due to missing audio or connection issues.</p></div>';
        }

        // Show results and scroll
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });

        // Re-init intersection observer for new paragraphs
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) entry.target.classList.add('fade-in');
            });
        }, { threshold: 0.1 });
        document.querySelectorAll('.story-paragraph, .gallery-item').forEach(p => observer.observe(p));
        
        console.log("[DEBUG] UI Update complete.");
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
});