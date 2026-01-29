#!/usr/bin/env python3
"""
删除数据库中的历史记录
"""
import sqlite3

def clear_database():
    """删除数据库中的所有历史记录"""
    db_path = 'data/text_factor.db'
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"连接到数据库: {db_path}")
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"发现 {len(tables)} 个表:")
        for table in tables:
            table_name = table[0]
            # 获取表中的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 条记录")
            
            # 删除表中的所有记录
            if count > 0:
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"    ✓ 已删除所有记录")
        
        # 提交更改
        conn.commit()
        print("\n✓ 所有历史记录已成功删除")
        
        # 验证删除结果
        print("\n验证删除结果:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 条记录")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    clear_database()
