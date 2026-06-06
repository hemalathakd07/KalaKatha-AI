/**
 * KalaKatha AI — Frontend JavaScript with Smooth Animations
 * Handles form interactions, loading states, audio playback, and smooth animations.
 */

const SPEECH_LANG_CODES = {
    English: "en-IN",
    Kannada: "kn-IN",
    Hindi: "hi-IN",
    Tamil: "ta-IN",
    Bengali: "bn-IN",
};

const RECOGNITION_LANG_CODES = {
    English: "en-IN",
    Kannada: "kn-IN",
    Hindi: "hi-IN",
    Tamil: "ta-IN",
    Bengali: "bn-IN",
};

const FALLBACK_IMAGE_URL = "/static/images/placeholder.svg";
const MAX_IMAGE_RETRIES = 3;

document.addEventListener("DOMContentLoaded", function () {
    initAnimations();
    initStoryForm();
    initListenButton();
    initVideoButton();
    initRecordButton();
    initStoryImages();
});

/**
 * Initialize smooth animations for story elements as they come into view.
 */
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px",
    };

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
            try {
                await speakWithBrowserFallback(storyContent, language);
            } catch (error) {
                showAudioBar(
                    audioBar,
                    audioStatus,
                    "Narration unavailable for " + language + "."
                );
            }
            resetListenButton();
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
        }
    });

    if (stopAudioBtn) {
        stopAudioBtn.addEventListener("click", stopPlayback);
    }
}

/**
 * Generate a slideshow video from the story illustration and narration.
 */
function initVideoButton() {
    const videoBtn = document.getElementById("videoBtn");
    const videoPlayer = document.getElementById("storyVideoPlayer");
    const videoElement = document.getElementById("storyVideoElement");
    const storyId = getStoryId();

    if (!videoBtn || !storyId) return;

    videoBtn.addEventListener("click", async function () {
        videoBtn.disabled = true;
        videoBtn.textContent = "Generating video...";

        try {
            const response = await fetch("/story/" + encodeURIComponent(storyId) + "/video");
            const data = await response.json();

            if (!response.ok || !data.video_url) {
                throw new Error(data.error || "Could not generate video.");
            }

            if (videoElement) {
                videoElement.src = data.video_url;
                videoElement.load();
            }

            if (videoPlayer) {
                videoPlayer.classList.remove("hidden");
            }

            videoBtn.innerHTML = '<span class="btn-icon">🎬</span> Video Ready';
        } catch (error) {
            videoBtn.innerHTML = '<span class="btn-icon">🎬</span> Generate Video';
            alert(error.message || "Video generation failed.");
        } finally {
            videoBtn.disabled = false;
        }
    });
}

/**
 * Record Grandma's Story — browser Web Speech API transcription.
 */
function initRecordButton() {
    const recordBtn = document.getElementById("recordBtn");
    const storyTitleInput = document.getElementById("story_title");
    const languageSelect = document.getElementById("language");
    const recordStatus = document.getElementById("recordStatus");
    const transcriptPreview = document.getElementById("transcriptPreview");

    if (!recordBtn) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        recordBtn.disabled = true;
        if (recordStatus) {
            recordStatus.textContent = "Speech recognition requires Chrome or Edge.";
        }
        return;
    }

    recordBtn.disabled = false;

    let recognition = null;
    let isRecording = false;
    let finalTranscript = "";

    function setRecordStatus(message) {
        if (recordStatus) {
            recordStatus.textContent = message;
        }
    }

    function updateTranscriptPreview(text) {
        if (transcriptPreview) {
            transcriptPreview.textContent = text || "Your transcript will appear here.";
        }
    }

    function getRecognitionLanguage() {
        const selectedLanguage = languageSelect ? languageSelect.value : "English";
        return RECOGNITION_LANG_CODES[selectedLanguage] || "en-IN";
    }

    async function storeTranscript(transcript) {
        const language = languageSelect ? languageSelect.value : "English";

        try {
            await fetch("/speech-to-text", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    transcript: transcript,
                    language: language,
                }),
            });
        } catch (error) {
            console.warn("Transcript storage skipped:", error);
        }
    }

    recordBtn.addEventListener("click", function () {
        if (isRecording) {
            recognition.stop();
            return;
        }

        finalTranscript = "";
        recognition = new SpeechRecognition();
        recognition.lang = getRecognitionLanguage();
        recognition.interimResults = true;
        recognition.continuous = true;

        recognition.onstart = function () {
            isRecording = true;
            recordBtn.textContent = "Stop Recording";
            recordBtn.classList.add("recording");
            setRecordStatus("Listening... speak clearly near the microphone.");
            updateTranscriptPreview("");
        };

        recognition.onresult = function (event) {
            let interimTranscript = "";

            for (let index = event.resultIndex; index < event.results.length; index += 1) {
                const result = event.results[index];
                if (result.isFinal) {
                    finalTranscript += result[0].transcript + " ";
                } else {
                    interimTranscript += result[0].transcript;
                }
            }

            updateTranscriptPreview((finalTranscript + interimTranscript).trim());
        };

        recognition.onerror = function (event) {
            setRecordStatus("Recording error: " + event.error);
        };

        recognition.onend = async function () {
            isRecording = false;
            recordBtn.textContent = "Record Grandma's Story";
            recordBtn.classList.remove("recording");

            const transcript = finalTranscript.trim();
            if (!transcript) {
                setRecordStatus("No speech detected. Try again.");
                return;
            }

            if (storyTitleInput) {
                storyTitleInput.value = transcript;
            }

            await storeTranscript(transcript);
            setRecordStatus("Transcript saved. You can now generate the story.");
            updateTranscriptPreview(transcript);
        };

        recognition.start();
    });
}

/**
 * Story illustration gallery — loading states, retry support, and fallback image.
 */
function initStoryImages() {
    const galleryItems = document.querySelectorAll(".gallery-item");

    galleryItems.forEach(function (item, itemIndex) {
        const img = item.querySelector(".story-illustration");
        const loader = item.querySelector(".gallery-loader");
        const errorPanel = item.querySelector(".gallery-error");
        const retryBtn = item.querySelector(".gallery-retry-btn");
        const rawUrl = item.getAttribute("data-image-url");

        if (!img || !rawUrl) {
            console.warn("[KalaKatha images] Gallery item missing img or data-image-url", item);
            return;
        }

        let retryCount = 0;
        const primaryUrl = normalizeImageUrl(rawUrl);

        console.info("[KalaKatha images] Rendering illustration", {
            itemIndex: itemIndex,
            rawUrl: rawUrl,
            normalizedUrl: primaryUrl,
            initialSrc: img.src,
        });

        function showLoader() {
            if (loader) loader.classList.remove("hidden");
            if (errorPanel) errorPanel.classList.add("hidden");
            img.classList.add("is-loading");
            img.classList.remove("is-loaded");
            img.style.display = "block";
        }

        function showImage(source) {
            if (loader) loader.classList.add("hidden");
            if (errorPanel) errorPanel.classList.add("hidden");
            img.classList.remove("is-loading");
            img.classList.add("is-loaded");
            console.info("[KalaKatha images] Loaded successfully", {
                itemIndex: itemIndex,
                src: img.src,
                source: source || "unknown",
                width: img.naturalWidth,
                height: img.naturalHeight,
            });
        }

        function showError(message, details) {
            if (loader) loader.classList.add("hidden");
            if (errorPanel) errorPanel.classList.remove("hidden");
            img.classList.remove("is-loading", "is-loaded");
            img.style.display = "none";
            console.error("[KalaKatha images] Load failed", {
                itemIndex: itemIndex,
                message: message,
                rawUrl: rawUrl,
                normalizedUrl: primaryUrl,
                currentSrc: img.src,
                retryCount: retryCount,
                details: details || null,
            });
        }

        function showFallbackImage(reason) {
            console.warn("[KalaKatha images] Using fallback placeholder", {
                itemIndex: itemIndex,
                reason: reason,
                originalUrl: primaryUrl,
            });

            if (loader) loader.classList.add("hidden");
            if (errorPanel) errorPanel.classList.add("hidden");
            img.style.display = "block";
            img.classList.remove("is-loading");
            img.classList.add("is-loaded");
            img.src = FALLBACK_IMAGE_URL;
        }

        function attachHandlers() {
            img.onload = function () {
                if (img.src.includes("placeholder.svg")) {
                    showImage("fallback");
                    return;
                }

                if (img.naturalWidth > 0) {
                    showImage("pollinations");
                } else {
                    showError("Image loaded with zero dimensions.", {
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                    });
                }
            };

            img.onerror = function (event) {
                console.error("[KalaKatha images] onerror event", {
                    itemIndex: itemIndex,
                    src: img.src,
                    retryCount: retryCount,
                    event: event,
                });

                if (retryCount < MAX_IMAGE_RETRIES) {
                    retryCount += 1;
                    loadImage(retryCount, "retry-" + retryCount);
                    return;
                }

                showFallbackImage("max retries reached");
            };
        }

        function loadImage(attempt, reason) {
            const requestUrl = buildImageRequestUrl(primaryUrl, attempt || 1);

            console.info("[KalaKatha images] Requesting image", {
                itemIndex: itemIndex,
                attempt: attempt || 1,
                reason: reason || "initial",
                requestUrl: requestUrl,
            });

            showLoader();
            attachHandlers();
            img.src = requestUrl;
        }

        attachHandlers();

        if (img.complete && img.naturalWidth > 0 && normalizeImageUrl(img.currentSrc || img.src) === primaryUrl) {
            console.info("[KalaKatha images] Reusing already-loaded browser image", {
                itemIndex: itemIndex,
                src: img.src,
            });
            showImage("browser-cache");
            return;
        }

        loadImage(1, "initial");

        if (retryBtn) {
            retryBtn.addEventListener("click", function () {
                retryCount = 0;
                loadImage(1, "manual-retry");
            });
        }
    });
}

/**
 * Normalize Pollinations URLs and keep model=flux for free-tier generation.
 */
function normalizeImageUrl(url) {
    if (!url || !url.includes("pollinations.ai")) {
        return url;
    }

    let normalized = url;

    if (!normalized.includes("model=")) {
        const separator = normalized.includes("?") ? "&" : "?";
        normalized += separator + "model=flux";
    }

    if (!normalized.includes("width=")) {
        normalized += "&width=1024";
    }

    if (!normalized.includes("height=")) {
        normalized += "&height=1024";
    }

    if (!normalized.includes("nologo=")) {
        normalized += "&nologo=true";
    }

    return normalized;
}

/**
 * Build a retry URL with cache-busting and optional seed offset.
 */
function buildImageRequestUrl(baseUrl, attempt) {
    const separator = baseUrl.includes("?") ? "&" : "?";
    return baseUrl + separator + "t=" + Date.now() + "&retry=" + attempt;
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

function getStoryContent() {
    return readStoryJson("storyContentData", "");
}

function getStoryId() {
    return readStoryJson("storyIdData", null);
}

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

function showAudioBar(audioBar, audioStatus, message) {
    if (!audioBar) return;
    audioBar.classList.remove("hidden");
    if (audioStatus) {
        audioStatus.textContent = message;
    }

    audioBar.offsetHeight;
    audioBar.style.animation = "none";
    setTimeout(function () {
        audioBar.style.animation = "slideInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
    }, 10);
}

function hideAudioBar(audioBar) {
    if (!audioBar) return;
    audioBar.style.animation = "slideOutDown 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
    setTimeout(function () {
        audioBar.classList.add("hidden");
        audioBar.style.animation = "";
    }, 400);
}

function smoothTransitionToPage(url) {
    document.body.style.animation = "fadeOut 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
    setTimeout(function () {
        window.location.href = url;
    }, 400);
}
