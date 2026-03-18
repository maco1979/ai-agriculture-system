# Supabase数据库连接测试脚本
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.production')

def test_supabase_connection():
    try:
        # 获取连接字符串
        database_url = os.getenv('DATABASE_URL')
        print(f"连接字符串: {database_url[:50]}...")
        
        # 连接数据库
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL版本: {version[0]}")
        
        # 检查表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"✅ 找到 {len(tables)} 张表")
        
        for table in tables[:5]:  # 显示前5张表
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    exit(0 if success else 1)
