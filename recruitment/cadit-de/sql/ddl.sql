CREATE TABLE movies (
    movie_id SERIAL PRIMARY KEY,
    title TEXT,
    one_line TEXT,
    year_start INTEGER,
    year_end INTEGER,
    rating FLOAT,
    votes FLOAT,
    run_time INTEGER,
    gross FLOAT
);

CREATE TABLE movie_directors (
    movie_id INTEGER REFERENCES movies(movie_id),
    director_id INTEGER REFERENCES directors(director_id),
    PRIMARY KEY (movie_id, director_id)
);

CREATE TABLE movie_genres (
    movie_id INTEGER REFERENCES movies(movie_id),
    genre_id INTEGER REFERENCES genres(genre_id),
    PRIMARY KEY (movie_id, genre_id)
);

CREATE TABLE movie_stars (
    movie_id INTEGER REFERENCES movies(movie_id),
    actor_id INTEGER REFERENCES stars(actor_id),
    PRIMARY KEY (movie_id, actor_id)
);

CREATE TABLE stars (
    actor_id SERIAL PRIMARY KEY,
    actor_name TEXT
);

CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name TEXT
);

CREATE TABLE directors (
    director_id SERIAL PRIMARY KEY,
    director_name TEXT
);
