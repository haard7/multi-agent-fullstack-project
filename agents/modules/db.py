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

    def __exit__(self, exc_type, exc_val):
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
            "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (customerid) DO UPDATE SET {}"
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
        select_stmt = SQL("SELECT * FROM {} WHERE customerid = %s").format(
            Identifier(table_name)
        )
        self.cur.execute(select_stmt, (_id,))
        return self.cur.fetchone()

    def get_all(self, table_name):
        select_all_stmt = SQL("SELECT * FROM {}").format(Identifier(table_name))
        self.cur.execute(select_all_stmt)
        return self.cur.fetchall()

    def run_sql(self, sql) -> str:
        self.cur.execute(sql)
        columns = [desc[0] for desc in self.cur.description]
        res = self.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        json_result = json.dumps(list_of_dicts, indent=4, default=self.datetime_handler)
        return json_result

    def datetime_handler(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

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
            AND pg_namespace.nspname = 'public'
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

    # New function to handle product recommendation
    def recommend_product(self, sql) -> str:
        self.cur.execute(sql)
        columns = [desc[0] for desc in self.cur.description]
        res = self.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        json_result = json.dumps(list_of_dicts, indent=4, default=self.datetime_handler)
        return json_result

    def fetch_damaged_package_url(self, order_id):
        try:
            self.cur.execute(
                "SELECT damaged_package_img FROM Package_damaged WHERE orderid = %s",
                (order_id,),
            )
            result = self.cur.fetchone()
            if result:
                damaged_package_url = result[0]
                # return f"<img {damaged_package_url}>"
                return damaged_package_url
            else:
                return "Damaged package not found"
        except Exception as e:
            raise e

    def fetch_defect_product_url(self, order_id):
        try:
            self.cur.execute(
                "SELECT defect_product_img FROM Product_defect WHERE orderid = %s",
                (order_id,),
            )
            result = self.cur.fetchone()
            if result:
                defect_product_url = result[0]
                # return f"<img {defect_product_url}>"
                return defect_product_url
            else:
                return "Defective product not found"
        except Exception as e:
            raise e

    def buy_product(
        self,
        firstname,
        lastname,
        email,
        phonenumber,
        shippingaddress,
        creditcardnumber,
        productid,
        quantity,
    ):
        try:
            # Step 1: Insert customer details into the `customers` table
            insert_customer_query = """
            INSERT INTO customers (firstname, lastname, email, phonenumber, shippingaddress, creditcardnumber)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING customerid;
            """
            customer_data = (
                firstname,
                lastname,
                email,
                phonenumber,
                shippingaddress,
                creditcardnumber,
            )

            # Execute the insert query and get the new customerid
            self.cur.execute(insert_customer_query, customer_data)
            customerid = self.cur.fetchone()[0]  # Fetch the generated customerid

            # Step 2: Fetch product price
            self.cur.execute(
                "SELECT price FROM products WHERE productid = %s", (productid,)
            )
            product_price = self.cur.fetchone()[0]
            total_price = product_price * quantity

            # Step 3: Insert order details into the `orders` table
            insert_order_query = """
            INSERT INTO orders (customerid, productid, orderdate, quantity, totalprice, orderstatus)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING orderid;
            """
            order_data = (
                customerid,
                productid,
                datetime.now(),
                quantity,
                total_price,
                "pending",  # Setting the initial order status as "pending"
            )

            # Execute the insert query and get the new orderid
            self.cur.execute(insert_order_query, order_data)
            orderid = self.cur.fetchone()[0]  # Fetch the generated orderid

            # Commit the transaction
            self.conn.commit()

            # Return the newly created orderid as confirmation
            return orderid

        except Exception as e:
            # Rollback the transaction in case of any error
            self.conn.rollback()
            raise e

        # old recommend_product function
        # def recommend_product(self, gender=None, primary_color=None, price_range=None):
        # query = "SELECT * FROM products WHERE 1=1"
        # params = []
        # if gender:
        #     query += " AND gender = %s"
        #     params.append(gender)
        # if primary_color:
        #     query += " AND primarycolor = %s"
        #     params.append(primary_color)
        # if price_range:
        #     query += " AND price BETWEEN %s AND %s"
        #     params.extend(price_range)

        # self.cur.execute(query, tuple(params))
        # products = self.cur.fetchall()
        # return products

        # old - 1.1 function to handle product purchase and customer details saving

        # def buy_product(self, customer_details, product_id, quantity):
        #     try:
        #         # Save or update customer details first
        #         self.upsert("customers", customer_details)
        #         customer_id = customer_details.get("customerid")

        #         # Fetch product price
        #         self.cur.execute(
        #             "SELECT price FROM products WHERE productid = %s", (product_id,)
        #         )
        #         product_price = self.cur.fetchone()[0]
        #         total_price = product_price * quantity

        #         # Create a new order
        #         order_data = {
        #             # "orderid": self._generate_order_id(),
        #             "customerid": customer_id,
        #             "productid": product_id,
        #             "orderdate": datetime.now(),
        #             "quantity": quantity,
        #             "totalprice": total_price,
        #             "orderstatus": "pending",
        #         }
        #         self.upsert("orders", order_data)

        #         # Fetch the newly created order to return details
        #         self.cur.execute(
        #             "SELECT * FROM orders WHERE orderid = %s", (order_data["orderid"],)
        #         )
        #         order_details = self.cur.fetchone()
        #         return order_details

        #     except Exception as e:
        #         self.conn.rollback()
        #         raise e

        # New function to get order status based on order_id

    def get_order_status(self, order_id):
        try:
            self.cur.execute(
                "SELECT orderdate, orderstatus FROM orders WHERE orderid = %s",
                (order_id,),
            )
            order_status = self.cur.fetchone()
            if order_status:
                return order_status
            else:
                return "Order not found"
        except Exception as e:
            raise e

    def get_totalprice(self, order_id):
        """
        Retrieves the total price for a given order ID.
        """
        try:
            # Execute SQL query to retrieve totalprice for the specified order_id
            self.cur.execute(
                "SELECT totalprice FROM orders WHERE orderid = %s",
                (order_id,),
            )
            total_price = self.cur.fetchone()

            # Check if the result exists and return it, otherwise return "Order not found"
            if total_price:
                return total_price[0]  # Access the first element of the result tuple
            else:
                return "Order not found"
        except Exception as e:
            raise e

    # Helper function to generate unique order ID (custom logic can be implemented)
    def _generate_order_id(self):
        self.cur.execute("SELECT MAX(orderid) FROM orders")
        max_order_id = self.cur.fetchone()[0]
        if max_order_id is None:
            return 1
        return max_order_id + 1
