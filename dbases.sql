CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, id_stock INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        price REAL NOT NULL, shares INTEGER NOT NULL, date NUMERIC NOT NULL,
                        FOREIGN KEY(id_stock) REFERENCES stocks(id),
                        FOREIGN KEY(user_id) REFERENCES users(id));

CREATE TABLE stocks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL UNIQUE)

CREATE INDEX user_id ON transactions (user_id); !id_stock не не надо

CREATE UNIQUE INDEX stock_name ON stocks (name);

