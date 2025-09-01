"""
Advanced Multi-Feature Chat Application
A production-ready messaging platform combining features from WhatsApp, Snapchat, and Telegram
"""

import streamlit as st
import asyncio
import json
import hashlib
import jwt
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import base64
import io
import re
import uuid
import time
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import os
from pathlib import Path
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=1000, key="chatrefresh")

# =============================
# Configure Streamlit page
# =============================
st.set_page_config(
    page_title="ChatFusion Pro",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# Custom CSS for modern UI
# =============================
st.markdown(
    """
<style>
    /* Modern color scheme */
    :root {
        --primary-color: #5865F2;
        --secondary-color: #7289DA;
        --success-color: #43B581;
        --danger-color: #F04747;
        --warning-color: #FAA61A;
        --dark-bg: #2C2F33;
        --darker-bg: #23272A;
        --light-text: #FFFFFF;
        --muted-text: #99AAB5;
        --message-bg: #40444B;
        --online-status: #43B581;
        --away-status: #FAA61A;
        --offline-status: #747F8D;
    }

    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }

    /* Chat interface */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }

    .message-bubble {
        max-width: 70%;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 18px;
        word-wrap: break-word;
        animation: slideIn 0.3s ease;
    }

    .message-sent {
        background: linear-gradient(135deg, #5865F2, #7289DA);
        color: white;
        margin-left: auto;
        margin-right: 10px;
        border-bottom-right-radius: 4px;
    }

    .message-received {
        background: #E3E5E8;
        color: #2C2F33;
        margin-right: auto;
        margin-left: 10px;
        border-bottom-left-radius: 4px;
    }

    .user-status { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
    .status-online { background-color: var(--online-status); }
    .status-away { background-color: var(--away-status); }
    .status-offline { background-color: var(--offline-status); }

    .typing-indicator { display: inline-block; padding: 8px 12px; background: #E3E5E8; border-radius: 18px; margin: 10px; }
    .typing-indicator span { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #99AAB5; margin: 0 2px; animation: typing 1.4s infinite; }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-10px); } }
    @keyframes slideIn { from { opacity: 0; transform: translateY(10px);} to { opacity: 1; transform: translateY(0);} }

    .story-container { display: flex; overflow-x: auto; padding: 15px 0; gap: 15px; }
    .story-item { min-width: 80px; text-align: center; cursor: pointer; transition: transform 0.2s; }
    .story-item:hover { transform: scale(1.05); }
    .story-avatar { width: 70px; height: 70px; border-radius: 50%; border: 3px solid var(--primary-color); padding: 2px; background: white; display:flex; align-items:center; justify-content:center; }

    .group-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 15px 15px 0 0; margin: -20px -20px 20px -20px; }

    .upload-area { border: 2px dashed #7289DA; border-radius: 15px; padding: 30px; text-align: center; background: rgba(88, 101, 242, 0.05); transition: all 0.3s; }
    .upload-area:hover { background: rgba(88, 101, 242, 0.1); border-color: #5865F2; }

    .custom-button { background: linear-gradient(135deg, #5865F2, #7289DA); color: white; border: none; padding: 10px 20px; border-radius: 25px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
    .custom-button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(88, 101, 242, 0.3); }

    .chat-list-item { padding: 12px; border-radius: 10px; margin: 5px 0; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 10px; }
    .chat-list-item:hover { background: rgba(88, 101, 242, 0.1); transform: translateX(5px); }
    .chat-list-item.active { background: linear-gradient(135deg, #5865F2, #7289DA); color: white; }

    .notification-badge { background: #F04747; color: white; border-radius: 50%; padding: 2px 6px; font-size: 12px; font-weight: bold; margin-left: auto; }

    .voice-player { background: #40444B; border-radius: 25px; padding: 10px 20px; display: flex; align-items: center; gap: 10px; color: white; }
    .message-reactions { display: flex; gap: 5px; margin-top: 5px; flex-wrap: wrap; }
    .reaction-chip { background: rgba(88, 101, 242, 0.1); border: 1px solid rgba(88, 101, 242, 0.3); border-radius: 15px; padding: 2px 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; }
    .reaction-chip:hover { background: rgba(88, 101, 242, 0.2); transform: scale(1.1); }

    .divider { height:1px; background: rgba(0,0,0,0.08); margin: 10px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# Database Models and Enums
# =============================
class UserStatus(Enum):
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"
    BUSY = "busy"

class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    VOICE = "voice"
    LOCATION = "location"
    CONTACT = "contact"
    POLL = "poll"

class MessageStatus(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"

@dataclass
class User:
    user_id: str
    username: str
    email: str
    phone: Optional[str]
    avatar: Optional[str]
    status_message: str
    online_status: UserStatus
    last_seen: datetime
    created_at: datetime
    is_verified: bool = False
    two_factor_enabled: bool = False

@dataclass
class Message:
    message_id: str
    sender_id: str
    recipient_id: Optional[str]
    content: str
    message_type: MessageType
    status: MessageStatus
    timestamp: datetime
    edited_at: Optional[datetime] = None
    reply_to: Optional[str] = None
    reactions: Dict[str, List[str]] = None
    is_deleted: bool = False
    expires_at: Optional[datetime] = None
    group_id: Optional[str] = None

@dataclass
class Group:
    group_id: str
    name: str
    description: str
    avatar: Optional[str]
    creator_id: str
    admin_ids: List[str]
    member_ids: List[str]
    created_at: datetime
    settings: Dict[str, Any]

@dataclass
class Story:
    story_id: str
    user_id: str
    content: str
    media_url: Optional[str]
    created_at: datetime
    expires_at: datetime
    views: List[str]
    reactions: Dict[str, List[str]]
    is_highlight: bool = False

# =============================
# Database Manager
# =============================
class DatabaseManager:
    def __init__(self, db_path="chat_app.db"):
        self.db_path = db_path
        self.init_database()

    def _connect(self):
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def init_database(self):
        """Initialize database tables"""
        conn = self._connect()
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT,
                avatar TEXT,
                status_message TEXT,
                online_status TEXT,
                last_seen TIMESTAMP,
                created_at TIMESTAMP,
                is_verified BOOLEAN DEFAULT FALSE,
                two_factor_enabled BOOLEAN DEFAULT FALSE,
                settings TEXT
            )
            """
        )

        # Messages table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT,
                group_id TEXT,
                content TEXT,
                message_type TEXT,
                status TEXT,
                timestamp TIMESTAMP,
                edited_at TIMESTAMP,
                reply_to TEXT,
                reactions TEXT,
                is_deleted BOOLEAN DEFAULT FALSE,
                expires_at TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id)
            )
            """
        )

        # Groups table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                avatar TEXT,
                creator_id TEXT NOT NULL,
                admin_ids TEXT,
                member_ids TEXT,
                created_at TIMESTAMP,
                settings TEXT,
                FOREIGN KEY (creator_id) REFERENCES users(user_id)
            )
            """
        )

        # Stories table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stories (
                story_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT,
                media_url TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                views TEXT,
                reactions TEXT,
                is_highlight BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        # Contacts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                nickname TEXT,
                is_blocked BOOLEAN DEFAULT FALSE,
                is_favorite BOOLEAN DEFAULT FALSE,
                added_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (contact_id) REFERENCES users(user_id),
                UNIQUE(user_id, contact_id)
            )
            """
        )

        # Channels table (not fully used; placeholder for future)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                avatar TEXT,
                owner_id TEXT NOT NULL,
                moderator_ids TEXT,
                subscriber_ids TEXT,
                category TEXT,
                is_public BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP,
                settings TEXT,
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            )
            """
        )

        conn.commit()
        conn.close()

    # ---------- Users ----------
    def create_user(self, username: str, email: str, password: str) -> Optional[User]:
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (
                    user_id, username, email, password_hash,
                    status_message, online_status, last_seen, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    email,
                    password_hash,
                    "Hey there! I'm using ChatFusion",
                    UserStatus.ONLINE.value,
                    datetime.now(),
                    datetime.now(),
                ),
            )
            conn.commit()
            return self.get_user_by_id(user_id)
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, phone, avatar, status_message,
                   online_status, last_seen, created_at, is_verified, two_factor_enabled
            FROM users WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                phone=row[3],
                avatar=row[4],
                status_message=row[5],
                online_status=UserStatus(row[6]),
                last_seen=row[7],
                created_at=row[8],
                is_verified=bool(row[9]),
                two_factor_enabled=bool(row[10]),
            )
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, phone, avatar, status_message,
                   online_status, last_seen, created_at, is_verified, two_factor_enabled
            FROM users WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                phone=row[3],
                avatar=row[4],
                status_message=row[5],
                online_status=UserStatus(row[6]),
                last_seen=row[7],
                created_at=row[8],
                is_verified=bool(row[9]),
                two_factor_enabled=bool(row[10]),
            )
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, phone, avatar, status_message,
                   online_status, last_seen, created_at, is_verified, two_factor_enabled
            FROM users
            WHERE username = ? AND password_hash = ?
            """,
            (username, password_hash),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                phone=row[3],
                avatar=row[4],
                status_message=row[5],
                online_status=UserStatus(row[6]),
                last_seen=row[7],
                created_at=row[8],
                is_verified=bool(row[9]),
                two_factor_enabled=bool(row[10]),
            )
        return None

    # ---------- Contacts ----------
    def add_contact(self, user_id: str, contact_id: str, nickname: Optional[str] = None):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO contacts (user_id, contact_id, nickname, added_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, contact_id, nickname, datetime.now()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_user_contacts(self, user_id: str) -> List[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.contact_id, u.username, u.avatar, u.status_message, u.online_status,
                   c.nickname, c.is_favorite, c.is_blocked
            FROM contacts c
            JOIN users u ON c.contact_id = u.user_id
            WHERE c.user_id = ? AND c.is_blocked = FALSE
            ORDER BY c.is_favorite DESC, u.username
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        contacts = []
        for row in rows:
            contacts.append(
                {
                    "user_id": row[0],
                    "username": row[1],
                    "avatar": row[2],
                    "status_message": row[3],
                    "online_status": row[4],
                    "nickname": row[5],
                    "is_favorite": bool(row[6]),
                    "is_blocked": bool(row[7]),
                }
            )
        return contacts

    # ---------- Messages ----------
    def send_message(
        self,
        sender_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        recipient_id: Optional[str] = None,
        group_id: Optional[str] = None,
        expires_minutes: Optional[int] = None,
    ) -> Message:
        message_id = str(uuid.uuid4())
        timestamp = datetime.now()
        expires_at = (
            timestamp + timedelta(minutes=expires_minutes) if expires_minutes else None
        )
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (
                message_id, sender_id, recipient_id, group_id, content,
                message_type, status, timestamp, edited_at, reply_to, reactions, is_deleted, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                sender_id,
                recipient_id,
                group_id,
                content,
                message_type.value,
                MessageStatus.SENT.value,
                timestamp,
                None,
                None,
                json.dumps({}),
                False,
                expires_at,
            ),
        )
        conn.commit()
        conn.close()
        return Message(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            group_id=group_id,
            content=content,
            message_type=message_type,
            status=MessageStatus.SENT,
            timestamp=timestamp,
            reactions={},
            expires_at=expires_at,
        )

    def get_messages(
        self, user_id: str, contact_id: str, limit: int = 50
    ) -> List[Message]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message_id, sender_id, recipient_id, group_id, content, message_type,
                   status, timestamp, edited_at, reply_to, reactions, is_deleted, expires_at
            FROM messages
            WHERE ((sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?))
              AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, contact_id, contact_id, user_id, datetime.now(), limit),
        )
        rows = cursor.fetchall()
        conn.close()
        messages: List[Message] = []
        for row in rows:
            reactions = json.loads(row[10]) if row[10] else {}
            messages.append(
                Message(
                    message_id=row[0],
                    sender_id=row[1],
                    recipient_id=row[2],
                    group_id=row[3],
                    content=row[4],
                    message_type=MessageType(row[5]),
                    status=MessageStatus(row[6]),
                    timestamp=row[7],
                    edited_at=row[8],
                    reply_to=row[9],
                    reactions=reactions,
                    is_deleted=bool(row[11]),
                    expires_at=row[12],
                )
            )
        return messages[::-1]

    # ---------- Groups ----------
    def create_group(
        self, name: str, description: str, creator_id: str, member_ids: List[str]
    ) -> Group:
        group_id = str(uuid.uuid4())
        created_at = datetime.now()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO groups (
                group_id, name, description, creator_id, admin_ids, member_ids, created_at, settings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                name,
                description,
                creator_id,
                json.dumps([creator_id]),
                json.dumps(list(set([creator_id] + member_ids))),
                created_at,
                json.dumps({}),
            ),
        )
        conn.commit()
        conn.close()
        return Group(
            group_id=group_id,
            name=name,
            description=description,
            avatar=None,
            creator_id=creator_id,
            admin_ids=[creator_id],
            member_ids=list(set([creator_id] + member_ids)),
            created_at=created_at,
            settings={},
        )

    def get_group(self, group_id: str) -> Optional[Group]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT group_id, name, description, avatar, creator_id, admin_ids, member_ids, created_at, settings FROM groups WHERE group_id = ?",
            (group_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return Group(
            group_id=row[0],
            name=row[1],
            description=row[2] or "",
            avatar=row[3],
            creator_id=row[4],
            admin_ids=json.loads(row[5] or "[]"),
            member_ids=json.loads(row[6] or "[]"),
            created_at=row[7],
            settings=json.loads(row[8] or "{}"),
        )

    def get_user_groups(self, user_id: str) -> List[Group]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups")
        rows = cursor.fetchall()
        conn.close()
        groups: List[Group] = []
        for row in rows:
            member_ids = json.loads(row[6] or "[]")
            if user_id in member_ids:
                groups.append(
                    Group(
                        group_id=row[0],
                        name=row[1],
                        description=row[2] or "",
                        avatar=row[3],
                        creator_id=row[4],
                        admin_ids=json.loads(row[5] or "[]"),
                        member_ids=member_ids,
                        created_at=row[7],
                        settings=json.loads(row[8] or "{}"),
                    )
                )
        return groups

    def get_group_messages(self, group_id: str, limit: int = 100) -> List[Message]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message_id, sender_id, recipient_id, group_id, content, message_type,
                   status, timestamp, edited_at, reply_to, reactions, is_deleted, expires_at
            FROM messages
            WHERE group_id = ? AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (group_id, datetime.now(), limit),
        )
        rows = cursor.fetchall()
        conn.close()
        out: List[Message] = []
        for row in rows:
            out.append(
                Message(
                    message_id=row[0],
                    sender_id=row[1],
                    recipient_id=row[2],
                    group_id=row[3],
                    content=row[4],
                    message_type=MessageType(row[5]),
                    status=MessageStatus(row[6]),
                    timestamp=row[7],
                    edited_at=row[8],
                    reply_to=row[9],
                    reactions=json.loads(row[10] or "{}"),
                    is_deleted=bool(row[11]),
                    expires_at=row[12],
                )
            )
        return out[::-1]

# =============================
# Authentication Manager
# =============================
class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv("CHATFUSION_SECRET", "change-me-in-prod")

    def generate_token(self, user: User) -> str:
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# =============================
# Media Handler (mock)
# =============================
class MediaHandler:
    @staticmethod
    def process_image(image_data: bytes) -> str:
        return base64.b64encode(image_data).decode()

    @staticmethod
    def process_video(video_data: bytes) -> str:
        return base64.b64encode(video_data).decode()

    @staticmethod
    def process_audio(audio_data: bytes) -> str:
        return base64.b64encode(audio_data).decode()

# =============================
# Real-time Handler (simulated)
# =============================
class RealtimeHandler:
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.typing_users: Dict[str, List[str]] = {}

    def connect_user(self, user_id: str):
        self.connections[user_id] = {"status": UserStatus.ONLINE, "last_activity": datetime.now()}

    def disconnect_user(self, user_id: str):
        if user_id in self.connections:
            del self.connections[user_id]

    def send_typing_indicator(self, user_id: str, recipient_id: str):
        if recipient_id not in self.typing_users:
            self.typing_users[recipient_id] = []
        if user_id not in self.typing_users[recipient_id]:
            self.typing_users[recipient_id].append(user_id)

    def clear_typing(self, recipient_id: str):
        self.typing_users.pop(recipient_id, None)

# =============================
# UI Components
# =============================
class UIComponents:
    @staticmethod
    def render_message(message: Message, current_user_id: str, users: Dict[str, User]):
        is_sent = message.sender_id == current_user_id
        sender = users.get(message.sender_id)
        message_class = "message-sent" if is_sent else "message-received"
        name_prefix = "" if is_sent else (f"**{sender.username}**\n" if sender else "")
        body = name_prefix + (message.content if message.message_type == MessageType.TEXT else f"[{message.message_type.value.upper()}]")
        st.markdown(
            f'<div class="message-bubble {message_class}">{body}</div>',
            unsafe_allow_html=True,
        )
        status_icon = {MessageStatus.SENT: "✓", MessageStatus.DELIVERED: "✓✓", MessageStatus.READ: "✓✓"}.get(message.status, "")
        time_str = message.timestamp.strftime("%H:%M")
        st.caption(f"{time_str} {status_icon}")
        if message.reactions:
            reaction_html = '<div class="message-reactions">'
            for emoji, users_list in message.reactions.items():
                reaction_html += f'<span class="reaction-chip">{emoji} {len(users_list)}</span>'
            reaction_html += "</div>"
            st.markdown(reaction_html, unsafe_allow_html=True)

    @staticmethod
    def render_chat_list(contacts: List[Dict], active_chat: Optional[str]):
        st.sidebar.markdown("### 💬 Chats")
        search = st.sidebar.text_input("🔍 Search conversations", key="chat_search")
        filtered_contacts = [c for c in contacts if (search.lower() in c["username"].lower())] if search else contacts
        for contact in filtered_contacts:
            status_class = f"status-{contact['online_status']}"
            active_class = "active" if contact["user_id"] == active_chat else ""
            chat_html = f"""
            <div class="chat-list-item {active_class}">
                <span class="user-status {status_class}"></span>
                <div>
                    <strong>{contact['username']}</strong><br>
                    <small>{contact['status_message']}</small>
                </div>
            </div>
            """
            st.sidebar.markdown(chat_html, unsafe_allow_html=True)
            if st.sidebar.button(f"Open • {contact['username']}", key=f"chat_{contact['user_id']}", use_container_width=True):
                st.session_state.active_chat = contact["user_id"]
                st.rerun()

    @staticmethod
    def render_story_bar(stories: List[Story], users: Dict[str, User]):
        st.markdown("### 📸 Stories")
        story_html = '<div class="story-container">'
        story_html += """
        <div class="story-item">
            <div class="story-avatar">➕</div>
            <small>Your Story</small>
        </div>
        """
        for story in stories[:10]:
            user = users.get(story.user_id)
            if user:
                story_html += f"""
                <div class=\"story-item\">
                    <div class=\"story-avatar\">👤</div>
                    <small>{user.username}</small>
                </div>
                """
        story_html += "</div>"
        st.markdown(story_html, unsafe_allow_html=True)

    @staticmethod
    def render_typing_indicator(typing_users: List[str], users: Dict[str, User]):
        if typing_users:
            names = ", ".join([users.get(uid).username if users.get(uid) else "Someone" for uid in typing_users])
            st.caption(f"{names} is typing…")
            st.markdown(
                """
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =============================
# Main Application
# =============================
class ChatApplication:
    def __init__(self):
        self.db = DatabaseManager()
        self.auth = AuthManager()
        self.media = MediaHandler()
        self.realtime = RealtimeHandler()
        self.ui = UIComponents()
        self.init_session_state()

    # ---------- Session State ----------
    def init_session_state(self):
        if "user" not in st.session_state:
            st.session_state.user: Optional[User] = None
        if "token" not in st.session_state:
            st.session_state.token = None
        if "active_chat" not in st.session_state:
            st.session_state.active_chat: Optional[str] = None
        if "active_group" not in st.session_state:
            st.session_state.active_group: Optional[str] = None
        if "active_page" not in st.session_state:
            st.session_state.active_page = "Chats"
        if "messages" not in st.session_state:
            st.session_state.messages: Dict[str, List[Message]] = {}
        if "users_cache" not in st.session_state:
            st.session_state.users_cache: Dict[str, User] = {}
        if "stories" not in st.session_state:
            st.session_state.stories: List[Story] = []
        if "typing" not in st.session_state:
            st.session_state.typing: Dict[str, List[str]] = {}

    # ---------- Auth UI ----------
    def auth_ui(self):
        st.markdown("## 🔐 Sign in to ChatFusion Pro")
        tab_login, tab_signup = st.tabs(["Login", "Create account"])
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in")
                if submitted:
                    user = self.db.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.token = self.auth.generate_token(user)
                        self.realtime.connect_user(user.user_id)
                        st.success("Logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
        with tab_signup:
            with st.form("signup_form", clear_on_submit=True):
                username = st.text_input("Username", help="Unique handle")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create account")
                if submitted:
                    if password != confirm:
                        st.error("Passwords do not match.")
                    elif len(username) < 3:
                        st.error("Username too short.")
                    else:
                        user = self.db.create_user(username, email, password)
                        if user:
                            st.success("Account created. Please login.")
                        else:
                            st.error("Username or email already exists.")

    # ---------- Helpers ----------
    def _load_contacts(self) -> List[Dict[str, Any]]:
        if not st.session_state.user:
            return []
        return self.db.get_user_contacts(st.session_state.user.user_id)

    def _cache_user(self, user: Optional[User]):
        if user and user.user_id not in st.session_state.users_cache:
            st.session_state.users_cache[user.user_id] = user

    # ---------- Main UI ----------
    def main_ui(self):
        user = st.session_state.user
        if not user:
            self.auth_ui()
            return

        # Sidebar
        with st.sidebar:
            st.markdown(f"### 👋 Hello, **{user.username}**")
            page = st.radio(
                "Navigate",
                ["Chats", "Groups", "Contacts", "Stories", "Profile", "Settings"],
                index=["Chats", "Groups", "Contacts", "Stories", "Profile", "Settings"].index(st.session_state.active_page),
            )
            st.session_state.active_page = page
            st.divider()
            contacts = self._load_contacts()
            self.ui.render_chat_list(contacts, st.session_state.active_chat)
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                self.realtime.disconnect_user(user.user_id)
                for k in ["user", "token", "active_chat", "active_group"]:
                    st.session_state[k] = None
                st.success("Logged out.")
                st.rerun()

        # Main area
        if page == "Chats":
            self.page_chats()
        elif page == "Groups":
            self.page_groups()
        elif page == "Contacts":
            self.page_contacts()
        elif page == "Stories":
            self.page_stories()
        elif page == "Profile":
            self.page_profile()
        elif page == "Settings":
            self.page_settings()

    # ---------- Pages ----------
    def page_chats(self):
    st.title("💬 Chats")

    user: User = st.session_state.user
    active = st.session_state.active_chat

    # 🔄 Auto-refresh every 3 seconds
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="chatrefresh")

    # Sidebar chat list
    contacts = self.db.get_user_contacts(user.user_id)
    self.ui.render_chat_list(contacts, active_chat=active)

    # If no active chat, show a message
    if not active:
        st.info("👈 Select a chat from the sidebar to start messaging.")
        return

    # Load messages
    messages = self.db.get_messages(user.user_id, active, limit=50)

    # Render chat header
    contact = next((c for c in contacts if c['user_id'] == active), None)
    if contact:
        st.markdown(f"### {contact['username']}")

    # Show messages
    users_dict = {c['user_id']: User(**c) for c in contacts if isinstance(c, dict)}
    for msg in messages:
        self.ui.render_message(msg, current_user_id=user.user_id, users=users_dict)

    st.markdown("---")

    # === Input area ===
    if "send_clicked" not in st.session_state:
        st.session_state.send_clicked = False

    txt = st.text_input("Type your message...", key="chat_input")
    minutes = st.slider("⏳ Message expiry (minutes)", 0, 60, 0)

    if st.button("Send"):
        st.session_state.send_clicked = True

    if st.session_state.send_clicked and txt.strip():
        self.db.send_message(
            sender_id=user.user_id,
            recipient_id=active,
            content=txt,
            message_type=MessageType.TEXT,
        )
        st.session_state.send_clicked = False  # reset
        st.rerun()


        with col_right:
            st.markdown("### ⚙️ Chat Tools")
            new_username = st.text_input("Add contact by username")
            if st.button("Add", use_container_width=True) and new_username:
                target = self.db.get_user_by_username(new_username)
                if target:
                    self.db.add_contact(user.user_id, target.user_id)
                    st.success("Added contact.")
                    st.rerun()
                else:
                    st.error("No user with that username.")
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.write("**Quick info**")
            if st.session_state.active_chat:
                u = self.db.get_user_by_id(st.session_state.active_chat)
                if u:
                    st.json({"username": u.username, "status": u.online_status.value, "bio": u.status_message})

    def page_groups(self):
        user = st.session_state.user
        st.markdown("# 👥 Groups")
        colA, colB = st.columns([2, 3], gap="large")
        with colA:
            groups = self.db.get_user_groups(user.user_id)
            options = {g.name: g.group_id for g in groups}
            chosen = st.selectbox("Your groups", list(options.keys()) if options else ["(none)"])
            if options:
                st.session_state.active_group = options[chosen]
            with st.expander("➕ Create group"):
                g_name = st.text_input("Group name")
                g_desc = st.text_area("Description")
                invite_username = st.text_input("Invite by username (optional)")
                if st.button("Create") and g_name:
                    members = []
                    if invite_username:
                        u = self.db.get_user_by_username(invite_username)
                        if u:
                            members.append(u.user_id)
                    grp = self.db.create_group(g_name, g_desc, user.user_id, members)
                    st.success(f"Group '{grp.name}' created.")
                    st.rerun()
        with colB:
            gid = st.session_state.active_group
            if not gid:
                st.info("Select or create a group.")
                return
            grp = self.db.get_group(gid)
            if not grp:
                st.error("Group not found.")
                return
            st.markdown(f"### {grp.name}")
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            # preload users in cache
            for uid in grp.member_ids:
                self._cache_user(self.db.get_user_by_id(uid))
            msgs = self.db.get_group_messages(gid, limit=300)
            for m in msgs:
                self.ui.render_message(m, user.user_id, st.session_state.users_cache)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.form("send_group_form", clear_on_submit=True):
                txt = st.text_input("Message group…")
                expire = st.selectbox("Disappear in", ["Never", "10 min", "60 min", "24 h"], index=0)
                send = st.form_submit_button("Send")
                if send and txt:
                    minutes = None
                    if expire == "10 min":
                        minutes = 10
                    elif expire == "60 min":
                        minutes = 60
                    elif expire == "24 h":
                        minutes = 1440
                    self.db.send_message(
                        sender_id=user.user_id,
                        content=txt,
                        message_type=MessageType.TEXT,
                        group_id=gid,
                        expires_minutes=minutes,
                    )
                    st.rerun()

    def page_contacts(self):
        user = st.session_state.user
        st.markdown("# 📇 Contacts")
        contacts = self.db.get_user_contacts(user.user_id)
        if not contacts:
            st.info("You have no contacts yet. Add by username below.")
        df = pd.DataFrame(contacts)
        if not df.empty:
            st.dataframe(df[["username", "status_message", "online_status", "is_favorite"]], use_container_width=True)
        st.markdown("### ➕ Add contact")
        username = st.text_input("Username to add")
        if st.button("Add contact") and username:
            other = self.db.get_user_by_username(username)
            if other:
                self.db.add_contact(user.user_id, other.user_id)
                st.success("Contact added.")
                st.rerun()
            else:
                st.error("User not found.")

    def page_stories(self):
        st.markdown("# 📸 Stories")
        self.ui.render_story_bar(st.session_state.stories, st.session_state.users_cache)
        st.info("Stories UI is a visual placeholder in this MVP.")

    def page_profile(self):
        user = st.session_state.user
        st.markdown("# 👤 Profile")
        with st.form("profile_form"):
            status = st.text_area("Status message", value=user.status_message)
            visibility = st.selectbox("Online status", [s.value for s in UserStatus], index=[s.value for s in UserStatus].index(user.online_status.value))
            save = st.form_submit_button("Save profile")
            if save:
                conn = self.db._connect()
                cur = conn.cursor()
                cur.execute("UPDATE users SET status_message = ?, online_status = ? WHERE user_id = ?", (status, visibility, user.user_id))
                conn.commit(); conn.close()
                # update in-memory
                st.session_state.user = self.db.get_user_by_id(user.user_id)
                st.success("Profile updated.")

    def page_settings(self):
        st.markdown("# ⚙️ Settings")
        with st.expander("Security"):
            st.checkbox("Enable 2FA (placeholder)")
            st.text_input("Backup email", value=st.session_state.user.email)
        with st.expander("Privacy"):
            st.checkbox("Read receipts", value=True)
            st.checkbox("Typing indicators", value=True)
        with st.expander("About"):
            st.write("ChatFusion Pro – Streamlit MVP. Local SQLite DB, simulated realtime.")

# =============================
# Run the app
# =============================
app = ChatApplication()
app.main_ui()
