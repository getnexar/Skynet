import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio(loop_scope="function")

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.list_sessions.return_value = []
    return db

@pytest.mark.asyncio
async def test_status_command():
    from supervisor.telegram_bot import SkynetBot

    bot = SkynetBot("fake_token", "12345", MagicMock())

    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await bot.cmd_status(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Skynet" in call_args or "session" in call_args.lower()
