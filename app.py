import streamlit as st
import sqlite3
import hashlib
import datetime
import uuid
import time
import json
import base64
from PIL import Image
import io
import os
from typing import Dict, List, Optional, Tuple

# Page configuration
st.set_page_config(
    page_title="ChatFlow - Advanced Messaging",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, WhatsApp-inspired design
st.markdown("""
<style>
    /* Global styles */
    .main {
        padding: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #25d366 0%, #128c7e 100%);
        color: white;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        height: 70vh;
        overflow-y: auto;
    }
    
    /* Message bubbles */
    .message-sent {
        background: linear-gradient(135deg, #dcf8c6 0%, #b8e6b8 100%);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 8px 0 8px auto;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        position: relative;
        animation: slideInRight 0.3s ease;
    }
    
    .message-received {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 8px auto 8px 0;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        position: relative;
        animation: slideInLeft 0.3s ease;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Chat list item */
    .chat-item {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .chat-item:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Story circle */
    .story-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(45deg, #833ab4, #fd1d1d, #fcb045);
        padding: 3px;
        display: inline-block;
        margin: 0 10px;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .story-circle:hover {
        transform: scale(1.1);
    }
    
    .story-inner {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #333;
    }
    
    /* Status indicators */
    .online-indicator {
        width: 12px;
        height: 12px;
        background: #4CAF50;
        border-radius: 50%;
        display: inline-block;
        margin-left: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Input styling */
    .stTextInput input {
        border-radius: 25px;
        border: 2px solid #25d366;
        padding: 12px 20px;
        font-size: 16px;
    }
    
    .stTextInput input:focus {
        box-shadow: 0 0 0 3px rgba(37, 211, 102, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
    }
    
    /* Profile card */
    .profile-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-flex;
        align-items: center;
        padding: 8px 12px;
        background: #f0f0f0;
        border-radius: 12px;
        margin: 8px 0;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #999;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    /* Media preview */
    .media-preview {
        border-radius: 12px;
        overflow: hidden;
        margin: 8px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .media-preview:hover {
        transform: scale(1.02);
    }
    
    /* Notification badge */
    .notification-badge {
        background: #ff4757;
        color: white;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 12px;
        font-weight: bold;
        position: absolute;
        top: -5px;
        right: -5px;
        min-width: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class DatabaseManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize the database with all required tables"""
        conn = sqlite3.connect('chatflow.db')
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                avatar_url TEXT,
                bio TEXT,
                status TEXT DEFAULT 'Hey there! I am using ChatFlow.',
                is_online BOOLEAN DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                privacy_settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                chat_type TEXT NOT NULL CHECK (chat_type IN ('individual', 'group', 'channel')),
                name TEXT,
                description TEXT,
                avatar_url TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}',
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                content TEXT,
                message_type TEXT DEFAULT 'text',
                media_url TEXT,
                reply_to TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                edited_at TIMESTAMP,
                deleted_at TIMESTAMP,
                is_forwarded BOOLEAN DEFAULT 0,
                reactions TEXT DEFAULT '{}',
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                FOREIGN KEY (sender_id) REFERENCES users (user_id),
                FOREIGN KEY (reply_to) REFERENCES messages (message_id)
            )
        ''')
        
        # Chat participants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_participants (
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_muted BOOLEAN DEFAULT 0,
                PRIMARY KEY (chat_id, user_id),
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Stories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                story_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT,
                media_url TEXT,
                story_type TEXT DEFAULT 'text',
                background_color TEXT DEFAULT '#ffffff',
                expiry_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                view_count INTEGER DEFAULT 0,
                privacy_settings TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Story views table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_views (
                story_id TEXT NOT NULL,
                viewer_id TEXT NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (story_id, viewer_id),
                FOREIGN KEY (story_id) REFERENCES stories (story_id),
                FOREIGN KEY (viewer_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str, phone: str = None) -> bool:
        """Create a new user"""
        try:
            conn = sqlite3.connect('chatflow.db')
            cursor = conn.cursor()
            
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (user_id, username, email, password_hash, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, phone))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        conn = sqlite3.connect('chatflow.db')
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT user_id, username, email, phone, avatar_url, bio, status
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'email': result[2],
                'phone': result[3],
                'avatar_url': result[4],
                'bio': result[5],
                'status': result[6]
            }
        return None
    
    def get_user_chats(self, user_id: str) -> List[Dict]:
        """Get all chats for a user"""
        conn = sqlite3.connect('chatflow.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.chat_id, c.chat_type, c.name, c.avatar_url, c.created_at,
                   (SELECT content FROM messages WHERE chat_id = c.chat_id 
                    ORDER BY timestamp DESC LIMIT 1) as last_message,
                   (SELECT timestamp FROM messages WHERE chat_id = c.chat_id 
                    ORDER BY timestamp DESC LIMIT 1) as last_message_time
            FROM chats c
            JOIN chat_participants cp ON c.chat_id = cp.chat_id
            WHERE cp.user_id = ?
            ORDER BY last_message_time DESC
        ''', (user_id,))
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                'chat_id': row[0],
                'chat_type': row[1],
                'name': row[2] or 'Unknown',
                'avatar_url': row[3],
                'created_at': row[4],
                'last_message': row[5] or 'No messages yet',
                'last_message_time': row[6]
            })
        
        conn.close()
        return chats
    
    def get_chat_messages(self, chat_id: str, limit: int = 50) -> List[Dict]:
        """Get messages for a specific chat"""
        conn = sqlite3.connect('chatflow.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.message_id, m.sender_id, m.content, m.message_type, 
                   m.media_url, m.timestamp, u.username, u.avatar_url, m.reactions
            FROM messages m
            JOIN users u ON m.sender_id = u.user_id
            WHERE m.chat_id = ? AND m.deleted_at IS NULL
            ORDER BY m.timestamp DESC
            LIMIT ?
        ''', (chat_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message_id': row[0],
                'sender_id': row[1],
                'content': row[2],
                'message_type': row[3],
                'media_url': row[4],
                'timestamp': row[5],
                'sender_name': row[6],
                'sender_avatar': row[7],
                'reactions': json.loads(row[8] or '{}')
            })
        
        conn.close()
        return list(reversed(messages))
    
    def send_message(self, chat_id: str, sender_id: str, content: str, 
                    message_type: str = 'text', media_url: str = None) -> bool:
        """Send a new message"""
        try:
            conn = sqlite3.connect('chatflow.db')
            cursor = conn.cursor()
            
            message_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO messages (message_id, chat_id, sender_id, content, message_type, media_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, chat_id, sender_id, content, message_type, media_url))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def create_chat(self, chat_type: str, name: str, created_by: str, participants: List[str]) -> str:
        """Create a new chat"""
        conn = sqlite3.connect('chatflow.db')
        cursor = conn.cursor()
        
        chat_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO chats (chat_id, chat_type, name, created_by)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, chat_type, name, created_by))
        
        # Add participants
        for user_id in participants:
            cursor.execute('''
                INSERT OR IGNORE INTO chat_participants (chat_id, user_id)
                VALUES (?, ?)
            ''', (chat_id, user_id))
        
        conn.commit()
        conn.close()
        return chat_id
    
    def get_user_stories(self, user_id: str) -> List[Dict]:
        """Get active stories for a user"""
        conn = sqlite3.connect('chatflow.db')
        cursor = conn.cursor()
        
        cursor.execute('''
    SELECT s.story_id, s.content, s.media_url, s.story_type, 
           s.background_color, s.created_at, s.view_count, u.username, u.avatar_url
    FROM stories s
    JOIN users u ON s.user_id = u.user_id
    WHERE s.expiry_time > datetime('now') 
    ORDER BY s.created_at DESC
''')

        
        stories = []
        for row in cursor.fetchall():
            stories.append({
                'story_id': row[0],
                'content': row[1],
                'media_url': row[2],
                'story_type': row[3],
                'background_color': row[4],
                'created_at': row[5],
                'view_count': row[6],
                'username': row[7],
                'avatar_url': row[8]
            })
        
        conn.close()
        return stories

class ChatFlowApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'current_chat' not in st.session_state:
            st.session_state.current_chat = None
        if 'chats' not in st.session_state:
            st.session_state.chats = []
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'page' not in st.session_state:
            st.session_state.page = 'login'
        if 'typing_users' not in st.session_state:
            st.session_state.typing_users = []
        if 'theme' not in st.session_state:
            st.session_state.theme = 'light'
    
    def render_login_page(self):
        """Render the login/register page"""
        st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 2rem;'>Welcome to ChatFlow</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="profile-card">
                <h2 style="color: white; margin-bottom: 1rem;">💬 Advanced Messaging Platform</h2>
                <p style="color: rgba(255,255,255,0.8); margin-bottom: 2rem;">
                    Connect, share, and communicate with friends and family
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                st.markdown("### Sign In")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                
                if st.button("Sign In", key="login_btn"):
                    user = self.db.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = 'main'
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            with tab2:
                st.markdown("### Create Account")
                new_username = st.text_input("Username", key="reg_username")
                new_email = st.text_input("Email", key="reg_email")
                new_phone = st.text_input("Phone (optional)", key="reg_phone")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                if st.button("Create Account", key="register_btn"):
                    if new_password != confirm_password:
                        st.error("Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    elif self.db.create_user(new_username, new_email, new_password, new_phone):
                        st.success("Account created successfully! Please sign in.")
                    else:
                        st.error("Username or email already exists")
    
    def render_sidebar(self):
        """Render the sidebar with chats and navigation"""
        with st.sidebar:
            # User profile section
            st.markdown(f"""
            <div class="profile-card">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="width: 50px; height: 50px; background: linear-gradient(45deg, #25d366, #128c7e); 
                                border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                                color: white; font-weight: bold; font-size: 18px; margin-right: 12px;">
                        {st.session_state.user['username'][0].upper()}
                    </div>
                    <div>
                        <div style="color: white; font-weight: bold;">{st.session_state.user['username']}</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 12px;">
                            {st.session_state.user.get('status', 'Hey there! I am using ChatFlow.')}
                            <span class="online-indicator"></span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Navigation menu
            st.markdown("### Menu")
            menu_option = st.selectbox("", [
                "💬 Chats", 
                "📺 Stories", 
                "📢 Channels", 
                "👥 Groups", 
                "📞 Calls", 
                "⚙️ Settings"
            ], key="menu_select")
            
            if menu_option == "💬 Chats":
                self.render_chat_list()
            elif menu_option == "📺 Stories":
                self.render_stories_section()
            elif menu_option == "👥 Groups":
                self.render_groups_section()
            elif menu_option == "⚙️ Settings":
                self.render_settings_section()
            
            # Logout button
            if st.button("🚪 Logout", key="logout_btn"):
                st.session_state.clear()
                st.rerun()
    
    def render_chat_list(self):
        """Render the list of chats"""
        st.markdown("#### Recent Chats")
        
        # Refresh chats
        st.session_state.chats = self.db.get_user_chats(st.session_state.user['user_id'])
        
        # New chat button
        if st.button("➕ New Chat", key="new_chat_btn"):
            st.session_state.show_new_chat = True
        
        # Display chat list
        for chat in st.session_state.chats:
            chat_time = datetime.datetime.fromisoformat(chat['last_message_time']).strftime("%H:%M") if chat['last_message_time'] else ""
            
            st.markdown(f"""
            <div class="chat-item" onclick="selectChat('{chat['chat_id']}')">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <div style="width: 40px; height: 40px; background: linear-gradient(45deg, #ff6b6b, #ee5a24); 
                                    border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                                    color: white; font-weight: bold; margin-right: 12px;">
                            {chat['name'][0].upper()}
                        </div>
                        <div>
                            <div style="color: white; font-weight: bold; font-size: 14px;">{chat['name']}</div>
                            <div style="color: rgba(255,255,255,0.7); font-size: 12px; max-width: 150px; 
                                        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {chat['last_message']}
                            </div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: rgba(255,255,255,0.6); font-size: 11px;">{chat_time}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Handle chat selection
            if st.button(f"Open {chat['name']}", key=f"open_{chat['chat_id']}", type="secondary"):
                st.session_state.current_chat = chat
                st.session_state.messages = self.db.get_chat_messages(chat['chat_id'])
                st.rerun()
    
    def render_stories_section(self):
        """Render stories section"""
        st.markdown("#### Stories")
        
        # Add story button
        if st.button("📷 Add Story", key="add_story_btn"):
            st.session_state.show_story_creator = True
        
        # Stories list
        stories = self.db.get_user_stories(st.session_state.user['user_id'])
        
        for i in range(0, len(stories), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(stories):
                    story = stories[i + j]
                    with col:
                        st.markdown(f"""
                        <div class="story-circle">
                            <div class="story-inner">
                                {story['username'][0].upper()}
                            </div>
                        </div>
                        <div style="color: white; text-align: center; font-size: 12px; margin-top: 5px;">
                            {story['username'][:8]}...
                        </div>
                        """, unsafe_allow_html=True)
    
    def render_groups_section(self):
        """Render groups section"""
        st.markdown("#### Groups")
        
        if st.button("👥 Create Group", key="create_group_btn"):
            st.session_state.show_group_creator = True
        
        # List user's groups
        group_chats = [chat for chat in st.session_state.chats if chat['chat_type'] == 'group']
        
        for group in group_chats:
            st.markdown(f"""
            <div class="chat-item">
                <div style="display: flex; align-items: center;">
                    <div style="width: 40px; height: 40px; background: linear-gradient(45deg, #4834d4, #686de0); 
                                border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                                color: white; font-weight: bold; margin-right: 12px;">
                        👥
                    </div>
                    <div>
                        <div style="color: white; font-weight: bold;">{group['name']}</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 12px;">Group • 5 members</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_settings_section(self):
        """Render settings section"""
        st.markdown("#### Settings")
        
        # Theme selection
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], key="theme_select")
        
        # Privacy settings
        st.markdown("**Privacy**")
        show_last_seen = st.checkbox("Show last seen", value=True)
        show_profile_photo = st.checkbox("Show profile photo to everyone", value=True)
        
        # Notification settings
        st.markdown("**Notifications**")
        message_notifications = st.checkbox("Message notifications", value=True)
        group_notifications = st.checkbox("Group notifications", value=True)
        
        # Account settings
        st.markdown("**Account**")
        if st.button("Edit Profile", key="edit_profile_btn"):
            st.session_state.show_profile_editor = True
        
        if st.button("Change Password", key="change_password_btn"):
            st.session_state.show_password_change = True
    
    def render_main_chat_area(self):
        """Render the main chat interface"""
        if not st.session_state.current_chat:
            # Welcome screen
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: center; height: 60vh; flex-direction: column;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">💬</div>
                <h2 style="color: #666; text-align: center;">Welcome to ChatFlow</h2>
                <p style="color: #999; text-align: center; max-width: 400px;">
                    Select a chat from the sidebar to start messaging, or create a new chat to connect with friends.
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Chat header
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); 
                        padding: 15px 20px; border-radius: 15px 15px 0 0; margin-bottom: 0;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 45px; height: 45px; background: rgba(255,255,255,0.2); 
                                border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                                color: white; font-weight: bold; margin-right: 15px;">
                        {st.session_state.current_chat['name'][0].upper()}
                    </div>
                    <div>
                        <div style="color: white; font-weight: bold; font-size: 16px;">
                            {st.session_state.current_chat['name']}
                        </div>
                        <div style="color: rgba(255,255,255,0.8); font-size: 12px;">
                            Online <span class="online-indicator"></span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📞", key="voice_call_btn"):
                st.info("Voice call feature - Coming soon!")
        
        with col3:
            if st.button("📹", key="video_call_btn"):
                st.info("Video call feature - Coming soon!")
        
        # Messages container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display messages
        for message in st.session_state.messages:
            is_sent = message['sender_id'] == st.session_state.user['user_id']
            
            if is_sent:
                st.markdown(f"""
                <div class="message-sent">
                    <div style="margin-bottom: 5px;">{message['content']}</div>
                    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 5px;">
                        <span style="font-size: 11px; color: #666;">
                            {datetime.datetime.fromisoformat(message['timestamp']).strftime('%H:%M')}
                        </span>
                        <span style="color: #4CAF50;">✓✓</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-received">
                    <div style="font-size: 12px; color: #25d366; font-weight: bold; margin-bottom: 3px;">
                        {message['sender_name']}
                    </div>
                    <div style="margin-bottom: 5px;">{message['content']}</div>
                    <div style="font-size: 11px; color: #666; text-align: right;">
                        {datetime.datetime.fromisoformat(message['timestamp']).strftime('%H:%M')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Typing indicator
        if st.session_state.typing_users:
            st.markdown("""
            <div class="typing-indicator">
                <span style="margin-right: 8px; font-size: 12px; color: #666;">Someone is typing</span>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input area
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 6, 1, 1])
        
        with col1:
            if st.button("📎", key="attach_btn"):
                st.session_state.show_attachment_menu = True
        
        with col2:
            if st.button("😊", key="emoji_btn"):
                st.session_state.show_emoji_picker = True
        
        with col3:
            new_message = st.text_input("", placeholder="Type a message...", key="message_input")
        
        with col4:
            if st.button("🎤", key="voice_btn"):
                st.info("Voice message feature - Coming soon!")
        
        with col5:
            if st.button("📤", key="send_btn") or (new_message and st.session_state.get("enter_pressed")):
                if new_message.strip():
                    success = self.db.send_message(
                        st.session_state.current_chat['chat_id'],
                        st.session_state.user['user_id'],
                        new_message
                    )
                    if success:
                        st.session_state.messages = self.db.get_chat_messages(st.session_state.current_chat['chat_id'])
                        st.rerun()
    
    def render_attachment_menu(self):
        """Render attachment menu popup"""
        if st.session_state.get('show_attachment_menu'):
            st.markdown("### Share")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📷 Camera", key="camera_btn"):
                    st.info("Camera feature - Coming soon!")
                    st.session_state.show_attachment_menu = False
                
                if st.button("🖼️ Gallery", key="gallery_btn"):
                    uploaded_file = st.file_uploader("Choose image", type=['jpg', 'jpeg', 'png', 'gif'])
                    if uploaded_file:
                        st.success("Image uploaded! Feature in development.")
                        st.session_state.show_attachment_menu = False
            
            with col2:
                if st.button("📄 Document", key="document_btn"):
                    uploaded_file = st.file_uploader("Choose document", type=['pdf', 'doc', 'docx', 'txt'])
                    if uploaded_file:
                        st.success("Document uploaded! Feature in development.")
                        st.session_state.show_attachment_menu = False
                
                if st.button("🎵 Audio", key="audio_btn"):
                    uploaded_file = st.file_uploader("Choose audio", type=['mp3', 'wav', 'ogg'])
                    if uploaded_file:
                        st.success("Audio uploaded! Feature in development.")
                        st.session_state.show_attachment_menu = False
            
            with col3:
                if st.button("📍 Location", key="location_btn"):
                    st.info("Location sharing - Coming soon!")
                    st.session_state.show_attachment_menu = False
                
                if st.button("👤 Contact", key="contact_btn"):
                    st.info("Contact sharing - Coming soon!")
                    st.session_state.show_attachment_menu = False
            
            if st.button("❌ Cancel", key="cancel_attach_btn"):
                st.session_state.show_attachment_menu = False
    
    def render_emoji_picker(self):
        """Render emoji picker"""
        if st.session_state.get('show_emoji_picker'):
            st.markdown("### Emojis")
            
            emojis = ["😀", "😂", "😍", "🤔", "😢", "😡", "👍", "👎", "❤️", "🎉", 
                     "🔥", "💯", "😎", "🤗", "😴", "🙄", "😱", "🤯", "🥳", "😇"]
            
            cols = st.columns(5)
            for i, emoji in enumerate(emojis):
                with cols[i % 5]:
                    if st.button(emoji, key=f"emoji_{i}"):
                        # Add emoji to message input
                        current_message = st.session_state.get('message_input', '')
                        st.session_state.message_input = current_message + emoji
                        st.session_state.show_emoji_picker = False
                        st.rerun()
            
            if st.button("❌ Close", key="close_emoji_btn"):
                st.session_state.show_emoji_picker = False
    
    def render_new_chat_dialog(self):
        """Render new chat creation dialog"""
        if st.session_state.get('show_new_chat'):
            st.markdown("### Start New Chat")
            
            chat_type = st.selectbox("Chat Type", ["Individual", "Group", "Channel"])
            
            if chat_type == "Individual":
                username = st.text_input("Enter username to chat with")
                if st.button("Start Chat", key="start_individual_chat"):
                    if username:
                        # Create individual chat
                        chat_id = self.db.create_chat('individual', f"Chat with {username}", 
                                                    st.session_state.user['user_id'], 
                                                    [st.session_state.user['user_id']])
                        st.success(f"Chat with {username} created!")
                        st.session_state.show_new_chat = False
                        st.rerun()
            
            elif chat_type == "Group":
                group_name = st.text_input("Group Name")
                group_description = st.text_area("Group Description (optional)")
                members = st.text_area("Add members (usernames, one per line)")
                
                if st.button("Create Group", key="create_group"):
                    if group_name:
                        member_list = [m.strip() for m in members.split('\n') if m.strip()]
                        member_list.append(st.session_state.user['user_id'])
                        
                        chat_id = self.db.create_chat('group', group_name, 
                                                    st.session_state.user['user_id'], 
                                                    member_list)
                        st.success(f"Group '{group_name}' created!")
                        st.session_state.show_new_chat = False
                        st.rerun()
            
            if st.button("Cancel", key="cancel_new_chat"):
                st.session_state.show_new_chat = False
    
    def render_story_creator(self):
        """Render story creation interface"""
        if st.session_state.get('show_story_creator'):
            st.markdown("### Create Story")
            
            story_type = st.selectbox("Story Type", ["Text", "Image", "Video"])
            
            if story_type == "Text":
                story_text = st.text_area("Your story text", height=100)
                background_color = st.color_picker("Background Color", "#667eea")
                
                if story_text:
                    st.markdown(f"""
                    <div style="background: {background_color}; color: white; padding: 40px; 
                                border-radius: 15px; text-align: center; font-size: 18px; 
                                min-height: 200px; display: flex; align-items: center; 
                                justify-content: center;">
                        {story_text}
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button("Share Story", key="share_text_story"):
                    if story_text:
                        st.success("Story shared! (Feature in development)")
                        st.session_state.show_story_creator = False
            
            elif story_type == "Image":
                uploaded_image = st.file_uploader("Choose image", type=['jpg', 'jpeg', 'png'])
                story_caption = st.text_input("Add a caption (optional)")
                
                if uploaded_image:
                    st.image(uploaded_image, caption=story_caption)
                    
                    if st.button("Share Story", key="share_image_story"):
                        st.success("Image story shared! (Feature in development)")
                        st.session_state.show_story_creator = False
            
            if st.button("Cancel", key="cancel_story"):
                st.session_state.show_story_creator = False
    
    def render_profile_editor(self):
        """Render profile editing interface"""
        if st.session_state.get('show_profile_editor'):
            st.markdown("### Edit Profile")
            
            # Profile picture
            st.markdown("**Profile Picture**")
            uploaded_avatar = st.file_uploader("Upload new avatar", type=['jpg', 'jpeg', 'png'])
            
            # Basic info
            new_bio = st.text_area("Bio", value=st.session_state.user.get('bio', ''), 
                                  placeholder="Tell us about yourself...")
            new_status = st.text_input("Status Message", 
                                      value=st.session_state.user.get('status', 'Hey there! I am using ChatFlow.'))
            
            # Privacy settings
            st.markdown("**Privacy Settings**")
            last_seen_privacy = st.selectbox("Last Seen", ["Everyone", "My Contacts", "Nobody"])
            profile_photo_privacy = st.selectbox("Profile Photo", ["Everyone", "My Contacts", "Nobody"])
            about_privacy = st.selectbox("About", ["Everyone", "My Contacts", "Nobody"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Save Changes", key="save_profile"):
                    # Update profile logic here
                    st.success("Profile updated successfully!")
                    st.session_state.show_profile_editor = False
            
            with col2:
                if st.button("Cancel", key="cancel_profile_edit"):
                    st.session_state.show_profile_editor = False
    
    def run(self):
        """Main application runner"""
        if st.session_state.page == 'login' or not st.session_state.user:
            self.render_login_page()
        else:
            # Main app layout
            self.render_sidebar()
            
            # Main content area
            with st.container():
                # Handle popup dialogs
                if st.session_state.get('show_attachment_menu'):
                    self.render_attachment_menu()
                elif st.session_state.get('show_emoji_picker'):
                    self.render_emoji_picker()
                elif st.session_state.get('show_new_chat'):
                    self.render_new_chat_dialog()
                elif st.session_state.get('show_story_creator'):
                    self.render_story_creator()
                elif st.session_state.get('show_profile_editor'):
                    self.render_profile_editor()
                else:
                    self.render_main_chat_area()
        
        # Auto-refresh for real-time updates
        time.sleep(0.1)

# Initialize and run the app
if __name__ == "__main__":
    app = ChatFlowApp()
    app.run()
