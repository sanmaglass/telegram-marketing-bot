import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from ai_engine import analyze_product, generate_marketing_content, generate_marketing_image, parse_angles

load_dotenv()

# Health Check for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Enable logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos from the user."""
    user = update.effective_user
    await update.message.reply_text(f"¡Hola {user.first_name}! He recibido la foto. Analizando tu producto para crear 5 anuncios profesionales... 🚀")
    
    # Get the highest resolution photo
    photo_file = await update.message.photo[-1].get_file()
    image_path = "input_product.jpg"
    await photo_file.download_to_drive(image_path)
    
    try:
        # 1. Analyze with Gemini
        description = analyze_product(image_path)
        
        # 2. Generate 5 marketing angles
        await update.message.reply_text("Pensando en los mejores ángulos de venta... 💡")
        marketing_content = generate_marketing_content(description)
        angles = parse_angles(marketing_content)
        
        if not angles:
            await update.message.reply_text("Hubo un problema generando los anuncios. Por favor intenta de nuevo.")
            return

        # 3. Generate and send images for each angle
        await update.message.reply_text(f"Generando 5 imágenes en HD con el modelo Flux. Esto puede tardar unos segundos... 📸")
        
        for i, angle in enumerate(angles):
            name = angle.get('name', 'Anuncio')
            copy = angle.get('copy', 'Sin texto')
            prompt = angle.get('image_prompt', '')
            
            # Message progress
            await update.message.reply_text(f"🎨 Generando {name}...")
            
            image_fn = generate_marketing_image(prompt, i)
            
            if image_fn:
                with open(image_fn, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=f"📝 *{name}*\n\n{copy}",
                        parse_mode='Markdown'
                    )
                # Cleanup
                if os.path.exists(image_fn):
                    os.remove(image_fn)
            else:
                await update.message.reply_text(f"No pude generar la imagen para: {name}\n\n{copy}")

        await update.message.reply_text("¡Listo! Aquí tienes tus 5 anuncios profesionales. ¿Qué te parecen? 😊")

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Lo siento, ocurrió un error procesando tu imagen. Asegúrate de que las llaves API en el archivo .env sean correctas.")
    
    finally:
        # Cleanup input image
        if os.path.exists(image_path):
            os.remove(image_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /start handler."""
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

from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# ... (rest of the imports and functions remain the same) ...

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        token = token.strip()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key.strip()
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    if not token:
        logging.error("No se encontró TELEGRAM_BOT_TOKEN en el archivo .env")
        return


    # Start Flask in a background thread
    logging.info("Iniciando servidor de Health Check...")
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(token).build()
    
    # Handlers - Use CommandHandler for better reliability
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logging.info("Bot iniciado y escuchando... 🚀")
    
    # run_polling matches the standard way to run the bot
    # We use it inside main() which is called by asyncio.run()
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        logging.info("Polling iniciado correctamente.")
        # Keep it alive
        while True:
            await asyncio.sleep(10)

if __name__ == '__main__':
    try:
        logging.info("Arrancando aplicación con asyncio.run()...")
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.critical(f"Error fatal al arrancar: {e}")


