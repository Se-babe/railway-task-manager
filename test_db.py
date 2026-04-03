import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL not found in .env file")
    exit(1)

print(f"Connecting to: {database_url[:50]}...")

try:
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()
    
    print(f"\n✅ Connected successfully!")
    print(f"📝 Found {len(messages)} messages:")
    
    for msg in messages:
        print(f"  - {msg['name']}: {msg['message'][:50]}...")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")