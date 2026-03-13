import firebase_admin
from firebase_admin import credentials, firestore
import requests
import time
from datetime import datetime

# Configuración de Telegram
TELEGRAM_TOKEN = "8558038434:AAGZh740g6MjGmj1h2qAebB-Hij6DexPI0s"
CHAT_ID = "-1003658869096"

# Inicializar Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def notificar_telegram(contenido):
    """Envía la notificación premium al grupo"""
    try:
        titulo = contenido.get('titulo', 'Sin título').upper()
        año = contenido.get('año', 'N/A')
        rating = contenido.get('rating', '0')
        genero = contenido.get('categoria', contenido.get('genero', 'General')).capitalize()
        poster = contenido.get('poster', contenido.get('portada', ''))
        
        # Detección inteligente de idiomas
        idiomas = []
        if contenido.get('latino'): idiomas.append("🇲🇽 Latino")
        if contenido.get('español'): idiomas.append("🇪🇸 Castellano")
        if contenido.get('subtitulado'): idiomas.append("📝 Subtitulado")
        
        str_idiomas = " | ".join(idiomas) if idiomas else "🌐 Disponible"

        mensaje = (
            f"🎬 *¡NUEVO ESTRENO EN CINEMAX+!* 🎬\n\n"
            f"🔥 *{titulo}*\n"
            f"📅 *Año:* {año}\n"
            f"🌟 *Rating:* {rating} / 10\n"
            f"🎭 *Género:* {genero}\n"
            f"🔊 *Idiomas:* {str_idiomas}\n\n"
            f"🍿 Disfruta sin anuncios aquí:\n"
            f"🚀 [VER AHORA EN CINEMAX+](https://pelixplushdz.netlify.app/ver.html?id={contenido.get('id', '')})"
        )

        # Enviar con póster (estilo cartelera)
        if poster:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json={
                "chat_id": CHAT_ID,
                "photo": poster,
                "caption": mensaje,
                "parse_mode": "Markdown"
            })
        print(f"✅ Bot: Publicado '{titulo}' en Telegram.")
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

def iniciar_bot():
    print("🚀 Bot CineMax+ Activado. Vigilando Firebase...")
    
    # Esta bandera evita que el bot publique todo lo viejo al arrancar
    arranque_inicial = True

    def on_snapshot(col_snapshot, changes, read_time):
        nonlocal arranque_inicial
        if arranque_inicial:
            arranque_inicial = False
            print("📊 Historial cargado. Esperando subidas nuevas...")
            return
            
        for change in changes:
            if change.type.name == 'ADDED':
                doc = change.document.to_dict()
                doc['id'] = change.document.id
                notificar_telegram(doc)

    # Escuchar Películas y Series en tiempo real
    db.collection('peliculas').on_snapshot(on_snapshot)
    db.collection('series').on_snapshot(on_snapshot)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    iniciar_bot()
