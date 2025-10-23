#!/usr/bin/env python3
"""
修复数据库表结构 - 添加缺失的列
用于解决 "no such column: is_new_today" 错误
"""

import sqlite3
import sys

def fix_database(db_path='job_scraper.db'):
    """添加缺失的数据库列"""
    
    print("🔧 开始修复数据库表结构...")
    print(f"📁 数据库文件: {db_path}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查现有列
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前列 ({len(columns)}个):")
        for col in columns:
            print(f"  - {col}")
        print()
        
        # 需要添加的列
        required_columns = {
            'source': ('TEXT', '"seek"'),
            'is_new_today': ('BOOLEAN', '0'),
            'is_active': ('BOOLEAN', '1'),
            'first_seen_date': ('TIMESTAMP', 'CURRENT_TIMESTAMP'),
            'last_seen_date': ('TIMESTAMP', 'CURRENT_TIMESTAMP'),
        }
        
        added = []
        skipped = []
        
        for col_name, (col_type, default_value) in required_columns.items():
            if col_name not in columns:
                try:
                    sql = f'ALTER TABLE jobs ADD COLUMN {col_name} {col_type} DEFAULT {default_value}'
                    cursor.execute(sql)
                    added.append(col_name)
                    print(f"✅ 添加列: {col_name} ({col_type})")
                except Exception as e:
                    print(f"❌ 添加列 {col_name} 失败: {e}")
            else:
                skipped.append(col_name)
        
        conn.commit()
        
        # 验证修复后的结构
        print("\n验证修复结果:")
        cursor.execute("PRAGMA table_info(jobs)")
        columns_after = [col[1] for col in cursor.fetchall()]
        print(f"修复后共有 {len(columns_after)} 列\n")
        
        # 确认数据量
        cursor.execute('SELECT COUNT(*) FROM jobs')
        count = cursor.fetchone()[0]
        print(f"📊 数据库中共有 {count} 个职位\n")
        
        # 显示统计
        if 'is_active' in columns_after:
            cursor.execute('SELECT COUNT(*) FROM jobs WHERE is_active = 1')
            active_count = cursor.fetchone()[0]
            print(f"   - 活跃职位: {active_count}")
        
        if 'is_new_today' in columns_after:
            cursor.execute('SELECT COUNT(*) FROM jobs WHERE is_new_today = 1')
            new_count = cursor.fetchone()[0]
            print(f"   - 今日新增: {new_count}")
        
        if 'source' in columns_after:
            cursor.execute('SELECT source, COUNT(*) FROM jobs GROUP BY source')
            source_stats = cursor.fetchall()
            print(f"   - 来源统计:")
            for source, cnt in source_stats:
                print(f"     • {source or 'Unknown'}: {cnt}")
        
        conn.close()
        
        # 总结
        print("\n" + "=" * 60)
        if added:
            print(f"🎉 成功添加 {len(added)} 个列: {', '.join(added)}")
        if skipped:
            print(f"ℹ️  跳过已存在的 {len(skipped)} 个列")
        if not added and not skipped:
            print("✅ 所有必需列都已存在")
        print("=" * 60)
        
        print("\n📝 下一步:")
        print("   1. 重启服务: ./stop_services.sh && ./start_services.sh")
        print("   2. 测试API: curl http://localhost:8080/api/jobs")
        print("   3. 刷新浏览器访问网页")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'job_scraper.db'
    success = fix_database(db_path)
    sys.exit(0 if success else 1)

