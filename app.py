from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, render_template_string, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Guestbook - PostgreSQL on Railway</title>
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
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px; 
            background: var(--bg-color);
            color: var(--text-color);
        }
        
        .container { 
            background: var(--container-bg); 
            padding: 20px; 
            border-radius: 10px; 
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 28px;
            font-weight: bold;
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
        }
        
        button:hover { background: #5a67d8; }
        
        .message { 
            border: 1px solid var(--border-color); 
            margin: 10px 0; 
            padding: 15px; 
            border-radius: 5px; 
            background: var(--message-bg);
        }
        
        .name { font-weight: bold; color: #667eea; }
        .delete { color: red; cursor: pointer; float: right; font-size: 20px; }
        .likes { color: #ff4444; cursor: pointer; margin-left: 10px; }
        .theme-toggle { float: right; margin-top: -40px; cursor: pointer; }
        .search-bar { margin: 20px 0; }
        .search-bar input { width: 100%; padding: 10px; }
        
        .leaderboard {
            margin-top: 30px;
            padding: 20px;
            background: var(--message-bg);
            border-radius: 10px;
        }
        
        .leaderboard-item { padding: 8px; border-bottom: 1px solid var(--border-color); }
        .date { font-size: 11px; opacity: 0.7; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <button class="theme-toggle" onclick="toggleTheme()">🌓 Dark/Light</button>
        <h1>🐘 Guestbook - PostgreSQL on Railway</h1>
        
        <div class="stats">
            <div class="stat-card"><div class="stat-number" id="totalMessages">0</div><div>Total Messages</div></div>
            <div class="stat-card"><div class="stat-number" id="totalLikes">0</div><div>Total Likes</div></div>
            <div class="stat-card"><div class="stat-number" id="avgLikes">0</div><div>Avg Likes</div></div>
        </div>
        
        <div>
            <input type="text" id="name" placeholder="Your name">
            <textarea id="message" placeholder="Your message" rows="3"></textarea>
            <button onclick="addMessage()">✍️ Sign Guestbook</button>
        </div>
        
        <div class="search-bar">
            <input type="text" id="search" placeholder="🔍 Search messages..." onkeyup="loadMessages()">
        </div>
        
        <div id="messages"></div>
        
        <div class="leaderboard">
            <h3>🏆 Top Contributors</h3>
            <div id="leaderboard"></div>
        </div>
    </div>
    
    <script>
        let currentTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', currentTheme);
        
        function toggleTheme() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.body.setAttribute('data-theme', currentTheme);
            localStorage.setItem('theme', currentTheme);
        }
        
        function loadMessages() {
            const search = document.getElementById('search').value;
            fetch(`/api/messages?search=${encodeURIComponent(search)}`)
                .then(res => res.json())
                .then(data => {
                    displayMessages(data.messages);
                    document.getElementById('totalMessages').textContent = data.stats.total_messages;
                    document.getElementById('totalLikes').textContent = data.stats.total_likes;
                    document.getElementById('avgLikes').textContent = data.stats.avg_likes;
                    
                    const leaderboardHtml = data.leaderboard.map((u, i) => 
                        `<div class="leaderboard-item">${i+1}. ${u.name} - ${u.message_count} msgs, ${u.total_likes} likes ❤️</div>`
                    ).join('');
                    document.getElementById('leaderboard').innerHTML = leaderboardHtml || '<div>No data yet</div>';
                })
                .catch(err => console.error('Error:', err));
        }
        
        function displayMessages(messages) {
            if (messages.length === 0) {
                document.getElementById('messages').innerHTML = '<div style="text-align:center;padding:40px;">✨ No messages yet. Be the first to sign!</div>';
                return;
            }
            
            const html = messages.map(msg => `
                <div class="message">
                    <span class="delete" onclick="deleteMessage(${msg.id})">🗑️</span>
                    <div><span class="name">${escapeHtml(msg.name)}</span></div>
                    <div>${escapeHtml(msg.message)}</div>
                    <div class="date">${msg.created_at} 
                        <span class="likes" onclick="likeMessage(${msg.id})">❤️ ${msg.likes}</span>
                    </div>
                </div>
            `).join('');
            document.getElementById('messages').innerHTML = html;
        }
        
        function addMessage() {
            const name = document.getElementById('name').value.trim();
            const message = document.getElementById('message').value.trim();
            if (!name || !message) { alert('Please fill both fields!'); return; }
            
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
            fetch(`/api/messages/${id}/like`, {method: 'PUT'}).then(() => loadMessages());
        }
        
        function deleteMessage(id) {
            if (confirm('Delete this message?')) {
                fetch(`/api/messages/${id}`, {method: 'DELETE'}).then(() => loadMessages());
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        loadMessages();
        setInterval(loadMessages, 5000);
    </script>
</body>
</html>
'''

def get_db_connection():
    """Get PostgreSQL connection using DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise Exception("❌ DATABASE_URL not found! Please check your .env file")
    
    print(f"📡 Connecting to PostgreSQL...")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def init_database():
    """Initialize PostgreSQL tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for faster searches
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_name ON messages(name);
        CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC);
    ''')
    
    conn.commit()
    conn.close()
    print("✅ PostgreSQL tables created successfully!")

def row_to_dict(row):
    """Convert database row to dictionary"""
    return dict(row) if row else None

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
            WHERE name ILIKE %s OR message ILIKE %s 
            ORDER BY created_at DESC
        ''', (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
    
    messages = [row_to_dict(row) for row in cursor.fetchall()]
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total, COALESCE(SUM(likes), 0) as likes FROM messages")
    stats_row = cursor.fetchone()
    total_messages = stats_row['total'] or 0
    total_likes = stats_row['likes'] or 0
    avg_likes = round(total_likes / total_messages, 1) if total_messages > 0 else 0
    
    # Get leaderboard
    cursor.execute('''
        SELECT name, COUNT(*) as message_count, COALESCE(SUM(likes), 0) as total_likes
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
    
    cursor.execute(
        "INSERT INTO messages (name, message) VALUES (%s, %s) RETURNING *",
        (data['name'], data['message'])
    )
    new_msg = row_to_dict(cursor.fetchone())
    conn.commit()
    conn.close()
    
    return jsonify(new_msg), 201

@app.route('/api/messages/<int:msg_id>/like', methods=['PUT'])
def like_message(msg_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE messages SET likes = likes + 1 WHERE id = %s RETURNING *",
        (msg_id,)
    )
    updated = row_to_dict(cursor.fetchone())
    conn.commit()
    conn.close()
    
    return jsonify(updated) if updated else ('', 404)

@app.route('/api/messages/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM messages WHERE id = %s RETURNING id", (msg_id,))
    deleted = cursor.fetchone()
    conn.commit()
    conn.close()
    
    return jsonify({'deleted': msg_id}) if deleted else ('', 404)

if __name__ == '__main__':
    print("🐘 PostgreSQL Guestbook App")
    print("=" * 50)
    
    # Test database connection
    try:
        init_database()
        print("✅ Database ready!")
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Created .env file with DATABASE_URL")
        print("   2. Used the PUBLIC PostgreSQL URL (not internal)")
        print("   3. Railway PostgreSQL service is running")
        exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Server running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)