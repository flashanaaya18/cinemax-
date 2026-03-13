#!/usr/bin/env python3
"""
🎬 PANEL DE ADMINISTRACIÓN PELIXPLUSHDZ CON TMDB - VERSIÓN PREMIUM
✨ Diseño mejorado con animaciones y interfaz atractiva
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import re
import requests
from datetime import datetime
from urllib.parse import quote
import sys
import time
import threading

# Configuración de TMDB
TMDB_API_KEY = "9869fab7c867e72214c8628c6029ec74"
TMDB_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5ODY5ZmFiN2M4NjdlNzIyMTRjODYyOGM2MDI5ZWM3NCIsIm5iZiI6MTc1OTI2NzMzMi43MDg5OTk5LCJzdWIiOiI2OGRjNGEwNDE1NWQwOWZjZGQyZGY0MTMiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0._sxkF_bWFZtZOQU_8GcEa4x7TawgM_CB9zA43VzSiAY"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/original"

# Headers para TMDB
TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json"
}

# Configuración de Telegram
TELEGRAM_TOKEN = "8558038434:AAGZh740g6MjGmj1h2qAebB-Hij6DexPI0s"
CHAT_ID = "-1003658869096" # ID actualizado del grupo cinemax+

def notificar_telegram(contenido, tipo="película"):
    """Envía una notificación al grupo de Telegram con detalles visuales premium"""
    try:
        titulo = contenido.get('titulo', 'Sin título').upper()
        año = contenido.get('año', 'N/A')
        rating = contenido.get('rating', '0')
        genero = contenido.get('categoria', contenido.get('genero', 'General')).capitalize()
        poster = contenido.get('poster', contenido.get('portada', ''))
        
        # Detección inteligente de idiomas
        idiomas = []
        if contenido.get('latino') and contenido.get('latino').strip(): 
            idiomas.append("🇲🇽 Latino")
        if contenido.get('español') and contenido.get('español').strip(): 
            idiomas.append("🇪🇸 Castellano")
        if contenido.get('subtitulado') and contenido.get('subtitulado').strip(): 
            idiomas.append("📝 Subtitulado")
        
        if not idiomas and contenido.get('url'):
            idiomas.append("🌐 Online")
            
        str_idiomas = " | ".join(idiomas) if idiomas else "Por definir"

        mensaje = f"🎬 *¡NUEVO ESTRENO EN CINEMAX+!* 🎬\n\n"
        mensaje += f"🔥 *{titulo}*\n"
        mensaje += f"📅 *Año:* {año}\n"
        mensaje += f"🌟 *Rating:* {rating} / 10\n"
        mensaje += f"🎭 *Género:* {genero}\n"
        mensaje += f"🔊 *Idiomas:* {str_idiomas}\n\n"
        mensaje += f"🍿 Disfruta de la mejor calidad premium sin anuncios aquí:\n"
        mensaje += f"🚀 [VER AHORA EN CINEMAX+](https://pelixplushdz.netlify.app/ver.html?id={contenido.get('id', '')})"

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        # Enviar foto con el mensaje como pie de foto (más elegante)
        if poster:
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            requests.post(url_photo, json={
                "chat_id": CHAT_ID,
                "photo": poster,
                "caption": mensaje,
                "parse_mode": "Markdown"
            })
        else:
            requests.post(url, json={
                "chat_id": CHAT_ID,
                "text": mensaje,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            })
            
        return True
    except Exception as e:
        print(f"Error notificado a Telegram: {e}")
        return False

# Colores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[35m'
    ORANGE = '\033[33m'
    PINK = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Animaciones
def show_loading(text="Cargando", duration=2):
    """Muestra una animación de carga"""
    animation = "⣾⣽⣻⢿⡿⣟⣯⣷"
    for i in range(duration * 10):
        sys.stdout.write(f"\r{Colors.CYAN}{animation[i % len(animation)]} {text}...{Colors.END}")
        sys.stdout.flush()
        time.sleep(0.1)
    print()

def print_header():
    """Imprime un encabezado atractivo"""
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}🎬  P A N E L   D E   A D M I N I S T R A C I Ó N  🎬{Colors.END}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}✨  PELIXPLUSHDZ PREMIUM - TMDB INTEGRADO  ✨{Colors.END}")
    print(f"{Colors.BLUE}📊  Versión: 3.0 | Conectado a Firebase y TMDB{Colors.END}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.END}")

def print_section(title):
    """Imprime una sección con estilo"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")

def print_success(msg):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    """Imprime un mensaje de error"""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    """Imprime un mensaje informativo"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    """Imprime un mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_movie_card(title, year, rating, category, destacado=False):
    """Muestra una tarjeta de película atractiva"""
    icons = ""
    if destacado:
        icons += f"{Colors.YELLOW}🏆{Colors.END} "
    
    print(f"{Colors.CYAN}┌{'─'*58}┐{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END} {icons}{Colors.BOLD}{title[:45]:<45}{Colors.END} {Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END} 📅 {year:<8} ⭐ {rating:<4} 🏷️ {category:<15} {Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}└{'─'*58}┘{Colors.END}")

def print_serie_card(title, year, seasons, episodes, category, destacado=False):
    """Muestra una tarjeta de serie atractiva"""
    icons = ""
    if destacado:
        icons += f"{Colors.YELLOW}🏆{Colors.END} "
    
    print(f"{Colors.PINK}┌{'─'*58}┐{Colors.END}")
    print(f"{Colors.PINK}│{Colors.END} {icons}{Colors.BOLD}{title[:45]:<45}{Colors.END} {Colors.PINK}│{Colors.END}")
    print(f"{Colors.PINK}│{Colors.END} 📅 {year:<8} 📊 T{sessions:<2} E{episodes:<3} 🏷️ {category:<15} {Colors.PINK}│{Colors.END}")
    print(f"{Colors.PINK}└{'─'*58}┘{Colors.END}")

# Inicializar Firebase con animación
def init_firebase():
    """Inicializa Firebase con animación"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🎬 Inicializando PelixplushdZ Premium...{Colors.END}")
    show_loading("Conectando a Firebase", 1)
    
    try:
        cred = credentials.Certificate('serviceAccountKey.json')
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        print_success("✅ Conexión establecida con Firebase Firestore")
        show_loading("Conectando a TMDB API", 1)
        print_success("🔗 Conectado a TMDB API")
        return db
        
    except Exception as e:
        print_error(f"Error al conectar: {str(e)}")
        return None

# ============================================
# FUNCIONES AUXILIARES CON ANIMACIONES
# ============================================

def buscar_en_tmdb(query):
    """Busca películas en TMDB con animación"""
    try:
        show_loading(f"Buscando '{query}' en TMDB")
        
        params = {
            "query": query,
            "include_adult": False,
            "language": "es-ES",
            "page": 1
        }
        
        response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            headers=TMDB_HEADERS,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            resultados = data.get("results", [])
            
            if not resultados:
                print_error("No se encontraron resultados en TMDB")
                return None
            
            print(f"\n{Colors.GREEN}🎬 Encontrados {len(resultados)} resultados:{Colors.END}\n")
            
            for i, pelicula in enumerate(resultados[:10], 1):
                titulo = pelicula.get("title", "Sin título")
                año = pelicula.get("release_date", "")[:4] if pelicula.get("release_date") else "N/A"
                rating = pelicula.get("vote_average", 0)
                descripcion = pelicula.get("overview", "Sin descripción")
                
                if len(descripcion) > 100:
                    descripcion = descripcion[:100] + "..."
                
                print(f"{Colors.CYAN}{i:2d}.{Colors.END} {Colors.BOLD}{titulo}{Colors.END} ({año})")
                print(f"    {Colors.YELLOW}⭐{Colors.END} {rating}/10 | {Colors.BLUE}📝{Colors.END} {descripcion}")
                print(f"    {Colors.PURPLE}🆔{Colors.END} ID TMDB: {pelicula.get('id')}\n")
            
            return resultados[:10]
        else:
            print_error(f"Error TMDB: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Error en la búsqueda: {str(e)}")
        return None

def buscar_serie_tmdb(query):
    """Busca series en TMDB con animación"""
    try:
        show_loading(f"Buscando serie '{query}' en TMDB")
        
        params = {
            "query": query,
            "include_adult": False,
            "language": "es-ES",
            "page": 1
        }
        
        response = requests.get(
            f"{TMDB_BASE_URL}/search/tv",
            headers=TMDB_HEADERS,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            resultados = data.get("results", [])
            
            if not resultados:
                print_error("No se encontraron series en TMDB")
                return None
            
            print(f"\n{Colors.GREEN}📺 Encontradas {len(resultados)} series:{Colors.END}\n")
            
            for i, serie in enumerate(resultados[:10], 1):
                titulo = serie.get("name", "Sin título")
                año = serie.get("first_air_date", "")[:4] if serie.get("first_air_date") else "N/A"
                rating = serie.get("vote_average", 0)
                descripcion = serie.get("overview", "Sin descripción")
                
                if len(descripcion) > 100:
                    descripcion = descripcion[:100] + "..."
                
                print(f"{Colors.PINK}{i:2d}.{Colors.END} {Colors.BOLD}{titulo}{Colors.END} ({año})")
                print(f"    {Colors.YELLOW}⭐{Colors.END} {rating}/10 | {Colors.BLUE}📝{Colors.END} {descripcion}")
                print(f"    {Colors.PURPLE}🆔{Colors.END} ID TMDB: {serie.get('id')}\n")
            
            return resultados[:10]
        return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def obtener_detalles_tmdb(movie_id):
    """Obtiene detalles completos de una película desde TMDB"""
    try:
        show_loading(f"Obteniendo detalles de ID: {movie_id}")
        
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            headers=TMDB_HEADERS,
            params={"language": "es-ES"}
        )
        
        if response.status_code != 200:
            print_error(f"Error al obtener detalles: {response.status_code}")
            return None
        
        pelicula = response.json()
        
        # Obtener créditos para el director
        response_credits = requests.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}/credits",
            headers=TMDB_HEADERS,
            params={"language": "es-ES"}
        )
        
        director = "Desconocido"
        if response_credits.status_code == 200:
            credits = response_credits.json()
            for crew in credits.get("crew", []):
                if crew.get("job") == "Director":
                    director = crew.get("name", "Desconocido")
                    break
        
        # Obtener género principal
        genero_principal = "Drama"
        if pelicula.get("genres"):
            genero_principal = pelicula["genres"][0]["name"]
        
        # Construir URL del póster
        poster_path = pelicula.get("poster_path")
        poster_url = f"{TMDB_IMAGE_URL}{poster_path}" if poster_path else "https://via.placeholder.com/300x450/333333/ffffff?text=No+Image"
        
        # Preparar datos
        datos = {
            'titulo': pelicula.get("title", "Sin título"),
            'titulo_original': pelicula.get("original_title", ""),
            'sisposesis': pelicula.get("overview", "Sin descripción"),
            'año': pelicula.get("release_date", "")[:4] if pelicula.get("release_date") else "N/A",
            'duracion': pelicula.get("runtime", 0),
            'director': director,
            'genero_tmdb': genero_principal,
            'rating_tmdb': pelicula.get("vote_average", 0),
            'votos_tmdb': pelicula.get("vote_count", 0),
            'poster': poster_url,
            'fondo': f"{TMDB_IMAGE_URL}{pelicula.get('backdrop_path')}" if pelicula.get("backdrop_path") else "",
            'tmdb_id': movie_id,
            'fecha_agregado': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print_success("Datos obtenidos de TMDB")
        return datos
        
    except Exception as e:
        print_error(f"Error al obtener detalles: {str(e)}")
        return None

def obtener_detalles_serie_tmdb(tv_id):
    """Obtiene detalles de una serie desde TMDB"""
    try:
        show_loading(f"Obteniendo detalles de serie ID: {tv_id}")
        
        response = requests.get(
            f"{TMDB_BASE_URL}/tv/{tv_id}",
            headers=TMDB_HEADERS,
            params={"language": "es-ES"}
        )
        
        if response.status_code != 200:
            print_error(f"Error al obtener detalles: {response.status_code}")
            return None
        
        serie = response.json()
        
        # Género principal
        genero_principal = "Drama"
        if serie.get("genres"):
            genero_principal = serie["genres"][0]["name"]
            
        # Poster
        poster_path = serie.get("poster_path")
        poster_url = f"{TMDB_IMAGE_URL}{poster_path}" if poster_path else "https://via.placeholder.com/300x450?text=No+Poster"
        
        # Temporadas y episodios
        temporadas = serie.get("number_of_seasons", 1)
        episodios = serie.get("number_of_episodes", 1)
        
        # Año
        año = serie.get("first_air_date", "")[:4] if serie.get("first_air_date") else "N/A"
        
        # Datos
        datos = {
            'titulo': serie.get("name", "Sin título"),
            'sinopsis': serie.get("overview", "Sin descripción"),
            'año': año,
            'temporada': temporadas,
            'episodios': episodios,
            'categoria': genero_principal.lower(),
            'rating': serie.get("vote_average", 0),
            'portada': poster_url,
            'fondo': f"{TMDB_IMAGE_URL}{serie.get('backdrop_path')}" if serie.get("backdrop_path") else "",
            'tmdb_id': tv_id,
            'fecha_agregado': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': 'serie'
        }
        
        return datos
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def mostrar_detalles_tmdb(detalles):
    """Muestra los detalles obtenidos de TMDB con diseño atractivo"""
    print(f"\n{Colors.PURPLE}{'═'*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}📋 DETALLES DE LA PELÍCULA (TMDB){Colors.END}")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}")
    
    print(f"{Colors.YELLOW}🎬 Título:{Colors.END} {Colors.BOLD}{detalles['titulo']}{Colors.END}")
    if detalles.get('titulo_original') and detalles['titulo_original'] != detalles['titulo']:
        print(f"   {Colors.GREEN}Título original:{Colors.END} {detalles['titulo_original']}")
    
    print(f"{Colors.BLUE}📅 Año:{Colors.END} {detalles['año']}")
    print(f"{Colors.CYAN}⏱️  Duración:{Colors.END} {detalles['duracion']} min")
    print(f"{Colors.PINK}🎭 Género TMDB:{Colors.END} {detalles['genero_tmdb']}")
    print(f"{Colors.GREEN}🎬 Director:{Colors.END} {detalles['director']}")
    print(f"{Colors.YELLOW}⭐ Rating TMDB:{Colors.END} {detalles['rating_tmdb']}/10 ({detalles['votos_tmdb']} votos)")
    
    if detalles.get('sisposesis'):
        print(f"\n{Colors.CYAN}📝 Sinopsis:{Colors.END}")
        print(f"{detalles['sisposesis']}")
    
    print(f"\n{Colors.PURPLE}🔗 ID TMDB:{Colors.END} {detalles['tmdb_id']}")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}")

def mostrar_detalles_serie_tmdb(detalles):
    """Muestra los detalles obtenidos de TMDB para una serie"""
    print(f"\n{Colors.PURPLE}{'═'*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}📋 DETALLES DE LA SERIE (TMDB){Colors.END}")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}")
    
    print(f"{Colors.YELLOW}📺 Título:{Colors.END} {Colors.BOLD}{detalles['titulo']}{Colors.END}")
    print(f"{Colors.BLUE}📅 Año:{Colors.END} {detalles['año']}")
    print(f"{Colors.GREEN}📊 Temporadas:{Colors.END} {detalles['temporada']}")
    print(f"{Colors.GREEN}📊 Episodios:{Colors.END} {detalles['episodios']}")
    print(f"{Colors.PINK}🎭 Categoría:{Colors.END} {detalles['categoria']}")
    print(f"{Colors.YELLOW}⭐ Rating:{Colors.END} {detalles['rating']}/10")
    
    if detalles.get('sinopsis'):
        print(f"\n{Colors.CYAN}📝 Sinopsis:{Colors.END}")
        print(f"{detalles['sinopsis']}")
    
    print(f"\n{Colors.PURPLE}🔗 ID TMDB:{Colors.END} {detalles['tmdb_id']}")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}")

# ============================================
# FUNCIÓN PRINCIPAL AGREGAR DESDE URL TMDB
# ============================================

def agregar_desde_url_tmdb():
    """Agrega contenido automáticamente desde una URL de TMDB"""
    print_section("AGREGAR DESDE URL TMDB")
    
    print(f"\n{Colors.CYAN}🌐 URLS SOPORTADAS:{Colors.END}")
    print(f"{Colors.YELLOW}• Películas:{Colors.END}")
    print(f"  {Colors.GREEN}https://www.themoviedb.org/movie/550-fight-club{Colors.END}")
    print(f"  {Colors.GREEN}https://www.themoviedb.org/movie/278{Colors.END}")
    print(f"{Colors.YELLOW}• Series:{Colors.END}")
    print(f"  {Colors.GREEN}https://www.themoviedb.org/tv/1399-game-of-thrones{Colors.END}")
    print(f"{Colors.YELLOW}• Solo ID:{Colors.END} {Colors.CYAN}550{Colors.END} o {Colors.CYAN}1399{Colors.END}")
    
    print(f"\n{Colors.PURPLE}{'─'*60}{Colors.END}")
    
    url = input(f"\n{Colors.CYAN}📥 Pega la URL o ID de TMDB: {Colors.END}").strip()
    
    if not url:
        print_error("URL vacía")
        return
    
    content_type = None
    content_id = None
    
    # Si es solo un número
    if url.isdigit():
        content_id = int(url)
        print(f"\n{Colors.GREEN}📋 ID detectado: {content_id}{Colors.END}")
        tipo = input(f"{Colors.CYAN}¿Es película o serie? (m/s): {Colors.END}").strip().lower()
        content_type = 'movie' if tipo == 'm' else 'tv' if tipo == 's' else 'movie'
    
    # Si es una URL
    else:
        patterns = [
            r'themoviedb\.org/movie/(\d+)',
            r'tmdb\.org/movie/(\d+)',
            r'/movie/(\d+)',
            r'api\.themoviedb\.org/3/movie/(\d+)',
            r'themoviedb\.org/tv/(\d+)',
            r'tmdb\.org/tv/(\d+)',
            r'/tv/(\d+)',
            r'api\.themoviedb\.org/3/tv/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                content_id = int(match.group(1))
                if 'movie' in pattern or '/movie/' in url.lower():
                    content_type = 'movie'
                elif 'tv' in pattern or '/tv/' in url.lower():
                    content_type = 'tv'
                break
    
    if not content_id or not content_type:
        print_error("No se pudo extraer el ID o tipo de TMDB")
        return
    
    print(f"\n{Colors.GREEN}🎬 ID TMDB detectado: {content_id}{Colors.END}")
    print(f"{Colors.GREEN}🎬 Tipo: {'Serie' if content_type == 'tv' else 'Película'}{Colors.END}")
    
    if content_type == 'movie':
        detalles = obtener_detalles_tmdb(content_id)
        
        if not detalles:
            return
        
        mostrar_detalles_tmdb(detalles)
        
        print_section("CONFIGURACIÓN AUTOMÁTICA")
        
        genero_tmdb = detalles.get('genero_tmdb', '').lower()
        mapeo_generos = {
            'acción': 'accion', 'action': 'accion',
            'terror': 'terror', 'horror': 'terror',
            'crimen': 'crimen', 'crime': 'crimen',
            'aventura': 'aventura', 'adventure': 'aventura',
            'suspense': 'suspenso', 'thriller': 'suspenso',
            'drama': 'drama', 'comedia': 'comedia',
            'comedy': 'comedia', 'fantasía': 'fantasia',
            'fantasy': 'fantasia', 'ciencia ficción': 'ciencia ficcion',
            'science fiction': 'ciencia ficcion', 'animación': 'animacion',
            'animation': 'animacion', 'romance': 'romance',
            'misterio': 'misterio', 'mystery': 'misterio'
        }
        
        categoria_auto = 'drama'
        for genero_key, categoria in mapeo_generos.items():
            if genero_key in genero_tmdb:
                categoria_auto = categoria
                break
        
        rating_tmdb = detalles.get('rating_tmdb', 0)
        votos_tmdb = detalles.get('votos_tmdb', 0)
        destacado = rating_tmdb >= 7.5 and votos_tmdb > 1000
        tendencias = votos_tmdb > 5000
        estreno = int(detalles.get('año', 0)) >= datetime.now().year - 1
        
        print(f"{Colors.CYAN}🏷️  Categoría automática:{Colors.END} {categoria_auto}")
        print(f"{Colors.YELLOW}⭐ Rating TMDB:{Colors.END} {rating_tmdb}/10 ({votos_tmdb} votos)")
        print(f"{Colors.GREEN}🏆 Destacado:{Colors.END} {'Sí' if destacado else 'No'}")
        print(f"{Colors.ORANGE}🔥 En tendencias:{Colors.END} {'Sí' if tendencias else 'No'}")
        print(f"{Colors.PINK}🆕 Es estreno:{Colors.END} {'Sí' if estreno else 'No'}")
        
        usar_auto = input(f"\n{Colors.CYAN}¿Usar configuración automática? (s/n): {Colors.END}").strip().lower()
        
        if usar_auto == 's':
            detalles['categoria'] = categoria_auto
            detalles['rating'] = rating_tmdb
            detalles['destacado'] = destacado
            detalles['tendencias'] = tendencias
            detalles['estreno'] = estreno
            print_success("Configuración automática aplicada")
        else:
            print_section("CONFIGURACIÓN MANUAL")
            
            categoria = input(f"{Colors.CYAN}Categoría [{categoria_auto}]: {Colors.END}").strip()
            detalles['categoria'] = categoria if categoria else categoria_auto
            
            rating = input(f"{Colors.CYAN}Rating (1-10) [{rating_tmdb}]: {Colors.END}").strip()
            detalles['rating'] = float(rating) if rating else rating_tmdb
            
            detalles['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n) [{'s' if destacado else 'n'}]: {Colors.END}").strip().lower() == 's'
            detalles['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n) [{'s' if tendencias else 'n'}]: {Colors.END}").strip().lower() == 's'
            detalles['estreno'] = input(f"{Colors.CYAN}¿Es estreno? (s/n) [{'s' if estreno else 'n'}]: {Colors.END}").strip().lower() == 's'
        
        print_section("URLS DE REPRODUCCIÓN")
        
        detalles['url'] = input(f"{Colors.CYAN}URL principal (opcional): {Colors.END}").strip()
        detalles['español'] = input(f"{Colors.CYAN}URL español (opcional): {Colors.END}").strip()
        detalles['latino'] = input(f"{Colors.CYAN}URL latino (opcional): {Colors.END}").strip()
        detalles['subtitulado'] = input(f"{Colors.CYAN}URL subtitulado (opcional): {Colors.END}").strip()
        
        confirmar = input(f"\n{Colors.GREEN}¿Agregar esta película? (s/n): {Colors.END}").strip().lower()
        
        if confirmar == 's':
            slug = re.sub(r'[^a-z0-9]+', '-', detalles['titulo'].lower()).strip('-')
            doc_id = f"{slug}-{detalles['año']}-{detalles['tmdb_id']}"
            
            try:
                doc_ref = db.collection('peliculas').document(doc_id)
                detalles['id'] = doc_id
                doc_ref.set(detalles)
                
                print_success(f"Película '{detalles['titulo']}' agregada exitosamente!")
                print(f"{Colors.CYAN}📁 ID Firestore: {doc_id}{Colors.END}")
                print(f"{Colors.CYAN}🔗 ID TMDB: {detalles['tmdb_id']}{Colors.END}")
                
                # Notificar a Telegram
                show_loading("Notificando a Telegram", 1)
                if notificar_telegram(detalles, "película"):
                    print_success("Notificación enviada a Telegram")
                
            except Exception as e:
                print_error(f"Error al guardar: {str(e)}")
        else:
            print_error("Operación cancelada")
            
    elif content_type == 'tv':
        detalles = obtener_detalles_serie_tmdb(content_id)
        
        if not detalles:
            return
        
        mostrar_detalles_serie_tmdb(detalles)
        
        print_section("CONFIGURACIÓN PARA SERIE")
        
        categoria_tmdb = detalles.get('categoria', '').lower()
        mapeo_generos = {
            'acción': 'accion', 'action': 'accion',
            'terror': 'terror', 'horror': 'terror',
            'crimen': 'crimen', 'crime': 'crimen',
            'aventura': 'aventura', 'adventure': 'aventura',
            'suspense': 'suspenso', 'thriller': 'suspenso',
            'drama': 'drama', 'comedia': 'comedia',
            'comedy': 'comedia', 'fantasía': 'fantasia',
            'fantasy': 'fantasia', 'ciencia ficción': 'ciencia ficcion',
            'science fiction': 'ciencia ficcion', 'animación': 'animacion',
            'animation': 'animacion', 'romance': 'romance',
            'misterio': 'misterio', 'mystery': 'misterio'
        }
        
        categoria_auto = 'drama'
        for genero_key, categoria in mapeo_generos.items():
            if genero_key in categoria_tmdb:
                categoria_auto = categoria
                break
        
        rating_tmdb = detalles.get('rating', 0)
        destacado = rating_tmdb >= 7.5
        tendencias = rating_tmdb >= 7.0
        estreno = int(detalles.get('año', 0)) >= datetime.now().year - 1
        
        print(f"{Colors.CYAN}🏷️  Categoría automática:{Colors.END} {categoria_auto}")
        print(f"{Colors.YELLOW}⭐ Rating TMDB:{Colors.END} {rating_tmdb}/10")
        print(f"{Colors.GREEN}📊 Temporadas:{Colors.END} {detalles.get('temporada', 1)}")
        print(f"{Colors.GREEN}📊 Episodios:{Colors.END} {detalles.get('episodios', 1)}")
        print(f"{Colors.GREEN}🏆 Destacado:{Colors.END} {'Sí' if destacado else 'No'}")
        print(f"{Colors.ORANGE}🔥 En tendencias:{Colors.END} {'Sí' if tendencias else 'No'}")
        print(f"{Colors.PINK}🆕 Es estreno:{Colors.END} {'Sí' if estreno else 'No'}")
        
        usar_auto = input(f"\n{Colors.CYAN}¿Usar configuración automática? (s/n): {Colors.END}").strip().lower()
        
        if usar_auto == 's':
            detalles['categoria'] = categoria_auto
            detalles['destacado'] = destacado
            detalles['tendencias'] = tendencias
            detalles['estreno'] = estreno
            print_success("Configuración automática aplicada")
        else:
            print_section("CONFIGURACIÓN MANUAL")
            
            categoria = input(f"{Colors.CYAN}Categoría [{categoria_auto}]: {Colors.END}").strip()
            detalles['categoria'] = categoria if categoria else categoria_auto
            
            print(f"\n{Colors.YELLOW}📊 Temporadas actuales: {detalles.get('temporada', 1)}{Colors.END}")
            if input(f"{Colors.CYAN}¿Cambiar? (s/n): {Colors.END}").strip().lower() == 's':
                nueva_temporada = input(f"{Colors.CYAN}Nuevo número: {Colors.END}").strip()
                if nueva_temporada.isdigit():
                    detalles['temporada'] = int(nueva_temporada)
            
            print(f"\n{Colors.YELLOW}📊 Episodios actuales: {detalles.get('episodios', 1)}{Colors.END}")
            if input(f"{Colors.CYAN}¿Cambiar? (s/n): {Colors.END}").strip().lower() == 's':
                nuevo_episodios = input(f"{Colors.CYAN}Nuevo número: {Colors.END}").strip()
                if nuevo_episodios.isdigit():
                    detalles['episodios'] = int(nuevo_episodios)
            
            detalles['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n): {Colors.END}").strip().lower() == 's'
            detalles['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n): {Colors.END}").strip().lower() == 's'
            detalles['estreno'] = input(f"{Colors.CYAN}¿Es estreno? (s/n): {Colors.END}").strip().lower() == 's'
        
        print_section("URL DE REPRODUCCIÓN")
        detalles['url'] = input(f"{Colors.CYAN}URL de la serie (opcional): {Colors.END}").strip()
        
        confirmar = input(f"\n{Colors.GREEN}¿Agregar esta serie? (s/n): {Colors.END}").strip().lower()
        
        if confirmar == 's':
            slug = re.sub(r'[^a-z0-9]+', '-', detalles['titulo'].lower()).strip('-')
            doc_id = f"serie-{slug}-{detalles['tmdb_id']}"
            
            try:
                doc_ref = db.collection('series').document(doc_id)
                detalles['id'] = doc_id
                doc_ref.set(detalles)
                
                print_success(f"Serie '{detalles['titulo']}' agregada exitosamente!")
                print(f"{Colors.CYAN}📁 ID Firestore: {doc_id}{Colors.END}")
                print(f"{Colors.CYAN}🔗 ID TMDB: {detalles['tmdb_id']}{Colors.END}")
                print(f"{Colors.CYAN}📊 Temporadas: {detalles.get('temporada', 1)}{Colors.END}")
                print(f"{Colors.CYAN}📊 Episodios: {detalles.get('episodios', 1)}{Colors.END}")
                
                # Notificar a Telegram
                show_loading("Notificando a Telegram", 1)
                if notificar_telegram(detalles, "serie"):
                    print_success("Notificación enviada a Telegram")
                
                # Agregar episodios automáticamente
                if input(f"\n{Colors.CYAN}¿Agregar episodios desde TMDB? (s/n): {Colors.END}").lower() == 's':
                    show_loading("Descargando episodios con imágenes")
                    total_seasons = detalles.get('temporada', 1)
                    
                    # Estructura para el documento principal (opcional pero ayuda al frontend)
                    temporadas_map = {}
                    
                    for s in range(1, total_seasons + 1):
                        print(f"{Colors.BLUE}   Procesando Temporada {s}...{Colors.END}")
                        s_url = f"{TMDB_BASE_URL}/tv/{detalles['tmdb_id']}/season/{s}"
                        s_resp = requests.get(s_url, headers=TMDB_HEADERS, params={"language": "es-ES"})
                        
                        if s_resp.status_code == 200:
                            s_data = s_resp.json()
                            episodes = s_data.get('episodes', [])
                            
                            batch = db.batch()
                            episodios_dict = {}
                            
                            for ep in episodes:
                                ep_num = ep.get('episode_number')
                                ep_data = {
                                    'titulo': ep.get('name', f'Episodio {ep_num}'),
                                    'url': '',
                                    'temporada': s,
                                    'numero': ep_num,
                                    'sinopsis': ep.get('overview', ''),
                                    'imagen': f"{TMDB_IMAGE_URL}{ep.get('still_path')}" if ep.get('still_path') else detalles['portada']
                                }
                                
                                # Guardar en subcolección (para escalabilidad)
                                ep_ref = doc_ref.collection('temporadas').document(f"s{s}e{ep_num}")
                                batch.set(ep_ref, ep_data)
                                
                                # Guardar en el mapa para el documento principal (lo que espera ver.html actualmente)
                                episodios_dict[f"Episodio {ep_num}"] = ep_data
                            
                            temporadas_map[str(s)] = {'episodios': episodios_dict}
                            batch.commit()
                            print(f"{Colors.GREEN}   ✅ {len(episodes)} episodios guardados con imágenes.{Colors.END}")
                    
                    # Actualizar el documento principal con el mapa de temporadas
                    doc_ref.update({'temporadas': temporadas_map})
                    print_success("Mapa de temporadas actualizado en el documento principal.")
                
            except Exception as e:
                print_error(f"Error al guardar: {str(e)}")
        else:
            print_error("Operación cancelada")

# ============================================
# FUNCIONES RESTANTES CON DISEÑO MEJORADO
# ============================================

def confirmar_agregar(detalles_tmdb):
    """Confirma y completa los datos para agregar"""
    print_section("COMPLETAR INFORMACIÓN")
    
    pelicula = detalles_tmdb.copy()
    
    print(f"\n{Colors.YELLOW}Categorías disponibles:{Colors.END}")
    print(f"{Colors.CYAN}accion, terror, crimen, aventura, suspenso, drama, comedia,")
    print(f"fantasia, ciencia ficcion, animacion, romance, misterio, documental, musical{Colors.END}")
    
    categoria = input(f"\n{Colors.CYAN}Categoría para PelixplushdZ: {Colors.END}").strip().lower()
    pelicula['categoria'] = categoria if categoria else detalles_tmdb['genero_tmdb'].lower()
    
    print_section("URLS DE REPRODUCCIÓN")
    pelicula['url'] = input(f"{Colors.CYAN}URL principal: {Colors.END}").strip()
    pelicula['español'] = input(f"{Colors.CYAN}URL español: {Colors.END}").strip()
    pelicula['latino'] = input(f"{Colors.CYAN}URL latino: {Colors.END}").strip()
    pelicula['subtitulado'] = input(f"{Colors.CYAN}URL subtitulado: {Colors.END}").strip()
    
    rating_personal = input(f"\n{Colors.CYAN}Rating personalizado (1-10) [{detalles_tmdb['rating_tmdb']}]: {Colors.END}").strip()
    if rating_personal:
        pelicula['rating'] = float(rating_personal)
    else:
        pelicula['rating'] = detalles_tmdb['rating_tmdb']
    
    print_section("ETIQUETAS ESPECIALES")
    pelicula['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n): {Colors.END}").strip().lower() == 's'
    pelicula['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n): {Colors.END}").strip().lower() == 's'
    pelicula['estreno'] = input(f"{Colors.CYAN}¿Es estreno? (s/n): {Colors.END}").strip().lower() == 's'
    
    print_section("RESUMEN FINAL")
    campos = ['titulo', 'año', 'categoria', 'rating', 'destacado', 'tendencias']
    for campo in campos:
        print(f"  {Colors.YELLOW}{campo}:{Colors.END} {pelicula.get(campo, 'N/A')}")
    
    confirmar = input(f"\n{Colors.GREEN}¿Agregar esta película? (s/n): {Colors.END}").strip().lower()
    
    if confirmar == 's':
        slug = re.sub(r'[^a-z0-9]+', '-', pelicula['titulo'].lower()).strip('-')
        doc_id = f"{slug}-{pelicula['año']}-{pelicula['tmdb_id']}"
        
        try:
            doc_ref = db.collection('peliculas').document(doc_id)
            doc_ref.set(pelicula)
            
            print_success(f"Película '{pelicula['titulo']}' agregada!")
            print(f"{Colors.CYAN}📁 ID Firestore: {doc_id}{Colors.END}")
            
        except Exception as e:
            print_error(f"Error al guardar: {str(e)}")
    else:
        print_error("Cancelado")

def confirmar_agregar_serie(detalles_tmdb):
    """Confirma y completa los datos para agregar una serie"""
    print_section("COMPLETAR INFORMACIÓN DE SERIE")
    
    serie = detalles_tmdb.copy()
    
    print(f"\n{Colors.YELLOW}Categorías disponibles:{Colors.END}")
    print(f"{Colors.CYAN}accion, terror, crimen, aventura, suspenso, drama, comedia,")
    print(f"fantasia, ciencia ficcion, animacion, romance, misterio, documental{Colors.END}")
    
    categoria = input(f"\n{Colors.CYAN}Categoría [{serie['categoria']}]: {Colors.END}").strip().lower()
    serie['categoria'] = categoria if categoria else serie['categoria']
    
    print(f"\n{Colors.YELLOW}📊 Temporadas actuales: {serie['temporada']}{Colors.END}")
    if input(f"{Colors.CYAN}¿Cambiar? (s/n): {Colors.END}").strip().lower() == 's':
        nueva = input(f"{Colors.CYAN}Nuevo número: {Colors.END}").strip()
        if nueva.isdigit():
            serie['temporada'] = int(nueva)
    
    print(f"\n{Colors.YELLOW}📊 Episodios actuales: {serie['episodios']}{Colors.END}")
    if input(f"{Colors.CYAN}¿Cambiar? (s/n): {Colors.END}").strip().lower() == 's':
        nueva = input(f"{Colors.CYAN}Nuevo número: {Colors.END}").strip()
        if nueva.isdigit():
            serie['episodios'] = int(nueva)
    
    print_section("URL DE REPRODUCCIÓN")
    serie['url'] = input(f"{Colors.CYAN}URL de la serie: {Colors.END}").strip()
    
    rating_personal = input(f"\n{Colors.CYAN}Rating personalizado (1-10) [{serie['rating']}]: {Colors.END}").strip()
    if rating_personal:
        serie['rating'] = float(rating_personal)
    
    print_section("ETIQUETAS ESPECIALES")
    serie['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n): {Colors.END}").strip().lower() == 's'
    serie['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n): {Colors.END}").strip().lower() == 's'
    serie['estreno'] = input(f"{Colors.CYAN}¿Es estreno? (s/n): {Colors.END}").strip().lower() == 's'
    
    print_section("RESUMEN FINAL")
    print(f"{Colors.YELLOW}📺 Título:{Colors.END} {serie['titulo']}")
    print(f"{Colors.BLUE}📅 Año:{Colors.END} {serie['año']}")
    print(f"{Colors.GREEN}📊 Temporadas:{Colors.END} {serie['temporada']}")
    print(f"{Colors.GREEN}📊 Episodios:{Colors.END} {serie['episodios']}")
    print(f"{Colors.PINK}🏷️  Categoría:{Colors.END} {serie['categoria']}")
    print(f"{Colors.YELLOW}⭐ Rating:{Colors.END} {serie['rating']}/10")
    
    confirmar = input(f"\n{Colors.GREEN}¿Agregar esta serie? (s/n): {Colors.END}").strip().lower()
    
    if confirmar == 's':
        slug = re.sub(r'[^a-z0-9]+', '-', serie['titulo'].lower()).strip('-')
        doc_id = f"serie-{slug}-{serie['tmdb_id']}"
        
        try:
            doc_ref = db.collection('series').document(doc_id)
            doc_ref.set(serie)
            
            print_success(f"Serie '{serie['titulo']}' agregada!")
            print(f"{Colors.CYAN}📁 ID Firestore: {doc_id}{Colors.END}")
            
        except Exception as e:
            print_error(f"Error al guardar: {str(e)}")
    else:
        print_error("Cancelado")

def agregar_pelicula_tmdb():
    """Agrega película usando datos de TMDB"""
    print_section("AGREGAR PELÍCULA DESDE TMDB")
    
    print(f"\n{Colors.CYAN}🔍 Buscar película por nombre")
    print(f"{Colors.CYAN}📝 O ingresar ID TMDB directamente{Colors.END}")
    print(f"{Colors.YELLOW}0.{Colors.END} ↩️  Volver al menú")
    
    opcion = input(f"\n{Colors.CYAN}Elige una opción (0 para volver): {Colors.END}").strip()
    
    if opcion == "0":
        return
    
    if opcion.isdigit() and len(opcion) <= 5:
        movie_id = int(opcion)
        detalles = obtener_detalles_tmdb(movie_id)
        
        if not detalles:
            return
            
        mostrar_detalles_tmdb(detalles)
        confirmar_agregar(detalles)
        
    else:
        resultados = buscar_en_tmdb(opcion)
        
        if not resultados:
            return
        
        seleccion = input(f"\n{Colors.CYAN}Selecciona un número (0 para cancelar): {Colors.END}").strip()
        
        if not seleccion.isdigit() or seleccion == "0":
            print_error("Cancelado")
            return
        
        idx = int(seleccion) - 1
        if 0 <= idx < len(resultados):
            movie_id = resultados[idx]["id"]
            detalles = obtener_detalles_tmdb(movie_id)
            
            if detalles:
                mostrar_detalles_tmdb(detalles)
                confirmar_agregar(detalles)
        else:
            print_error("Selección inválida")

def agregar_serie_tmdb():
    """Agrega serie desde TMDB con información completa"""
    print_section("AGREGAR SERIE DESDE TMDB")
    
    print(f"\n{Colors.CYAN}🔍 Buscar serie por nombre")
    print(f"{Colors.CYAN}📝 O ingresar ID TMDB directamente{Colors.END}")
    print(f"{Colors.YELLOW}0.{Colors.END} ↩️  Volver al menú")
    
    opcion = input(f"\n{Colors.CYAN}Elige una opción (0 para volver): {Colors.END}").strip()
    
    if opcion == "0":
        return
    
    if opcion.isdigit() and len(opcion) <= 5:
        tv_id = int(opcion)
        detalles = obtener_detalles_serie_tmdb(tv_id)
        
        if not detalles:
            return
            
        mostrar_detalles_serie_tmdb(detalles)
        confirmar_agregar_serie(detalles)
        
    else:
        resultados = buscar_serie_tmdb(opcion)
        
        if not resultados:
            return
        
        seleccion = input(f"\n{Colors.CYAN}Selecciona un número (0 para cancelar): {Colors.END}").strip()
        
        if not seleccion.isdigit() or seleccion == "0":
            print_error("Cancelado")
            return
        
        idx = int(seleccion) - 1
        if 0 <= idx < len(resultados):
            tv_id = resultados[idx]["id"]
            detalles = obtener_detalles_serie_tmdb(tv_id)
            
            if detalles:
                mostrar_detalles_serie_tmdb(detalles)
                confirmar_agregar_serie(detalles)
        else:
            print_error("Selección inválida")

def agregar_pelicula_manual():
    """Agrega película manualmente (sin TMDB)"""
    print_section("AGREGAR PELÍCULA MANUALMENTE")
    
    pelicula = {}
    pelicula['titulo'] = input(f"{Colors.CYAN}Título: {Colors.END}").strip()
    pelicula['sisposesis'] = input(f"{Colors.CYAN}Descripción: {Colors.END}").strip()
    pelicula['año'] = input(f"{Colors.CYAN}Año: {Colors.END}").strip()
    
    print(f"\n{Colors.YELLOW}Categorías disponibles:{Colors.END}")
    print(f"{Colors.CYAN}accion, terror, crimen, aventura, suspenso, drama, comedia,")
    print(f"fantasia, ciencia ficcion, animacion, romance, misterio, documental, musical{Colors.END}")
    
    pelicula['categoria'] = input(f"\n{Colors.CYAN}Categoría: {Colors.END}").strip().lower()
    
    pelicula['poster'] = input(f"{Colors.CYAN}URL del poster (opcional): {Colors.END}").strip() or 'https://via.placeholder.com/300x450/333333/ffffff?text=No+Image'
    
    print_section("URLS DE REPRODUCCIÓN")
    pelicula['url'] = input(f"{Colors.CYAN}URL principal: {Colors.END}").strip()
    pelicula['español'] = input(f"{Colors.CYAN}URL español: {Colors.END}").strip()
    pelicula['latino'] = input(f"{Colors.CYAN}URL latino: {Colors.END}").strip()
    pelicula['subtitulado'] = input(f"{Colors.CYAN}URL subtitulado: {Colors.END}").strip()
    
    rating = input(f"\n{Colors.CYAN}Rating (1-10): {Colors.END}").strip()
    pelicula['rating'] = float(rating) if rating else 5.0
    
    print_section("ETIQUETAS ESPECIALES")
    pelicula['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n): {Colors.END}").strip().lower() == 's'
    pelicula['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n): {Colors.END}").strip().lower() == 's'
    pelicula['fecha_agregado'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pelicula['tmdb_id'] = None
    
    print_section("RESUMEN")
    for key, value in pelicula.items():
        if value:
            print(f"  {Colors.YELLOW}{key}:{Colors.END} {value}")
    
    confirmar = input(f"\n{Colors.GREEN}¿Agregar esta película? (s/n): {Colors.END}").strip().lower()
    
    if confirmar == 's':
        slug = re.sub(r'[^a-z0-9]+', '-', pelicula['titulo'].lower()).strip('-')
        doc_id = f"{slug}-{pelicula['año']}"
        
        doc_ref = db.collection('peliculas').document(doc_id)
        doc_ref.set(pelicula)
        
        print_success(f"Película '{pelicula['titulo']}' agregada!")
        print(f"{Colors.CYAN}📁 ID: {doc_id}{Colors.END}")
    else:
        print_error("Cancelado")

def agregar_serie_manual():
    """Agrega serie manualmente"""
    print_section("AGREGAR SERIE MANUAL")
    
    serie = {}
    
    serie['titulo'] = input(f"{Colors.CYAN}Título: {Colors.END}").strip()
    
    temporada_input = input(f"{Colors.CYAN}Número de temporadas: {Colors.END}").strip()
    serie['temporada'] = int(temporada_input) if temporada_input.isdigit() else 1
    
    episodios_input = input(f"{Colors.CYAN}Número de episodios: {Colors.END}").strip()
    serie['episodios'] = int(episodios_input) if episodios_input.isdigit() else 1
    
    print(f"\n{Colors.YELLOW}Categorías disponibles:{Colors.END}")
    print(f"{Colors.CYAN}accion, terror, crimen, aventura, suspenso, drama, comedia,")
    print(f"fantasia, ciencia ficcion, animacion, romance, misterio, documental{Colors.END}")
    
    serie['categoria'] = input(f"\n{Colors.CYAN}Categoría: {Colors.END}").strip().lower()
    serie['año'] = input(f"{Colors.CYAN}Año de estreno: {Colors.END}").strip()
    serie['url'] = input(f"{Colors.CYAN}URL de reproducción: {Colors.END}").strip()
    serie['portada'] = input(f"{Colors.CYAN}URL de la portada (opcional): {Colors.END}").strip() or "https://via.placeholder.com/300x450?text=No+Portada"
    serie['sinopsis'] = input(f"{Colors.CYAN}Sinopsis: {Colors.END}").strip()
    
    rating_input = input(f"\n{Colors.CYAN}Rating (1-10): {Colors.END}").strip()
    serie['rating'] = float(rating_input) if rating_input else 0.0
    
    print_section("ETIQUETAS ESPECIALES")
    serie['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n): {Colors.END}").strip().lower() == 's'
    serie['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n): {Colors.END}").strip().lower() == 's'
    serie['estreno'] = input(f"{Colors.CYAN}¿Es estreno? (s/n): {Colors.END}").strip().lower() == 's'
    
    serie['tipo'] = 'serie'
    serie['fecha_agregado'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    serie['tmdb_id'] = None
    
    print_section("RESUMEN DE LA SERIE")
    print(f"{Colors.YELLOW}📺 Título:{Colors.END} {serie['titulo']}")
    print(f"{Colors.GREEN}📊 Temporadas:{Colors.END} {serie['temporada']}")
    print(f"{Colors.GREEN}📊 Episodios:{Colors.END} {serie['episodios']}")
    print(f"{Colors.PINK}🏷️  Categoría:{Colors.END} {serie['categoria']}")
    print(f"{Colors.BLUE}📅 Año:{Colors.END} {serie['año']}")
    
    confirmar = input(f"\n{Colors.GREEN}¿Agregar esta serie? (s/n): {Colors.END}").strip().lower()
    
    if confirmar == 's':
        slug = re.sub(r'[^a-z0-9]+', '-', serie['titulo'].lower()).strip('-')
        doc_id = f"serie-{slug}-{serie.get('año', '')}"
        
        try:
            doc_ref = db.collection('series').document(doc_id)
            doc_ref.set(serie)
            
            print_success(f"Serie '{serie['titulo']}' agregada!")
            print(f"{Colors.CYAN}📁 ID Firestore: {doc_id}{Colors.END}")
            
        except Exception as e:
            print_error(f"Error al guardar: {str(e)}")
    else:
        print_error("Cancelado")

def eliminar_serie():
    """Elimina una serie de la base de datos"""
    print_section("ELIMINAR SERIE")
    
    termino = input(f"{Colors.CYAN}Buscar serie por título: {Colors.END}").strip().lower()
    
    if not termino:
        print_error("Término vacío")
        return
    
    try:
        series_ref = db.collection('series')
        series = list(series_ref.stream())
        
        resultados = []
        for serie in series:
            datos = serie.to_dict()
            titulo = datos.get('titulo', '').lower()
            if termino in titulo:
                resultados.append((serie.id, datos))
        
        if not resultados:
            print_error(f"No se encontraron series para '{termino}'")
            return
        
        print(f"\n{Colors.GREEN}🔍 Resultados: {len(resultados)} series{Colors.END}\n")
        
        for i, (serie_id, datos) in enumerate(resultados, 1):
            print(f"{Colors.CYAN}{i:3d}.{Colors.END} {datos.get('titulo', 'Sin título')}")
            print(f"     {Colors.BLUE}📅 {datos.get('año', 'N/A')} | 🏷️ {datos.get('categoria', 'N/A')}{Colors.END}")
            print(f"     {Colors.GREEN}📊 T:{datos.get('temporada', 'N/A')} | E:{datos.get('episodios', 'N/A')}{Colors.END}")
            print()
        
        seleccion = input(f"{Colors.CYAN}Selecciona el número (0 para cancelar): {Colors.END}").strip()
        
        if not seleccion.isdigit() or seleccion == "0":
            print_error("Cancelado")
            return
        
        idx = int(seleccion) - 1
        if 0 <= idx < len(resultados):
            serie_id, datos = resultados[idx]
            
            print_warning(f"Vas a eliminar: {datos.get('titulo', 'Sin título')}")
            print_warning("Esta acción NO se puede deshacer\n")
            
            confirmar = input(f"{Colors.RED}¿Estás SEGURO? Escribe 'ELIMINAR': {Colors.END}").strip()
            
            if confirmar == 'ELIMINAR':
                doc_ref = db.collection('series').document(serie_id)
                doc_ref.delete()
                print_success(f"Serie '{datos.get('titulo')}' eliminada")
            else:
                print_error("Cancelado")
                
        else:
            print_error("Selección inválida")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def listar_peliculas():
    """Lista todas las películas en la base de datos"""
    print_section("LISTA DE PELÍCULAS")
    
    try:
        peliculas_ref = db.collection('peliculas')
        peliculas = list(peliculas_ref.stream())
        
        if not peliculas:
            print_info("No hay películas en la base de datos")
            return
        
        print(f"\n{Colors.GREEN}🎬 Total: {len(peliculas)} películas{Colors.END}\n")
        
        for i, pelicula in enumerate(peliculas, 1):
            datos = pelicula.to_dict()
            icons = ""
            if datos.get('destacado'):
                icons += f"{Colors.YELLOW}🏆 {Colors.END}"
            if datos.get('tendencias'):
                icons += f"{Colors.RED}🔥 {Colors.END}"
            if datos.get('estreno'):
                icons += f"{Colors.PINK}🆕 {Colors.END}"
            
            origen = f"{Colors.BLUE}🌐 TMDB{Colors.END}" if datos.get('tmdb_id') else f"{Colors.CYAN}📝 Manual{Colors.END}"
            
            print_movie_card(
                datos.get('titulo', 'Sin título'),
                datos.get('año', 'N/A'),
                datos.get('rating', 'N/A'),
                datos.get('categoria', 'N/A'),
                datos.get('destacado', False)
            )
            print(f"     {Colors.CYAN}📁 ID: {pelicula.id} | {origen}{Colors.END}\n")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def listar_series():
    """Lista todas las series en la base de datos"""
    print_section("LISTA DE SERIES")
    
    try:
        series_ref = db.collection('series')
        series = list(series_ref.stream())
        
        if not series:
            print_info("No hay series en la base de datos")
            return
        
        print(f"\n{Colors.GREEN}📺 Total: {len(series)} series{Colors.END}\n")
        
        for i, serie in enumerate(series, 1):
            datos = serie.to_dict()
            icons = ""
            if datos.get('destacado'):
                icons += f"{Colors.YELLOW}🏆 {Colors.END}"
            if datos.get('tendencias'):
                icons += f"{Colors.RED}🔥 {Colors.END}"
            if datos.get('estreno'):
                icons += f"{Colors.PINK}🆕 {Colors.END}"
            
            origen = f"{Colors.BLUE}🌐 TMDB{Colors.END}" if datos.get('tmdb_id') else f"{Colors.CYAN}📝 Manual{Colors.END}"
            
            print_serie_card(
                datos.get('titulo', 'Sin título'),
                datos.get('año', 'N/A'),
                datos.get('temporada', 'N/A'),
                datos.get('episodios', 'N/A'),
                datos.get('categoria', 'N/A'),
                datos.get('destacado', False)
            )
            print(f"     {Colors.CYAN}📁 ID: {serie.id} | {origen}{Colors.END}\n")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def buscar_pelicula_local():
    """Busca películas en la base de datos local"""
    print_section("BUSCAR PELÍCULA LOCAL")
    
    termino = input(f"{Colors.CYAN}Buscar por título o categoría: {Colors.END}").strip().lower()
    
    if not termino:
        print_error("Término vacío")
        return
    
    try:
        peliculas_ref = db.collection('peliculas')
        peliculas = list(peliculas_ref.stream())
        
        resultados = []
        for pelicula in peliculas:
            datos = pelicula.to_dict()
            titulo = datos.get('titulo', '').lower()
            categoria = datos.get('categoria', '').lower()
            
            if termino in titulo or termino in categoria:
                resultados.append((pelicula.id, datos))
        
        if not resultados:
            print_error(f"No se encontraron resultados para '{termino}'")
            return
        
        print(f"\n{Colors.GREEN}🔍 Resultados: {len(resultados)} películas{Colors.END}\n")
        
        for i, (pelicula_id, datos) in enumerate(resultados, 1):
            icons = ""
            if datos.get('destacado'):
                icons += f"{Colors.YELLOW}🏆 {Colors.END}"
            if datos.get('tendencias'):
                icons += f"{Colors.RED}🔥 {Colors.END}"
            if datos.get('estreno'):
                icons += f"{Colors.PINK}🆕 {Colors.END}"
            
            print(f"{Colors.CYAN}{i:3d}.{Colors.END} {icons}{datos.get('titulo', 'Sin título')}")
            print(f"     {Colors.BLUE}📅 {datos.get('año', 'N/A')} | 🏷️ {datos.get('categoria', 'N/A')}{Colors.END}")
            print(f"     {Colors.GREEN}📁 ID: {pelicula_id}{Colors.END}")
            print()
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def buscar_serie_local():
    """Busca series en la base de datos local"""
    print_section("BUSCAR SERIE LOCAL")
    
    termino = input(f"{Colors.CYAN}Buscar por título o categoría: {Colors.END}").strip().lower()
    
    if not termino:
        print_error("Término vacío")
        return
    
    try:
        series_ref = db.collection('series')
        series = list(series_ref.stream())
        
        resultados = []
        for serie in series:
            datos = serie.to_dict()
            titulo = datos.get('titulo', '').lower()
            categoria = datos.get('categoria', '').lower()
            
            if termino in titulo or termino in categoria:
                resultados.append((serie.id, datos))
        
        if not resultados:
            print_error(f"No se encontraron resultados para '{termino}'")
            return
        
        print(f"\n{Colors.GREEN}🔍 Resultados: {len(resultados)} series{Colors.END}\n")
        
        for i, (serie_id, datos) in enumerate(resultados, 1):
            icons = ""
            if datos.get('destacado'):
                icons += f"{Colors.YELLOW}🏆 {Colors.END}"
            if datos.get('tendencias'):
                icons += f"{Colors.RED}🔥 {Colors.END}"
            if datos.get('estreno'):
                icons += f"{Colors.PINK}🆕 {Colors.END}"
            
            print(f"{Colors.PINK}{i:3d}.{Colors.END} {icons}{datos.get('titulo', 'Sin título')}")
            print(f"     {Colors.BLUE}📅 {datos.get('año', 'N/A')} | 🏷️ {datos.get('categoria', 'N/A')}{Colors.END}")
            print(f"     {Colors.GREEN}📊 T:{datos.get('temporada', 'N/A')} | E:{datos.get('episodios', 'N/A')}{Colors.END}")
            print(f"     {Colors.CYAN}📁 ID: {serie_id}{Colors.END}")
            print()
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def editar_pelicula():
    """Edita una película existente"""
    print_section("EDITAR PELÍCULA")
    
    termino = input(f"{Colors.CYAN}Buscar película a editar: {Colors.END}").strip().lower()
    
    if not termino:
        print_error("Término vacío")
        return
    
    try:
        peliculas_ref = db.collection('peliculas')
        peliculas = list(peliculas_ref.stream())
        
        resultados = []
        for pelicula in peliculas:
            datos = pelicula.to_dict()
            titulo = datos.get('titulo', '').lower()
            if termino in titulo:
                resultados.append((pelicula.id, datos))
        
        if not resultados:
            print_error(f"No se encontraron resultados para '{termino}'")
            return
        
        print(f"\n{Colors.GREEN}🔍 Resultados: {len(resultados)} películas{Colors.END}\n")
        
        for i, (pelicula_id, datos) in enumerate(resultados, 1):
            print(f"{Colors.CYAN}{i:3d}.{Colors.END} {datos.get('titulo', 'Sin título')} ({datos.get('año', 'N/A')})")
            print(f"     {Colors.BLUE}🏷️ {datos.get('categoria', 'N/A')} | ⭐ {datos.get('rating', 'N/A')}{Colors.END}")
            print()
        
        seleccion = input(f"{Colors.CYAN}Selecciona el número (0 para cancelar): {Colors.END}").strip()
        
        if not seleccion.isdigit() or seleccion == "0":
            print_error("Cancelado")
            return
        
        idx = int(seleccion) - 1
        if 0 <= idx < len(resultados):
            pelicula_id, datos = resultados[idx]
            
            print(f"\n{Colors.CYAN}✏️  Editando: {datos.get('titulo', 'Sin título')}{Colors.END}")
            print(f"{Colors.PURPLE}{'─'*40}{Colors.END}")
            
            print(f"{Colors.YELLOW}Campos actuales:{Colors.END}")
            for key, value in datos.items():
                if key not in ['fecha_agregado', 'tmdb_id']:
                    print(f"  {Colors.CYAN}{key}:{Colors.END} {value}")
            
            print(f"\n{Colors.CYAN}¿Qué deseas editar?{Colors.END}")
            print(f"{Colors.YELLOW}1.{Colors.END} 📝 Descripción")
            print(f"{Colors.YELLOW}2.{Colors.END} 🏷️  Categoría")
            print(f"{Colors.YELLOW}3.{Colors.END} 🌐 URLs de reproducción")
            print(f"{Colors.YELLOW}4.{Colors.END} ⭐ Rating")
            print(f"{Colors.YELLOW}5.{Colors.END} 🏷️  Etiquetas")
            print(f"{Colors.YELLOW}6.{Colors.END} 📤 Actualizar desde TMDB")
            print(f"{Colors.YELLOW}7.{Colors.END} ❌ Cancelar")
            
            opcion_editar = input(f"\n{Colors.CYAN}Selecciona opción (1-7): {Colors.END}").strip()
            
            if opcion_editar == "1":
                nueva_desc = input(f"{Colors.CYAN}Nueva descripción: {Colors.END}").strip()
                if nueva_desc:
                    datos['sisposesis'] = nueva_desc
            
            elif opcion_editar == "2":
                nueva_cat = input(f"{Colors.CYAN}Nueva categoría: {Colors.END}").strip()
                if nueva_cat:
                    datos['categoria'] = nueva_cat.lower()
            
            elif opcion_editar == "3":
                print_section("NUEVAS URLS")
                datos['url'] = input(f"{Colors.CYAN}URL principal: {Colors.END}").strip() or datos.get('url', '')
                datos['español'] = input(f"{Colors.CYAN}URL español: {Colors.END}").strip() or datos.get('español', '')
                datos['latino'] = input(f"{Colors.CYAN}URL latino: {Colors.END}").strip() or datos.get('latino', '')
                datos['subtitulado'] = input(f"{Colors.CYAN}URL subtitulado: {Colors.END}").strip() or datos.get('subtitulado', '')
            
            elif opcion_editar == "4":
                nuevo_rating = input(f"{Colors.CYAN}Nuevo rating (1-10): {Colors.END}").strip()
                if nuevo_rating:
                    datos['rating'] = float(nuevo_rating)
            
            elif opcion_editar == "5":
                print_section("NUEVAS ETIQUETAS")
                datos['destacado'] = input(f"{Colors.CYAN}¿Destacada? (s/n): {Colors.END}").strip().lower() == 's'
                datos['tendencias'] = input(f"{Colors.CYAN}¿En tendencias? (s/n): {Colors.END}").strip().lower() == 's'
                datos['estreno'] = input(f"{Colors.CYAN}¿Es estreno? (s/n): {Colors.END}").strip().lower() == 's'
            
            elif opcion_editar == "6":
                if datos.get('tmdb_id'):
                    nuevos_datos = obtener_detalles_tmdb(datos['tmdb_id'])
                    if nuevos_datos:
                        campos_personales = ['categoria', 'url', 'español', 'latino', 'subtitulado', 
                                          'destacado', 'tendencias', 'estreno']
                        for campo in campos_personales:
                            if campo in datos:
                                nuevos_datos[campo] = datos[campo]
                        
                        datos = nuevos_datos
                        print_success("Datos actualizados desde TMDB")
                else:
                    print_error("Esta película no tiene ID de TMDB")
            
            elif opcion_editar == "7":
                print_error("Edición cancelada")
                return
            
            else:
                print_error("Opción inválida")
                return
            
            confirmar = input(f"\n{Colors.GREEN}¿Guardar cambios? (s/n): {Colors.END}").strip().lower()
            
            if confirmar == 's':
                doc_ref = db.collection('peliculas').document(pelicula_id)
                doc_ref.set(datos)
                print_success(f"Película '{datos.get('titulo')}' actualizada")
            else:
                print_error("Cambios descartados")
                
        else:
            print_error("Selección inválida")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def eliminar_pelicula():
    """Elimina una película específica"""
    print_section("ELIMINAR PELÍCULA")
    
    termino = input(f"{Colors.CYAN}Buscar película a eliminar: {Colors.END}").strip().lower()
    
    if not termino:
        print_error("Término vacío")
        return
    
    try:
        peliculas_ref = db.collection('peliculas')
        peliculas = list(peliculas_ref.stream())
        
        resultados = []
        for pelicula in peliculas:
            datos = pelicula.to_dict()
            titulo = datos.get('titulo', '').lower()
            if termino in titulo:
                resultados.append((pelicula.id, datos))
        
        if not resultados:
            print_error(f"No se encontraron resultados para '{termino}'")
            return
        
        print(f"\n{Colors.GREEN}🔍 Resultados: {len(resultados)} películas{Colors.END}\n")
        
        for i, (pelicula_id, datos) in enumerate(resultados, 1):
            print(f"{Colors.CYAN}{i:3d}.{Colors.END} {datos.get('titulo', 'Sin título')} ({datos.get('año', 'N/A')})")
            print(f"     {Colors.BLUE}📁 ID: {pelicula_id}{Colors.END}")
            print()
        
        seleccion = input(f"{Colors.CYAN}Selecciona el número (0 para cancelar): {Colors.END}").strip()
        
        if not seleccion.isdigit() or seleccion == "0":
            print_error("Cancelado")
            return
        
        idx = int(seleccion) - 1
        if 0 <= idx < len(resultados):
            pelicula_id, datos = resultados[idx]
            
            print_warning(f"Vas a eliminar: {datos.get('titulo', 'Sin título')}")
            print_warning("Esta acción NO se puede deshacer\n")
            
            confirmar = input(f"{Colors.RED}¿Estás SEGURO? Escribe 'ELIMINAR': {Colors.END}").strip()
            
            if confirmar == 'ELIMINAR':
                doc_ref = db.collection('peliculas').document(pelicula_id)
                doc_ref.delete()
                print_success(f"Película '{datos.get('titulo')}' eliminada")
            else:
                print_error("Cancelado")
                
        else:
            print_error("Selección inválida")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def eliminar_todas_peliculas():
    """Elimina todas las películas (con confirmación)"""
    print_section("ELIMINAR TODAS LAS PELÍCULAS")
    
    print_warning("¡ADVERTENCIA CRÍTICA!")
    print_warning("Esta acción eliminará TODAS las películas de la base de datos")
    print_warning("NO se puede deshacer\n")
    
    try:
        peliculas_ref = db.collection('peliculas')
        peliculas = list(peliculas_ref.stream())
        
        if not peliculas:
            print_info("No hay películas para eliminar")
            return
        
        print(f"{Colors.RED}📊 Total de películas a eliminar: {len(peliculas)}{Colors.END}")
        print(f"\n{Colors.YELLOW}Últimas 5 películas en la base de datos:{Colors.END}")
        for i, pelicula in enumerate(peliculas[-5:], 1):
            datos = pelicula.to_dict()
            print(f"  {Colors.CYAN}{i}.{Colors.END} {datos.get('titulo', 'Sin título')} ({datos.get('año', 'N/A')})")
        
    except Exception as e:
        print_error(f"Error al obtener datos: {str(e)}")
        return
    
    confirmar1 = input(f"\n{Colors.RED}¿Continuar con la eliminación? (si/no): {Colors.END}").strip().lower()
    
    if confirmar1 != 'si':
        print_success("Operación cancelada")
        return
    
    confirmar2 = input(f"{Colors.RED}Escribe 'ELIMINAR-TODO-PERMANENTEMENTE': {Colors.END}").strip()
    
    if confirmar2 != 'ELIMINAR-TODO-PERMANENTEMENTE':
        print_success("Operación cancelada")
        return
    
    try:
        show_loading(f"Eliminando {len(peliculas)} películas", 2)
        
        batch = db.batch()
        for pelicula in peliculas:
            batch.delete(pelicula.reference)
        
        batch.commit()
        
        print_success(f"{len(peliculas)} películas eliminadas")
        print_info("La base de datos ahora está vacía")
        
    except Exception as e:
        print_error(f"Error: {str(e)}")

def verificar_conexion_tmdb():
    """Verifica la conexión con TMDB API"""
    print_section("VERIFICANDO CONEXIÓN TMDB")
    
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/550",
            headers=TMDB_HEADERS,
            params={"language": "es-ES"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Conexión exitosa a TMDB API")
            print(f"{Colors.CYAN}📡 Status: {response.status_code}{Colors.END}")
            print(f"{Colors.GREEN}🎬 Película de prueba: {data.get('title')}{Colors.END}")
            print(f"{Colors.BLUE}📅 Año: {data.get('release_date', '')[:4]}{Colors.END}")
            print(f"{Colors.YELLOW}⭐ Rating: {data.get('vote_average')}/10{Colors.END}")
            print(f"{Colors.PURPLE}🔑 API Key válida: {'9869fa...' + TMDB_API_KEY[-6:]}{Colors.END}")
            
            print(f"\n{Colors.CYAN}🔍 Probando búsqueda...{Colors.END}")
            search_response = requests.get(
                f"{TMDB_BASE_URL}/search/movie",
                headers=TMDB_HEADERS,
                params={"query": "avatar", "language": "es-ES"}
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                print_success("Búsqueda funcionando")
                print(f"{Colors.GREEN}📊 Resultados: {search_data.get('total_results', 0)} películas{Colors.END}")
            else:
                print_error(f"Búsqueda falló: {search_response.status_code}")
                
        else:
            print_error(f"Error de conexión: {response.status_code}")
            
    except Exception as e:
        print_error(f"Error en la conexión: {str(e)}")

def generar_sitemap():
    """Genera un archivo sitemap.xml con todas las películas"""
    print_section("GENERANDO SITEMAP.XML")
    
    base_url = "https://pelixplushdz.netlify.app"
    
    try:
        peliculas_ref = db.collection('peliculas')
        peliculas = list(peliculas_ref.stream())
        
        if not peliculas:
            print_info("No hay películas para generar el sitemap")
            return

        show_loading(f"Procesando {len(peliculas)} películas")
        
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        sitemap_content += f'  <url>\n    <loc>{base_url}/</loc>\n    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
        
        for pelicula in peliculas:
            doc_id = pelicula.id
            sitemap_content += f'  <url>\n    <loc>{base_url}/ver.html?id={doc_id}</loc>\n    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
            
        sitemap_content += '</urlset>'
        
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
            
        print_success(f"sitemap.xml generado con {len(peliculas) + 1} URLs")
        print(f"{Colors.CYAN}📁 Archivo guardado en: {os.path.abspath('sitemap.xml')}{Colors.END}")
        
    except Exception as e:
        print_error(f"Error al generar sitemap: {str(e)}")

def gestionar_codigos_vip():
    """Menú para gestionar usuarios VIP"""
    while True:
        print_section("GESTIÓN DE USUARIOS VIP")
        print(f"{Colors.YELLOW}1.{Colors.END} 📋 Listar usuarios")
        print(f"{Colors.YELLOW}2.{Colors.END} ➕ Agregar usuario")
        print(f"{Colors.YELLOW}3.{Colors.END} 🗑️  Eliminar usuario")
        print(f"{Colors.YELLOW}0.{Colors.END} ↩️  Volver")
        
        opcion = input(f"\n{Colors.CYAN}Selecciona una opción: {Colors.END}").strip()
        
        if opcion == '0':
            break
        elif opcion == '1':
            print_section("USUARIOS VIP REGISTRADOS")
            try:
                docs = db.collection('usuarios').stream()
                count = 0
                for doc in docs:
                    data = doc.to_dict()
                    print(f"{Colors.GREEN}👤 Nombre: {data.get('nombre', 'Desconocido')}{Colors.END}")
                    print(f"{Colors.BLUE}📅 Creado:  {data.get('fecha_creacion', 'N/A')}{Colors.END}")
                    print(f"{Colors.PURPLE}{'─'*20}{Colors.END}")
                    count += 1
                if count == 0:
                    print_info("No hay usuarios VIP registrados.")
            except Exception as e:
                print_error(f"Error: {str(e)}")
        elif opcion == '2':
            nombre = input(f"\n{Colors.CYAN}👤 Ingrese el nombre del nuevo usuario: {Colors.END}").strip()
            
            if nombre:
                try:
                    db.collection('usuarios').add({
                        'nombre': nombre,
                        'activo': True,
                        'fecha_creacion': datetime.now().strftime('%Y-%m-d %H:%M:%S')
                    })
                    print_success(f"Usuario '{nombre}' agregado")
                except Exception as e:
                    print_error(f"Error: {str(e)}")
        elif opcion == '3':
            nombre = input(f"\n{Colors.CYAN}👤 Ingrese el nombre del usuario a eliminar: {Colors.END}").strip()
            if nombre:
                try:
                    docs = db.collection('usuarios').where('nombre', '==', nombre).stream()
                    found = False
                    for doc in docs:
                        doc.reference.delete()
                        found = True
                        print_success(f"Usuario '{nombre}' eliminado")
                    
                    if not found:
                        print_warning("No se encontró ese usuario.")
                except Exception as e:
                    print_error(f"Error: {str(e)}")

def mostrar_menu():
    """Muestra el menú principal con diseño atractivo"""
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}🎬  M E N Ú   P R I N C I P A L  🎬{Colors.END}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}{Colors.BOLD}🚀 OPCIÓN RÁPIDA:{Colors.END} Pega URL de TMDB")
    print(f"{Colors.CYAN}{Colors.BOLD}📦 GESTIÓN DE PELÍCULAS:{Colors.END}")
    print(f"{Colors.YELLOW}1.{Colors.END} 📤 Agregar película (menú completo)")
    print(f"{Colors.YELLOW}2.{Colors.END} 🔍 Buscar en TMDB y agregar")
    print(f"{Colors.YELLOW}3.{Colors.END} 📋 Listar películas locales")
    print(f"{Colors.YELLOW}4.{Colors.END} 🔎 Buscar película local")
    print(f"{Colors.YELLOW}5.{Colors.END} ✏️  Editar película")
    print(f"{Colors.YELLOW}6.{Colors.END} 🗑️  Eliminar película")
    print(f"{Colors.YELLOW}7.{Colors.END} 💥 Eliminar todas las películas")
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}📺 GESTIÓN DE SERIES:{Colors.END}")
    print(f"{Colors.YELLOW}8.{Colors.END} 📺 Agregar Serie (TMDB)")
    print(f"{Colors.YELLOW}9.{Colors.END} 📝 Agregar Serie (Manual)")
    print(f"{Colors.YELLOW}10.{Colors.END} 🗑️  Eliminar Serie")
    print(f"{Colors.YELLOW}11.{Colors.END} 📋 Listar series locales")
    print(f"{Colors.YELLOW}12.{Colors.END} 🔎 Buscar serie local")
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}⚙️  HERRAMIENTAS:{Colors.END}")
    print(f"{Colors.YELLOW}13.{Colors.END} 🌐 Verificar conexión TMDB")
    print(f"{Colors.YELLOW}14.{Colors.END} 🗺️  Generar Sitemap.xml")
    print(f"{Colors.YELLOW}15.{Colors.END} 💎 Gestionar Usuarios VIP")
    
    print(f"\n{Colors.YELLOW}0.{Colors.END} 🚪 Salir")
    print(f"{Colors.PURPLE}{'='*70}{Colors.END}")

def main():
    """Función principal"""
    global db
    db = init_firebase()
    
    if not db:
        print_error("No se pudo conectar a Firebase. Saliendo...")
        return
    
    while True:
        print_header()
        mostrar_menu()
        
        entrada = input(f"\n{Colors.CYAN}{Colors.BOLD}👉 Selecciona opción (0-15) o pega URL de TMDB: {Colors.END}").strip()
        
        # Verificar si es una URL de TMDB
        if 'tmdb' in entrada.lower() or 'themoviedb' in entrada.lower() or (entrada.isdigit() and len(entrada) < 10):
            agregar_desde_url_tmdb()
            input(f"\n{Colors.CYAN}Presiona Enter para continuar...{Colors.END}")
            continue
        
        opcion = entrada
        
        if opcion == '1':
            print_section("AGREGAR PELÍCULA")
            print(f"{Colors.YELLOW}1.{Colors.END} 🔍 Buscar en TMDB")
            print(f"{Colors.YELLOW}2.{Colors.END} 🌐 Pegar URL TMDB")
            print(f"{Colors.YELLOW}3.{Colors.END} 📝 Agregar manualmente")
            print(f"{Colors.YELLOW}4.{Colors.END} ↩️  Volver")
            
            sub_opcion = input(f"\n{Colors.CYAN}Elige opción (1-4): {Colors.END}").strip()
            
            if sub_opcion == '1':
                agregar_pelicula_tmdb()
            elif sub_opcion == '2':
                agregar_desde_url_tmdb()
            elif sub_opcion == '3':
                agregar_pelicula_manual()
            elif sub_opcion == '4':
                continue
            
        elif opcion == '2':
            query = input(f"\n{Colors.CYAN}🔍 Buscar película en TMDB: {Colors.END}").strip()
            if query:
                agregar_pelicula_tmdb()
            
        elif opcion == '3':
            listar_peliculas()
        elif opcion == '4':
            buscar_pelicula_local()
        elif opcion == '5':
            editar_pelicula()
        elif opcion == '6':
            eliminar_pelicula()
        elif opcion == '7':
            eliminar_todas_peliculas()
        elif opcion == '8':
            agregar_serie_tmdb()
        elif opcion == '9':
            agregar_serie_manual()
        elif opcion == '10':
            eliminar_serie()
        elif opcion == '11':
            listar_series()
        elif opcion == '12':
            buscar_serie_local()
        elif opcion == '13':
            verificar_conexion_tmdb()
        elif opcion == '14':
            generar_sitemap()
        elif opcion == '15':
            gestionar_codigos_vip()
        elif opcion == '0':
            print(f"\n{Colors.PURPLE}{'='*60}{Colors.END}")
            print(f"{Colors.CYAN}👋 ¡Hasta pronto! Gracias por usar PelixplushdZ Premium{Colors.END}")
            print(f"{Colors.YELLOW}🎬 Apagando sistema...{Colors.END}")
            print(f"{Colors.PURPLE}{'='*60}{Colors.END}")
            break
        else:
            print_error("Opción inválida. Por favor, selecciona 0-15")
        
        input(f"\n{Colors.CYAN}Presiona Enter para continuar...{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Operación cancelada por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error fatal: {str(e)}{Colors.END}")