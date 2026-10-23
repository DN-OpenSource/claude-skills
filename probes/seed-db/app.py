import sqlite3

db = sqlite3.connect("shop.db")


def user_totals():
    return db.execute(
        "SELECT u.name, o.total FROM users u"
        " JOIN orders o ON o.user_id = u.id"
        " JOIN order_items i ON i.order_id = o.id"
    ).fetchall()
