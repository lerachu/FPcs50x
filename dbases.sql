CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE plan (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, 
                    title TEXT NOT NULL, description TEXT NOT NULL, comment TEXT, link TEXT, complexity INTEGER NOT NULL,
                    importance INTEGER NOT NULL, completeness INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id));

CREATE UNIQUE INDEX username ON users (username);
CREATE INDEX userid ON plan (user_id);

CREATE TABLE questionnaire (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL UNIQUE, 
                            name TEXT NOT NULL, profession TEXT NOT NULL, goal TEXT NOT NULL,
                            deadline "NUMERIC NOT NULL",
                            FOREIGN KEY(user_id) REFERENCES users(id));

CREATE INDEX useridq ON questionnaire (user_id);

CREATE TABLE inspiration (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL,
                          picture TEXT NOT NULL, comment TEXT NOT NULL, link TEXT,
                          FOREIGN KEY(user_id) REFERENCES users(id));

CREATE INDEX useridinsp ON inspiration (user_id);


ALTER TABLE plan
  ADD importance INTEGER NOT NULL;


  дату поменять с нумерика в текст

  убрать дату в плане


UPDATE questionnaire SET deadline = "11/11/2025" WHERE user_id = "2";


ALTER TABLE questionnaire ALTER COLUMN deadline TEXT; не работает 

DELETE FROM "table_name"
WHERE "condition";

ALTER TABLE plan
  ADD date NUMERIC;