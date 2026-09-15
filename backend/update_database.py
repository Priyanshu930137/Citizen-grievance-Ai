import sqlite3


DATABASE_NAME = "citizen_connect.db"


connection = sqlite3.connect(
    DATABASE_NAME
)

cursor = connection.cursor()


# ==========================================
# ADD COLUMNS TO GRIEVANCES TABLE
# ==========================================

columns_to_add = [

    (
        "assigned_technician_id",
        "INTEGER"
    ),

    (
        "assigned_technician_name",
        "VARCHAR(150)"
    ),

    (
        "diagnosis",
        "TEXT"
    ),

    (
        "resolution_note",
        "TEXT"
    )

]


for column_name, column_type in columns_to_add:

    try:

        cursor.execute(

            f"""
            ALTER TABLE grievances
            ADD COLUMN {column_name} {column_type}
            """

        )

        connection.commit()


        print(

            f"SUCCESS: {column_name} column added."

        )


    except sqlite3.OperationalError as error:

        print(

            f"DATABASE MESSAGE for {column_name}:",
            error

        )


connection.close()


print(
    "\nDatabase update completed."
)