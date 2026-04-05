from __future__ import annotations

import os
import time
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
DEFAULT_REQUEST_TIMEOUT = int (os.getenv("DEFAULT_REQUEST_TIMEOUT", 20))
MAX_API_RETRIES = int (os.getenv("MAX_API_RETRIES", 2))

CHAT_MODES = ("general", "professor", "college_buddy", "roaster")
IGNORED_MESSAGE_KEYS = {"raw", "is_teaching_mode", "mode"}


def build_login_payload(email: str, password: str) -> dict[str, str]:
    return {
        "email": email.strip(),
        "password": password,
    }


def build_register_payload(username: str, email: str, password: str) -> dict[str, str]:
    return {
        "username": username.strip(),
        "email": email.strip(),
        "password": password,
    }


def build_create_chat_payload(name: str, mode: str) -> dict[str, str]:
    payload: dict[str, str] = {"mode": mode}
    chat_name = name.strip()
    if chat_name:
        payload["name"] = chat_name
    return payload


def build_send_message_payload(content: str) -> dict[str, str]:
    return {"content": content}


def init_state() -> None:
    defaults = {
        "api_base_url": DEFAULT_API_BASE_URL,
        "token": None,
        "user": None,
        "auth_page": "login",
        "current_chat_id": None,
        "chats": [],
        "selected_mode": CHAT_MODES[0],
        "new_chat_name": "",
        "pending_request": None,
        "auth_notice": None,
        "messages_cache": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def set_page(page: str) -> None:
    st.session_state.auth_page = page


def headers() -> dict[str, str]:
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api_url(path: str) -> str:
    base_url = st.session_state.api_base_url.rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def clean_text(value: Any) -> str:
    return str(value).replace("\\n", "\n").strip()


def sanitize_error_message(
    exc: Exception,
    fallback: str = "Something went wrong. Please try again.",
) -> str:
    if isinstance(exc, requests.Timeout):
        return "The request timed out. Please try again in a moment."

    if isinstance(exc, requests.ConnectionError):
        return "Unable to reach the server right now. Please check if the backend is running."

    if isinstance(exc, requests.HTTPError):
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        raw_message = clean_text(exc)

        if status_code == 400:
            return raw_message or "We could not process that request. Please verify your input and try again."
        if status_code == 401:
            return "Your session has expired. Please sign in again."
        if status_code == 403:
            return "You do not have permission to perform this action."
        if status_code == 404:
            return "The requested resource was not found."
        if status_code == 408:
            return "The request timed out. Please try again."
        if status_code == 429:
            return "Too many requests in a short time. Please wait a bit and try again."
        if status_code is not None and status_code >= 500:
            return "Server error while processing your request. Please try again shortly."

        return raw_message or fallback

    message = clean_text(exc)
    return message or fallback


def show_error(exc: Exception, fallback: str) -> None:
    st.error(sanitize_error_message(exc, fallback))


def is_unauthorized_error(exc: Exception) -> bool:
    return isinstance(exc, requests.HTTPError) and getattr(getattr(exc, "response", None), "status_code", None) == 401


def redirect_to_login(message: str | None = None) -> None:
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.chats = []
    st.session_state.messages_cache = {}
    st.session_state.auth_page = "login"
    if message:
        st.session_state.auth_notice = message


def render_message_content(content: Any) -> None:
    if isinstance(content, dict):
        for key, value in content.items():
            if key in IGNORED_MESSAGE_KEYS or value is None:
                continue
            rendered_value = clean_text(value)
            if not rendered_value:
                continue
            heading = key.replace("_", " ").title()
            st.markdown(f"### {heading}")
            st.markdown(rendered_value)
        return

    st.markdown(clean_text(content))


def api_request(method: str, path: str, payload: dict[str, Any] | None = None, auth: bool = False) -> Any:
    request_headers = {"Content-Type": "application/json"}
    if auth:
        request_headers.update(headers())

    response = None
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            response = requests.request(
                method=method,
                url=api_url(path),
                json=payload,
                headers=request_headers,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
            break
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == MAX_API_RETRIES:
                raise requests.HTTPError(
                    "We are facing some problems on our side. Please retry in a few seconds."
                ) from exc
            time.sleep(0.8 * attempt)

    if response is None:
        raise requests.HTTPError("No response from backend.")

    if response.ok:
        if response.content:
            return response.json()
        return None

    try:
        detail = response.json().get("detail")
    except Exception:
        detail = response.text or f"Request failed with status {response.status_code}"
    raise requests.HTTPError(detail, response=response)


def login_user(email: str, password: str) -> None:
    payload = build_login_payload(email, password)
    data = api_request("POST", "/auth/login", payload)
    st.session_state.token = data["access_token"]
    st.session_state.user = {"email": email}
    st.session_state.current_chat_id = None
    st.session_state.chats = []
    st.session_state.messages_cache = {}
    st.session_state.auth_notice = None
    set_page("chat")
    st.rerun()


def register_user(username: str, email: str, password: str) -> None:
    payload = build_register_payload(username, email, password)
    data = api_request("POST", "/auth/register", payload)
    st.session_state.user = data
    set_page("login")
    st.success("Account created. You can log in now.")


def load_chats() -> list[dict[str, Any]]:
    chats = api_request("GET", "/chats/all", auth=True)
    st.session_state.chats = chats
    if chats and st.session_state.current_chat_id not in {chat["id"] for chat in chats}:
        st.session_state.current_chat_id = chats[0]["id"]
    if not chats:
        st.session_state.current_chat_id = None
    return chats


def get_or_load_chats() -> list[dict[str, Any]]:
    cached_chats = st.session_state.get("chats") or []
    if cached_chats:
        return cached_chats
    return load_chats()


def create_chat(name: str, mode: str) -> None:
    payload = build_create_chat_payload(name, mode)
    chat = api_request("POST", "/chats/create", payload, auth=True)
    st.session_state.current_chat_id = chat["id"]
    st.session_state.messages_cache[str(chat["id"])] = []
    load_chats()
    st.rerun()


def load_messages(chat_id: str) -> list[dict[str, Any]]:
    return api_request("GET", f"/chats/{chat_id}/messages", auth=True)


def get_or_load_messages(chat_id: str) -> list[dict[str, Any]]:
    cache_key = str(chat_id)
    messages_cache = st.session_state.messages_cache
    if cache_key not in messages_cache:
        messages_cache[cache_key] = load_messages(chat_id)
    return messages_cache[cache_key]


def send_message(chat_id: str, content: str) -> Any:
    payload = build_send_message_payload(content)
    return api_request("POST", f"/chats/{chat_id}/send", payload, auth=True)


def normalize_assistant_content(send_response: Any) -> Any:
    """Normalize /send response shapes to assistant message content when possible."""
    if send_response is None:
        return None

    if isinstance(send_response, dict):
        # Fallback path may return a message object with 'content'.
        if "content" in send_response:
            return send_response.get("content")

        # Parsed response path returns a structured payload directly.
        return send_response

    if isinstance(send_response, str):
        return send_response

    return None


def delete_chat(chat_id: str) -> None:
    api_request("DELETE", f"/chats/{chat_id}/delete", auth=True)
    st.session_state.messages_cache.pop(str(chat_id), None)
    st.session_state.current_chat_id = None
    load_chats()
    st.rerun()


def logout() -> None:
    for key in (
        "token",
        "user",
        "current_chat_id",
        "chats",
        "pending_request",
        "auth_notice",
        "messages_cache",
    ):
        st.session_state.pop(key, None)
    init_state()
    st.rerun()


def render_api_controls() -> None:
    with st.sidebar:
        if st.session_state.get("token"):
            user = st.session_state.get("user") or {}
            st.caption(f"Signed in as {user.get('username') or user.get('email', 'user')}")
            if st.button("Logout", use_container_width=True):
                logout()


def render_auth_page() -> None:
    st.title("Code Buddy")
    st.caption("Sign in to continue or create a new account.")

    auth_notice = st.session_state.get("auth_notice")
    if auth_notice:
        st.warning(auth_notice)
        st.session_state.auth_notice = None

    if st.session_state.auth_page == "login":
        st.subheader("Login")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                try:
                    login_user(email.strip(), password)
                except Exception as exc:
                    show_error(exc, "Login failed. Please check your credentials and try again.")

        if st.button("Need an account? Register", use_container_width=True):
            set_page("register")
            st.rerun()

    else:
        st.subheader("Register")
        with st.form("register_form", clear_on_submit=False):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password", help="8 to 10 characters")
            submitted = st.form_submit_button("Create account", use_container_width=True)
            if submitted:
                try:
                    register_user(username.strip(), email.strip(), password)
                except Exception as exc:
                    show_error(exc, "Registration failed. Please review your details and try again.")

        if st.button("Already have an account? Login", use_container_width=True):
            set_page("login")
            st.rerun()


def render_sidebar_chat_bar(chats: list[dict[str, Any]]) -> None:
    with st.sidebar.expander("Chats", expanded=True):
        with st.form("new_chat_form", clear_on_submit=True):
            st.text_input("Chat name", key="new_chat_name")
            st.selectbox(
                "Mode",
                options=list(CHAT_MODES),
                key="selected_mode",
            )
            create_pressed = st.form_submit_button("New chat", use_container_width=True)
            if create_pressed:
                try:
                    create_chat(
                        st.session_state.new_chat_name,
                        st.session_state.selected_mode,
                    )
                except Exception as exc:
                    if is_unauthorized_error(exc):
                        redirect_to_login("Your session expired. Please log in again.")
                        st.rerun()
                    show_error(exc, "Unable to create a new chat right now. Please try again.")

        st.divider()
        if not chats:
            st.info("No chats yet. Create one above.")
            return

        for chat in chats:
            is_active = chat["id"] == st.session_state.current_chat_id
            label = f"{'▶ ' if is_active else ''}{chat['name']}"
            if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                st.session_state.current_chat_id = chat["id"]
                get_or_load_messages(chat["id"])
                st.rerun()


def process_pending_request() -> None:
    pending_request = st.session_state.get("pending_request")
    if not pending_request:
        return

    chat_id = pending_request.get("chat_id")
    content = pending_request.get("content")
    if not chat_id or not content:
        st.session_state.pending_request = None
        return

    st.session_state.current_chat_id = chat_id
    cache_key = str(chat_id)
    messages_cache = st.session_state.messages_cache
    chat_messages = messages_cache.setdefault(cache_key, [])

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                send_response = send_message(chat_id, content)
            except Exception as exc:
                if is_unauthorized_error(exc):
                    if pending_request.get("user_added") and chat_messages:
                        chat_messages.pop()
                    redirect_to_login("Your session expired. Please log in again.")
                    st.rerun()

                if pending_request.get("user_added") and chat_messages:
                    chat_messages.pop()
                st.session_state.pending_request = None
                show_error(exc, "Unable to send your message right now. Please try again.")
                return

    assistant_content = normalize_assistant_content(send_response)
    if assistant_content is not None:
        chat_messages.append({"sender": "assistant", "content": assistant_content})
        render_message_content(assistant_content)

    st.session_state.pending_request = None


def render_chat_view() -> None:
    try:
        chats = get_or_load_chats()
    except Exception as exc:
        if is_unauthorized_error(exc):
            redirect_to_login("Your session expired. Please log in again.")
            st.rerun()
        show_error(exc, "Unable to load chats right now. Please refresh and try again.")
        return

    render_sidebar_chat_bar(chats)

    st.title("Chat")
    st.caption("A minimal ChatGPT-style workspace backed by your FastAPI app.")

    if not st.session_state.current_chat_id:
        st.info("Select an existing chat from the sidebar or create a new one.")
        return

    current_chat = next(
        (chat for chat in chats if chat["id"] == st.session_state.current_chat_id),
        None,
    )

    if current_chat:
        col_left, col_right = st.columns([4, 1])
        with col_left:
            st.subheader(current_chat["name"])
            st.caption(f"Mode: {current_chat['mode']}")
        with col_right:
            if st.button("Delete chat", use_container_width=True):
                try:
                    delete_chat(current_chat["id"])
                except Exception as exc:
                    if is_unauthorized_error(exc):
                        redirect_to_login("Your session expired. Please log in again.")
                        st.rerun()
                    show_error(exc, "Unable to delete this chat right now. Please try again.")
                    return

    try:
        messages = get_or_load_messages(st.session_state.current_chat_id)
    except Exception as exc:
        if is_unauthorized_error(exc):
            redirect_to_login("Your session expired. Please log in again.")
            st.rerun()
        show_error(exc, "Unable to load messages right now. Please try again.")
        return

    pending_request = st.session_state.get("pending_request")
    if (
        pending_request
        and pending_request.get("chat_id") == st.session_state.current_chat_id
        and not pending_request.get("user_added")
    ):
        messages.append({"sender": "user", "content": pending_request.get("content", "")})
        pending_request["user_added"] = True
        st.session_state.pending_request = pending_request

    for message in messages:
        role = "assistant" if message["sender"] == "assistant" else "user"
        with st.chat_message(role):
            render_message_content(message["content"])

    if pending_request and pending_request.get("chat_id") == st.session_state.current_chat_id:
        process_pending_request()

    prompt = st.chat_input("Type a message")
    if prompt:
        st.session_state.pending_request = {
            "chat_id": st.session_state.current_chat_id,
            "content": prompt,
            "user_added": False,
        }
        st.rerun()


def main() -> None:
    init_state()
    st.set_page_config(page_title="Code Buddy", page_icon="💬", layout="wide")
    render_api_controls()

    if not st.session_state.get("token"):
        render_auth_page()
        return

    render_chat_view()


if __name__ == "__main__":
    main()