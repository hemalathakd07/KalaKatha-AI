/**
 * KalaKatha AI — Frontend JavaScript with Smooth Animations
 * Handles form interactions, loading states, audio playback, and smooth animations.
 */

document.addEventListener("DOMContentLoaded", function () {
    initAnimations();
    initStoryForm();
    initListenButton();
    initRecordButton();
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

/**
 * Listen to Story button — placeholder for TTS integration with smooth transitions.
 * Uses browser SpeechSynthesis as a basic fallback demo.
 */
function initListenButton() {
    const listenBtn = document.getElementById("listenBtn");
    const audioBar = document.getElementById("audioBar");
    const audioStatus = document.getElementById("audioStatus");
    const stopAudioBtn = document.getElementById("stopAudioBtn");

    if (!listenBtn) return;

    let isSpeaking = false;

    listenBtn.addEventListener("click", function () {
        const storyContent = getStoryContent();

        if (!storyContent) {
            showAudioBar(audioBar, audioStatus, "No story content available.");
            return;
        }

        // Check if browser supports speech synthesis (demo fallback)
        if ("speechSynthesis" in window) {
            if (isSpeaking) {
                window.speechSynthesis.cancel();
                isSpeaking = false;
                hideAudioBar(audioBar);
                return;
            }

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
        }
    });

    if (stopAudioBtn) {
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
 * Read story text from the hidden JSON script tag on story.html.
 */
function getStoryContent() {
    const dataEl = document.getElementById("storyContentData");
    if (!dataEl) return "";

    try {
        return JSON.parse(dataEl.textContent);
    } catch (error) {
        return "";
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
