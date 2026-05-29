##demmo 
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

        output_file = "s3://s3-mw-snowflake/output/new_forecast_details_data.parquet"

        con = duckdb.connect()

        con.execute("""
        CREATE OR REPLACE SECRET (
            TYPE s3,
            PROVIDER credential_chain
        );
        """)

        con.execute("SET home_directory='/tmp'")

        con.execute("INSTALL httpfs;")
        con.execute("LOAD httpfs;")

        con.execute("INSTALL mysql;")
        con.execute("LOAD mysql;")

        logging.info("Connecting to MySQL...")

        con.execute(f"""
            ATTACH 'host={host} user={user} password={password} port=3306 database={database}'
            AS mysqldb (TYPE mysql);
        """)

        logging.info("Exporting to S3...")

        con.execute(f"""
            COPY (
                SELECT * FROM mysqldb.forecast_details
            )
            TO '{output_file}'
            (FORMAT PARQUET);
        """)

        logging.info("Done!")

    except Exception as e:
        logging.error(f"ETL failed: {e}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    run_etl()