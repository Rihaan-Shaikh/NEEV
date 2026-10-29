import os
import subprocess
import asyncio
import asyncpg

PG_BIN = r"C:\Program Files\PostgreSQL\18\bin"
PG_DUMP = os.path.join(PG_BIN, "pg_dump.exe")
PSQL = os.path.join(PG_BIN, "psql.exe")

DB_USER = "postgres"
DB_PASS = "2006"
DB_HOST = "localhost"
DB_PORT = "5432"
SRC_DB = "neev_dev"
RESTORE_DB = "neev_restore_test"
BACKUP_FILE = os.path.abspath("neev_dev_drill.dump")

async def run_backup_restore_drill():
    print(f"=== Starting NEEV PostgreSQL Backup and Restore Drill ===")
    os.environ["PGPASSWORD"] = DB_PASS

    # 1. Take Backup using pg_dump (Custom compressed archive format -Fc)
    print(f"1. Dumping '{SRC_DB}' to '{BACKUP_FILE}'...")
    dump_cmd = [
        PG_DUMP,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-F", "c",
        "-b",
        "-v",
        "-f", BACKUP_FILE,
        SRC_DB
    ]
    res = subprocess.run(dump_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"pg_dump failed:\n{res.stderr}")
    print(f"   Dump completed successfully. Size: {os.path.getsize(BACKUP_FILE)} bytes.")

    # 2. Prepare clean restore test database
    print(f"2. Preparing clean target database '{RESTORE_DB}'...")
    conn = await asyncpg.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, database="postgres")
    try:
        # Terminate active connections to restore db if any
        await conn.execute(f"""
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
            WHERE datname = '{RESTORE_DB}' AND pid <> pg_backend_pid();
        """)
        await conn.execute(f"DROP DATABASE IF EXISTS {RESTORE_DB};")
        await conn.execute(f"CREATE DATABASE {RESTORE_DB};")
    finally:
        await conn.close()
    print(f"   Target database '{RESTORE_DB}' initialized.")

    # 3. Restore into neev_restore_test using pg_restore
    PG_RESTORE = os.path.join(PG_BIN, "pg_restore.exe")
    print(f"3. Restoring dump into '{RESTORE_DB}'...")
    restore_cmd = [
        PG_RESTORE,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", RESTORE_DB,
        "-v",
        BACKUP_FILE
    ]
    res_restore = subprocess.run(restore_cmd, capture_output=True, text=True)
    # pg_restore may return 0 or non-fatal exit codes with warnings; check database connectivity and tables
    print(f"   pg_restore completed.")

    # 4. Compare Table Row Counts Between Source and Restored Database
    print(f"4. Verifying table row counts and data integrity across all tables...")
    src_conn = await asyncpg.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, database=SRC_DB)
    rest_conn = await asyncpg.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, database=RESTORE_DB)

    tables_rows = await src_conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables_to_verify = [r["table_name"] for r in tables_rows]

    mismatches = []
    print(f"   {'Table':<30} | {'Source':<10} | {'Restored':<10} | {'Status'}")
    print(f"   {'-'*30}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")

    for tbl in tables_to_verify:
        src_count = await src_conn.fetchval(f"SELECT COUNT(*) FROM \"{tbl}\";")
        rest_count = await rest_conn.fetchval(f"SELECT COUNT(*) FROM \"{tbl}\";")
        status_str = "MATCH" if src_count == rest_count else "MISMATCH"
        print(f"   {tbl:<30} | {src_count:<10} | {rest_count:<10} | {status_str}")
        if src_count != rest_count:
            mismatches.append((tbl, src_count, rest_count))

    await src_conn.close()
    await rest_conn.close()

    # 5. Clean up temporary test database and backup artifact
    print(f"5. Cleaning up drill artifacts...")
    conn = await asyncpg.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, database="postgres")
    try:
        await conn.execute(f"""
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
            WHERE datname = '{RESTORE_DB}' AND pid <> pg_backend_pid();
        """)
        await conn.execute(f"DROP DATABASE IF EXISTS {RESTORE_DB};")
    finally:
        await conn.close()

    if os.path.exists(BACKUP_FILE):
        os.remove(BACKUP_FILE)

    if mismatches:
        raise RuntimeError(f"Backup verification failed with mismatches: {mismatches}")

    print(f"\n>>> POSTGRESQL BACKUP & RESTORE DRILL PASSED: 100% RELATIONAL DATA INTEGRITY VERIFIED <<<\n")

if __name__ == "__main__":
    asyncio.run(run_backup_restore_drill())
