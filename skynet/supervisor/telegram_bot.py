"""
Skynet Telegram Bot - Mobile notifications and control interface.

Provides commands for monitoring and controlling Skynet sessions via Telegram.
"""

import logging
from typing import Optional, Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logger = logging.getLogger(__name__)


class SkynetBot:
    """Telegram bot for Skynet mobile notifications and control."""

    def __init__(self, token: str, chat_id: str, db: Any):
        """
        Initialize the Skynet Telegram bot.

        Args:
            token: Telegram bot API token
            chat_id: Authorized chat ID for commands
            db: Database interface for session data
        """
        self.token = token
        self.chat_id = str(chat_id)
        self.db = db
        self.application: Optional[Application] = None
        self.notifications_paused = False

    async def start(self) -> None:
        """Initialize the Application, add handlers, and start polling."""
        self.application = Application.builder().token(self.token).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("sessions", self.cmd_sessions))
        self.application.add_handler(CommandHandler("view", self.cmd_view))
        self.application.add_handler(CommandHandler("journal", self.cmd_journal))
        self.application.add_handler(CommandHandler("skills", self.cmd_skills))
        self.application.add_handler(CommandHandler("pause", self.cmd_pause))
        self.application.add_handler(CommandHandler("unmute", self.cmd_unmute))

        # Add message handler for natural language replies
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info("Skynet Telegram bot started")

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Skynet Telegram bot stopped")

    def _is_authorized(self, update: Update) -> bool:
        """
        Check if the chat ID matches the authorized chat.

        Args:
            update: Telegram update object

        Returns:
            True if authorized, False otherwise
        """
        if update.effective_chat is None:
            return False
        return str(update.effective_chat.id) == self.chat_id

    async def cmd_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /start command - welcome message with available commands.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        welcome_message = """Welcome to Skynet Bot!

Available commands:
/status - Show system status and session info
/sessions - List all sessions with status icons
/view <session_id> - View last 5 messages from a session
/journal - Journal feature (coming soon)
/skills - Skills management (coming soon)
/pause - Pause notifications
/unmute - Resume notifications

I'm here to keep you informed about your Claude Code sessions!"""

        await update.message.reply_text(welcome_message)

    async def cmd_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /status command - show sessions count, running count, system health.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        try:
            sessions = self.db.list_sessions() if hasattr(self.db, 'list_sessions') else []
            total_sessions = len(sessions)
            running_sessions = sum(
                1 for s in sessions
                if hasattr(s, 'status') and s.status == 'running'
            )

            notification_status = "paused" if self.notifications_paused else "active"

            status_message = f"""Skynet Status Report

Sessions: {total_sessions} total, {running_sessions} running
Notifications: {notification_status}
System: healthy

Use /sessions to see detailed session list."""

            await update.message.reply_text(status_message)

        except Exception as e:
            logger.error(f"Error in cmd_status: {e}")
            await update.message.reply_text(
                "Skynet status: Error retrieving session data."
            )

    async def cmd_sessions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /sessions command - list sessions with status icons.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        try:
            sessions = self.db.list_sessions() if hasattr(self.db, 'list_sessions') else []

            if not sessions:
                await update.message.reply_text("No sessions found.")
                return

            lines = ["Sessions:\n"]
            for session in sessions[:20]:  # Limit to 20 sessions
                # Determine status icon
                status = getattr(session, 'status', 'unknown')
                if status == 'running':
                    icon = "[RUNNING]"
                elif status == 'completed':
                    icon = "[DONE]"
                elif status == 'error':
                    icon = "[ERROR]"
                else:
                    icon = "[?]"

                session_id = getattr(session, 'session_id', 'unknown')[:8]
                project = getattr(session, 'project_name', 'Unknown')
                lines.append(f"{icon} {session_id} - {project}")

            await update.message.reply_text("\n".join(lines))

        except Exception as e:
            logger.error(f"Error in cmd_sessions: {e}")
            await update.message.reply_text("Error retrieving sessions.")

    async def cmd_view(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /view command - view last 5 messages from a session.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        if not context.args:
            await update.message.reply_text(
                "Usage: /view <session_id>\n\nProvide a session ID to view messages."
            )
            return

        session_id = context.args[0]

        try:
            # Try to get messages from database
            messages = []
            if hasattr(self.db, 'get_session_messages'):
                messages = self.db.get_session_messages(session_id, limit=5)
            elif hasattr(self.db, 'get_messages'):
                messages = self.db.get_messages(session_id, limit=5)

            if not messages:
                await update.message.reply_text(
                    f"No messages found for session {session_id[:8]}..."
                )
                return

            lines = [f"Last 5 messages from {session_id[:8]}...:\n"]
            for msg in messages:
                role = getattr(msg, 'role', 'unknown')
                content = getattr(msg, 'content', str(msg))
                # Truncate long messages
                if len(content) > 200:
                    content = content[:200] + "..."
                lines.append(f"[{role.upper()}] {content}")

            await update.message.reply_text("\n\n".join(lines))

        except Exception as e:
            logger.error(f"Error in cmd_view: {e}")
            await update.message.reply_text(
                f"Error retrieving messages for session {session_id[:8]}..."
            )

    async def cmd_journal(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /journal command - placeholder for journal feature.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        await update.message.reply_text(
            "Journal feature coming soon!\n\n"
            "This will allow you to browse and search your Skynet journal entries."
        )

    async def cmd_skills(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /skills command - placeholder for skills feature.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        await update.message.reply_text(
            "Skills management coming soon!\n\n"
            "This will allow you to view and manage Claude's learned skills."
        )

    async def cmd_pause(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /pause command - pause notifications.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        self.notifications_paused = True
        await update.message.reply_text(
            "Notifications paused.\n\nUse /unmute to resume notifications."
        )

    async def cmd_unmute(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /unmute command - resume notifications.

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            await update.message.reply_text("Unauthorized access.")
            return

        self.notifications_paused = False
        await update.message.reply_text(
            "Notifications resumed.\n\nYou will now receive session updates."
        )

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle natural language messages (non-command text).

        Args:
            update: Telegram update object
            context: Callback context
        """
        if not self._is_authorized(update):
            return

        message_text = update.message.text.lower()

        # Simple natural language processing for common queries
        if "status" in message_text:
            await self.cmd_status(update, context)
        elif "session" in message_text:
            await self.cmd_sessions(update, context)
        elif "help" in message_text:
            await self.cmd_start(update, context)
        else:
            await update.message.reply_text(
                "I didn't understand that. Use /start to see available commands."
            )

    async def send_notification(self, message: str) -> bool:
        """
        Send a proactive notification to the authorized chat.

        Args:
            message: The notification message to send

        Returns:
            True if sent successfully, False otherwise
        """
        if self.notifications_paused:
            logger.debug("Notification skipped (paused): %s", message[:50])
            return False

        if self.application is None:
            logger.warning("Cannot send notification: bot not started")
            return False

        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            logger.info("Notification sent: %s", message[:50])
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
