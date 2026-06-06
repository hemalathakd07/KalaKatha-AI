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