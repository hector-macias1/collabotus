import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app.models.models import User, UserSkill
from app.services.skill_service import SkillService

logger = logging.getLogger(__name__)

start_message = """
¡Hola 👋! 
Soy @CollabotusBot, tu asistente para la gestión colaborativa de proyectos.  

**Mis principales funcionalidades son:**  
✅ Registrar y actualizar tus habilidades técnicas.  
✅ Crear y administrar proyectos en grupos.  
✅ Asignar tareas automáticamente según habilidades.  
✅ Seguir el progreso de tareas con notificaciones inteligentes.  
✅ Acceder a planes premium para más beneficios.

**Menú de opciones:**  
▫️ `/registro` → Registrar tus habilidades.  
▫️ `/actualizar_habilidades` → Actualizar tu perfil técnico.  
▫️ `/misproyectos` → Ver proyectos activos.  
▫️ `/premium` → Mejorar a plan premium (creación ilimitada de proyectos).  
▫️ `/ayuda` → Guía de uso y soporte.  

También puedes usar el botón **Menú** (👇) para navegar fácilmente.  

¡Empecemos! ¿Qué deseas hacer? 😊  
"""

help_message = """
📚 **Centro de Ayuda y Comandos Disponibles**  

¡Hola! Soy tu asistente para gestión de proyectos. Aquí tienes una guía rápida:  

🔍 **Comandos principales** (usa con `/comando`):  
▫️ `/registro` → Registra tus habilidades técnicas (solo en chat privado).  
▫️ `/actualizar_habilidades` → Modifica tu perfil técnico.  
▫️ `/misproyectos` → Lista tus proyectos activos.  
▫️ `/premium` → Mejora a plan premium (proyectos ilimitados).  
▫️ `/nuevoproyecto` → Crea un nuevo proyecto (solo en grupos).  
▫️ `/agregartarea` → Añade una tarea a un proyecto.  
▫️ `/actualizartarea` → Cambia estado/fecha de una tarea.  
▫️ `/finalizarproyecto` → Cierra un proyecto (solo administradores).  
▫️ `/ayuda` → Muestra este mensaje.  

⚙️ **Funcionalidades Premium** (con `/premium`):  
- Proyectos ilimitados y equipos sin restricciones.  
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage /start command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id = chat_id,
        text = start_message,
        parse_mode='Markdown'
    )

    await update.message.reply_text(f"El chat ID de este grup es: {chat_id}")

    if not (user := await User.get_or_none(id=user_id)):
        await update.message.reply_text(
            "❗No estás registrado en el sistema. Utiliza el comando /registro para registrarte."
        )
        return
    
async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage /ayuda command"""
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id = chat_id,
        text = help_message,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage all messages"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not (user := await User.get_or_none(id=user_id)):
        await update.message.reply_text(
            "❗No estás registrado en el sistema. Utiliza el comando /registro para registrarte."
        )
        return

    await context.bot.send_message(
        chat_id = chat_id,
        text = '❗Introduce un comando válido'
    )