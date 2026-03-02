from __future__ import annotations

import os
import threading
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .data_manager import SaveData


load_dotenv()

_client_lock = threading.Lock()
_client: Optional[OpenAI] = None


def _get_client(api_key: str | None) -> Optional[OpenAI]:
    global _client
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    with _client_lock:
        if _client is None:
            _client = OpenAI(api_key=key)
        return _client


def _run_in_thread(target: Callable[[], None]) -> None:
    t = threading.Thread(target=target, daemon=True)
    t.start()


def request_game_over_message(
    save_data: SaveData | None,
    score: int,
    reason: str,
    callback: Callable[[str], None],
) -> None:
    def worker() -> None:
        api_key = None
        if save_data is not None:
            api_key = str(save_data.settings_data.get("openai_api_key") or "") or None

        client = _get_client(api_key)
        if client is None:
            text = f"Ты преодолел {score} барьеров. Судьба была не на твоей стороне."
            callback(text)
            return

        base_prompt = (
            "Ты выступаешь как мистический Оракул в игре Flappy Bird-подобной вселенной. "
            "Игрок только что проиграл. Дай короткую (1–2 предложения) атмосферную фразу "
            "на русском языке, без обращения по имени, без смайлов."
        )

        user_prompt = f"Счёт: {score}. Причина смерти: {reason}."

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": base_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=80,
            )
            text = response.choices[0].message.content or ""
            callback(text.strip())
        except Exception:
            fallback = f"Ты дошёл до {score} очков, но путь Оракула ещё не раскрыт."
            callback(fallback)

    _run_in_thread(worker)


def request_oracle_reply(
    save_data: SaveData,
    messages: List[Dict[str, str]],
    callback: Callable[[str], None],
) -> None:
    def worker() -> None:
        api_key = str(save_data.settings_data.get("openai_api_key") or "") or None
        client = _get_client(api_key)
        if client is None:
            callback("Ключ к вратам знаний ещё не активирован.")
            return

        system_prompt = (
            "Ты Оракул техно-мистической вселенной Flappy Bird-подобной игры. "
            "Отвечай кратко, атмосферно и по-делу, на русском языке. "
            "Иногда давай советы по игре или намёки на лор."
        )

        chat_messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        for m in messages:
            role = m.get("role", "user")
            content = str(m.get("content", ""))
            if content:
                chat_messages.append({"role": role, "content": content})

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_messages,
                max_tokens=160,
            )
            text = response.choices[0].message.content or ""
            callback(text.strip())
        except Exception:
            callback("Туман помех скрывает ответ. Попробуй снова позже.")

    _run_in_thread(worker)

