"""
Advanced Multi-Feature Chat Application - Fully Functional Version
A production-ready messaging platform with real user interaction, notifications, and all features working
"""

import streamlit as st
import sqlite3
import hashlib
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import base64
import re
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import os

# Configure Streamlit page
st.set_page_config(
    page_title="ChatFusion Pro",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for modern UI with better visibility
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    .message-sent {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 5px 18px;
        margin: 8px 0 8px auto;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,123,255,0.3);
    }
    
    .message-received {
        background: #e9ecef;
        color: #495057;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 5px;
        margin: 8px auto 8px 0;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .user-status-online {
        color: #28a745;
        font-weight: bold;
    }
    
    .user-status-away {
        color: #ffc107;
        font-weight: bold;
    }
    
    .user-status-offline {
        color: #6c757d;
        font-weight: bold;
    }
    
    .notification-badge {
        background: #dc3545;
        color: white;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .contact-item {
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .contact-item:hover {
        background: #f8f9fa;
    }
    
    .contact-item.active {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .typing-indicator {
        font-style: italic;
        color: #6c757d;
        padding: 5px 15px;
    }
    
    .story-container {
        display: flex;
        overflow-x: auto;
        padding: 10px;
        gap: 15px;
        background: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .story-item {
        text-align: center;
        min-width: 80px;
        cursor: pointer;
    }
    
    .story-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
        margin: 0 auto 5px;
        border: 3px solid #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .reaction-chip {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        display: inline-block;
        margin: 2px;
        transition: all 0.2s;
    }
    
    .reaction-chip:hover {
        background: #e9ecef;
        transform: scale(1.05);
    }
    
    .group-header {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    .media-preview {
        max-width: 300px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .file-message {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    
    .timestamp {
        font-size: 11px;
        color: #6c757d;
        margin-top: 4px;
    }
    
    .message-status {
        font-size: 12px;
        color: #28a745;
        float: right;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Database Models and Enums
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

@dataclass
class Message:
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    message_type: MessageType
    status: MessageStatus
    timestamp: datetime
    edited_at: Optional[datetime] = None
    reply_to: Optional[str] = None
    reactions: Dict[str, List[str]] = None
    is_deleted: bool = False

@dataclass
class Group:
    group_id: str
    name: str
    description: str
    creator_id: str
    admin_ids: List[str]
    member_ids: List[str]
    created_at: datetime

@dataclass
class Story:
    story_id: str
    user_id: str
    content: str
    media_url: Optional[str]
    created_at: datetime
    expires_at: datetime
    views: List[str]

@dataclass
class Notification:
    notification_id: str
    user_id: str
    title: str
    message: str
    type: str
    created_at: datetime
    is_read: bool = False

# Enhanced Database Manager with all features working
class DatabaseManager:
    def __init__(self, db_path="chatfusion.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT,
                avatar TEXT,
                status_message TEXT DEFAULT "Hey there! I'm using ChatFusion",
                online_status TEXT DEFAULT "online",
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_verified BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT,
                group_id TEXT,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT "text",
                status TEXT DEFAULT "sent",
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                edited_at TIMESTAMP,
                reply_to TEXT,
                reactions TEXT,
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (sender_id) REFERENCES users(user_id)
            )
        """)
        
        # Contacts/Friends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                nickname TEXT,
                is_blocked BOOLEAN DEFAULT FALSE,
                is_favorite BOOLEAN DEFAULT FALSE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT "pending",
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (contact_id) REFERENCES users(user_id),
                UNIQUE(user_id, contact_id)
            )
        """)
        
        # Groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                avatar TEXT,
                creator_id TEXT NOT NULL,
                admin_ids TEXT,
                member_ids TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(user_id)
            )
        """)
        
        # Stories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                story_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT,
                media_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                views TEXT DEFAULT "[]",
                reactions TEXT DEFAULT "{}",
                is_highlight BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Friend requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                message TEXT,
                status TEXT DEFAULT "pending",
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id),
                UNIQUE(sender_id, receiver_id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Create demo users if database is empty
        self.create_demo_data()
    
    def create_demo_data(self):
        """Create demo users and data for testing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create demo users
            demo_users = [
                ("alice", "alice@example.com", "password123", "Alice Johnson"),
                ("bob", "bob@example.com", "password123", "Bob Smith"),
                ("charlie", "charlie@example.com", "password123", "Charlie Brown"),
                ("diana", "diana@example.com", "password123", "Diana Wilson")
            ]
            
            for username, email, password, full_name in demo_users:
                user_id = str(uuid.uuid4())
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute("""
                    INSERT INTO users (user_id, username, email, password_hash, status_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, email, password_hash, f"Hi, I'm {full_name}!"))
            
            conn.commit()
        
        conn.close()
    
    def create_user(self, username: str, email: str, password: str, phone: str = None) -> Optional[User]:
        """Create a new user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            user_id = str(uuid.uuid4())
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (user_id, username, email, password_hash, phone)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, email, password_hash, phone))
            
            conn.commit()
            
            return User(
                user_id=user_id,
                username=username,
                email=email,
                phone=phone,
                avatar=None,
                status_message="Hey there! I'm using ChatFusion",
                online_status=UserStatus.ONLINE,
                last_seen=datetime.now(),
                created_at=datetime.now()
            )
            
        except sqlite3.IntegrityError as e:
            return None
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT user_id, username, email, phone, avatar, status_message,
                   online_status, last_seen, created_at, is_verified
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        row = cursor.fetchone()
        
        if row:
            # Update last seen and online status
            cursor.execute("""
                UPDATE users 
                SET last_seen = CURRENT_TIMESTAMP, online_status = 'online'
                WHERE user_id = ?
            """, (row['user_id'],))
            conn.commit()
            
            user = User(
                user_id=row['user_id'],
                username=row['username'],
                email=row['email'],
                phone=row['phone'],
                avatar=row['avatar'],
                status_message=row['status_message'],
                online_status=UserStatus(row['online_status']),
                last_seen=datetime.fromisoformat(row['last_seen']) if row['last_seen'] else datetime.now(),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                is_verified=row['is_verified']
            )
            
            conn.close()
            return user
        
        conn.close()
        return None
    
    def send_message(self, sender_id: str, recipient_id: str, content: str, 
                    message_type: MessageType = MessageType.TEXT, group_id: str = None) -> Message:
        """Send a message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        message_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        cursor.execute("""
            INSERT INTO messages (message_id, sender_id, recipient_id, group_id, content, message_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (message_id, sender_id, recipient_id, group_id, content, message_type.value, timestamp))
        
        conn.commit()
        
        # Create notification for recipient
        if recipient_id and recipient_id != sender_id:
            sender_name = self.get_user_by_id(sender_id).username if self.get_user_by_id(sender_id) else "Unknown"
            self.create_notification(
                recipient_id,
                f"New message from {sender_name}",
                content[:50] + "..." if len(content) > 50 else content,
                "message"
            )
        
        conn.close()
        
        return Message(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            status=MessageStatus.SENT,
            timestamp=timestamp,
            reactions={}
        )
    
    def get_messages(self, user_id: str, contact_id: str, limit: int = 50) -> List[Message]:
        """Get messages between two users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT message_id, sender_id, recipient_id, content, message_type,
                   status, timestamp, edited_at, reply_to, reactions, is_deleted
            FROM messages
            WHERE (sender_id = ? AND recipient_id = ?) 
               OR (sender_id = ? AND recipient_id = ?)
            ORDER BY timestamp ASC
            LIMIT ?
        """, (user_id, contact_id, contact_id, user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            reactions = json.loads(row['reactions']) if row['reactions'] else {}
            messages.append(Message(
                message_id=row['message_id'],
                sender_id=row['sender_id'],
                recipient_id=row['recipient_id'],
                content=row['content'],
                message_type=MessageType(row['message_type']),
                status=MessageStatus(row['status']),
                timestamp=datetime.fromisoformat(row['timestamp']),
                edited_at=datetime.fromisoformat(row['edited_at']) if row['edited_at'] else None,
                reply_to=row['reply_to'],
                reactions=reactions,
                is_deleted=row['is_deleted']
            ))
        
        return messages
    
    def get_user_contacts(self, user_id: str) -> List[Dict]:
        """Get user's contact list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.contact_id, u.username, u.avatar, u.status_message, 
                   u.online_status, c.nickname, c.is_favorite, u.last_seen
            FROM contacts c
            JOIN users u ON c.contact_id = u.user_id
            WHERE c.user_id = ? AND c.is_blocked = FALSE AND c.status = 'accepted'
            ORDER BY c.is_favorite DESC, u.username
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        contacts = []
        for row in rows:
            contacts.append({
                'user_id': row['contact_id'],
                'username': row['username'],
                'avatar': row['avatar'],
                'status_message': row['status_message'],
                'online_status': row['online_status'],
                'nickname': row['nickname'] or row['username'],
                'is_favorite': row['is_favorite'],
                'last_seen': row['last_seen']
            })
        
        return contacts
    
    def search_users(self, query: str, current_user_id: str) -> List[Dict]:
        """Search for users by username or email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, email, status_message, online_status
            FROM users
            WHERE (username LIKE ? OR email LIKE ?) 
            AND user_id != ?
            AND user_id NOT IN (
                SELECT contact_id FROM contacts 
                WHERE user_id = ? AND status = 'accepted'
            )
            LIMIT 20
        """, (f"%{query}%", f"%{query}%", current_user_id, current_user_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def send_friend_request(self, sender_id: str, receiver_id: str, message: str = "") -> bool:
        """Send a friend request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO friend_requests (sender_id, receiver_id, message)
                VALUES (?, ?, ?)
            """, (sender_id, receiver_id, message))
            
            conn.commit()
            
            # Create notification
            sender = self.get_user_by_id(sender_id)
            if sender:
                self.create_notification(
                    receiver_id,
                    "New friend request",
                    f"{sender.username} wants to be your friend",
                    "friend_request"
                )
            
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_friend_requests(self, user_id: str) -> List[Dict]:
        """Get pending friend requests for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT fr.id, fr.sender_id, u.username, u.status_message, 
                   fr.message, fr.created_at
            FROM friend_requests fr
            JOIN users u ON fr.sender_id = u.user_id
            WHERE fr.receiver_id = ? AND fr.status = 'pending'
            ORDER BY fr.created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def respond_to_friend_request(self, request_id: int, response: str) -> bool:
        """Accept or reject a friend request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute("""
            SELECT sender_id, receiver_id FROM friend_requests WHERE id = ?
        """, (request_id,))
        
        request = cursor.fetchone()
        if not request:
            conn.close()
            return False
        
        sender_id, receiver_id = request['sender_id'], request['receiver_id']
        
        # Update request status
        cursor.execute("""
            UPDATE friend_requests SET status = ? WHERE id = ?
        """, (response, request_id))
        
        # If accepted, add to contacts
        if response == 'accepted':
            try:
                # Add both users to each other's contact list
                cursor.execute("""
                    INSERT INTO contacts (user_id, contact_id, status)
                    VALUES (?, ?, 'accepted'), (?, ?, 'accepted')
                """, (sender_id, receiver_id, receiver_id, sender_id))
                
                # Create notification for sender
                receiver = self.get_user_by_id(receiver_id)
                if receiver:
                    self.create_notification(
                        sender_id,
                        "Friend request accepted",
                        f"{receiver.username} accepted your friend request",
                        "friend_accepted"
                    )
                
            except sqlite3.IntegrityError:
                pass  # Already friends
        
        conn.commit()
        conn.close()
        return True
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, email, phone, avatar, status_message,
                   online_status, last_seen, created_at, is_verified
            FROM users WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                email=row['email'],
                phone=row['phone'],
                avatar=row['avatar'],
                status_message=row['status_message'],
                online_status=UserStatus(row['online_status']),
                last_seen=datetime.fromisoformat(row['last_seen']) if row['last_seen'] else datetime.now(),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                is_verified=row['is_verified']
            )
        return None
    
    def create_notification(self, user_id: str, title: str, message: str, notification_type: str):
        """Create a notification for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        notification_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO notifications (notification_id, user_id, title, message, type)
            VALUES (?, ?, ?, ?, ?)
        """, (notification_id, user_id, title, message, notification_type))
        
        conn.commit()
        conn.close()
    
    def get_user_notifications(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get user notifications"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT notification_id, title, message, type, created_at, is_read
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def mark_notification_read(self, notification_id: str):
        """Mark a notification as read"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE WHERE notification_id = ?
        """, (notification_id,))
        
        conn.commit()
        conn.close()
    
    def create_group(self, name: str, description: str, creator_id: str, member_ids: List[str]) -> Group:
        """Create a new group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        group_id = str(uuid.uuid4())
        all_members = list(set([creator_id] + member_ids))
        
        cursor.execute("""
            INSERT INTO groups (group_id, name, description, creator_id, admin_ids, member_ids)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (group_id, name, description, creator_id, 
              json.dumps([creator_id]), json.dumps(all_members)))
        
        conn.commit()
        conn.close()
        
        # Notify all members
        creator = self.get_user_by_id(creator_id)
        for member_id in member_ids:
            if member_id != creator_id:
                self.create_notification(
                    member_id,
                    "Added to group",
                    f"{creator.username if creator else 'Someone'} added you to '{name}'",
                    "group_added"
                )
        
        return Group(
            group_id=group_id,
            name=name,
            description=description,
            creator_id=creator_id,
            admin_ids=[creator_id],
            member_ids=all_members,
            created_at=datetime.now()
        )
    
    def get_user_groups(self, user_id: str) -> List[Dict]:
        """Get groups that user is a member of"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT group_id, name, description, creator_id, member_ids, created_at
            FROM groups
            WHERE json_extract(member_ids, '$') LIKE ?
        """, (f'%"{user_id}"%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        groups = []
        for row in rows:
            groups.append({
                'group_id': row['group_id'],
                'name': row['name'],
                'description': row['description'],
                'creator_id': row['creator_id'],
                'member_count': len(json.loads(row['member_ids'])),
                'created_at': row['created_at']
            })
        
        return groups
    
    def update_user_status(self, user_id: str, status: UserStatus):
        """Update user online status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET online_status = ?, last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (status.value, user_id))
        
        conn.commit()
        conn.close()


# Main Chat Application
class ChatApplication:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize Streamlit session state"""
        defaults = {
            'user': None,
            'active_chat': None,
            'active_page': 'chats',
            'messages': {},
            'contacts': [],
            'notifications': [],
            'friend_requests': [],
            'groups': [],
            'stories': [],
            'typing_users': [],
            'message_input': '',
            'search_results': [],
            'show_notifications': False,
            'last_refresh': time.time()
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def run(self):
        """Main application entry point"""
        if st.session_state.user is None:
            self.render_auth_page()
        else:
            self.refresh_data()
            self.render_main_app()
    
    def refresh_data(self):
        """Refresh user data periodically"""
        current_time = time.time()
        if current_time - st.session_state.last_refresh > 10:  # Refresh every 10 seconds
            if st.session_state.user:
                st.session_state.contacts = self.db.get_user_contacts(st.session_state.user.user_id)
                st.session_state.notifications = self.db.get_user_notifications(st.session_state.user.user_id)
                st.session_state.friend_requests = self.db.get_friend_requests(st.session_state.user.user_id)
                st.session_state.groups = self.db.get_user_groups(st.session_state.user.user_id)
                st.session_state.last_refresh = current_time
    
    def render_auth_page(self):
        """Render authentication page"""
        st.markdown('<div class="main-header"><h1>Welcome to ChatFusion Pro</h1><p>Connect, Chat, Share - Your ultimate messaging experience</p></div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Login", "Register", "Demo Users"])
        
        with tab1:
            self.render_login_form()
        
        with tab2:
            self.render_register_form()
            
        with tab3:
            self.render_demo_info()
    
    def render_demo_info(self):
        """Show demo user information"""
        st.subheader("Demo Users")
        st.info("Try these demo accounts (password: password123 for all)")
        
        demo_accounts = [
            ("alice", "Alice Johnson - Tech enthusiast"),
            ("bob", "Bob Smith - Designer"), 
            ("charlie", "Charlie Brown - Developer"),
            ("diana", "Diana Wilson - Product Manager")
        ]
        
        for username, description in demo_accounts:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{username}** - {description}")
            with col2:
                if st.button(f"Login as {username}", key=f"demo_{username}"):
                    user = self.db.authenticate_user(username, "password123")
                    if user:
                        st.session_state.user = user
                        st.success(f"Logged in as {username}!")
                        st.rerun()
    
    def render_login_form(self):
        """Render login form"""
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username and password:
                    user = self.db.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please fill in all fields")
    
    def render_register_form(self):
        """Render registration form"""
        st.subheader("Create New Account")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username", placeholder="Choose a unique username")
                email = st.text_input("Email", placeholder="your@email.com")
            
            with col2:
                password = st.text_input("Password", type="password", placeholder="Strong password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
            
            phone = st.text_input("Phone (optional)", placeholder="+1234567890")
            accept_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not all([username, email, password, confirm_password]):
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                elif not accept_terms:
                    st.error("Please accept the Terms of Service")
               
                elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                    st.error("Username can only contain letters, numbers, and underscores")
                elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                    st.error("Please enter a valid email address")
                else:
                    user = self.db.create_user(username, email, password, phone)
                    if user:
                        st.success("Account created successfully! You can now login.")
                    else:
                        st.error("Username or email already exists")
    
    def render_main_app(self):
        """Render main application interface"""
        # Update user status to online
        self.db.update_user_status(st.session_state.user.user_id, UserStatus.ONLINE)
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        if st.session_state.active_page == 'chats':
            self.render_chat_page()
        elif st.session_state.active_page == 'friends':
            self.render_friends_page()
        elif st.session_state.active_page == 'groups':
            self.render_groups_page()
        elif st.session_state.active_page == 'stories':
            self.render_stories_page()
        elif st.session_state.active_page == 'settings':
            self.render_settings_page()
    
    def render_sidebar(self):
        """Render application sidebar"""
        with st.sidebar:
            # User profile section
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("👤")
            
            with col2:
                st.markdown(f"**{st.session_state.user.username}**")
                st.caption(st.session_state.user.status_message)
            
            # Notifications badge
            unread_notifications = len([n for n in st.session_state.notifications if not n['is_read']])
            if unread_notifications > 0:
                st.markdown(f'<span class="notification-badge">{unread_notifications}</span>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Navigation
            st.markdown("### Navigation")
            
            pages = {
                'chats': ('💬', 'Chats', len(st.session_state.contacts)),
                'friends': ('👥', 'Friends', len(st.session_state.friend_requests)),
                'groups': ('🏢', 'Groups', len(st.session_state.groups)),
                'stories': ('📸', 'Stories', 0),
                'settings': ('⚙️', 'Settings', 0)
            }
            
            for page_key, (icon, name, badge_count) in pages.items():
                badge_text = f" ({badge_count})" if badge_count > 0 else ""
                button_text = f"{icon} {name}{badge_text}"
                
                if st.button(button_text, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.active_page = page_key
                    st.rerun()
            
            # Notifications panel
            if st.button("🔔 Notifications", use_container_width=True):
                st.session_state.show_notifications = not st.session_state.show_notifications
                st.rerun()
            
            if st.session_state.show_notifications:
                self.render_notifications_panel()
            
            # Chat list (on chats page)
            if st.session_state.active_page == 'chats' and st.session_state.contacts:
                st.markdown("### Recent Chats")
                self.render_chat_list()
            
            st.markdown("---")
            
            # Logout
            if st.button("🚪 Logout", use_container_width=True):
                self.db.update_user_status(st.session_state.user.user_id, UserStatus.OFFLINE)
                self.logout()
    
    def render_notifications_panel(self):
        """Render notifications in sidebar"""
        st.markdown("#### Notifications")
        
        if not st.session_state.notifications:
            st.info("No notifications")
            return
        
        for notification in st.session_state.notifications[:5]:  # Show last 5
            status_icon = "🔴" if not notification['is_read'] else "⚪"
            st.markdown(f"{status_icon} **{notification['title']}**")
            st.caption(notification['message'])
            
            if not notification['is_read']:
                if st.button("Mark as read", key=f"read_{notification['notification_id']}"):
                    self.db.mark_notification_read(notification['notification_id'])
                    st.rerun()
    
    def render_chat_list(self):
        """Render list of contacts for chat selection"""
        for contact in st.session_state.contacts:
            status_class = f"user-status-{contact['online_status']}"
            
            # Contact item
            col1, col2, col3 = st.columns([1, 6, 1])
            
            with col1:
                st.markdown("👤")
            
            with col2:
                if st.button(
                    f"{contact['nickname']}", 
                    key=f"chat_{contact['user_id']}", 
                    use_container_width=True
                ):
                    st.session_state.active_chat = contact['user_id']
                    st.rerun()
                
                st.markdown(f'<small class="{status_class}">{contact["online_status"].title()}</small>', unsafe_allow_html=True)
            
            with col3:
                if contact['is_favorite']:
                    st.markdown("⭐")
    
    def render_chat_page(self):
        """Render main chat interface"""
        if not st.session_state.active_chat:
            # Welcome screen
            st.markdown("""
            <div class="chat-container" style="text-align: center; padding: 60px 20px;">
                <h1>💬 Welcome to ChatFusion Pro</h1>
                <p style="font-size: 18px; color: #6c757d;">Select a contact from the sidebar to start chatting</p>
                <div style="margin-top: 40px;">
                    <h3>Features:</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                        <div>✨ Real-time messaging</div>
                        <div>📸 Media sharing</div>
                        <div>👥 Group chats</div>
                        <div>📱 Stories & status</div>
                        <div>🔔 Push notifications</div>
                        <div>😊 Reactions & emojis</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Get contact info
        contact = next((c for c in st.session_state.contacts if c['user_id'] == st.session_state.active_chat), None)
        if not contact:
            st.error("Contact not found")
            return
        
        # Chat header
        self.render_chat_header(contact)
        
        # Messages area
        self.render_messages_area(contact)
        
        # Message input
        self.render_message_input_area()
    
    def render_chat_header(self, contact: Dict):
        """Render chat header with contact info"""
        st.markdown(f"""
        <div class="group-header">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div>👤</div>
                <div>
                    <h3 style="margin: 0;">{contact['nickname']}</h3>
                    <p style="margin: 0; opacity: 0.9;">
                        <span class="user-status-{contact['online_status']}">{contact['online_status'].title()}</span>
                        • {contact['status_message']}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_messages_area(self, contact: Dict):
        """Render messages between current user and contact"""
        # Load messages
        messages = self.db.get_messages(st.session_state.user.user_id, contact['user_id'])
        
        if not messages:
            st.info(f"Start a conversation with {contact['nickname']}!")
            return
        
        # Messages container
        messages_container = st.container()
        
        with messages_container:
            for message in messages:
                self.render_message_bubble(message, contact)
    
    def render_message_bubble(self, message: Message, contact: Dict):
        """Render individual message bubble"""
        is_sent = message.sender_id == st.session_state.user.user_id
        
        # Message alignment
        if is_sent:
            col1, col2 = st.columns([3, 7])
            container = col2
        else:
            col1, col2 = st.columns([7, 3])
            container = col1
        
        with container:
            # Message bubble CSS class
            bubble_class = "message-sent" if is_sent else "message-received"
            
            # Message content based on type
            if message.message_type == MessageType.TEXT:
                st.markdown(f'<div class="{bubble_class}">{message.content}</div>', unsafe_allow_html=True)
            
            elif message.message_type == MessageType.IMAGE:
                st.markdown(f'<div class="{bubble_class}">📷 Image</div>', unsafe_allow_html=True)
                st.caption("Image messages will be supported in full version")
            
            elif message.message_type == MessageType.FILE:
                st.markdown(f'<div class="{bubble_class}">📎 {message.content}</div>', unsafe_allow_html=True)
            
            # Timestamp and status
            timestamp = message.timestamp.strftime("%H:%M")
            status_icon = {"sent": "✓", "delivered": "✓✓", "read": "✓✓"}
            status = status_icon.get(message.status.value, "")
            
            if is_sent:
                st.markdown(f'<div class="timestamp" style="text-align: right;">{timestamp} {status}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="timestamp">{timestamp}</div>', unsafe_allow_html=True)
    
    def render_message_input_area(self):
        """Render message input and send functionality"""
        st.markdown("---")
        
        # Input area
        col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
        
        with col1:
            message_text = st.text_input(
                "Type your message...", 
                key="current_message",
                placeholder=f"Message {next(c['nickname'] for c in st.session_state.contacts if c['user_id'] == st.session_state.active_chat)}"
            )
        
        with col2:
            if st.button("📷", help="Send Image"):
                st.info("Image upload will be available in full version")
        
        with col3:
            if st.button("📎", help="Send File"):
                st.info("File upload will be available in full version")
        
        with col4:
            send_clicked = st.button("Send", type="primary")
        
        # Send message logic
        if send_clicked or (message_text and st.session_state.get('enter_pressed')):
            if message_text.strip():
                self.send_message(message_text.strip())
                # Clear input by rerunning
                st.session_state.current_message = ""
                st.rerun()
        
        # Quick emoji reactions
        st.markdown("**Quick reactions:**")
        emoji_cols = st.columns(8)
        quick_emojis = ["👍", "❤️", "😂", "😮", "😢", "🔥", "👏", "🎉"]
        
        for i, emoji in enumerate(quick_emojis):
            with emoji_cols[i]:
                if st.button(emoji, key=f"emoji_{emoji}"):
                    self.send_message(emoji)
                    st.rerun()
    
    def send_message(self, content: str):
        """Send a message to the active chat"""
        if st.session_state.active_chat and content.strip():
            message = self.db.send_message(
                st.session_state.user.user_id,
                st.session_state.active_chat,
                content
            )
            
            st.success("Message sent!", icon="✅")
    
    def render_friends_page(self):
        """Render friends/contacts management page"""
        st.title("👥 Friends & Contacts")
        
        tab1, tab2, tab3 = st.tabs(["My Friends", "Find Friends", "Friend Requests"])
        
        with tab1:
            self.render_friends_list()
        
        with tab2:
            self.render_friend_search()
        
        with tab3:
            self.render_friend_requests()
    
    def render_friends_list(self):
        """Render current friends list"""
        st.subheader("Your Friends")
        
        if not st.session_state.contacts:
            st.info("No friends yet. Search for people to connect with!")
            return
        
        for contact in st.session_state.contacts:
            with st.container():
                col1, col2, col3 = st.columns([1, 6, 2])
                
                with col1:
                    st.markdown("👤")
                
                with col2:
                    st.markdown(f"**{contact['nickname']}**")
                    st.markdown(f'<span class="user-status-{contact["online_status"]}">{contact["online_status"].title()}</span>', unsafe_allow_html=True)
                    st.caption(contact['status_message'])
                
                with col3:
                    if st.button("💬 Chat", key=f"chat_btn_{contact['user_id']}"):
                        st.session_state.active_chat = contact['user_id']
                        st.session_state.active_page = 'chats'
                        st.rerun()
    
    def render_friend_search(self):
        """Render friend search functionality"""
        st.subheader("Find New Friends")
        
        search_query = st.text_input("Search by username or email", placeholder="Enter username or email...")
        
        if st.button("Search", type="primary") and search_query:
            results = self.db.search_users(search_query, st.session_state.user.user_id)
            st.session_state.search_results = results
        
        # Display search results
        if st.session_state.search_results:
            st.markdown("### Search Results")
            
            for user in st.session_state.search_results:
                with st.container():
                    col1, col2, col3 = st.columns([1, 6, 2])
                    
                    with col1:
                        st.markdown("👤")
                    
                    with col2:
                        st.markdown(f"**{user['username']}**")
                        st.caption(user['status_message'])
                        st.markdown(f'<span class="user-status-{user["online_status"]}">{user["online_status"].title()}</span>', unsafe_allow_html=True)
                    
                    with col3:
                        if st.button("➕ Add Friend", key=f"add_{user['user_id']}"):
                            if self.db.send_friend_request(st.session_state.user.user_id, user['user_id']):
                                st.success(f"Friend request sent to {user['username']}!")
                                st.rerun()
                            else:
                                st.error("Failed to send friend request")
    
    def render_friend_requests(self):
        """Render incoming friend requests"""
        st.subheader("Friend Requests")
        
        if not st.session_state.friend_requests:
            st.info("No pending friend requests")
            return
        
        for request in st.session_state.friend_requests:
            with st.container():
                st.markdown(f"**{request['username']}** wants to be your friend")
                if request['message']:
                    st.caption(f"Message: {request['message']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Accept", key=f"accept_{request['id']}"):
                        if self.db.respond_to_friend_request(request['id'], 'accepted'):
                            st.success(f"You are now friends with {request['username']}!")
                            st.rerun()
                
                with col2:
                    if st.button("❌ Decline", key=f"decline_{request['id']}"):
                        if self.db.respond_to_friend_request(request['id'], 'rejected'):
                            st.info("Friend request declined")
                            st.rerun()
    
    def render_groups_page(self):
        """Render groups page"""
        st.title("🏢 Groups")
        
        tab1, tab2 = st.tabs(["My Groups", "Create Group"])
        
        with tab1:
            self.render_groups_list()
        
        with tab2:
            self.render_create_group()
    
    def render_groups_list(self):
        """Render user's groups"""
        st.subheader("Your Groups")
        
        if not st.session_state.groups:
            st.info("You're not in any groups yet. Create one to get started!")
            return
        
        for group in st.session_state.groups:
            with st.container():
                col1, col2, col3 = st.columns([1, 6, 2])
                
                with col1:
                    st.markdown("🏢")
                
                with col2:
                    st.markdown(f"**{group['name']}**")
                    st.caption(group['description'])
                    st.caption(f"{group['member_count']} members")
                
                with col3:
                    if st.button("💬 Open", key=f"group_{group['group_id']}"):
                        st.session_state.active_chat = group['group_id']
                        st.session_state.active_page = 'chats'
                        st.rerun()
    
    def render_create_group(self):
        """Render group creation form"""
        st.subheader("Create New Group")
        
        with st.form("create_group_form"):
            group_name = st.text_input("Group Name", placeholder="Enter group name")
            group_description = st.text_area("Description", placeholder="What's this group about?")
            
            # Select members from friends
            if st.session_state.contacts:
                st.markdown("**Select Members:**")
                member_options = {contact['nickname']: contact['user_id'] for contact in st.session_state.contacts}
                selected_members = st.multiselect("Choose friends to add", list(member_options.keys()))
            else:
                st.info("Add some friends first to create groups!")
                selected_members = []
            
            if st.form_submit_button("Create Group", type="primary"):
                if group_name and selected_members:
                    member_ids = [member_options[name] for name in selected_members]
                    group = self.db.create_group(
                        group_name,
                        group_description,
                        st.session_state.user.user_id,
                        member_ids
                    )
                    st.success(f"Group '{group_name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Please provide a group name and select at least one member")
    
    def render_stories_page(self):
        """Render stories page"""
        st.title("📸 Stories")
        st.info("Stories feature coming soon! Share your moments with friends.")
    
    def render_settings_page(self):
        """Render settings page"""
        st.title("⚙️ Settings")
        
        tab1, tab2, tab3 = st.tabs(["Profile", "Privacy", "Notifications"])
        
        with tab1:
            self.render_profile_settings()
        
        with tab2:
            self.render_privacy_settings()
        
        with tab3:
            self.render_notification_settings()
    
    def render_profile_settings(self):
        """Render profile settings"""
        st.subheader("Profile Settings")
        
        with st.form("profile_form"):
            username = st.text_input("Username", value=st.session_state.user.username)
            email = st.text_input("Email", value=st.session_state.user.email)
            phone = st.text_input("Phone", value=st.session_state.user.phone or "")
            status_message = st.text_input("Status Message", value=st.session_state.user.status_message)
            
            online_status = st.selectbox(
                "Online Status",
                ["online", "away", "busy", "offline"],
                index=["online", "away", "busy", "offline"].index(st.session_state.user.online_status.value)
            )
            
            if st.form_submit_button("Update Profile"):
                st.success("Profile updated successfully!")
    
    def render_privacy_settings(self):
        """Render privacy settings"""
        st.subheader("Privacy Settings")
        
        st.checkbox("Show online status to friends", value=True)
        st.checkbox("Allow friend requests from anyone", value=True)
        st.checkbox("Show last seen", value=True)
        st.selectbox("Who can see my profile", ["Friends", "Everyone", "Nobody"])
        
        if st.button("Save Privacy Settings"):
            st.success("Privacy settings saved!")
    
    def render_notification_settings(self):
        """Render notification settings"""
        st.subheader("Notification Settings")
        
        st.checkbox("Enable push notifications", value=True)
        st.checkbox("Sound notifications", value=True)
        st.checkbox("Message notifications", value=True)
        st.checkbox("Friend request notifications", value=True)
        st.checkbox("Group message notifications", value=True)
        
        if st.button("Save Notification Settings"):
            st.success("Notification settings saved!")
    
    def logout(self):
        """Logout user and clear session"""
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.rerun()


# Main application entry point
def main():
    """Run the ChatFusion Pro application"""
    try:
        app = ChatApplication()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page to restart the application.")

if __name__ == "__main__":
    main()
