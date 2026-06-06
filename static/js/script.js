document.addEventListener('DOMContentLoaded', () => {
    const storyId = JSON.parse(document.getElementById('storyIdData').textContent);
    const listenBtn = document.getElementById('listenBtn');
    const videoBtn = document.getElementById('videoBtn');
    const storyAudioPlayer = document.getElementById('storyAudioPlayer');
    const audioPlayerTracks = document.getElementById('audioPlayerTracks');
    const storyVideoPlayer = document.getElementById('storyVideoPlayer');
    const storyVideoElement = document.getElementById('storyVideoElement');

    // Helper to toggle loading state
    const toggleLoading = (btn, isLoading, text) => {
        btn.disabled = isLoading;
        btn.querySelector('.btn-text').textContent = text;
        const loader = btn.querySelector('.spinner') || btn.querySelector('.btn-loader');
        if (loader) loader.classList.toggle('hidden', !isLoading);
    };

<<<<<<< Updated upstream
    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add("fade-in");
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll(".story-paragraph").forEach(function (el) {
        observer.observe(el);
    });

    document.querySelectorAll(".gallery-item, .image-placeholder").forEach(function (el) {
        observer.observe(el);
    });

    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener("click", function (event) {
            event.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
}

/**
 * Story generation form — show loading state on submit with animations.
 */
function initStoryForm() {
    const form = document.getElementById("storyForm");
    const generateBtn = document.getElementById("generateBtn");

    if (!form || !generateBtn) return;

    form.addEventListener("submit", function () {
        generateBtn.disabled = true;
        // Replace inner content to isolate the spinner from the text
        generateBtn.innerHTML = '<span class="btn-loader spinner"></span> <span>Generating Story...</span>';
        generateBtn.classList.add("loading");
        generateBtn.disabled = true;

        const loader = generateBtn.querySelector(".btn-loader");
        if (loader) {
            loader.classList.add("spinner");
        }
    });
}

/**
 * Listen to Story button — uses gTTS audio from the server,
 * with browser SpeechSynthesis as a fallback.
 */
function initListenButton() {
    const listenBtn = document.getElementById("listenBtn");
    const audioBar = document.getElementById("audioBar");
    const audioStatus = document.getElementById("audioStatus");
    const stopAudioBtn = document.getElementById("stopAudioBtn");

    if (!listenBtn) return;

    let isPlaying = false;
    let currentAudio = null;

    function resetListenButton() {
        isPlaying = false;
        currentAudio = null;
        listenBtn.classList.remove("loading");
        listenBtn.disabled = false;
        hideAudioBar(audioBar);
        listenBtn.innerHTML = '<span class="btn-icon">🔊</span> Listen to Story';
    }

    function stopPlayback() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio.onended = null;
            currentAudio.onerror = null;
            currentAudio = null;
        }

        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }

        resetListenButton();
    }

    function animateStoryParagraphs() {
        document.querySelectorAll(".story-paragraph").forEach(function (el, index) {
            el.style.animation = "fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) " + (index * 0.1) + "s both";
        });
    }

    function setPlayingState(message) {
        isPlaying = true;
        listenBtn.classList.add("loading");
        showAudioBar(audioBar, audioStatus, message);
        listenBtn.innerHTML = '<span class="btn-icon">⏹</span> Stop Narration';
        animateStoryParagraphs();
    }

    function playAudioSequence(urls) {
        return new Promise(function (resolve, reject) {
            let index = 0;

            function playNext() {
                if (index >= urls.length) {
                    currentAudio = null;
                    resolve();
                    return;
                }

                currentAudio = new Audio(urls[index]);
                currentAudio.onended = function () {
                    index += 1;
                    playNext();
                };
                currentAudio.onerror = function () {
                    reject(new Error("Audio playback failed."));
                };

                currentAudio.play().catch(reject);
            }

            playNext();
        });
    }

    function speakWithBrowserFallback(storyContent, language) {
        return new Promise(function (resolve, reject) {
            if (!("speechSynthesis" in window)) {
                reject(new Error("Speech synthesis is not supported."));
                return;
            }

            const utterance = new SpeechSynthesisUtterance(storyContent);
            utterance.lang = SPEECH_LANG_CODES[language] || "en-IN";
            utterance.rate = 0.9;
            utterance.pitch = 1;

            utterance.onstart = function () {
                setPlayingState("Playing narration (" + language + ")...");
            };

            utterance.onend = function () {
                resolve();
            };

            utterance.onerror = function () {
                reject(new Error("Browser narration failed."));
            };

            window.speechSynthesis.speak(utterance);
        });
    }

    listenBtn.addEventListener("click", async function () {
        if (isPlaying) {
            stopPlayback();
            return;
        }

        const storyContent = getStoryContent();
        const storyId = getStoryId();
        const language = getStoryLanguage();

        if (!storyContent) {
            showAudioBar(audioBar, audioStatus, "No story content available.");
            return;
        }

        if (!storyId) {
=======
    // Handle Narration Generation
    if (listenBtn) {
        listenBtn.addEventListener('click', async () => {
            toggleLoading(listenBtn, true, 'Generating Narration...');
            
>>>>>>> Stashed changes
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
                    storyVideoElement.src = data.video_url;
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