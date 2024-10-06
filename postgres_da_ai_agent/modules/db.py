from datetime import datetime
import json
import psycopg2
from psycopg2.sql import SQL, Identifier


class PostgresManager:
    def __init__(self):
        self.conn = None
        self.cur = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def connect_with_url(self, url):
        self.conn = psycopg2.connect(url)
        self.cur = self.conn.cursor()

    def upsert(self, table_name, _dict):
        columns = _dict.keys()
        values = [SQL("%s")] * len(columns)
        upsert_stmt = SQL(
            "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (id) DO UPDATE SET {}"
        ).format(
            Identifier(table_name),
            SQL(", ").join(map(Identifier, columns)),
            SQL(", ").join(values),
            SQL(", ").join(
                [
                    SQL("{} = EXCLUDED.{}").format(Identifier(k), Identifier(k))
                    for k in columns
                ]
            ),
        )
        self.cur.execute(upsert_stmt, list(_dict.values()))
        self.conn.commit()

    def delete(self, table_name, _id):
        delete_stmt = SQL("DELETE FROM {} WHERE id = %s").format(Identifier(table_name))
        self.cur.execute(delete_stmt, (_id,))
        self.conn.commit()

    def get(self, table_name, _id):
        select_stmt = SQL("SELECT * FROM {} WHERE id = %s").format(
            Identifier(table_name)
        )
        self.cur.execute(select_stmt, (_id,))
        return self.cur.fetchone()

    def get_all(self, table_name):
        select_all_stmt = SQL("SELECT * FROM {}").format(Identifier(table_name))
        self.cur.execute(select_all_stmt)
        return self.cur.fetchall()

    # def run_sql(self, sql):
    #     self.cur.execute(sql)
    #     return self.cur.fetchall()

    def run_sql(self, sql) -> str:
        self.cur.execute(sql)
        columns = [desc[0] for desc in self.cur.description]
        res = self.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        json_result = json.dumps(list_of_dicts, indent=4, default=self.datetime_handler)
        return json_result

    def datetime_handler(self, obj):
        """
        Handle datetime objects when serializing to JSON.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)  # or just return the object unchanged, or another default value

    def get_table_definition(self, table_name):
        get_def_stmt = """
        SELECT pg_class.relname as tablename,
            pg_attribute.attnum,
            pg_attribute.attname,
            format_type(atttypid, atttypmod)
        FROM pg_class
        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
        JOIN pg_attribute ON pg_attribute.attrelid = pg_class.oid
        WHERE pg_attribute.attnum > 0
            AND pg_class.relname = %s
            AND pg_namespace.nspname = 'public'  -- Assuming you're interested in public schema
        """
        self.cur.execute(get_def_stmt, (table_name,))
        rows = self.cur.fetchall()
        create_table_stmt = "CREATE TABLE {} (\n".format(table_name)
        for row in rows:
            create_table_stmt += "{} {},\n".format(row[2], row[3])
        create_table_stmt = create_table_stmt.rstrip(",\n") + "\n);"
        return create_table_stmt

    def get_all_table_names(self):
        get_all_tables_stmt = (
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        )
        self.cur.execute(get_all_tables_stmt)
        return [row[0] for row in self.cur.fetchall()]

    def get_table_definitions_for_prompt(self):
        table_names = self.get_all_table_names()
        definitions = []
        for table_name in table_names:
            definitions.append(self.get_table_definition(table_name))
        return "\n\n".join(definitions)

    def save_customer(
        self, firstname, lastname, email, phonenumber, shippingaddress, creditcardnumber
    ):
        try:
            # Check if customer exists
            self.cur.execute(
                "SELECT customerid FROM customers WHERE email = %s", (email,)
            )
            existing_customer = self.cur.fetchone()

            if existing_customer:
                # Update existing customer
                update_stmt = SQL(
                    """
                    UPDATE customers
                    SET firstname = %s, lastname = %s, phonenumber = %s,
                        shippingaddress = %s, creditcardnumber = %s
                    WHERE email = %s
                    RETURNING customerid
                """
                )
                self.cur.execute(
                    update_stmt,
                    (
                        firstname,
                        lastname,
                        phonenumber,
                        shippingaddress,
                        creditcardnumber,
                        email,
                    ),
                )
            else:
                # Insert new customer
                insert_stmt = SQL(
                    """
                    INSERT INTO customers
                    (firstname, lastname, email, phonenumber, shippingaddress, creditcardnumber)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING customerid
                """
                )
                self.cur.execute(
                    insert_stmt,
                    (
                        firstname,
                        lastname,
                        email,
                        phonenumber,
                        shippingaddress,
                        creditcardnumber,
                    ),
                )

            customer_id = self.cur.fetchone()[0]
            self.conn.commit()
            return customer_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def create_order(
        self, customer_id, product_id, order_date, quantity, total_price, order_status
    ):
        try:
            insert_stmt = SQL(
                """
                INSERT INTO orders
                (customerid, productid, orderdate, quantity, totalprice, orderstatus)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING orderid
            """
            )
            self.cur.execute(
                insert_stmt,
                (
                    customer_id,
                    product_id,
                    order_date,
                    quantity,
                    total_price,
                    order_status,
                ),
            )
            order_id = self.cur.fetchone()[0]
            self.conn.commit()
            return order_id
        except Exception as e:
            self.conn.rollback()
            raise e


# def get_product_id(self, product_name):
#     """
#     Retrieve the product ID from the 'products' table based on the product name.
#     """
#     select_product_stmt = """
#     SELECT id FROM products WHERE product_name = %s;
#     """
#     self.cur.execute(select_product_stmt, (product_name,))
#     result = self.cur.fetchone()
#     return result[0] if result else None
