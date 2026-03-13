// Firebase Configuration (Loaded from firebase-config.js)
const firebaseConfig = window.CineMaxConfig ? window.CineMaxConfig.firebase : {
    apiKey: "MISSING_KEY",
    authDomain: "MISSING",
    projectId: "MISSING",
    databaseURL: "MISSING",
    storageBucket: "MISSING",
    messagingSenderId: "000000",
    appId: "MISSING"
};

// TMDB Configuration
const TMDB_API_KEY = window.CineMaxConfig ? window.CineMaxConfig.tmdb.apiKey : "MISSING_TMDB_KEY";

// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const rtdb = firebase.database();

// Security & Stealth Mode: Disable console output and protect source code
(function protectApp() {
    // 1. Suppress all console logs/errors in production to hide technical details
    const noop = () => {};
    console.log = noop;
    console.warn = noop;
    console.error = noop;

    // 2. Anti-DevTools: Block Common keys
    document.addEventListener('keydown', (e) => {
        // Block F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U (View Source)
        if (
            e.keyCode === 123 || 
            (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74 || e.keyCode === 67)) ||
            (e.ctrlKey && e.keyCode === 85)
        ) {
            e.preventDefault();
            return false;
        }
    });

    // 3. Block Right Click
    document.addEventListener('contextmenu', (e) => e.preventDefault());

    // 4. Clear console periodically
    setInterval(() => {
        console.clear();
    }, 5000);
})();

// Enable Firestore Offline Persistence for smoother experience
db.enablePersistence({ synchronizeTabs: true }).catch((err) => {
    if (err.code == 'failed-precondition') {
        console.warn('Persistencia fallida: Múltiples pestañas abiertas');
    } else if (err.code == 'unimplemented') {
        console.warn('Persistencia no soportada por el navegador');
    }
});

// DOM Elements
const trendingMovies = document.getElementById('trendingMovies');
const estrenosMovies = document.getElementById('estrenosMovies');
const seriesRow = document.getElementById('seriesRow');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const movieModal = document.getElementById('movieModal');
const closeMovieModal = document.getElementById('closeMovieModal');
const videoModal = document.getElementById('videoModal');
const closeVideoModal = document.getElementById('closeVideoModal');
const videoPlayer = document.getElementById('videoPlayer');
const downloadInfoModal = document.getElementById('downloadInfoModal');
const closeDownloadInfoModal = document.getElementById('closeDownloadInfoModal');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const navLinks = document.getElementById('navLinks');
const heroSection = document.getElementById('heroSection');
const heroTitle = document.getElementById('heroTitle');
const heroDescription = document.getElementById('heroDescription');
const heroWatchBtn = document.getElementById('heroWatchBtn');
const heroDetailsBtn = document.getElementById('heroDetailsBtn');
const categoriasSections = document.getElementById('categorias-sections');
const footerCategories = document.getElementById('footerCategories');
const allSeriesGrid = document.getElementById('allSeriesGrid');
const mainSeriesContent = document.getElementById('mainSeriesContent');
const recentMovies = document.getElementById('recentMovies');

// State
let allMovies = [];
let moviesList = [];
let seriesList = [];
let seriesListRtdb = [];
let seriesListFirestore = [];
let allGenres = new Set();
let allYears = new Set();
let featuredMovie = null;
let currentVideoUrl = '';
let currentMovieTitle = '';
let updateTimeout = null;
let listenersInitialized = false;

// Categorías principales (puedes personalizar esto)
const mainCategories = [
    'Acción', 'Terror', 'Animación', 'Crimen', 'Suspenso',
    'Comedia', 'Aventura', 'Drama', 'Ciencia Ficción',
    'Romance', 'Documental', 'Fantasía', 'Musical', 'Misterio'
];

// Initialize app
async function initApp() {
    try {
        const hasAccess = checkAccess(); 
        setupEventListeners();
        setupBackToTop();
        initAdBlocker();
        
        if (hasAccess) {
            updateUIForAccessType();
            loadHeroFromCache();
            setupLiveIndicator();
            await loadMoviesFromFirebase();
            setupTVNavigation();
            listenersInitialized = true; // Activar notificaciones después de carga inicial
        }
    } catch (error) {
        console.error('Error inicializando la app:', error);
        showMessage('Error al cargar la plataforma', 'error');
    }
}

// Funciones de Acceso (Login Pro)
window.checkAccess = function () {
    const accessType = localStorage.getItem('userAccessType');
    const modal = document.getElementById('accessModal');
    
    if (!accessType) {
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('active');
        }
        // No cargar contenido hasta que se elija acceso
        return false;
    } else {
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('active');
        }
        return true;
    }
};

window.updateUIForAccessType = function () {
    const accessType = localStorage.getItem('userAccessType');
    const vipBtn = document.getElementById('vipUpgradeBtn');

    // Seleccionar elementos de series
    const navSeriesLinks = document.querySelectorAll('a[href="series.html"]');
    const seriesSection = document.getElementById('series');
    const mainSeriesContent = document.getElementById('mainSeriesContent');

    if (accessType === 'free') {
        if (vipBtn) {
            vipBtn.style.display = 'flex';
            vipBtn.style.alignItems = 'center';
            vipBtn.style.gap = '5px';
        }

        // Mostrar elementos de series normalmente
        navSeriesLinks.forEach(link => {
            link.style.display = 'inline-block';
            link.onclick = null;
        });

        if (seriesSection) {
            seriesSection.style.display = 'block';
        }
    } else {
        if (vipBtn) {
            vipBtn.style.display = 'none';
        }

        // Mostrar elementos de series para VIP
        navSeriesLinks.forEach(link => {
            if (link.className !== 'active' && !link.style.color) {
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'inline-block';
            }
        });

        if (seriesSection) {
            seriesSection.style.display = 'block';
        }
    }
};

window.selectFreeAccess = function () {
    // REGLA: No guardamos NADA del usuario en modo free
    localStorage.setItem('userAccessType', 'free');
    localStorage.removeItem('userName');
    localStorage.removeItem('userId');
    
    const modal = document.getElementById('accessModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
    
    showMessage('Bienvenido al modo Gratuito', 'success');
    updateUIForAccessType();
    
    // Cargar contenido ahora que tiene acceso
    loadMoviesFromFirebase().then(() => {
        setupTVNavigation();
    });
};

window.checkVipCode = async function () {
    const userInput = document.getElementById('vipUserInput');
    const errorMsg = document.getElementById('vipError');
    const btn = document.getElementById('vipSubmitBtn');
    const user = userInput.value.trim();

    if (!user) {
        errorMsg.style.display = 'block';
        errorMsg.textContent = 'Ingresa tu nombre o código';
        return;
    }

    // Estado de carga
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;
    errorMsg.style.display = 'none';

    try {
        // Consultar SOLO la colección 'codigos' como solicitó el usuario
        // Usamos .get() que es una petición única (No Listen / Real-time)
        const codeSnapshot = await db.collection('codigos')
            .where('codigo', '==', user)
            .get();

        const adminNames = ['admin', 'anaya', 'pelix', '23BY206'];

        if (!codeSnapshot.empty || adminNames.includes(user.toLowerCase())) {
            let userName = user;
            let userId = 'vip_' + Date.now();

            if (!codeSnapshot.empty) {
                const doc = codeSnapshot.docs[0].data();
                // Verificar si el campo 'activo' existe y es true
                if (doc.activo === false) {
                    errorMsg.style.display = 'block';
                    errorMsg.textContent = 'Este código VIP está desactivado.';
                    return;
                }
                userName = doc.nombre || user;
                userId = doc.codigo || user; // Usar el código mismo como ID para vincular historial

                // Guardar fechas de inicio y termina para el perfil
                localStorage.setItem('vipInicio', doc.inicio || 'No disponible');
                localStorage.setItem('vipTermina', doc.termina || 'No disponible');
            }
            
            localStorage.setItem('userAccessType', 'vip');
            localStorage.setItem('userName', userName);
            localStorage.setItem('userId', userId);
            
            document.getElementById('accessModal').classList.remove('active');
            document.getElementById('accessModal').style.display = 'none';
            
            showMessage(`¡Acceso VIP Concedido, ${userName}!`, 'success');
            updateUIForAccessType();
            
            // Recargar datos para mostrar contenido VIP
            loadMoviesFromFirebase().then(() => {
                setupTVNavigation();
            });
        } else {
            errorMsg.style.display = 'block';
            errorMsg.textContent = 'Código VIP no encontrado o inválido.';
        }
    } catch (error) {
        console.error("Error verificando VIP:", error);
        errorMsg.style.display = 'block';
        errorMsg.textContent = 'Error de conexión con Firebase. Revisa tu internet.';
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
};

// Smart TV Navigation Helper
function setupTVNavigation() {
    // 1. Focus Follower / Auto-Scroll Pro
    document.addEventListener('focusin', (e) => {
        const focused = e.target;
        
        // Centrar elemento enfocado suavemente
        setTimeout(() => {
            focused.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
        }, 50);

        // Si el foco se pierde (ej. al cerrar un modal), enviarlo al primer card
        if (!focused || focused === document.body) {
            const firstCard = document.querySelector('.movie-card, .btn, .nav-links a');
            if (firstCard) firstCard.focus();
        }
    });

    // 2. Teclas de dirección y accesos directos
    document.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        
        // Navegación Inteligente (Prevención de pérdida de foco)
        if (active === document.body) {
            const restartFocus = document.querySelector('.movie-card, .nav-links a');
            if (restartFocus) restartFocus.focus();
        }

        // Control de Reproducción (si existe el reproductor)
        const player = document.getElementById('videoPlayer');
        if (player && document.getElementById('videoModal').style.display === 'flex') {
            if (e.key === ' ' || e.keyCode === 32) { // Espacio para pausa
                e.preventDefault();
                // Enviar mensaje al iframe si es posible, o simplemente enfocarlo
                player.focus();
            }
        }

        // Botón "Atrás" universal para Smart TV
        const backKeys = [8, 27, 461, 10009];
        if (backKeys.includes(e.keyCode)) {
            // Si hay un modal abierto, cerrarlo en lugar de ir atrás en el historial
            const openModal = document.querySelector('.dns-modal.active, #videoModal[style*="display: flex"], #movieModal[style*="display: flex"]');
            if (openModal) {
                e.preventDefault();
                if (openModal.id === 'dnsModal') closeDnsModal();
                else if (openModal.id === 'videoModal') document.getElementById('closeVideoModal').click();
                else openModal.style.display = 'none';
                return;
            }

            // Si está en ver.html, ir al inicio
            if (window.location.pathname.includes('ver.html')) {
                window.location.href = 'index.html';
            }
        }
    });
}


// Favorites Logic
function getFavorites() {
    try {
        const favs = localStorage.getItem('cineMaxFavorites');
        return favs ? JSON.parse(favs) : [];
    } catch (e) {
        console.error('Error parsing favorites', e);
        return [];
    }
}

function toggleFavorite(movie) {
    let favs = getFavorites();
    const index = favs.findIndex(f => f.id === movie.id);
    
    if (index > -1) {
        favs.splice(index, 1);
        showMessage('Eliminado de favoritos', 'info');
    } else {
        favs.push({
            id: movie.id,
            titulo: movie.titulo,
            poster: movie.poster,
            rating: movie.rating,
            año: movie.año,
            categorias: movie.categorias,
            tipo: movie.tipo,
            tmdb_id: movie.tmdb_id,
            fecha_agregado: new Date().toISOString()
        });
        showMessage('Añadido a favoritos', 'success');
    }
    
    localStorage.setItem('cineMaxFavorites', JSON.stringify(favs));
    
    // Si estamos en perfil.html, refrescar la lista
    if (window.location.pathname.includes('perfil.html')) {
        displayUserFavorites();
    }
}

function isFavorite(movieId) {
    const favs = getFavorites();
    return favs.some(f => f.id === movieId);
}

// Back to Top Logic
function setupBackToTop() {
    const btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.id = 'backToTop';
    btn.tabIndex = 0;
    btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    btn.setAttribute('aria-label', 'Volver arriba');
    document.body.appendChild(btn);

    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            btn.classList.add('show');
        } else {
            btn.classList.remove('show');
        }
    });

    btn.onclick = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    btn.onkeydown = (e) => {
        if (e.key === 'Enter') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };
}

// Ad-Blocker & DNS Recommendation
function initAdBlocker() {
    // 1. Script level ad-blocking (Interceptar popups)
    const originalOpen = window.open;
    window.open = function(url, name, specs) {
        if (!url || url.includes('about:blank')) return null;
        const allowed = [window.location.hostname, 't.me', 'telegram.me', 'google.com', 'firebase'];
        const isAllowed = allowed.some(domain => url.includes(domain));
        
        if (isAllowed) {
            return originalOpen(url, name, specs);
        }
        console.warn('Bloqueado:', url);
        return null;
    };

    // 2. Internal Ad-Hider (Backup)
    setInterval(() => {
        const adPatterns = ['/ads/', 'popunder', 'overlay', 'banner-ad'];
        document.querySelectorAll('iframe, div, ins').forEach(el => {
            const content = (el.id + el.className + (el.src || '')).toLowerCase();
            if (adPatterns.some(p => content.includes(p))) {
                el.style.display = 'none';
                el.style.pointerEvents = 'none';
            }
        });
    }, 2000);

    // 3. DNS Modal Logic
    const dnsModal = document.getElementById('dnsModal');
    if (dnsModal) {
        window.showDnsModal = () => dnsModal.classList.add('active');
        window.closeDnsModal = () => dnsModal.classList.remove('active');
        
        dnsModal.addEventListener('click', (e) => {
            if (e.target === dnsModal) closeDnsModal();
        });
    }
}
// Live Indicator setup
function setupLiveIndicator() {
    const logo = document.querySelector('.logo');
    if (logo && !document.querySelector('.live-indicator')) {
        const indicator = document.createElement('div');
        indicator.className = 'live-indicator';
        indicator.style.cssText = 'margin-left: 15px; display: inline-flex; align-items: center;';
        indicator.innerHTML = '<span class="live-dot"></span> <span style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-dim);">Live Sync</span>';
        logo.after(indicator);
    }
}



// Load movies from Firebase with Real-time synchronization
function loadMoviesFromFirebase() {
    return new Promise((resolve, reject) => {
        console.log('Iniciando sincronización en tiempo real...');

        // 1. Cargar desde caché inmediatamente para respuesta instantánea
        const cacheData = localStorage.getItem('cineMaxDataCache');
        if (cacheData) {
            try {
                const parsed = JSON.parse(cacheData);
                moviesList = parsed.moviesList || [];
                seriesListRtdb = parsed.seriesListRtdb || [];
                seriesListFirestore = parsed.seriesListFirestore || [];
                console.log('Caché inicial cargada');
                mergeAndDisplayContent();
            } catch (e) {
                console.warn('Error leyendo caché inicial:', e);
            }
        }

        let moviesLoaded = false;
        let seriesRtdbLoaded = false;
        let seriesFirestoreLoaded = false;

        const checkInitialLoad = () => {
            if (moviesLoaded && seriesRtdbLoaded && seriesFirestoreLoaded) {
                console.log('Sincronización inicial completada');
                resolve();
            }
        };

        // Función optimizada para actualizar la UI con debounce
        const debouncedUpdate = () => {
            if (updateTimeout) clearTimeout(updateTimeout);
            updateTimeout = setTimeout(() => {
                mergeAndDisplayContent();
                
                // Guardar en caché después de cada actualización real para el siguiente refresco manual
                try {
                    const dataToCache = {
                        moviesList,
                        seriesListRtdb,
                        seriesListFirestore
                    };
                    localStorage.setItem('cineMaxDataCache', JSON.stringify(dataToCache));
                    localStorage.setItem('cineMaxDataCacheTime', new Date().getTime().toString());
                } catch (e) {}
            }, 300); // 300ms de espera para agrupar cambios
        };

        // A. Listener para Películas (Firestore)
        db.collection('peliculas').onSnapshot((snapshot) => {
            try {
                // Detectar si hay películas nuevas desde la última carga
                if (listenersInitialized) {
                    snapshot.docChanges().forEach(change => {
                        if (change.type === "added") {
                            const newData = change.document.data();
                            showMessage(`📽️ ¡Nuevo: ${newData.titulo}!`, 'success');
                        }
                    });
                }

                moviesList = [];
                allGenres.clear();

                snapshot.forEach(doc => {
                    const movieData = doc.data();
                    const movie = processMovieDoc(doc.id, movieData);
                    moviesList.push(movie);
                });

                if (!moviesLoaded) {
                    moviesLoaded = true;
                    checkInitialLoad();
                } else {
                    debouncedUpdate();
                }
            } catch (error) {
                console.error('Error en tiempo real (Peliculas):', error);
                if (!moviesLoaded) { moviesLoaded = true; checkInitialLoad(); }
            }
        }, (error) => {
            console.error('Error escuchando películas:', error);
            if (!moviesLoaded) { moviesLoaded = true; checkInitialLoad(); }
        });

        // B. Listener para Series (RTDB)
        rtdb.ref('series').on('value', (snapshot) => {
            try {
                const data = snapshot.val();
                
                // Si ya estamos inicializados y hay datos, comparamos para notificar
                if (listenersInitialized && data) {
                    const currentCount = seriesListRtdb.length;
                    const newEntries = Object.keys(data);
                    if (newEntries.length > currentCount && currentCount > 0) {
                        const lastKey = newEntries[newEntries.length - 1];
                        showMessage(`📺 ¡Nueva Serie: ${data[lastKey].titulo}!`, 'success');
                    }
                }

                seriesListRtdb = [];
                if (data) {
                    Object.keys(data).forEach(key => {
                        const serie = processSerieData(key, data[key]);
                        seriesListRtdb.push(serie);
                    });
                }

                if (!seriesRtdbLoaded) {
                    seriesRtdbLoaded = true;
                    checkInitialLoad();
                } else {
                    debouncedUpdate();
                }
            } catch (error) {
                console.error('Error en tiempo real (Series RTDB):', error);
                if (!seriesRtdbLoaded) { seriesRtdbLoaded = true; checkInitialLoad(); }
            }
        }, (error) => {
            console.error('Error escuchando series RTDB:', error);
            if (!seriesRtdbLoaded) { seriesRtdbLoaded = true; checkInitialLoad(); }
        });

        // C. Listener para Series (Firestore)
        db.collection('series').onSnapshot((snapshot) => {
            try {
                if (listenersInitialized) {
                    snapshot.docChanges().forEach(change => {
                        if (change.type === "added") {
                            const newData = change.document.data();
                            showMessage(`📺 ¡Nueva Serie: ${newData.titulo}!`, 'success');
                        }
                    });
                }

                seriesListFirestore = [];
                snapshot.forEach(doc => {
                    const serieData = doc.data();
                    const serie = processSerieFirestoreDoc(doc.id, serieData);
                    seriesListFirestore.push(serie);
                });

                if (!seriesFirestoreLoaded) {
                    seriesFirestoreLoaded = true;
                    checkInitialLoad();
                } else {
                    debouncedUpdate();
                }
            } catch (error) {
                console.error('Error en tiempo real (Series Firestore):', error);
                if (!seriesFirestoreLoaded) { seriesFirestoreLoaded = true; checkInitialLoad(); }
            }
        }, (error) => {
            console.error('Error escuchando series Firestore:', error);
            if (!seriesFirestoreLoaded) { seriesFirestoreLoaded = true; checkInitialLoad(); }
        });
    });
}

// Helpers para procesar datos (Extraídos para limpieza)
function processMovieDoc(id, data) {
    let categorias = [];
    if (data.categorias) {
        categorias = Array.isArray(data.categorias) ? data.categorias : data.categorias.split(',').map(c => c.trim());
    } else if (data.categoria) {
        categorias = [data.categoria];
    }
    
    categorias.forEach(cat => { if (cat) allGenres.add(cat.trim().toLowerCase()); });

    const movie = {
        id: id,
        titulo: data.titulo || 'Sin título',
        año: data.año || '2023',
        categorias: categorias.filter(c => c),
        destacado: data.destacado || false,
        director: data.director || 'Desconocido',
        duracion: parseInt(data.duracion) || 120,
        español: data.español || '',
        estreno: data.estreno || false,
        fondo: data.fondo || data.poster || '',
        poster: data.poster || 'https://via.placeholder.com/300x450?text=No+Poster',
        rating: parseFloat(data.rating) || 0,
        sinopsis: data.sinopsis || data.sisposesis || 'Sin descripción disponible.',
        latino: data.latino || '',
        subtitulado: data.subtitulado || '',
        tendencias: data.tendencias || false,
        url: data.url || '',
        tipo: data.tipo || 'pelicula',
        tmdb_id: data.tmdb_id,
        fecha_agregado: data.fecha_agregado || new Date().toISOString()
    };

    // Marcar como "NUEVO" si fue agregado en las últimas 48 horas
    const addedDate = new Date(movie.fecha_agregado);
    const timeDiff = (new Date()) - addedDate;
    movie.esNueva = timeDiff < (48 * 60 * 60 * 1000); 

    return movie;
}

function processSerieData(id, data) {
    let categorias = [];
    if (data.categoria) {
        categorias = Array.isArray(data.categoria) ? data.categoria : data.categoria.split(',').map(c => c.trim());
    }

    let numTemporadas = parseInt(data.temporada) || 0;
    let numEpisodios = parseInt(data.episodios) || 0;

    if (data.temporadas && typeof data.temporadas === 'object') {
        const temps = Object.keys(data.temporadas);
        numTemporadas = Math.max(numTemporadas, temps.length);
        let totalEps = 0;
        temps.forEach(t => {
            if (data.temporadas[t].episodios) totalEps += Object.keys(data.temporadas[t].episodios).length;
        });
        numEpisodios = Math.max(numEpisodios, totalEps);
    }

    const serie = {
        id: id,
        titulo: data.titulo || 'Sin título',
        año: data.año || new Date().getFullYear().toString(),
        categorias: categorias.filter(c => c),
        destacado: data.destacado || false,
        duracion: numEpisodios,
        temporadas: numTemporadas || 1,
        episodios: numEpisodios || 1,
        español: data.español || '',
        estreno: data.estreno || false,
        fondo: data.fondo || data.portada || '',
        poster: data.portada || 'https://via.placeholder.com/300x450?text=No+Poster',
        rating: parseFloat(data.rating) || 0,
        sinopsis: data.sinopsis || 'Sin descripción disponible.',
        latino: data.latino || '',
        subtitulado: data.subtitulado || '',
        tendencias: data.tendencias || false,
        url: data.url || '',
        tipo: 'serie',
        tmdb_id: data.tmdb_id,
        fecha_agregado: data.fecha_agregado || new Date().toISOString()
    };

    const addedDate = new Date(serie.fecha_agregado);
    const timeDiff = (new Date()) - addedDate;
    serie.esNueva = timeDiff < (48 * 60 * 60 * 1000);

    return serie;
}

function processSerieFirestoreDoc(id, data) {
    let categorias = [];
    if (data.categoria) {
        categorias = Array.isArray(data.categoria) ? data.categoria : data.categoria.split(',').map(c => c.trim());
    }

    const serie = {
        id: id,
        titulo: data.titulo || 'Sin título',
        año: data.año || new Date().getFullYear().toString(),
        categorias: categorias.filter(c => c),
        destacado: data.destacado || false,
        duracion: parseInt(data.episodios) || 0,
        temporadas: parseInt(data.temporada) || 1,
        episodios: parseInt(data.episodios) || 1,
        español: data.español || '',
        estreno: data.estreno || false,
        fondo: data.fondo || data.portada || '',
        poster: data.portada || 'https://via.placeholder.com/300x450?text=No+Poster',
        rating: parseFloat(data.rating) || 0,
        sinopsis: data.sinopsis || 'Sin descripción disponible.',
        latino: data.latino || '',
        subtitulado: data.subtitulado || '',
        tendencias: data.tendencias || false,
        url: data.url || '',
        tipo: 'serie',
        tmdb_id: data.tmdb_id,
        fecha_agregado: data.fecha_agregado || new Date().toISOString()
    };

    const addedDate = new Date(serie.fecha_agregado);
    const timeDiff = (new Date()) - addedDate;
    serie.esNueva = timeDiff < (48 * 60 * 60 * 1000);

    return serie;
}

function mergeAndDisplayContent() {
    const accessType = localStorage.getItem('userAccessType');

    // Combinar listas de series (RTDB + Firestore)
    const seriesMap = new Map();
    [...seriesListRtdb, ...seriesListFirestore].forEach(s => seriesMap.set(s.id, s));
    seriesList = Array.from(seriesMap.values());

    allMovies = [...moviesList, ...seriesList];

    allGenres.clear();
    allYears.clear();

    allMovies.forEach(movie => {
        movie.categorias.forEach(cat => {
            if (cat && cat.trim() !== '') {
                allGenres.add(cat.trim());
            }
        });
        allYears.add(movie.año);
    });

    console.log(`Contenido total cargado: ${allMovies.length}`);

    // Ordenar por fecha de agregado (más recientes primero)
    allMovies.sort((a, b) => new Date(b.fecha_agregado) - new Date(a.fecha_agregado));

    // Mostrar contenido
    displayRecentSubido();
    displayTrendingMovies();
    displayEstrenos();
    displaySeries();
    setupFeaturedMovie();
    displayCategorySections();
    displayFooterCategories();
    displayAllSeriesPage();
}

function displayRecentSubido() {
    if (!recentMovies) return;
    recentMovies.innerHTML = '';

    // No necesitamos filtrar más porque allMovies ya viene ordenado por fecha de agregado en mergeAndDisplayContent
    const recentAdditions = allMovies.slice(0, 10);

    if (recentAdditions.length === 0) {
        document.getElementById('recentSection').style.display = 'none';
        return;
    }

    const fragment = document.createDocumentFragment();
    recentAdditions.forEach(movie => {
        fragment.appendChild(createMovieCard(movie));
    });
    recentMovies.appendChild(fragment);
}

// Display trending movies
function displayTrendingMovies() {
    if (!trendingMovies) return;
    trendingMovies.innerHTML = '';

    // Obtener películas en tendencia
    const trending = allMovies.filter(m => m.tendencias || m.destacado);

    if (trending.length === 0) {
        trendingMovies.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-film"></i>
                <h3>No hay tendencias disponibles</h3>
            </div>
        `;
        return;
    }

    // Mostrar máximo 10 películas en tendencia
    const fragment = document.createDocumentFragment();
    trending.slice(0, 10).forEach(movie => {
        fragment.appendChild(createMovieCard(movie));
    });
    trendingMovies.appendChild(fragment);
}

// Display estrenos
function displayEstrenos() {
    if (!estrenosMovies) return;
    estrenosMovies.innerHTML = '';

    // Obtener estrenos (películas con flag estreno o del año actual)
    const currentYear = new Date().getFullYear().toString();
    const estrenos = allMovies.filter(m => m.estreno || m.año === currentYear);

    if (estrenos.length === 0) {
        estrenosMovies.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-film"></i>
                <h3>No hay estrenos disponibles</h3>
            </div>
        `;
        return;
    }

    // Mostrar máximo 10 estrenos
    const fragment = document.createDocumentFragment();
    estrenos.slice(0, 10).forEach(movie => {
        fragment.appendChild(createMovieCard(movie));
    });
    estrenosMovies.appendChild(fragment);
}

// Display series
function displaySeries() {
    if (!seriesRow) return;
    seriesRow.innerHTML = '';

    // Obtener solo series
    const series = allMovies.filter(m => m.tipo === 'serie');

    if (series.length === 0) {
        seriesRow.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-tv"></i>
                <h3>No hay series disponibles</h3>
            </div>
        `;
        return;
    }

    // Mostrar series
    const fragment = document.createDocumentFragment();
    series.slice(0, 20).forEach(serie => {
        fragment.appendChild(createMovieCard(serie));
    });
    seriesRow.appendChild(fragment);
}

// Display all series page
function displayAllSeriesPage() {
    if (!allSeriesGrid) return;

    allSeriesGrid.innerHTML = '';

    const series = allMovies.filter(m => m.tipo === 'serie');

    if (series.length === 0) {
        allSeriesGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-tv"></i>
                <h3>No hay series disponibles</h3>
            </div>
        `;
        return;
    }

    const fragment = document.createDocumentFragment();
    series.forEach(serie => {
        fragment.appendChild(createMovieCard(serie, true));
    });
    allSeriesGrid.appendChild(fragment);
}

// Display category sections
function displayCategorySections() {
    if (!categoriasSections) return;
    categoriasSections.innerHTML = '';

    let index = 0;

    function processNextBatch() {
        const start = performance.now();
        // Procesar durante máximo 12ms por frame para mantener 60fps
        while (index < mainCategories.length && performance.now() - start < 12) {
            const category = mainCategories[index++];

            // Filtrar películas de esta categoría
            const categoryMovies = allMovies.filter(movie =>
                movie.categorias.some(cat => {
                    const catNorm = cat.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    const categoryNorm = category.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

                    // Caso especial para Ciencia Ficción
                    if (categoryNorm.includes('ciencia ficcion') && (catNorm === 'sci-fi' || catNorm === 'scifi')) {
                        return true;
                    }

                    return catNorm.includes(categoryNorm) || categoryNorm.includes(catNorm);
                })
            );

            if (categoryMovies.length > 0) {
                const section = document.createElement('section');
                section.className = 'category-section';
                section.id = category.toLowerCase().replace(/\s+/g, '-');

                section.innerHTML = `
                    <div class="section-header">
                        <h2 class="section-title">${category}</h2>
                        <a href="#${category.toLowerCase().replace(/\s+/g, '-')}" class="view-all">Ver todo</a>
                    </div>
                    <div class="movies-row-container">
                        <div class="movies-row" id="movies-${category.toLowerCase().replace(/\s+/g, '-')}"></div>
                        <button class="scroll-btn scroll-left" onclick="scrollRow('movies-${category.toLowerCase().replace(/\s+/g, '-')}', -300)" aria-label="Anterior">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                        <button class="scroll-btn scroll-right" onclick="scrollRow('movies-${category.toLowerCase().replace(/\s+/g, '-')}', 300)" aria-label="Siguiente">
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                `;

                categoriasSections.appendChild(section);

                // Mostrar películas de esta categoría
                const row = document.getElementById(`movies-${category.toLowerCase().replace(/\s+/g, '-')}`);
                const fragment = document.createDocumentFragment();
                categoryMovies.slice(0, 10).forEach(movie => {
                    fragment.appendChild(createMovieCard(movie));
                });
                row.appendChild(fragment);
            }
        }

        if (index < mainCategories.length) {
            requestAnimationFrame(processNextBatch);
        }
    }

    requestAnimationFrame(processNextBatch);
}

// Create movie card
function createMovieCard(movie, isGrid = false) {
    if (!movie || !movie.id) {
        console.warn('Intento de crear una tarjeta con datos de película no válidos:', movie);
        return document.createDocumentFragment(); // Devuelve un fragmento vacío si no hay datos
    }

    const movieCard = document.createElement('div');
    movieCard.className = 'movie-card';

    // Badge de novedad en tiempo real
    if (movie.esNueva) {
        const badge = document.createElement('div');
        badge.className = 'badge badge-new';
        badge.innerHTML = '<i class="fas fa-bolt"></i> Nuevo';
        movieCard.appendChild(badge);
    }

    const posterUrl = movie.poster || 'https://via.placeholder.com/300x450?text=No+Poster';
    const rating = (typeof movie.rating === 'number') ? movie.rating.toFixed(1) : 'N/A';
    const year = movie.año || 'N/A';
    const categories = Array.isArray(movie.categorias) ? movie.categorias : [];

    movieCard.innerHTML = `
        <img src="${posterUrl}" alt="${movie.titulo}" class="movie-poster" loading="lazy" width="200" height="300">
        <div class="movie-info">
            <h3 class="movie-title">${movie.titulo || 'Sin Título'}</h3>
            <div class="movie-meta">
                <span class="rating"><i class="fas fa-star"></i> ${rating}</span>
                <span>${year}</span>
            </div>
            <div class="movie-genres">
                ${categories.slice(0, 2).map(cat => `<span class="genre">${cat}</span>`).join('')}
            </div>
        </div>
    `;

    const img = movieCard.querySelector('img');
    if (img) {
        img.onerror = () => {
            img.src = 'https://via.placeholder.com/300x450?text=Error+Img';
            img.classList.add('loaded');
        };
        img.onload = () => {
            img.classList.add('loaded');
        };
        if (img.complete) {
            img.classList.add('loaded');
        }
    }

    // Eventos
    movieCard.tabIndex = 0; // Hacer enfocable para control remoto / teclado
    
    movieCard.addEventListener('click', (e) => {
        if (!e.target.closest('button')) {
            window.location.href = `ver.html?id=${movie.id}`;
        }
    });

    movieCard.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            window.location.href = `ver.html?id=${movie.id}`;
        }
    });

    // Favorite Button
    const favBtn = document.createElement('button');
    favBtn.className = isFavorite(movie.id) ? 'fav-btn active' : 'fav-btn';
    favBtn.innerHTML = isFavorite(movie.id) ? '<i class="fas fa-heart"></i>' : '<i class="far fa-heart"></i>';
    favBtn.title = 'Añadir a favoritos';
    favBtn.onclick = (e) => {
        e.stopPropagation();
        toggleFavorite(movie);
        
        // Actualizar icono
        const isFav = isFavorite(movie.id);
        favBtn.className = isFav ? 'fav-btn active' : 'fav-btn';
        favBtn.innerHTML = isFav ? '<i class="fas fa-heart"></i>' : '<i class="far fa-heart"></i>';
    };
    movieCard.appendChild(favBtn);

    const playBtn = document.createElement('button');
    playBtn.className = 'btn btn-small';
    playBtn.innerHTML = '<i class="fas fa-play"></i> Ver';
    playBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        opacity: 0;
        transition: opacity 0.3s;
    `;
    playBtn.onclick = (e) => {
        e.stopPropagation();
        window.location.href = `ver.html?id=${movie.id}`;
    };

    movieCard.appendChild(playBtn);

    movieCard.addEventListener('mouseenter', () => {
        playBtn.style.opacity = '1';
    });

    movieCard.addEventListener('mouseleave', () => {
        playBtn.style.opacity = '0';
    });

    // Actualizar datos (Rating y Año) desde TMDB si existe ID
    if (movie.tmdb_id) {
        updateCardFromTMDB(movieCard, movie.tmdb_id, movie.tipo);
    }

    return movieCard;
}

async function updateCardFromTMDB(card, tmdbId, type) {
    try {
        const mediaType = type === 'serie' ? 'tv' : 'movie';
        const response = await fetch(`https://api.themoviedb.org/3/${mediaType}/${tmdbId}?api_key=${TMDB_API_KEY}&language=es-ES`);

        if (response.ok) {
            const data = await response.json();
            const rating = data.vote_average ? data.vote_average.toFixed(1) : null;
            const date = data.release_date || data.first_air_date;
            const year = date ? date.split('-')[0] : null;

            if (rating) {
                const ratingEl = card.querySelector('.rating');
                if (ratingEl) ratingEl.innerHTML = `<i class="fas fa-star"></i> ${rating}`;
            }

            if (year) {
                const metaDiv = card.querySelector('.movie-meta');
                if (metaDiv) {
                    const spans = metaDiv.querySelectorAll('span');
                    // El año suele ser el segundo elemento span (después del rating)
                    if (spans.length > 1) {
                        spans[1].textContent = year;
                    }
                }
            }
        }
    } catch (error) {
        // Fallo silencioso para no interrumpir la UI
    }
}

// Display footer categories
function displayFooterCategories() {
    if (!footerCategories) return;
    footerCategories.innerHTML = '';

    Array.from(allGenres).sort().forEach(genre => {
        const li = document.createElement('li');
        li.innerHTML = `<a href="categorias.html?cat=${encodeURIComponent(genre)}">${genre}</a>`;
        footerCategories.appendChild(li);
    });
}

// Cache Hero para mejorar LCP
function loadHeroFromCache() {
    const cachedHero = localStorage.getItem('heroCache');
    if (cachedHero && heroSection) {
        const movie = JSON.parse(cachedHero);
        updateHeroUI(movie);
    }
}

function updateHeroUI(movie) {
    if (!heroSection || !movie) return;
    const bgImage = movie.fondo || movie.poster;

    // Usar requestAnimationFrame para evitar bloqueos
    requestAnimationFrame(() => {
        heroSection.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('${bgImage}')`;
        heroTitle.textContent = movie.titulo;
        heroDescription.textContent = movie.sinopsis.substring(0, 150) + '...';
        
        heroWatchBtn.onclick = () => window.location.href = `ver.html?id=${movie.id}`;
        heroWatchBtn.tabIndex = 0;
        
        heroDetailsBtn.onclick = () => window.location.href = `ver.html?id=${movie.id}`;
        heroDetailsBtn.tabIndex = 0;
    });

}

// Setup featured movie
function setupFeaturedMovie() {
    if (!heroSection) return;
    if (allMovies.length === 0) return;

    // Obtener películas para el slider (Tendencias y Destacados)
    const sliderMovies = allMovies.filter(m => m.tendencias || m.destacado).slice(0, 10);

    if (sliderMovies.length === 0) {
        sliderMovies.push(allMovies[0]);
    }

    // Guardar primera película en caché para la próxima visita
    localStorage.setItem('heroCache', JSON.stringify(sliderMovies[0]));

    let currentIndex = 0;

    // Configurar transición suave para el fondo
    heroSection.style.transition = "background-image 1s ease-in-out";

    const updateHero = () => {
        const movie = sliderMovies[currentIndex];
        if (!movie) return;

        const bgImage = movie.fondo || movie.poster;

        // Precargar imagen para evitar parpadeos
        const img = new Image();
        img.src = bgImage;

        img.onload = () => {
            const content = document.querySelector('.hero-content');
            if (content) {
                // Desvanecer texto
                content.style.opacity = '0';
                content.style.transition = 'opacity 0.5s ease';

                setTimeout(() => {
                    // Cambiar contenido
                    updateHeroUI(movie);

                    // Reaparecer texto
                    content.style.opacity = '1';
                }, 500);
            }
        };
    };

    // Mostrar la primera inmediatamente
    updateHero();

    // Configurar rotación automática
    if (window.heroInterval) clearInterval(window.heroInterval);

    if (sliderMovies.length > 1) {
        window.heroInterval = setInterval(() => {
            currentIndex = (currentIndex + 1) % sliderMovies.length;
            updateHero();
        }, 8000); // Cambiar cada 8 segundos
    }
}

// Show movie details
function showMovieDetails(movieId) {
    const movie = allMovies.find(m => m.id === movieId);

    if (!movie) {
        showMessage('Película no encontrada', 'error');
        return;
    }

    document.getElementById('movieModalTitle').textContent = movie.titulo;

    const hasLatino = movie.latino && movie.latino.trim() !== '';
    const hasEspanol = movie.español && movie.español.trim() !== '';
    const hasSubtitulado = movie.subtitulado && movie.subtitulado.trim() !== '';

    const movieDetailsHTML = `
        <div class="movie-details-content">
            <div class="movie-details-grid">
                <div class="modal-poster-wrapper">
                    <div class="modal-loader"><div class="spinner"></div></div>
                    <img src="${movie.poster}" alt="${movie.titulo}" class="movie-poster-large" onload="this.parentElement.classList.add('loaded')">
                </div>
                <div class="movie-info-detailed">
                    <h2>${movie.titulo}</h2>
                    <div class="movie-meta-detailed">
                        <span><i class="fas fa-calendar"></i> ${movie.año}</span>
                        <span><i class="fas fa-clock"></i> ${Math.floor(movie.duracion / 60)}h ${movie.duracion % 60}m</span>
                        <span><i class="fas fa-clock"></i> ${movie.tipo === 'serie' ? (movie.temporadas + ' Temp - ' + movie.episodios + ' Eps') : (Math.floor(movie.duracion / 60) + 'h ' + movie.duracion % 60 + 'm')}</span>
                        <span><i class="fas fa-star" style="color: var(--warning-color);"></i> ${movie.rating.toFixed(1)}/10</span>
                        <span><i class="fas fa-user"></i> ${movie.director}</span>
                    </div>
                    
                    <div class="movie-description">
                        <h4>Sinopsis</h4>
                        <p>${movie.sinopsis}</p>
                    </div>
                    
                    <div class="movie-actions">
                        <button class="btn" onclick="playMovie(${JSON.stringify(movie).replace(/"/g, '&quot;')})">
                            <i class="fas fa-play"></i> ${movie.tipo === 'serie' ? 'Ver Serie' : 'Reproducir Película'}
                        </button>
                        <button class="btn btn-outline" style="border-color: #ff4757; color: #ff4757;" onclick="reportCurrentContentToBot('${movie.titulo}', '${movie.id}')">
                            <i class="fas fa-exclamation-triangle"></i> Reportar Error
                        </button>
                        <button class="btn btn-outline" onclick="movieModal.style.display='none'">
                            <i class="fas fa-times"></i> Cerrar
                        </button>
                    </div>
                    
                    ${hasLatino || hasEspanol || hasSubtitulado ? `
                    <div style="margin-top: 20px;">
                        <h4>Idiomas Disponibles:</h4>
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            ${hasLatino ? '<span class="badge" style="background-color: rgba(46, 204, 113, 0.2); color: var(--success-color);">Latino</span>' : ''}
                            ${hasEspanol ? '<span class="badge" style="background-color: rgba(52, 152, 219, 0.2); color: var(--info-color);">Español</span>' : ''}
                            ${hasSubtitulado ? '<span class="badge" style="background-color: rgba(155, 89, 182, 0.2); color: #9b59b6;">Subtitulado</span>' : ''}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

    document.getElementById('movieModalBody').innerHTML = movieDetailsHTML;
    movieModal.style.display = 'flex';
}

// Play movie
function playMovie(movie) {
    if (typeof checkFreeUserLimitBeforePlay === 'function' && !checkFreeUserLimitBeforePlay()) {
        return;
    }

    currentMovieTitle = movie.titulo;
    currentVideoUrl = movie.latino || movie.español || movie.subtitulado || movie.url;

    if (!currentVideoUrl || currentVideoUrl.trim() === '') {
        showMessage('No hay enlaces de reproducción disponibles', 'warning');
        return;
    }

    document.getElementById('videoModalTitle').textContent = `Reproduciendo: ${movie.titulo}`;

    // Configurar loader de video
    const videoContainer = document.querySelector('.video-container');
    let loader = videoContainer.querySelector('.video-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.className = 'video-loader';
        loader.innerHTML = '<div class="spinner"></div>';
        videoContainer.appendChild(loader);
    }

    loader.style.display = 'flex';
    videoPlayer.style.opacity = '0';
    videoPlayer.onload = () => {
        loader.style.display = 'none';
        videoPlayer.style.opacity = '1';
    };

    videoPlayer.src = currentVideoUrl;
    setupLanguageButtons(movie);
    videoModal.style.display = 'flex';
    saveToContinueWatching(movie.id);

    if (typeof startFreeUserTimer === 'function') startFreeUserTimer();
}

// Setup language buttons
function setupLanguageButtons(movie) {
    const languageSelection = document.getElementById('languageSelection');
    languageSelection.innerHTML = '';

    const languages = [];

    if (movie.latino && movie.latino.trim() !== '') {
        languages.push({
            name: 'Latino',
            url: movie.latino,
            icon: 'fas fa-globe-americas'
        });
    }

    if (movie.español && movie.español.trim() !== '') {
        languages.push({
            name: 'Español',
            url: movie.español,
            icon: 'fas fa-language'
        });
    }

    if (movie.subtitulado && movie.subtitulado.trim() !== '') {
        languages.push({
            name: 'Subtitulado',
            url: movie.subtitulado,
            icon: 'fas fa-closed-captioning'
        });
    }

    if (movie.url && movie.url.trim() !== '') {
        languages.push({
            name: 'Principal',
            url: movie.url,
            icon: 'fas fa-play'
        });
    }

    if (languages.length > 0) {
        const title = document.createElement('h3');
        title.className = 'language-title';
        title.textContent = 'Seleccionar Idioma:';
        languageSelection.appendChild(title);

        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'language-buttons';

        languages.forEach((lang, index) => {
            const button = document.createElement('button');
            button.className = index === 0 ? 'lang-btn active' : 'lang-btn';
            button.innerHTML = `<i class="${lang.icon}"></i> ${lang.name}`;
            button.onclick = () => {
                currentVideoUrl = lang.url;

                // Mostrar loader al cambiar de opción
                const loader = document.querySelector('.video-loader');
                if (loader) loader.style.display = 'flex';
                videoPlayer.style.opacity = '0';

                videoPlayer.src = lang.url;
                document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            };
            buttonsContainer.appendChild(button);
        });

        languageSelection.appendChild(buttonsContainer);
        
        // Botón de reporte dentro del modal de video
        const reportDiv = document.createElement('div');
        reportDiv.style.marginTop = '20px';
        reportDiv.style.textAlign = 'center';
        reportDiv.innerHTML = `
            <button class="btn btn-outline" style="border-color: #ff4757; color: #ff4757; font-size: 0.8rem; padding: 5px 15px;" 
                onclick="reportCurrentContentToBot('${movie.titulo}', '${movie.id}', currentVideoUrl)">
                <i class="fas fa-exclamation-triangle"></i> Reportar Enlace Caído
            </button>
        `;
        languageSelection.appendChild(reportDiv);

        languageSelection.style.display = 'block';
    } else {
        languageSelection.style.display = 'none';
    }
}

// Scroll row function (global para usar en onclick)
window.scrollRow = function (rowId, amount) {
    const row = document.getElementById(rowId);
    if (row) {
        row.scrollBy({
            left: amount,
            behavior: 'smooth'
        });
    }
};

// Search movies
function searchMovies() {
    const query = searchInput.value.toLowerCase().trim();
    const searchResultsSection = document.getElementById('searchResults');
    const searchResultsMovies = document.getElementById('searchResultsMovies');

    // Referencias a las secciones principales
    const tendencias = document.getElementById('tendencias');
    const estrenos = document.getElementById('estrenos');

    if (!query) {
        clearSearch();
        return;
    }

    // Ocultar secciones principales
    const recentSection = document.getElementById('recentSection');
    const continueWatchingSection = document.getElementById('continueWatching');
    const seriesSection = document.getElementById('series');
    
    if (continueWatchingSection) continueWatchingSection.style.display = 'none';
    if (recentSection) recentSection.style.display = 'none';
    if (tendencias) tendencias.style.display = 'none';
    if (estrenos) estrenos.style.display = 'none';
    if (seriesSection) seriesSection.style.display = 'none';
    if (categoriasSections) categoriasSections.style.display = 'none';
    if (mainSeriesContent) mainSeriesContent.style.display = 'none';
    if (heroSection) heroSection.style.display = 'none';

    // Mostrar sección de resultados
    if (searchResultsSection) {
        searchResultsSection.style.display = 'block';
        searchResultsMovies.innerHTML = '';

        // Filtrar películas y series
        const results = allMovies.filter(movie => {
            const title = movie.titulo.toLowerCase();
            const genres = movie.categorias.map(c => c.toLowerCase());
            return title.includes(query) || genres.some(g => g.includes(query));
        });

        if (results.length > 0) {
            results.forEach(movie => {
                searchResultsMovies.appendChild(createMovieCard(movie, true));
            });
        } else {
            searchResultsMovies.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 40px; background: rgba(255,255,255,0.03); border-radius: 15px; border: 1px dashed rgba(255,255,255,0.1);">
                    <i class="fas fa-search" style="font-size: 3rem; margin-bottom: 20px; color: var(--primary);"></i>
                    <h3 style="color: white;">No se encontró "${searchInput.value}" en nuestro catálogo</h3>
                    <p style="color: #888; margin-bottom: 20px;">Pero no te preocupes, puedes pedirlo ahora mismo.</p>
                    <button class="btn btn-primary" onclick="window.location.href='perfil.html#tmdbSearchInput'">
                        <i class="fas fa-bullhorn"></i> Pedir Película / Serie
                    </button>
                </div>
            `;
        }
    }
}

// Función global para limpiar búsqueda
window.clearSearch = function () {
    const searchResultsSection = document.getElementById('searchResults');

    if (searchInput) searchInput.value = '';
    if (searchResultsSection) searchResultsSection.style.display = 'none';

    // Restaurar secciones
    const estrenos = document.getElementById('estrenos');
    const recentSection = document.getElementById('recentSection');
    const seriesSection = document.getElementById('series');

    if (tendencias) tendencias.style.display = 'block';
    if (estrenos) estrenos.style.display = 'block';
    if (recentSection) recentSection.style.display = 'block';
    if (seriesSection) seriesSection.style.display = 'block';
    if (categoriasSections) categoriasSections.style.display = 'block';
    if (mainSeriesContent) mainSeriesContent.style.display = 'block';
    if (heroSection) heroSection.style.display = 'flex';

    // Restaurar "Continuar viendo" si corresponde
    loadContinueWatching();
};

// Setup event listeners
function setupEventListeners() {
    // Cerrar modales
    if (closeMovieModal) {
        closeMovieModal.addEventListener('click', () => {
            if (movieModal) movieModal.style.display = 'none';
        });
    }

    if (closeVideoModal) {
        closeVideoModal.addEventListener('click', () => {
            if (videoPlayer) videoPlayer.src = '';
            if (videoModal) videoModal.style.display = 'none';
        });
    }

    if (closeDownloadInfoModal) {
        closeDownloadInfoModal.addEventListener('click', () => {
            if (downloadInfoModal) downloadInfoModal.style.display = 'none';
        });
    }

    // Cerrar modales al hacer clic fuera
    window.addEventListener('click', (e) => {
        if (movieModal && e.target === movieModal) {
            movieModal.style.display = 'none';
        }
        if (videoModal && e.target === videoModal) {
            if (videoPlayer) videoPlayer.src = '';
            videoModal.style.display = 'none';
        }
        if (downloadInfoModal && e.target === downloadInfoModal) {
            downloadInfoModal.style.display = 'none';
        }
    });

    // Menú móvil
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            if (navLinks) navLinks.classList.toggle('active');
        });
    }

    // Cerrar menú al hacer clic en enlace
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 991 && navLinks) {
                navLinks.classList.remove('active');
            }
        });
    });

    // Búsqueda
    if (searchBtn) {
        searchBtn.addEventListener('click', searchMovies);
    }
    if (searchInput) {
        // Búsqueda en tiempo real
        searchInput.addEventListener('input', () => {
            // Limpiar si se borra el texto
            if (searchInput.value.trim() === '') {
                clearSearch();
                return;
            }

            // Usar un pequeño delay para no saturar si escriben muy rápido
            if (window.searchTimeout) clearTimeout(window.searchTimeout);
            window.searchTimeout = setTimeout(searchMovies, 300);
        });

        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                if (window.searchTimeout) clearTimeout(window.searchTimeout);
                searchMovies();
            }
        });
    }

    // Botón Quiero ser VIP
    const vipBtn = document.getElementById('vipUpgradeBtn');
    if (vipBtn) {
        vipBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = document.getElementById('accessModal');
            if (modal) modal.classList.add('active');
        });
    }
}

// Show message
function showMessage(message, type) {
    const messageEl = document.createElement('div');
    messageEl.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 15px 25px;
        border-radius: var(--border-radius);
        color: white;
        font-weight: 500;
        z-index: 9999;
        box-shadow: var(--box-shadow);
        animation: slideIn 0.3s ease-out;
        max-width: 400px;
    `;

    if (type === 'success') messageEl.style.backgroundColor = 'var(--success-color)';
    else if (type === 'error') messageEl.style.backgroundColor = 'var(--primary-color)';
    else if (type === 'warning') messageEl.style.backgroundColor = 'var(--warning-color)';
    else messageEl.style.backgroundColor = 'var(--info-color)';

    messageEl.textContent = message;
    document.body.appendChild(messageEl);

    setTimeout(() => {
        messageEl.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => document.body.removeChild(messageEl), 300);
    }, 3000);
}

// Add animation styles for messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }

    @keyframes cardEntrance {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .movie-card {
        animation: cardEntrance 0.5s ease-out forwards;
        opacity: 0;
    }
    
    .movie-poster {
        opacity: 0;
        transition: opacity 0.5s ease;
        background-color: #1a1a1a;
    }
    
    .movie-poster.loaded {
        opacity: 1;
    }

    .modal-poster-wrapper {
        position: relative;
        background: #1a1a1a;
        border-radius: 8px;
        overflow: hidden;
        aspect-ratio: 2/3;
        min-height: 300px;
    }
    .modal-loader {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1;
    }
    .modal-poster-wrapper .movie-poster-large {
        opacity: 0;
        transition: opacity 0.5s ease;
        position: relative;
        z-index: 2;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .modal-poster-wrapper.loaded .movie-poster-large {
        opacity: 1;
    }
    .modal-poster-wrapper.loaded .modal-loader {
        display: none;
    }

    .video-container {
        position: relative;
        background: #000;
        flex: 1;
        width: 100%;
        height: 100%;
        min-height: 0;
    }
    .video-loader {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 5;
        background: #000;
    }
    .video-player {
        transition: opacity 0.5s ease;
        width: 100%;
        height: 100%;
        border: none;
    }

    /* Estilos Fullscreen para el Modal de Video */
    #videoModal {
        padding: 0 !important;
    }
    #videoModal .modal-content {
        width: 100vw;
        height: 100vh;
        max-width: none;
        max-height: none;
        border-radius: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        background: #000;
    }
    #videoModal .modal-body {
        flex: 1;
        padding: 0;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// Ocultar modal de video
if (closeVideoModal) {
    closeVideoModal.addEventListener('click', () => {
        videoModal.style.display = 'none';
        videoPlayer.src = '';
        if (typeof stopFreeUserTimer === 'function') stopFreeUserTimer();
    });
}

// Ocultar modal de pelicula
if (closeMovieModal) {
    closeMovieModal.addEventListener('click', () => {
        movieModal.style.display = 'none';
    });
}

// Free time limit logic
window.freeUserTimer = null;
function startFreeUserTimer() {
    if (localStorage.getItem('userAccessType') === 'vip') return;
    if (window.freeUserTimer) clearInterval(window.freeUserTimer);

    window.freeUserTimer = setInterval(() => {
        let watchData = JSON.parse(localStorage.getItem('free_watch_data') || '{"date":"","seconds":0}');
        let today = new Date().toDateString();

        if (watchData.date !== today) {
            watchData = { date: today, seconds: 0 };
        }

        watchData.seconds += 1;
        localStorage.setItem('free_watch_data', JSON.stringify(watchData));

        let timeLeft = 3600 - watchData.seconds;

        if (timeLeft <= 0) {
            clearInterval(window.freeUserTimer);
            showLimitReachedMessage();
        } else if (timeLeft === 300) {
            showMessage('Te quedan 5 minutos de tiempo gratuito hoy.', 'warning');
        }
    }, 1000);
}

function stopFreeUserTimer() {
    if (window.freeUserTimer) clearInterval(window.freeUserTimer);
}

function checkFreeUserLimitBeforePlay() {
    if (localStorage.getItem('userAccessType') === 'vip') return true;
    let watchData = JSON.parse(localStorage.getItem('free_watch_data') || '{"date":"","seconds":0}');
    let today = new Date().toDateString();

    if (watchData.date === today && watchData.seconds >= 3600) {
        showLimitReachedMessage();
        return false;
    }
    return true;
}

function showLimitReachedMessage() {
    const vModal = document.getElementById('videoModal');
    if (vModal) vModal.style.display = 'none';
    if (videoPlayer) videoPlayer.src = '';

    let limitModal = document.getElementById('limitModal');
    if (!limitModal) {
        limitModal = document.createElement('div');
        limitModal.id = 'limitModal';
        limitModal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.95);z-index:99999;display:flex;justify-content:center;align-items:center;backdrop-filter:blur(10px);text-align:center;padding:20px;';
        limitModal.innerHTML = `
            <div style="background:#1f1f1f;padding:40px;border-radius:15px;max-width:500px;border:2px solid #ffd700;">
                <i class="fas fa-clock" style="font-size:4rem;color:#ffd700;margin-bottom:20px;"></i>
                <h2 style="color:white;margin-bottom:15px;">Tiempo agotado por hoy</h2>
                <p style="color:#ccc;margin-bottom:20px;font-size:1.1rem;">Has alcanzado el límite de 1 hora gratuita para el día de hoy. Podrás ver otra hora mañana.</p>
                <div style="background:rgba(255,215,0,0.1);padding:15px;border-radius:10px;margin-bottom:20px;border:1px solid rgba(255,215,0,0.3);">
                    <h3 style="color:#ffd700;margin-bottom:10px;"><i class="fas fa-crown"></i> ¿No quieres esperar?</h3>
                    <p style="color:#aaa;font-size:0.9rem;margin-bottom:15px;">Descarga nuestra app o sé usuario VIP para ver sin límite de tiempo.</p>
                    <button onclick="window.location.href='descargar.html'" style="background:linear-gradient(45deg, #ffd700, #ffb300);color:black;border:none;padding:12px 25px;border-radius:25px;font-weight:bold;cursor:pointer;width:100%;font-size:1.1rem;">
                        <i class="fas fa-download"></i> Descargar la App
                    </button>
                    <button onclick="window.location.href='index.html'; localStorage.removeItem('userAccessType');" style="background:transparent;color:#ffd700;border:1px solid #ffd700;padding:10px 20px;border-radius:25px;font-weight:bold;cursor:pointer;width:100%;margin-top:10px;">
                        <i class="fas fa-crown"></i> Soy VIP
                    </button>
                    <button onclick="document.getElementById('limitModal').style.display='none'" style="margin-top:15px; background:none; border:none; color:#888; cursor:pointer; text-decoration:underline;">Cerrar</button>
                </div>
            </div>
        `;
        document.body.appendChild(limitModal);
    }
    limitModal.style.display = 'flex';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);

// ============================================
// PAGINA DE CATEGORIAS
// ============================================
window.renderCategoryPage = function () {
    const categoryGrid = document.getElementById('categoryGrid');
    const categoryTabs = document.getElementById('categoryTabs');
    const categoryTitle = document.getElementById('categoryTitle');

    if (!categoryGrid || !categoryTabs || !categoryTitle) return;

    // Obtener parámetros de la URL
    const urlParams = new URLSearchParams(window.location.search);
    let selectedCategory = urlParams.get('cat');

    // Configurar pestañas
    categoryTabs.innerHTML = '';

    // Todas las opciones (combinar categorías de mainCategories y las extraídas)
    const allCategoriesArray = Array.from(new Set([...mainCategories, ...Array.from(allGenres)])).sort();

    // Validar categoría seleccionada y poner por defecto
    if (!selectedCategory || !allCategoriesArray.some(c => c.toLowerCase() === selectedCategory.toLowerCase())) {
        selectedCategory = allCategoriesArray[0] || 'Acción';
    }

    // Pestaña "Todas"
    const todasBtn = document.createElement('a');
    todasBtn.href = '?cat=todas';
    todasBtn.className = `category-tab ${selectedCategory === 'todas' ? 'active' : ''}`;
    todasBtn.innerText = 'Todas';
    categoryTabs.appendChild(todasBtn);

    // Llenar Pestañas
    allCategoriesArray.forEach(cat => {
        const catBtn = document.createElement('a');
        catBtn.href = `?cat=${encodeURIComponent(cat)}`;
        catBtn.className = `category-tab ${selectedCategory.toLowerCase() === cat.toLowerCase() ? 'active' : ''}`;
        catBtn.innerText = cat;
        categoryTabs.appendChild(catBtn);
    });

    // Título Actual
    categoryTitle.innerText = selectedCategory === 'todas' ? 'Todas las Categorías' : `Categoría: ${selectedCategory}`;

    categoryGrid.innerHTML = '';

    // Filtrar películas de esta categoría
    let categoryMovies = [];
    if (selectedCategory === 'todas') {
        categoryMovies = allMovies;
    } else {
        categoryMovies = allMovies.filter(movie =>
            movie.categorias && movie.categorias.some(c => {
                const cNorm = c.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                const catNorm = selectedCategory.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                return cNorm.includes(catNorm) || catNorm.includes(cNorm);
            })
        );
    }

    if (categoryMovies.length === 0) {
        categoryGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-film"></i>
                <h3>No hay contenido en esta categoría</h3>
            </div>
        `;
        return;
    }

    // Mostrar contenido
    const fragment = document.createDocumentFragment();
    categoryMovies.forEach(movie => {
        fragment.appendChild(createMovieCard(movie, true));
    });
    categoryGrid.appendChild(fragment);
};

// ============================================
// PAGINA DE ESTRENOS
// ============================================
window.renderEstrenosPage = function () {
    const estrenosGrid = document.getElementById('estrenosGrid');
    if (!estrenosGrid) return;

    estrenosGrid.innerHTML = '';

    const currentYear = new Date().getFullYear().toString();
    const estrenos = allMovies.filter(m => m.estreno || m.año === currentYear);

    if (estrenos.length === 0) {
        estrenosGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-film"></i>
                <h3>No hay estrenos disponibles en este momento</h3>
            </div>
        `;
        return;
    }

    const fragment = document.createDocumentFragment();
    estrenos.forEach(movie => {
        fragment.appendChild(createMovieCard(movie, true));
    });
    estrenosGrid.appendChild(fragment);
};

// ============================================
// PAGINA DE TENDENCIAS
// ============================================
window.renderTendenciasPage = function () {
    const tendenciasGrid = document.getElementById('tendenciasGrid');
    if (!tendenciasGrid) return;

    tendenciasGrid.innerHTML = '';

    const tendencias = allMovies.filter(m => m.tendencias || m.destacado);

    if (tendencias.length === 0) {
        tendenciasGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-film"></i>
                <h3>No hay tendencias disponibles en este momento</h3>
            </div>
        `;
        return;
    }

    const fragment = document.createDocumentFragment();
    tendencias.forEach(movie => {
        fragment.appendChild(createMovieCard(movie, true));
    });
    tendenciasGrid.appendChild(fragment);
};

// --- LÓGICA DE REPORTES TELEGRAM ---
window.reportCurrentContentToBot = async function(titulo, id, urlExtra = '') {
    const BOT_TOKEN = "8558038434:AAGZh740g6MjGmj1h2qAebB-Hij6DexPI0s";
    const CHAT_ID_PEDIDOS = "-5191457076"; // Grupo Pedidos

    const userName = localStorage.getItem('userName') || 'Usuario Web';
    const escapedEscapedTitle = titulo.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const mensaje = `🚨 <b>REPORTE DE ERROR / CONTENIDO</b> 🚨\n\n` +
                    `👤 <b>Usuario:</b> ${userName}\n` +
                    `🎬 <b>Título:</b> ${escapedEscapedTitle}\n` +
                    `🆔 <b>ID:</b> ${id}\n` +
                    (urlExtra ? `🔗 <b>Enlace:</b> ${urlExtra}\n` : '') +
                    `❌ <i>El usuario indica que hay un error o el enlace no funciona.</i>`;

    try {
        const response = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: CHAT_ID_PEDIDOS,
                text: mensaje,
                parse_mode: 'HTML'
            })
        });

        if (response.ok) {
            alert('🚨 Reporte enviado al administrador. ¡Gracias!');
        } else {
            const errData = await response.json();
            console.error('Telegram Report Error:', errData);
            alert('❌ Error Telegram: ' + (errData.description || 'Desconocido'));
        }
    } catch (e) {
        console.error('Fetch Report Error:', e);
        alert('❌ Error de conexión al enviar el reporte.');
    }
};