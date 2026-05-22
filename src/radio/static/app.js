document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');

    // Theme initialization
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light' || (!savedTheme && window.matchMedia('(prefers-color-scheme: light)').matches)) {
        document.body.classList.add('light-mode');
        themeIcon.textContent = '🌙';
    } else {
        themeIcon.textContent = '☀️';
    }

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        const isLight = document.body.classList.contains('light-mode');
        themeIcon.textContent = isLight ? '🌙' : '☀️';
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });

    const stationList = document.getElementById('station-list');
    const searchInput = document.getElementById('search-input');
    const nowPlaying = document.getElementById('now-playing');
    const stationNameDisplay = document.getElementById('current-station-name');
    const songTitleDisplay = document.getElementById('current-song-title');
    const stopBtn = document.getElementById('stop-btn');
    const recordBtn = document.getElementById('record-btn');
    const volumeSlider = document.getElementById('volume-slider');
    const equalizer = document.getElementById('equalizer');
    
    const langSelect = document.getElementById('language-select');
    
    // System Modal Elements
    const systemBtn = document.getElementById('system-btn');
    const systemModal = document.getElementById('system-modal');
    const closeModal = document.getElementById('close-modal');
    const systemStats = document.getElementById('system-stats');

    let allStations = [];
    let currentStationId = null;
    let isRecording = false;
    let locales = {};

    async function fetchLocalization() {
        try {
            // Get current language and available languages
            const langRes = await fetch('/api/language');
            if (!langRes.ok) throw new Error('Language API error');
            const langData = await langRes.json();
            
            // Populate select only if available exists
            if (langData.available) {
                // Clear and add placeholder if needed
                langSelect.innerHTML = '';
                
                // Sort by name for better UX
                const sortedLangs = Object.entries(langData.available).sort((a, b) => a[1].localeCompare(b[1]));
                
                for (const [code, name] of sortedLangs) {
                    const opt = document.createElement('option');
                    opt.value = code;
                    // Ensure full name is used, fallback to code if name is missing
                    opt.textContent = name || code.toUpperCase();
                    if (code === langData.current) opt.selected = true;
                    langSelect.appendChild(opt);
                }
            }

            // Get translations
            const locRes = await fetch('/api/locales');
            if (!locRes.ok) throw new Error('Locales API error');
            locales = await locRes.json();
            applyTranslations();
        } catch (error) {
            console.error('Localization error:', error);
            // Fallback for dropdown if it's empty
            if (langSelect.options.length === 0) {
                langSelect.innerHTML = '<option value="en">English</option><option value="tr">Türkçe</option>';
            }
        }
    }

    function applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (locales[key]) el.textContent = locales[key];
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (locales[key]) el.setAttribute('placeholder', locales[key]);
        });
    }

    langSelect.addEventListener('change', async (e) => {
        const newLang = e.target.value;
        try {
            await fetch(`/api/language/${newLang}`, { method: 'POST' });
            await fetchLocalization(); // Re-fetch translations
            if (allStations.length === 0) {
                 stationList.innerHTML = `<div class="loader-container"><p>${locales['web_stations_loading'] || 'Loading...'}</p></div>`;
            }
        } catch (error) {
            console.error('Error changing language:', error);
        }
    });

    // Toggle favorite logic attached to global document
    window.toggleFavorite = async function(e, id) {
        e.stopPropagation(); // Prevent play action
        try {
            const response = await fetch(`/api/favorite/${id}`, { method: 'POST' });
            const data = await response.json();
            
            // Update local state
            const station = allStations.find(s => s.id === id);
            if (station) station.is_favorite = data.is_favorite;
            
            // Re-render
            const term = searchInput.value.toLowerCase();
            const filtered = allStations.filter(s => 
                s.name.toLowerCase().includes(term) || 
                (s.genre && s.genre.toLowerCase().includes(term))
            );
            renderStations(filtered);
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    };

    // İstasyonları API'den çek
    async function fetchStations() {
        try {
            const response = await fetch('/api/stations');
            allStations = await response.json();
            renderStations(allStations);
        } catch (error) {
            console.error('Error fetching stations:', error);
            stationList.innerHTML = `<div class="loader-container"><p style="color: var(--stop-color);">${locales['msg_error'] || 'Error'}</p></div>`;
        }
    }

    // İstasyonları ekrana çiz
    function renderStations(stations) {
        stationList.innerHTML = '';
        if (stations.length === 0) {
            stationList.innerHTML = `<div class="loader-container"><p>${locales['web_no_results'] || 'No results found.'}</p></div>`;
            return;
        }

        stations.forEach(station => {
            const card = document.createElement('div');
            card.className = `station-card ${currentStationId === station.id ? 'active' : ''}`;
            
            // Baş harften ikon oluştur
            const initial = station.name.charAt(0).toUpperCase();

            card.innerHTML = `
                <div class="icon-wrapper">${initial}</div>
                <div class="name">${station.name}</div>
                <div class="genre">${station.genre || '-'}</div>
                <div class="fav-badge" onclick="toggleFavorite(event, '${station.id}')" style="cursor:pointer;" title="Fav">
                    ${station.is_favorite ? '⭐' : '☆'}
                </div>
            `;
            card.onclick = () => playStation(station.id);
            stationList.appendChild(card);
        });
    }

    // Oynat
    async function playStation(id) {
        try {
            // UI'da hemen aktif yap
            currentStationId = id;
            renderStations(allStations);
            stationNameDisplay.textContent = locales['web_connecting'] || 'Connecting...';
            songTitleDisplay.textContent = '';
            nowPlaying.classList.remove('hidden');

            await fetch(`/api/play/${id}`, { method: 'POST' });
            updateStatus();
        } catch (error) {
            console.error('Error playing station:', error);
        }
    }

    // Durdur
    async function stopPlayback() {
        try {
            await fetch('/api/stop', { method: 'POST' });
            currentStationId = null;
            updateStatus();
            renderStations(allStations);
        } catch (error) {
            console.error('Error stopping playback:', error);
        }
    }

    // Durum güncelleme
    async function updateStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();

            if (status.is_playing) {
                nowPlaying.classList.remove('hidden');
                
                if (status.current_station) {
                    stationNameDisplay.textContent = status.current_station.name;
                    if (currentStationId !== status.current_station.id) {
                        currentStationId = status.current_station.id;
                        renderStations(allStations); // Update active state on cards
                    }
                }

                if (status.current_song && status.current_song !== "-") {
                    songTitleDisplay.textContent = status.current_song;
                    equalizer.classList.remove('paused');
                } else {
                    songTitleDisplay.textContent = locales['web_live'] || 'Live Broadcast';
                    equalizer.classList.remove('paused');
                }

                // Sadece kullanıcı kaydırmıyorsa değeri güncelle
                if (document.activeElement !== volumeSlider) {
                    volumeSlider.value = status.volume;
                }

                // Update Recording UI
                if (status.is_recording) {
                    recordBtn.classList.add('recording');
                    isRecording = true;
                } else {
                    recordBtn.classList.remove('recording');
                    isRecording = false;
                }

            } else {
                nowPlaying.classList.add('hidden');
                currentStationId = null;
                equalizer.classList.add('paused');
                recordBtn.classList.remove('recording');
                isRecording = false;
            }
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    // Arama filtreleme
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allStations.filter(s => 
            s.name.toLowerCase().includes(term) || 
            (s.genre && s.genre.toLowerCase().includes(term))
        );
        renderStations(filtered);
    });

    stopBtn.addEventListener('click', stopPlayback);

    recordBtn.addEventListener('click', async () => {
        try {
            const endpoint = isRecording ? '/api/record/stop' : '/api/record/start';
            const response = await fetch(endpoint, { method: 'POST' });
            const result = await response.json();
            alert(result.message);
            updateStatus();
        } catch (error) {
            console.error('Recording error:', error);
        }
    });

    // change eventi: slider bırakıldığında tetiklenir
    volumeSlider.addEventListener('change', async (e) => {
        const vol = e.target.value;
        try {
            await fetch(`/api/volume/${vol}`, { method: 'POST' });
        } catch (error) {
            console.error('Error setting volume:', error);
        }
    });

    // System Modal Logic
    systemBtn.addEventListener('click', async () => {
        try {
            systemStats.innerHTML = '<div class="spinner" style="margin: 0 auto;"></div>';
            systemModal.classList.remove('hidden');
            const response = await fetch('/api/system');
            const data = await response.json();
            systemStats.innerHTML = `
                <p><strong>OS:</strong> ${data.os}</p>
                <p><strong>Python:</strong> ${data.python_version}</p>
                <p><strong>RAM:</strong> ${data.memory_usage_mb} MB</p>
                <p><strong>CPU:</strong> ${data.cpu_percent}%</p>
            `;
        } catch (error) {
            systemStats.innerHTML = `<p style="color:var(--stop-color);">${locales['msg_error'] || 'Error'}</p>`;
        }
    });

    closeModal.addEventListener('click', () => {
        systemModal.classList.add('hidden');
    });

    // İlk yükleme
    fetchLocalization();
    fetchStations();
    
    // Her 2 saniyede bir durumu kontrol et
    setInterval(updateStatus, 2000);
});
