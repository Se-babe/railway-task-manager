from flask import Flask, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    """Connect to PostgreSQL database"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # For local development
        return psycopg2.connect(
            host='localhost',
            database='railway_demo',
            user='postgres',
            password='postgres',
            cursor_factory=RealDictCursor
        )
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def init_database():
    """Create tables if they don't exist"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data if table is empty
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()['count']
    
    if count == 0:
        sample_tasks = [
            ('Learn Railway PaaS', 'Complete the deployment tutorial', 'pending'),
            ('Create Task API', 'Build Flask CRUD application', 'in-progress'),
            ('Write Documentation', 'Prepare report for assignment', 'pending')
        ]
        for task in sample_tasks:
            cur.execute(
                "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s)",
                task
            )
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def home():
    """Root endpoint - API information"""
    return jsonify({
        'name': 'Task Manager API',
        'version': '1.0.0',
        'status': 'running on Railway',
        'endpoints': {
            'GET /tasks': 'List all tasks',
            'GET /tasks/<id>': 'Get specific task',
            'POST /tasks': 'Create new task',
            'PUT /tasks/<id>': 'Update task',
            'DELETE /tasks/<id>': 'Delete task',
            'GET /health': 'Health check'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get single task by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cur.fetchone()
    cur.close()
    conn.close()
    
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s) RETURNING *",
        (data['title'], data.get('description', ''), data.get('status', 'pending'))
    )
    new_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(new_task), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update an existing task"""
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE tasks SET title = %s, description = %s, status = %s WHERE id = %s RETURNING *",
        (data.get('title'), data.get('description'), data.get('status'), task_id)
    )
    updated_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if updated_task:
        return jsonify(updated_task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if deleted:
        return jsonify({'message': 'Task deleted successfully'})
    return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization skipped: {e}")
        print("   (This is normal for local testing without PostgreSQL)")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)