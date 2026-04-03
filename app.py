from flask import Flask, request, render_template_string, jsonify
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# HTML Template with Stats, Search, and Dark Mode
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Guestbook Management</title>
    <style>
        :root {
            --bg-color: #f0f2f5;
            --container-bg: white;
            --text-color: #333;
            --message-bg: #f9f9f9;
            --border-color: #ddd;
        }
        
        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --container-bg: #2d2d2d;
            --text-color: #e0e0e0;
            --message-bg: #3d3d3d;
            --border-color: #555;
        }
        
        body { 
            font-family: Arial; 
            max-width: 1200px; 
            margin: 50px auto; 
            padding: 20px; 
            background: var(--bg-color);
            color: var(--text-color);
            transition: all 0.3s;
        }
        
        .container { 
            background: var(--container-bg); 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Stats Dashboard */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        /* Search Bar */
        .search-bar {
            margin-bottom: 20px;
        }
        
        .search-bar input {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 5px;
            background: var(--container-bg);
            color: var(--text-color);
            font-size: 16px;
        }
        
        /* Messages */
        .message { 
            border: 1px solid var(--border-color); 
            margin: 10px 0; 
            padding: 15px; 
            border-radius: 5px; 
            background: var(--message-bg);
        }
        
        .name { 
            font-weight: bold; 
            color: #667eea; 
            font-size: 16px;
        }
        
        .avatar {
            display: inline-block;
            width: 30px;
            height: 30px;
            background: #667eea;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            color: white;
            margin-right: 10px;
            font-size: 14px;
        }
        
        .date { 
            font-size: 12px; 
            color: var(--text-color); 
            opacity: 0.7;
            margin-top: 8px; 
        }
        
        .likes { 
            color: #ff4444; 
            cursor: pointer; 
            margin-left: 10px;
        }
        
        input, textarea { 
            width: 100%; 
            padding: 10px; 
            margin: 5px 0 15px 0; 
            border: 1px solid var(--border-color); 
            border-radius: 5px; 
            background: var(--container-bg);
            color: var(--text-color);
        }
        
        button { 
            background: #667eea; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px;
        }
        
        button:hover { background: #5a67d8; }
        
        .delete { 
            color: #ff4444; 
            cursor: pointer; 
            float: right; 
            font-size: 20px;
        }
        
        .theme-toggle {
            float: right;
            background: none;
            border: 1px solid var(--border-color);
            padding: 8px 15px;
            margin-top: -40px;
        }
        
        .leaderboard {
            margin-top: 30px;
            padding: 20px;
            background: var(--message-bg);
            border-radius: 10px;
        }
        
        .leaderboard-item {
            padding: 8px;
            border-bottom: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <button class="theme-toggle" onclick="toggleTheme()">Dark/Light Mode</button>
        <h1> Enhanced Guestbook - Railway PaaS Demo</h1>
        
        <!-- Statistics Dashboard -->
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalMessages">0</div>
                <div class="stat-label">Total Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalLikes">0</div>
                <div class="stat-label">Total Likes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="avgLikes">0</div>
                <div class="stat-label">Avg Likes/Message</div>
            </div>
        </div>
        
        <!-- Add Message Form -->
        <div>
            <input type="text" id="name" placeholder="Your name">
            <textarea id="message" placeholder="Your message" rows="3"></textarea>
            <button onclick="addMessage()"> Sign Guestbook</button>
        </div>
        
        <!-- Search Bar -->
        <div class="search-bar">
            <input type="text" id="search" placeholder="🔍 Search messages..." onkeyup="loadMessages()">
        </div>
        
        <!-- Messages Container -->
        <div id="messages"></div>
        
        <!-- Leaderboard -->
        <div class="leaderboard">
            <h3>Top Contributors</h3>
            <div id="leaderboard"></div>
        </div>
    </div>
    
    <script>
        let currentTheme = localStorage.getItem('theme') || 'light';
        
        function toggleTheme() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.body.setAttribute('data-theme', currentTheme);
            localStorage.setItem('theme', currentTheme);
        }
        
        // Set initial theme
        document.body.setAttribute('data-theme', currentTheme);
        
        function loadMessages() {
            const searchTerm = document.getElementById('search').value;
            fetch(`/api/messages?search=${encodeURIComponent(searchTerm)}`)
                .then(res => res.json())
                .then(data => {
                    displayMessages(data.messages);
                    updateStats(data.stats);
                    displayLeaderboard(data.leaderboard);
                });
        }
        
        function displayMessages(messages) {
            if (messages.length === 0) {
                document.getElementById('messages').innerHTML = '<div style="text-align:center;padding:40px;">✨ No messages found. Be the first to sign!</div>';
                return;
            }
            
            const html = messages.map(msg => {
                const avatar = msg.name.charAt(0).toUpperCase();
                return `
                    <div class="message">
                        <span class="delete" onclick="deleteMessage(${msg.id})">🗑️</span>
                        <div>
                            <span class="avatar">${avatar}</span>
                            <span class="name">${escapeHtml(msg.name)}</span>
                        </div>
                        <div style="margin-left: 40px;">${escapeHtml(msg.message)}</div>
                        <div class="date">
                            ${msg.created_at} 
                            <span class="likes" onclick="likeMessage(${msg.id})">
                                ${msg.likes > 0 ? '❤️' : '🤍'} ${msg.likes}
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
            document.getElementById('messages').innerHTML = html;
        }
        
        function updateStats(stats) {
            document.getElementById('totalMessages').textContent = stats.total_messages;
            document.getElementById('totalLikes').textContent = stats.total_likes;
            document.getElementById('avgLikes').textContent = stats.avg_likes;
        }
        
        function displayLeaderboard(leaderboard) {
            if (leaderboard.length === 0) {
                document.getElementById('leaderboard').innerHTML = '<div>No data yet</div>';
                return;
            }
            
            const html = leaderboard.map((user, index) => `
                <div class="leaderboard-item">
                    ${index + 1}. ${user.name} - ${user.message_count} messages, ${user.total_likes} likes ❤️
                </div>
            `).join('');
            document.getElementById('leaderboard').innerHTML = html;
        }
        
        function addMessage() {
            const name = document.getElementById('name').value.trim();
            const message = document.getElementById('message').value.trim();
            
            if (!name || !message) {
                alert('Please fill both fields!');
                return;
            }
            
            fetch('/api/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, message})
            }).then(() => {
                document.getElementById('name').value = '';
                document.getElementById('message').value = '';
                loadMessages();
            });
        }
        
        function likeMessage(id) {
            fetch(`/api/messages/${id}/like`, {method: 'PUT'})
                .then(() => loadMessages());
        }
        
        function deleteMessage(id) {
            if (confirm('Delete this message?')) {
                fetch(`/api/messages/${id}`, {method: 'DELETE'})
                    .then(() => loadMessages());
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Load messages every 5 seconds
        loadMessages();
        setInterval(loadMessages, 5000);
    </script>
</body>
</html>
'''

# Database setup (same as before)
def get_db_connection():
    """Returns appropriate database connection based on environment"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PRODUCTION: Use PostgreSQL on Railway
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # DEVELOPMENT: Use SQLite locally
        import sqlite3
        conn = sqlite3.connect('guestbook.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_database():
    """Initialize tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_sqlite = not os.environ.get('DATABASE_URL')
    
    if is_sqlite:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()

def row_to_dict(row):
    if hasattr(row, 'keys'):
        return dict(row)
    else:
        return {key: row[key] for key in row.keys()}

# API Endpoints
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/messages')
def get_messages():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get messages with search filter
    if search:
        cursor.execute('''
            SELECT * FROM messages 
            WHERE name LIKE ? OR message LIKE ? 
            ORDER BY created_at DESC
        ''', (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
    
    messages = [row_to_dict(row) for row in cursor.fetchall()]
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total, SUM(likes) as likes FROM messages")
    stats_row = cursor.fetchone()
    total_messages = stats_row['total'] or 0
    total_likes = stats_row['likes'] or 0
    avg_likes = round(total_likes / total_messages, 1) if total_messages > 0 else 0
    
    # Get leaderboard
    cursor.execute('''
        SELECT name, COUNT(*) as message_count, SUM(likes) as total_likes
        FROM messages
        GROUP BY name
        ORDER BY message_count DESC
        LIMIT 5
    ''')
    leaderboard = [row_to_dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'messages': messages,
        'stats': {
            'total_messages': total_messages,
            'total_likes': total_likes,
            'avg_likes': avg_likes
        },
        'leaderboard': leaderboard
    })

@app.route('/api/messages', methods=['POST'])
def add_message():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    
    if is_postgres:
        cursor.execute(
            "INSERT INTO messages (name, message) VALUES (%s, %s) RETURNING *",
            (data['name'], data['message'])
        )
        new_msg = row_to_dict(cursor.fetchone())
        conn.commit()
    else:
        cursor.execute(
            "INSERT INTO messages (name, message) VALUES (?, ?)",
            (data['name'], data['message'])
        )
        conn.commit()
        cursor.execute("SELECT * FROM messages WHERE id = last_insert_rowid()")
        new_msg = row_to_dict(cursor.fetchone())
    
    conn.close()
    return jsonify(new_msg), 201

@app.route('/api/messages/<int:msg_id>/like', methods=['PUT'])
def like_message(msg_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    
    if is_postgres:
        cursor.execute(
            "UPDATE messages SET likes = likes + 1 WHERE id = %s RETURNING *",
            (msg_id,)
        )
        updated = row_to_dict(cursor.fetchone())
        conn.commit()
    else:
        cursor.execute(
            "UPDATE messages SET likes = likes + 1 WHERE id = ?",
            (msg_id,)
        )
        conn.commit()
        cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
        updated = row_to_dict(cursor.fetchone())
    
    conn.close()
    return jsonify(updated) if updated else ('', 404)

@app.route('/api/messages/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    
    if is_postgres:
        cursor.execute("DELETE FROM messages WHERE id = %s RETURNING id", (msg_id,))
        deleted = cursor.fetchone()
        conn.commit()
    else:
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
    
    conn.close()
    return jsonify({'deleted': msg_id}) if deleted else ('', 404)

if __name__ == '__main__':
    init_database()
    print(" Guestbook with Stats & Search!")
    print("Features: Statistics, Search, Leaderboard, Dark Mode")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)