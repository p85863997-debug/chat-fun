# app.py
# Final corrected ChatFlow single-file app (defensive user checks + fixes)

import streamlit as st
import sqlite3
import hashlib
import datetime
import json
import base64
import os
from typing import Dict, List, Optional
import uuid
from PIL import Image
import io
from dataclasses import dataclass, field
from enum import Enum
import re

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="ChatFlow - Modern Messaging",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------
# CSS (keeps UI pleasant)
# -------------------------
def load_css():
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .chat-message { padding: 12px 16px; margin: 8px 0; border-radius: 18px; max-width: 70%; word-wrap: break-word; position: relative; display: block; }
    .chat-message.sent { background: linear-gradient(135deg,#007bff,#0056b3); color: white; margin-left: auto; border-bottom-right-radius: 6px; }
    .chat-message.received { background: #f8f9fa; color: #333; border: 1px solid #e9ecef; border-bottom-left-radius: 6px; }
    .chat-message.disappearing { background: linear-gradient(135deg,#ff6b6b,#ee5a52); color: white; }
    .message-meta { font-size: 11px; opacity: 0.75; margin-top: 6px; display: flex; gap: 8px; align-items:center; }
    .chat-container { height: 520px; overflow-y: auto; padding: 16px; background: linear-gradient(to bottom,#f8f9fa,#ffffff); border-radius: 12px; border:1px solid #e9ecef; }
    .message-reactions { display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
    .reaction { background: rgba(0,123,255,0.08); border:1px solid rgba(0,123,255,0.12); border-radius:12px; padding:2px 6px; font-size:12px; }
    </style>
    """,
        unsafe_allow_html=True,
    )

# -------------------------
# Enums & dataclasses
# -------------------------
class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"
    VIDEO = "video"


class MessageStatus(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    avatar: Optional[str] = None
    bio: str = ""
    is_online: bool = False
    last_seen: Optional[str] = None  # ISO string
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


@dataclass
class Message:
    id: str
    chat_id: str
    sender_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    status: MessageStatus = MessageStatus.SENT
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    edited_at: Optional[str] = None
    is_deleted: bool = False
    disappear_at: Optional[str] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)
    reply_to: Optional[str] = None


@dataclass
class Chat:
    id: str
    name: str
    is_group: bool = False
    participants: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    last_message_at: Optional[str] = None
    is_secret: bool = False


# -------------------------
# Database Manager
# -------------------------
class DatabaseManager:
    def __init__(self, db_name: str = "chatflow.db"):
        self.db_name = db_name
        self.init_db()

    def get_conn(self):
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_conn()
        cursor = conn.cursor()
        # Users
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                avatar TEXT,
                bio TEXT DEFAULT '',
                is_online INTEGER DEFAULT 0,
                last_seen TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        # Chats
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                is_group INTEGER DEFAULT 0,
                created_by TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                last_message_at TEXT,
                is_secret INTEGER DEFAULT 0
            )
            """
        )
        # Participants
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_participants (
                chat_id TEXT,
                user_id TEXT,
                is_admin INTEGER DEFAULT 0,
                joined_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (chat_id, user_id)
            )
            """
        )
        # Messages
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                status TEXT DEFAULT 'sent',
                created_at TEXT DEFAULT (datetime('now')),
                edited_at TEXT,
                is_deleted INTEGER DEFAULT 0,
                disappear_at TEXT,
                reactions TEXT,
                reply_to TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    # -- Users
    def create_user(self, user: User) -> bool:
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, avatar, bio, is_online, last_seen, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.username,
                    user.email,
                    user.password_hash,
                    user.avatar,
                    user.bio,
                    int(user.is_online),
                    user.last_seen,
                    user.created_at,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception:
            return False

    def get_user_by_username(self, username: str) -> Optional[User]:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                avatar=row["avatar"],
                bio=row["bio"] or "",
                is_online=bool(row["is_online"]),
                last_seen=row["last_seen"],
                created_at=row["created_at"],
            )
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                avatar=row["avatar"],
                bio=row["bio"] or "",
                is_online=bool(row["is_online"]),
                last_seen=row["last_seen"],
                created_at=row["created_at"],
            )
        return None

    def update_user_status(self, user_id: str, is_online: bool):
        conn = self.get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.utcnow().isoformat()
        cursor.execute(
            "UPDATE users SET is_online = ?, last_seen = ? WHERE id = ?",
            (int(is_online), now, user_id),
        )
        conn.commit()
        conn.close()

    # -- Chats
    def create_chat(self, chat: Chat, participants: List[str]) -> bool:
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chats (id, name, is_group, created_by, created_at, is_secret)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat.id, chat.name, int(chat.is_group), chat.created_by, chat.created_at, int(chat.is_secret)),
            )
            for participant in participants:
                is_admin = 1 if (chat.is_group and participant == chat.created_by) else 0
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO chat_participants (chat_id, user_id, is_admin)
                    VALUES (?, ?, ?)
                    """,
                    (chat.id, participant, is_admin),
                )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_user_chats(self, user_id: str) -> List[Dict]:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id, c.name, c.is_group, c.created_by, c.created_at, c.last_message_at, c.is_secret,
                   (SELECT COUNT(*) FROM chat_participants cp WHERE cp.chat_id = c.id) as participant_count,
                   (SELECT m.content FROM messages m WHERE m.chat_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message
            FROM chats c
            JOIN chat_participants cp ON c.id = cp.chat_id
            WHERE cp.user_id = ?
            ORDER BY c.last_message_at DESC, c.created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        chats = []
        for row in rows:
            chats.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "is_group": bool(row["is_group"]),
                    "created_by": row["created_by"],
                    "created_at": row["created_at"],
                    "last_message_at": row["last_message_at"],
                    "is_secret": bool(row["is_secret"]),
                    "participant_count": row["participant_count"],
                    "last_message": row["last_message"],
                }
            )
        return chats

    def get_direct_chat_between(self, user1: str, user2: str) -> Optional[Dict]:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id, c.name, c.is_group, c.created_by, c.created_at, c.last_message_at, c.is_secret
            FROM chats c
            WHERE c.is_group = 0
            AND c.id IN (
                SELECT cp1.chat_id FROM chat_participants cp1
                WHERE cp1.user_id = ?
                AND cp1.chat_id IN (
                    SELECT cp2.chat_id FROM chat_participants cp2
                    WHERE cp2.user_id = ?
                )
            )
            LIMIT 1
            """,
            (user1, user2),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "is_group": bool(row["is_group"]),
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "last_message_at": row["last_message_at"],
                "is_secret": bool(row["is_secret"]),
            }
        return None

    # -- Messages
    def send_message(self, message: Message) -> bool:
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (id, chat_id, sender_id, content, message_type, status, created_at,
                                      edited_at, is_deleted, disappear_at, reactions, reply_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.chat_id,
                    message.sender_id,
                    message.content,
                    message.message_type.value,
                    message.status.value,
                    message.created_at,
                    message.edited_at,
                    int(message.is_deleted),
                    message.disappear_at,
                    json.dumps(message.reactions) if message.reactions else None,
                    message.reply_to,
                ),
            )
            # update last_message_at
            cursor.execute("UPDATE chats SET last_message_at = ? WHERE id = ?", (message.created_at, message.chat_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def update_message_reactions(self, message_id: str, reactions: Dict[str, List[str]]) -> bool:
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE messages SET reactions = ? WHERE id = ?", (json.dumps(reactions), message_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def edit_message(self, message_id: str, new_content: str) -> bool:
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            now = datetime.datetime.utcnow().isoformat()
            cursor.execute("UPDATE messages SET content = ?, edited_at = ? WHERE id = ?", (new_content, now, message_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_message(self, message_id: str) -> bool:
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE messages SET is_deleted = 1 WHERE id = ?", (message_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_chat_messages(self, chat_id: str, limit: int = 200) -> List[Dict]:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.*, u.username as sender_username, u.avatar as sender_avatar
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.chat_id = ? AND m.is_deleted = 0
            ORDER BY m.created_at ASC
            LIMIT ?
            """,
            (chat_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        messages = []
        now = datetime.datetime.utcnow()
        for row in rows:
            disappear_at = row["disappear_at"]
            # skip messages whose disappear_at is in the past
            if disappear_at:
                try:
                    da = datetime.datetime.fromisoformat(disappear_at)
                    if da <= now:
                        continue
                except Exception:
                    # if can't parse, ignore the disappear filter
                    pass
            reactions = {}
            if row["reactions"]:
                try:
                    reactions = json.loads(row["reactions"])
                except Exception:
                    reactions = {}
            messages.append(
                {
                    "id": row["id"],
                    "chat_id": row["chat_id"],
                    "sender_id": row["sender_id"],
                    "content": row["content"],
                    "message_type": row["message_type"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "edited_at": row["edited_at"],
                    "is_deleted": bool(row["is_deleted"]),
                    "disappear_at": row["disappear_at"],
                    "reactions": reactions,
                    "reply_to": row["reply_to"],
                    "sender_username": row["sender_username"],
                    "sender_avatar": row["sender_avatar"],
                }
            )
        return messages

    # -- Search users
    def search_users(self, query: str, current_user_id: str, limit: int = 20) -> List[Dict]:
        conn = self.get_conn()
        cursor = conn.cursor()
        likeq = f"%{query}%"
        cursor.execute(
            """
            SELECT id, username, email, avatar, bio, is_online, last_seen
            FROM users
            WHERE (username LIKE ? OR email LIKE ?) AND id != ?
            LIMIT ?
            """,
            (likeq, likeq, current_user_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        users = []
        for row in rows:
            users.append(
                {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "avatar": row["avatar"],
                    "bio": row["bio"] or "",
                    "is_online": bool(row["is_online"]),
                    "last_seen": row["last_seen"],
                }
            )
        return users


# -------------------------
# File Manager
# -------------------------
class FileManager:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.ensure_upload_dir()

    def ensure_upload_dir(self):
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_uploaded_file(self, uploaded_file, user_id: str) -> Optional[str]:
        """
        - Images → returns data:image/png;base64,... (embedded)
        - Other files → saved under uploads/, returns file path
        """
        try:
            raw = uploaded_file.read()
            filename = uploaded_file.name
            file_ext = filename.split(".")[-1].lower() if "." in filename else ""
            if file_ext in ("png", "jpg", "jpeg", "gif", "webp"):
                # Convert to PNG base64 for safety
                image = Image.open(io.BytesIO(raw)).convert("RGBA")
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()
                return f"data:image/png;base64,{img_b64}"
            else:
                file_id = str(uuid.uuid4())
                safe_name = f"{file_id}_{user_id}_{filename}"
                path = os.path.join(self.upload_dir, safe_name)
                with open(path, "wb") as f:
                    f.write(raw)
                return path
        except Exception as e:
            st.error(f"Failed to save uploaded file: {e}")
            return None

    def save_image_as_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"


# -------------------------
# Auth Manager
# -------------------------
class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return AuthManager.hash_password(password) == password_hash


# -------------------------
# Chat Manager (helper)
# -------------------------
class ChatManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_direct_chat(self, user1_id: str, user2_id: str) -> Optional[str]:
        # Check if exists
        ex = self.db.get_direct_chat_between(user1_id, user2_id)
        if ex:
            return ex["id"]
        chat_id = str(uuid.uuid4())
        chat = Chat(id=chat_id, name="Direct Chat", is_group=False, created_by=user1_id)
        participants = [user1_id, user2_id]
        success = self.db.create_chat(chat, participants)
        return chat_id if success else None


# -------------------------
# Initialize managers (cached resource)
# -------------------------
@st.cache_resource
def init_managers():
    db = DatabaseManager()
    auth = AuthManager()
    chat_manager = ChatManager(db)
    file_manager = FileManager()
    return db, auth, chat_manager, file_manager


# -------------------------
# Main App
# -------------------------
class ChatFlowApp:
    def __init__(self):
        self.db, self.auth, self.chat_manager, self.file_manager = init_managers()
        self.init_session_state()

    def init_session_state(self):
        if "user" not in st.session_state:
            st.session_state.user = None
        if "current_chat" not in st.session_state:
            st.session_state.current_chat = None
        if "theme" not in st.session_state:
            st.session_state.theme = "light"
        if "message_draft" not in st.session_state:
            st.session_state.message_draft = ""
        if "_disappear" not in st.session_state:
            st.session_state._disappear = None
        if "_secret" not in st.session_state:
            st.session_state._secret = False
        if "_silent" not in st.session_state:
            st.session_state._silent = False

    def safe_user_id(self) -> Optional[str]:
        """
        Return a stable user id string from st.session_state.user, whether it's None, a dataclass User, or a dict.
        """
        u = st.session_state.get("user", None)
        if u is None:
            return None
        if hasattr(u, "id"):
            return getattr(u, "id")
        if isinstance(u, dict) and "id" in u:
            return u["id"]
        return None

    def run(self):
        load_css()
        st.title("💬 ChatFlow")
        if st.session_state.user is None:
            self.show_auth_page()
        else:
            # mark online (defensive)
            uid = self.safe_user_id()
            if uid:
                try:
                    self.db.update_user_status(uid, True)
                except Exception:
                    pass
            self.show_main_app()

    # -------------------------
    # Authentication pages
    # -------------------------
    def show_auth_page(self):
        st.markdown("<h1 style='text-align:center;color:#007bff;'>ChatFlow</h1>", unsafe_allow_html=True)
        st.write("Modern local messaging prototype — no API keys required.")
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        with tab1:
            self.show_login_form()
        with tab2:
            self.show_signup_form()

    def show_login_form(self):
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.form_submit_button("Sign In"):
                if not username or not password:
                    st.error("Please fill in both fields.")
                    return
                user = self.db.get_user_by_username(username)
                if user and self.auth.verify_password(password, user.password_hash):
                    st.session_state.user = user
                    st.success("Welcome back! 🎉")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    def show_signup_form(self):
        with st.form("signup_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm password", type="password", placeholder="Repeat password")
            bio = st.text_area("Bio (optional)", max_chars=150)
            if st.form_submit_button("Sign Up"):
                if not username or not email or not password:
                    st.error("Please complete required fields.")
                    return
                if password != confirm_password:
                    st.error("Passwords do not match.")
                    return
                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                    return
                if not re.match(r"^[a-zA-Z0-9_]+$", username):
                    st.error("Username can only contain letters, numbers, and underscores.")
                    return
                user = User(id=str(uuid.uuid4()), username=username, email=email, password_hash=self.auth.hash_password(password), bio=bio)
                ok = self.db.create_user(user)
                if ok:
                    st.success("Account created — please sign in.")
                else:
                    st.error("Username or email already exists.")

    # -------------------------
    # Main interface
    # -------------------------
    def show_main_app(self):
        # Sidebar (contacts, search, settings)
        with st.sidebar:
            self.show_sidebar()
        # Main content
        if st.session_state.current_chat:
            self.show_chat_interface()
        else:
            self.show_welcome_screen()

    def show_sidebar(self):
        user = st.session_state.get("user", None)
        username_display = ""
        if user is None:
            username_display = "(unknown)"
        elif hasattr(user, "username"):
            username_display = user.username
        elif isinstance(user, dict):
            username_display = user.get("username", "(unknown)")
        st.markdown(f"### 👋 {username_display}")

        # Quick stats (defensive)
        uid = self.safe_user_id()
        try:
            user_chats = self.db.get_user_chats(uid) if uid else []
        except Exception:
            user_chats = []
        st.markdown(f"**{len(user_chats)}** chats")

        # Theme toggle
        if st.button("🌓 Toggle Theme"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()

        st.markdown("---")
        st.markdown("### 🔍 Find people")
        search_query = st.text_input("Search users...", placeholder="username or email", key="sidebar_search")
        if search_query and uid:
            found = self.db.search_users(search_query, uid)
            for u in found:
                col1, col2 = st.columns([3, 1])
                with col1:
                    status = "🟢" if u["is_online"] else "⚫"
                    st.write(f"{status} **{u['username']}**")
                    if u["bio"]:
                        st.caption(u["bio"][:50] + ("..." if len(u["bio"]) > 50 else ""))
                with col2:
                    if st.button("💬", key=f"start_{u['id']}"):
                        chat_id = self.chat_manager.create_direct_chat(uid, u["id"])
                        if chat_id:
                            st.session_state.current_chat = chat_id
                            st.rerun()
        else:
            st.info("Search for people to start a chat")

        st.markdown("---")
        if st.button("👥 New Group Chat"):
            self.show_create_group_modal()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚙️ Settings"):
                self.show_settings_modal()
        with col2:
            # Logout: guard against missing/invalid user
            if st.button("🚪 Logout"):
                uid = self.safe_user_id()
                if uid:
                    try:
                        self.db.update_user_status(uid, False)
                    except Exception:
                        pass
                # clear session safely
                st.session_state.user = None
                st.session_state.current_chat = None
                st.rerun()

        # Recent chats
        st.markdown("---")
        st.markdown("### 💬 Recent Chats")
        if user_chats:
            for chat in user_chats:
                chat_name = chat["name"]
                if not chat["is_group"] and chat_name == "Direct Chat":
                    # Attempt to show other user's name (best-effort)
                    try:
                        conn = self.db.get_conn()
                        cur = conn.cursor()
                        cur.execute("SELECT user_id FROM chat_participants WHERE chat_id = ? AND user_id != ?", (chat["id"], uid))
                        r = cur.fetchone()
                        conn.close()
                        if r:
                            other = self.db.get_user_by_id(r["user_id"])
                            if other:
                                chat_name = other.username
                    except Exception:
                        pass

                if st.button(f"{'👥' if chat['is_group'] else '👤'} {chat_name}", key=f"chat_btn_{chat['id']}"):
                    st.session_state.current_chat = chat["id"]
                    st.rerun()
        else:
            st.info("No chats yet. Search people or create a new group.")

    def show_welcome_screen(self):
        st.markdown(
            """
            <div style='text-align:center;padding:30px;'>
                <h2 style='color:#007bff;'>Welcome to ChatFlow</h2>
                <p>Pick a chat from the sidebar or search for contacts to start chatting.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------
    # Chat interface
    # -------------------------
    def show_chat_interface(self):
        self.show_chat_header()
        messages_container = st.container()
        with messages_container:
            self.show_messages()
        st.markdown("---")
        self.show_message_input()

    def show_chat_header(self):
        st.markdown(
            """
            <div style="background: linear-gradient(90deg,#007bff,#0056b3); padding:12px; border-radius:8px; color:white;">
                <strong>Active Chat</strong> — local demo
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("📞 Voice"):
                st.info("Voice call requires WebRTC integration (not included in this local demo).")
        with col2:
            if st.button("📹 Video"):
                st.info("Video call requires WebRTC integration (not included in this local demo).")
        with col3:
            if st.button("🔍 Search"):
                self.show_search_in_chat()
        with col4:
            if st.button("ℹ️ Info"):
                self.show_chat_info()

    def show_messages(self):
        if not st.session_state.current_chat:
            st.info("Select a chat.")
            return
        messages = self.db.get_chat_messages(st.session_state.current_chat)
        if not messages:
            st.info("No messages yet — send the first one!")
            return
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in messages:
            self.render_message(message)
        st.markdown("</div>", unsafe_allow_html=True)
        # ensure scroll to bottom (Streamlit can't reliably auto-scroll but this helps)
        st.markdown('<div id="end-of-chat"></div>', unsafe_allow_html=True)

    def render_message(self, message: Dict):
        is_own = message["sender_id"] == self.safe_user_id()
        alignment = "sent" if is_own else "received"
        disappearing_class = "disappearing" if message.get("disappear_at") else ""
        content_html = self.render_message_content(message)
        # status icons
        status_icons = ""
        if is_own:
            if message["status"] == MessageStatus.SENT.value:
                status_icons = "✓"
            elif message["status"] == MessageStatus.DELIVERED.value:
                status_icons = "✓✓"
            elif message["status"] == MessageStatus.READ.value:
                status_icons = '<span style="color:#00b4d8;">✓✓</span>'
        # timestamp
        ts = message.get("created_at")
        try:
            timestamp = datetime.datetime.fromisoformat(ts).strftime("%H:%M")
        except Exception:
            timestamp = ts or ""
        # reactions
        reactions_html = self.render_reactions(message.get("reactions", {}))
        header = f"<strong>{message['sender_username']}</strong><br>" if not is_own else ""
        message_html = f"""
        <div class="chat-message {alignment} {disappearing_class}">
            {header}
            {content_html}
            <div class="message-meta">{timestamp} {status_icons}</div>
            {reactions_html}
        </div>
        """
        st.markdown(message_html, unsafe_allow_html=True)

        # action buttons (only shown inline for own messages)
        if is_own:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
            with col1:
                if st.button("📝", key=f"edit_{message['id']}"):
                    self.edit_message_modal(message["id"], message["content"])
            with col2:
                if st.button("🗑️", key=f"del_{message['id']}"):
                    self.delete_message_modal(message["id"])

        # reaction buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 6])
        cols = [col1, col2, col3, col4, col5]
        reactions = ["👍", "❤️", "😂", "😮", "😢"]
        for i, emoji in enumerate(reactions):
            with cols[i]:
                if st.button(emoji, key=f"react_{message['id']}_{i}"):
                    self.toggle_reaction(message["id"], emoji)

    def render_message_content(self, message: Dict) -> str:
        content = message["content"]
        mtype = message["message_type"]
        if mtype == MessageType.TEXT.value:
            return self.process_text_content(content)
        elif mtype == MessageType.IMAGE.value:
            # content could be data: URI or local path
            if content.startswith("data:image/"):
                return f'<img src="{content}" style="max-width:320px;border-radius:8px;">'
            else:
                # try reading file and base64-embedding
                try:
                    with open(content, "rb") as f:
                        b = base64.b64encode(f.read()).decode()
                        return f'<img src="data:image/png;base64,{b}" style="max-width:320px;border-radius:8px;">'
                except Exception:
                    # safe fallback: show filename and download button below
                    fname = os.path.basename(content)
                    return f'📎 {fname}'
        elif mtype == MessageType.FILE.value:
            fname = os.path.basename(content)
            return f'📎 {fname}'
        elif mtype == MessageType.VOICE.value:
            return f'🎤 <audio controls><source src="{content}" type="audio/mpeg"></audio>'
        elif mtype == MessageType.VIDEO.value:
            return f'🎥 <video controls style="max-width:320px;"><source src="{content}" type="video/mp4"></video>'
        return self.process_text_content(content)

    def process_text_content(self, content: str) -> str:
        # linkify
        url_pattern = r'(http[s]?://[^\s]+)'
        content = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', content)
        # mentions
        content = re.sub(r'@(\w+)', r'<span style="color:#007bff;">@\1</span>', content)
        # simple newline-><br>
        content = content.replace("\n", "<br>")
        return f"<div>{content}</div>"

    def render_reactions(self, reactions: Dict[str, List[str]]) -> str:
        if not reactions:
            return ""
        html = '<div class="message-reactions">'
        for emoji, users in reactions.items():
            html += f'<span class="reaction">{emoji} {len(users)}</span>'
        html += "</div>"
        return html

    # -------------------------
    # Message actions
    # -------------------------
    def show_message_input(self):
        col1, col2, col3, col4, col5 = st.columns([6, 1, 1, 1, 1])
        with col1:
            text = st.text_area("Type a message...", value=st.session_state.get("message_draft", ""), key="message_input", height=80)
            st.session_state.message_draft = text
        with col2:
            if st.button("📤", help="Send"):
                if text and text.strip():
                    self.send_text_message(text.strip())
                    st.session_state.message_draft = ""
                    st.rerun()
        with col3:
            uploaded = st.file_uploader("📎", type=["png", "jpg", "jpeg", "gif", "pdf", "docx", "txt", "zip", "mp4", "mov", "avi"], key="file_uploader")
            if uploaded:
                self.send_file_message(uploaded)
                st.rerun()
        with col4:
            if st.button("📷"):
                st.info("Camera integration requires streamlit-webrtc; not included in this demo.")
        with col5:
            if st.button("🎤"):
                st.info("Voice recording requires WebRTC integration (not included).")

        # Message options
        opt_col1, opt_col2, opt_col3 = st.columns(3)
        with opt_col1:
            disappearing = st.selectbox("Disappearing", options=[None, 60, 300, 3600, 86400], index=0, format_func=lambda x: "Off" if x is None else f"{x//60}m" if x < 3600 else f"{x//3600}h")
        with opt_col2:
            secret = st.checkbox("Secret Chat")
        with opt_col3:
            silent = st.checkbox("Silent")

        # store options into session for next message (simple)
        st.session_state._disappear = disappearing
        st.session_state._secret = secret
        st.session_state._silent = silent

    def send_text_message(self, content: str):
        if not st.session_state.current_chat:
            st.error("No chat selected.")
            return
        disappear_seconds = st.session_state.get("_disappear", None)
        disappear_at = None
        if disappear_seconds:
            disappear_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=disappear_seconds)).isoformat()
        message = Message(
            id=str(uuid.uuid4()),
            chat_id=st.session_state.current_chat,
            sender_id=self.safe_user_id() or "unknown",
            content=content,
            message_type=MessageType.TEXT,
            reactions={},
            disappear_at=disappear_at,
        )
        ok = self.db.send_message(message)
        if ok:
            st.success("Sent")
        else:
            st.error("Failed to send")

    def send_file_message(self, uploaded_file):
        if not st.session_state.current_chat:
            st.error("No chat selected.")
            return
        saved = self.file_manager.save_uploaded_file(uploaded_file, self.safe_user_id() or "anon")
        if not saved:
            st.error("Failed to save file.")
            return
        ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else ""
        if ext in ("png", "jpg", "jpeg", "gif", "webp"):
            mtype = MessageType.IMAGE
            content = saved  # likely a data URI
        elif ext in ("mp4", "mov", "avi"):
            mtype = MessageType.VIDEO
            content = saved
        else:
            mtype = MessageType.FILE
            content = saved
        msg = Message(id=str(uuid.uuid4()), chat_id=st.session_state.current_chat, sender_id=self.safe_user_id() or "unknown", content=content, message_type=mtype, reactions={})
        ok = self.db.send_message(msg)
        if ok:
            st.success("File sent!")
        else:
            st.error("Failed to send file.")

    def toggle_reaction(self, message_id: str, emoji: str):
        # fetch current message
        msgs = self.db.get_chat_messages(st.session_state.current_chat, limit=500)
        msg = next((m for m in msgs if m["id"] == message_id), None)
        if not msg:
            st.error("Message not found.")
            return
        reactions = msg.get("reactions", {}) or {}
        user_id = self.safe_user_id() or "unknown"
        users = reactions.get(emoji, [])
        if user_id in users:
            users.remove(user_id)
        else:
            users.append(user_id)
        if users:
            reactions[emoji] = users
        else:
            reactions.pop(emoji, None)
        self.db.update_message_reactions(message_id, reactions)
        st.rerun()

    def edit_message_modal(self, message_id: str, current_text: str):
        with st.expander("Edit Message", expanded=True):
            new_text = st.text_area("Edit content", value=current_text, key=f"edit_{message_id}")
            if st.button("Save", key=f"save_edit_{message_id}"):
                if not new_text.strip():
                    st.error("Content cannot be empty.")
                    return
                ok = self.db.edit_message(message_id, new_text.strip())
                if ok:
                    st.success("Message edited.")
                    st.rerun()
                else:
                    st.error("Failed to edit.")

    def delete_message_modal(self, message_id: str):
        with st.expander("Confirm Delete", expanded=True):
            if st.button("Yes, delete this message", key=f"confirm_del_{message_id}"):
                ok = self.db.delete_message(message_id)
                if ok:
                    st.success("Message deleted.")
                    st.rerun()
                else:
                    st.error("Failed to delete message.")

    # -------------------------
    # Group creation, settings, search
    # -------------------------
    def show_create_group_modal(self):
        with st.expander("Create Group", expanded=True):
            group_name = st.text_input("Group name")
            group_desc = st.text_area("Description (optional)")
            search_q = st.text_input("Search users to add", key="create_group_search")
            selected_users = []
            if search_q:
                uid = self.safe_user_id()
                users = self.db.search_users(search_q, uid) if uid else []
                for u in users:
                    if st.checkbox(u["username"], key=f"add_{u['id']}"):
                        selected_users.append(u["id"])
            if st.button("Create Group"):
                if not group_name or not selected_users:
                    st.error("Provide group name and select participants.")
                    return
                chat_id = str(uuid.uuid4())
                chat = Chat(id=chat_id, name=group_name, is_group=True, created_by=self.safe_user_id() or "unknown")
                participants = ([self.safe_user_id()] if self.safe_user_id() else []) + selected_users
                ok = self.db.create_chat(chat, participants)
                if ok:
                    st.success(f"Group '{group_name}' created.")
                    st.session_state.current_chat = chat_id
                    st.rerun()
                else:
                    st.error("Failed to create group.")

    def show_settings_modal(self):
        with st.expander("Settings", expanded=True):
            st.subheader("Profile")
            user = st.session_state.get("user", None)
            current_bio = ""
            if user is None:
                current_bio = ""
            elif hasattr(user, "bio"):
                current_bio = user.bio
            elif isinstance(user, dict):
                current_bio = user.get("bio", "")
            new_bio = st.text_area("Bio", value=current_bio, max_chars=150)
            avatar_file = st.file_uploader("Avatar", type=["png", "jpg", "jpeg"], key="avatar_upload")
            if st.button("Save profile"):
                try:
                    uid = self.safe_user_id()
                    if not uid:
                        st.error("No user found.")
                        return
                    conn = self.db.get_conn()
                    cursor = conn.cursor()
                    if avatar_file:
                        avatar_path = self.file_manager.save_uploaded_file(avatar_file, uid)
                        cursor.execute("UPDATE users SET bio = ?, avatar = ? WHERE id = ?", (new_bio, avatar_path, uid))
                    else:
                        cursor.execute("UPDATE users SET bio = ? WHERE id = ?", (new_bio, uid))
                    conn.commit()
                    conn.close()
                    st.success("Profile updated.")
                    # refresh session user
                    st.session_state.user = self.db.get_user_by_id(uid)
                except Exception as e:
                    st.error(f"Failed to update profile: {e}")

            st.markdown("---")
            st.subheader("App preferences")
            _notif = st.checkbox("Sound notifications", value=True)
            _autodl = st.checkbox("Auto-download media", value=True)
            if st.button("Save settings"):
                st.success("Settings saved (local only).")

    def show_search_in_chat(self):
        with st.expander("Search in Chat", expanded=True):
            q = st.text_input("Search messages...", key="search_in_chat_q")
            if q and st.session_state.current_chat:
                conn = self.db.get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT m.*, u.username FROM messages m JOIN users u ON m.sender_id = u.id
                    WHERE m.chat_id = ? AND m.content LIKE ? AND m.is_deleted = 0
                    ORDER BY m.created_at DESC LIMIT 50
                    """,
                    (st.session_state.current_chat, f"%{q}%"),
                )
                res = cur.fetchall()
                conn.close()
                if res:
                    st.write(f"Found {len(res)} messages")
                    for r in res:
                        try:
                            ts = datetime.datetime.fromisoformat(r["created_at"]).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            ts = r["created_at"]
                        st.write(f"**{r['username']}** ({ts}): {r['content'][:200]}")
                else:
                    st.info("No messages found.")

    def show_chat_info(self):
        with st.expander("Chat Info", expanded=True):
            if not st.session_state.current_chat:
                st.info("No chat selected.")
                return
            conn = self.db.get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT u.username, u.is_online, cp.is_admin, u.last_seen
                FROM chat_participants cp JOIN users u ON cp.user_id = u.id
                WHERE cp.chat_id = ?
                """,
                (st.session_state.current_chat,),
            )
            participants = cur.fetchall()
            conn.close()
            st.write(f"**Participants ({len(participants)}):**")
            for p in participants:
                uname = p["username"]
                is_online = bool(p["is_online"])
                is_admin = bool(p["is_admin"])
                last_seen = p["last_seen"]
                status = "🟢 Online" if is_online else f"⚫ Last seen: {last_seen or 'unknown'}"
                role = " (Admin)" if is_admin else ""
                st.write(f"- {uname}{role} — {status}")


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    app = ChatFlowApp()
    app.run()
