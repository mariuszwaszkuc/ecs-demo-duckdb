import os
import duckdb
import logging
import sys

logging.basicConfig(level=logging.INFO)


def run_etl():
    try:
        host = os.environ["DB_HOST"]
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        database = os.environ.get("DB_NAME", "big_pharma")

        s3_bucket = "s3://s3-mw-snowflake/output"

        con = duckdb.connect()

        # AWS credentials from ECS task role / AWS CLI / IAM role
        con.execute("""
        CREATE OR REPLACE SECRET (
            TYPE s3,
            PROVIDER credential_chain
        );
        """)

        con.execute("SET home_directory='/tmp'")

        # Extensions
        con.execute("INSTALL httpfs;")
        con.execute("LOAD httpfs;")

        con.execute("INSTALL mysql;")
        con.execute("LOAD mysql;")

        logging.info("Connecting to MySQL...")

        con.execute(f"""
            ATTACH 'host={host} user={user} password={password} port=3306 database={database}'
            AS mysqldb (TYPE mysql);
        """)

        logging.info("Fetching table list...")

        tables = con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'big_pharma'
              AND table_type = 'BASE TABLE'
        """).fetchall()

        if not tables:
            logging.warning("No tables found.")
            return

        logging.info(f"Found {len(tables)} tables")

        for table in tables:
            table_name = table[0]

            try:
                output_file = f"{s3_bucket}/{table_name}.parquet"

                logging.info(f"Exporting table: {table_name}")

                con.execute(f"""
                    COPY (
                        SELECT * FROM mysqldb.{table_name}
                    )
                    TO '{output_file}'
                    (FORMAT PARQUET);
                """)

                logging.info(f"Saved: {output_file}")

            except Exception as table_error:
                logging.error(
                    f"Failed exporting table {table_name}: {table_error}"
                )

        logging.info("ETL finished successfully!")

    except Exception as e:
        logging.error(f"ETL failed: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    run_etl()