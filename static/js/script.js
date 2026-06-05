/**
 * KalaKatha AI — Frontend JavaScript
 * Handles form interactions, loading states, and audio playback placeholder.
 */

document.addEventListener("DOMContentLoaded", function () {
    initStoryForm();
    initListenButton();
    initRecordButton();
});


/**
 * Story generation form — show loading state on submit.
 */
function initStoryForm() {
    const form = document.getElementById("storyForm");
    const generateBtn = document.getElementById("generateBtn");

    if (!form || !generateBtn) return;

    form.addEventListener("submit", function () {
        generateBtn.classList.add("loading");
        generateBtn.disabled = true;
    });
}


/**
 * Listen to Story button — placeholder for TTS integration.
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
                showAudioBar(audioBar, audioStatus, "Playing narration (browser demo)...");
                listenBtn.querySelector(".btn-text, .btn-icon")
                    ? (listenBtn.innerHTML = '<span class="btn-icon">⏹</span> Stop Narration')
                    : null;
            };

            utterance.onend = function () {
                isSpeaking = false;
                hideAudioBar(audioBar);
                listenBtn.innerHTML = '<span class="btn-icon">🔊</span> Listen to Story';
            };

            utterance.onerror = function () {
                isSpeaking = false;
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
 * Show the bottom audio status bar.
 */
function showAudioBar(audioBar, audioStatus, message) {
    if (!audioBar) return;
    audioBar.classList.remove("hidden");
    if (audioStatus) {
        audioStatus.textContent = message;
    }
}


/**
 * Hide the bottom audio status bar.
 */
function hideAudioBar(audioBar) {
    if (!audioBar) return;
    audioBar.classList.add("hidden");
}
