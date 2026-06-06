/**
 * KalaKatha AI — Frontend JavaScript with Smooth Animations
 * Handles form interactions, loading states, audio playback, and smooth animations.
 */

document.addEventListener("DOMContentLoaded", function () {
    initAnimations();
    initStoryForm();
    initListenButton();
    initRecordButton();
    initStoryImages();
});

/**
 * Initialize smooth animations for story elements as they come into view.
 */
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("fade-in");
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe story paragraphs for smooth reveal
    document.querySelectorAll(".story-paragraph").forEach((el) => {
        observer.observe(el);
    });

    // Observe gallery items for smooth reveal
    document.querySelectorAll(".gallery-item, .image-placeholder").forEach((el) => {
        observer.observe(el);
    });

    // Add smooth scroll behavior to all links
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
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
        generateBtn.classList.add("loading");
        generateBtn.disabled = true;

        // Add smooth animation to loading spinner
        const loader = generateBtn.querySelector(".btn-loader");
        if (loader) {
            loader.classList.add("spinner");
        }
    });
}

<<<<<<< HEAD

const SPEECH_LANG_CODES = {
    English: "en-IN",
    Kannada: "kn-IN",
    Hindi: "hi-IN",
    Tamil: "ta-IN",
    Bengali: "bn-IN",
};

/**
 * Listen to Story button — uses gTTS audio from the server,
 * with browser SpeechSynthesis as a fallback.
=======
/**
 * Listen to Story button — placeholder for TTS integration with smooth transitions.
 * Uses browser SpeechSynthesis as a basic fallback demo.
>>>>>>> 0b7a2767b7051ee070ef7fdb2a7ec5ff66593750
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

    function setPlayingState(message) {
        isPlaying = true;
        showAudioBar(audioBar, audioStatus, message);
        listenBtn.innerHTML = '<span class="btn-icon">⏹</span> Stop Narration';
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
            await speakWithBrowserFallback(storyContent, language)
                .then(resetListenButton)
                .catch(function () {
                    showAudioBar(
                        audioBar,
                        audioStatus,
                        "Narration unavailable for " + language + "."
                    );
                    resetListenButton();
                });
            return;
        }

        setPlayingState("Preparing " + language + " narration...");
        listenBtn.disabled = true;

        try {
            const response = await fetch("/story/" + encodeURIComponent(storyId) + "/narrate");
            const data = await response.json();

            if (!response.ok || !data.audio_urls || !data.audio_urls.length) {
                throw new Error(data.error || "Could not generate narration.");
            }

<<<<<<< HEAD
            setPlayingState("Playing " + language + " narration...");
            updateAudioPlayer(data.audio_urls);
            await playAudioSequence(data.audio_urls);
            resetListenButton();
        } catch (error) {
            try {
                await speakWithBrowserFallback(storyContent, language);
                resetListenButton();
            } catch (fallbackError) {
                showAudioBar(
                    audioBar,
                    audioStatus,
                    "Narration unavailable for " + language + "."
                );
                resetListenButton();
            }
        } finally {
            listenBtn.disabled = false;
=======
            const utterance = new SpeechSynthesisUtterance(storyContent);
            utterance.rate = 0.9;
            utterance.pitch = 1;

            utterance.onstart = function () {
                isSpeaking = true;
                listenBtn.classList.add("loading");
                listenBtn.disabled = true;

                // Smooth animation for audio bar appearance
                showAudioBar(audioBar, audioStatus, "Playing narration (browser demo)...");
                listenBtn.querySelector(".btn-text, .btn-icon")
                    ? (listenBtn.innerHTML = '<span class="btn-icon">⏹</span> Stop Narration')
                    : null;

                // Add smooth fade-in animation to audio content
                const storyElements = document.querySelectorAll(".story-paragraph");
                storyElements.forEach((el, index) => {
                    el.style.animation = `fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.1}s both`;
                });
            };

            utterance.onend = function () {
                isSpeaking = false;
                listenBtn.classList.remove("loading");
                listenBtn.disabled = false;
                hideAudioBar(audioBar);
                listenBtn.innerHTML = '<span class="btn-icon">🔊</span> Listen to Story';
            };

            utterance.onerror = function () {
                isSpeaking = false;
                listenBtn.classList.remove("loading");
                listenBtn.disabled = false;
                showAudioBar(audioBar, audioStatus, "Narration unavailable. Connect TTS API in text_to_speech.py.");
            };

            window.speechSynthesis.speak(utterance);
        } else {
            showAudioBar(
                audioBar,
                audioStatus,
                "AI narration coming soon! Connect gTTS in text_to_speech.py."
            );
>>>>>>> 0b7a2767b7051ee070ef7fdb2a7ec5ff66593750
        }
    });

    if (stopAudioBtn) {
<<<<<<< HEAD
        stopAudioBtn.addEventListener("click", stopPlayback);
=======
        stopAudioBtn.addEventListener("click", function () {
            if ("speechSynthesis" in window) {
                window.speechSynthesis.cancel();
            }
            isSpeaking = false;
            listenBtn.classList.remove("loading");
            listenBtn.disabled = false;
            hideAudioBar(audioBar);
            if (listenBtn) {
                listenBtn.innerHTML = '<span class="btn-icon">🔊</span> Listen to Story';
            }
        });
>>>>>>> 0b7a2767b7051ee070ef7fdb2a7ec5ff66593750
    }
}

/**
 * Record Grandma's Story button — UI placeholder notification.
 */
function initRecordButton() {
    const recordBtn = document.getElementById("recordBtn");

    if (!recordBtn) return;

    recordBtn.addEventListener("click", function () {
        alert(
            "Voice recording is coming soon!\n\n" +
            "This feature will let you record elders narrating folk tales " +
            "and convert their voices into permanent digital archives."
        );
    });
}

/**
 * Story illustration gallery — loading states and error handling.
 */
function initStoryImages() {
    const galleryItems = document.querySelectorAll(".gallery-item");

    galleryItems.forEach(function (item) {
        const img = item.querySelector(".story-illustration");
        const loader = item.querySelector(".gallery-loader");
        const errorPanel = item.querySelector(".gallery-error");
        const retryBtn = item.querySelector(".gallery-retry-btn");
        const rawUrl = item.getAttribute("data-image-url");

        if (!img || !rawUrl) return;

        const imageUrl = normalizeImageUrl(rawUrl);

        function showLoader() {
            if (loader) loader.classList.remove("hidden");
            if (errorPanel) errorPanel.classList.add("hidden");
            img.classList.remove("is-loaded");
            img.style.display = "block";
        }

        function showImage() {
            if (loader) loader.classList.add("hidden");
            if (errorPanel) errorPanel.classList.add("hidden");
            img.classList.add("is-loaded");
        }

        function showError() {
            if (loader) loader.classList.add("hidden");
            if (errorPanel) errorPanel.classList.remove("hidden");
            img.style.display = "none";
            img.classList.remove("is-loaded");
        }

        function attachHandlers() {
            img.onload = function () {
                if (img.naturalWidth > 0) {
                    showImage();
                } else {
                    showError();
                }
            };

            img.onerror = function () {
                showError();
            };
        }

        function loadImage() {
            showLoader();
            attachHandlers();

            const separator = imageUrl.includes("?") ? "&" : "?";
            img.src = imageUrl + separator + "t=" + Date.now();
        }

        attachHandlers();

        if (img.complete && img.naturalWidth > 0) {
            showImage();
        } else if (img.complete && img.naturalWidth === 0 && img.src) {
            loadImage();
        } else {
            img.src = imageUrl;
        }

        if (retryBtn) {
            retryBtn.addEventListener("click", loadImage);
        }
    });
}


/**
 * Fix older Pollinations URLs saved before model=flux was required.
 */
function normalizeImageUrl(url) {
    if (!url.includes("pollinations.ai")) {
        return url;
    }

    if (url.includes("model=")) {
        return url;
    }

    const separator = url.includes("?") ? "&" : "?";
    return url + separator + "model=flux&width=1024&height=1024";
}


/**
 * Populate the HTML audio player with generated narration tracks.
 */
function updateAudioPlayer(urls) {
    const player = document.getElementById("storyAudioPlayer");
    const tracks = document.getElementById("audioPlayerTracks");

    if (!player || !tracks || !urls || !urls.length) {
        return;
    }

    tracks.innerHTML = "";

    urls.forEach(function (url) {
        const audio = document.createElement("audio");
        audio.controls = true;
        audio.className = "story-audio-element";
        audio.src = url;
        tracks.appendChild(audio);
    });

    player.classList.remove("hidden");
}


/**
 * Read story text from the hidden JSON script tag on story.html.
 */
function getStoryContent() {
    return readStoryJson("storyContentData", "");
}

/**
 * Read story ID from the hidden JSON script tag on story.html.
 */
function getStoryId() {
    return readStoryJson("storyIdData", null);
}

/**
 * Read story language from the hidden JSON script tag on story.html.
 */
function getStoryLanguage() {
    return readStoryJson("storyLanguageData", "English");
}

function readStoryJson(elementId, fallback) {
    const dataEl = document.getElementById(elementId);
    if (!dataEl) return fallback;

    try {
        return JSON.parse(dataEl.textContent);
    } catch (error) {
        return fallback;
    }
}

/**
 * Show the bottom audio status bar with smooth animation.
 */
function showAudioBar(audioBar, audioStatus, message) {
    if (!audioBar) return;
    audioBar.classList.remove("hidden");
    if (audioStatus) {
        audioStatus.textContent = message;
    }

    // Trigger animation by removing class before re-adding
    audioBar.offsetHeight;
    audioBar.style.animation = "none";
    setTimeout(() => {
        audioBar.style.animation = "slideInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
    }, 10);
}

/**
 * Hide the bottom audio status bar with smooth fade-out animation.
 */
function hideAudioBar(audioBar) {
    if (!audioBar) return;
    audioBar.style.animation = "slideOutDown 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
    setTimeout(() => {
        audioBar.classList.add("hidden");
        audioBar.style.animation = "";
    }, 400);
}

/**
 * Smooth page transition helper for navigation.
 */
function smoothTransitionToPage(url) {
    const body = document.body;
    body.style.animation = "fadeOut 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
    setTimeout(() => {
        window.location.href = url;
    }, 400);
}
