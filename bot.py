import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from dotenv import load_dotenv
from ai_engine import analyze_product, generate_marketing_content, generate_marketing_image, parse_angles, configure_ai

load_dotenv()

# Health Check for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"Flask arrancando en puerto {port}...")
    app.run(host='0.0.0.0', port=port)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /start handler."""
    logging.info(f"Comando /start recibido de {update.effective_user.first_name}")
    await update.message.reply_text(
        "¡Bienvenido al Bot de Marketing Pro! 🤖📈\n\n"
        "Envíame la foto de tu producto y yo crearé 5 anuncios profesionales con textos persuasivos e imágenes en HD utilizando IA avanzada.\n\n"
        "Ángulos que atacamos:\n"
        "1. Deseo/Aspiración\n"
        "2. Conexión emocional\n"
        "3. Urgencia/Escasez\n"
        "4. Prueba social\n"
        "5. Beneficio Racional"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos from the user."""
    user = update.effective_user
    logging.info(f"Foto recibida de {user.first_name}")
    await update.message.reply_text(f"¡Hola {user.first_name}! He recibido la foto. Analizando tu producto para crear 5 anuncios profesionales... 🚀")
    
    photo_file = await update.message.photo[-1].get_file()
    image_path = "input_product.jpg"
    await photo_file.download_to_drive(image_path)
    
    try:
        description = analyze_product(image_path)
        await update.message.reply_text("Pensando en los mejores ángulos de venta... 💡")
        marketing_content = generate_marketing_content(description)
        angles = parse_angles(marketing_content)
        
        if not angles:
            await update.message.reply_text("Hubo un problema generando los anuncios. Por favor intenta de nuevo.")
            return

        await update.message.reply_text(f"Generando 5 imágenes en HD con el modelo Flux. Esto puede tardar unos segundos... 📸")
        
        for i, angle in enumerate(angles):
            name = angle.get('name', 'Anuncio')
            copy = angle.get('copy', 'Sin texto')
            prompt = angle.get('image_prompt', '')
            
            await update.message.reply_text(f"🎨 Generando {name}...")
            image_fn = generate_marketing_image(prompt, i)
            
            if image_fn:
                with open(image_fn, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=f"📝 *{name}*\n\n{copy}",
                        parse_mode='Markdown'
                    )
                if os.path.exists(image_fn):
                    os.remove(image_fn)
            else:
                await update.message.reply_text(f"No pude generar la imagen para: {name}\n\n{copy}")

        await update.message.reply_text("¡Listo! Aquí tienes tus 5 anuncios profesionales. ¿Qué te parecen? 😊")

    except Exception as e:
        logging.error(f"Error procesando imagen: {e}")
        await update.message.reply_text("Lo siento, ocurrió un error procesando tu imagen. Revisa los logs en Render para más detalles.")
    
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        token = token.strip()
    
    # Configure AI once at startup
    configure_ai()

    if not token:
        logging.error("No se encontró TELEGRAM_BOT_TOKEN")
    else:
        # Start Flask in background
        threading.Thread(target=run_flask, daemon=True).start()
        
        # Standard run_polling call (it handles its own loop and signals)
        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        logging.info("Bot arrancando via run_polling... 🚀")
        application.run_polling()
