import pandas as pd
import re
from sqlalchemy import create_engine

# Database connection parameters
db_params = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",  # Change to your database host
    "port": "5432",  # Change to your database port
}
db_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
engine = create_engine(db_url)


def extract_directors_stars(text):
    text = text.replace("\n", "")
    if "Director" in text and "Star" in text:
        parts = text.split("|")
        director = parts[0].split(":")[1].strip().split(", ")
        stars = parts[1].split(":")[1].strip().split(", ")
    elif "Star" in text:
        director = None
        stars = text.split(":")[1].strip().split(", ")
    elif "Director" in text:
        director = text.split(":")[1].strip().split(", ")
        stars = None
    else:
        director = None
        stars = None
    return director, stars


def extract_numbers(text):
    if isinstance(text, str):
        numbers = re.findall(r"\d+", text)
        return [int(num) for num in numbers]
    else:
        return None


def clean(df):
    # Clean and preprocess data
    df["title"] = df["MOVIES"].str.strip()

    df["directors"], df["stars"] = zip(*df["STARS"].apply(extract_directors_stars))

    df["year"] = df["YEAR"].apply(extract_numbers)
    df["year_start"] = df["year"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None
    )
    df["year_end"] = df["year"].apply(
        lambda x: x[1] if isinstance(x, list) and len(x) > 1 else None
    )

    df["genres"] = df["GENRE"].apply(
        lambda x: x.replace("\n", "").strip().split(", ")
        if isinstance(x, str)
        else None
    )

    df["votes"] = pd.to_numeric(df["VOTES"].str.replace(",", ""), errors="coerce")

    df["gross"] = pd.to_numeric(df["Gross"].str.strip("$M"), errors="coerce")

    df = df.rename(
        columns={"ONE-LINE": "one_line", "RATING": "rating", "RunTime": "run_time"}
    )[
        [
            "title",
            "year_start",
            "year_end",
            "genres",
            "rating",
            "one_line",
            "directors",
            "stars",
            "votes",
            "run_time",
            "gross",
        ]
    ]

    return df


def main():
    df = pd.read_csv("movies.csv")
    df = clean(df)

    # Data Normalization
    ## Add movie_id column to dataframe
    df["movie_id"] = df.index

    ## Normalize Genres
    movie_genre_df = df.explode("genres")[["movie_id", "genres"]]
    genres_df = pd.DataFrame(
        movie_genre_df["genres"].explode().unique(), columns=["genre_name"]
    )
    genres_df["genre_id"] = genres_df.index
    movie_genre_df = movie_genre_df.merge(
        genres_df, left_on="genres", right_on="genre_name", how="left"
    )[["movie_id", "genre_id"]]

    ## Normalize Directors
    movie_director_df = df.explode("directors")[["movie_id", "directors"]]
    directors_df = pd.DataFrame(
        movie_director_df["directors"].explode().unique(), columns=["director_name"]
    )
    directors_df["director_id"] = directors_df.index
    movie_director_df = movie_director_df.merge(
        directors_df, left_on="directors", right_on="director_name", how="left"
    )[["movie_id", "director_id"]]

    ## Normalize Stars (Actors)
    movie_star_df = df.explode("stars")[["movie_id", "stars"]]
    stars_df = pd.DataFrame(
        movie_star_df["stars"].explode().unique(), columns=["actor_name"]
    )
    stars_df["actor_id"] = stars_df.index
    movie_star_df = movie_star_df.merge(
        stars_df, left_on="stars", right_on="actor_name", how="left"
    )[["movie_id", "actor_id"]]

    ## Drop unnecessary columns
    movies_df = df.drop(columns=["directors", "stars", "genres"])

    # Insert data into the database
    movies_df.to_sql(
        name="movies",
        con=engine,
        schema="public",
        if_exists="replace",
        method="multi",
        index=False,
    )
    genres_df.to_sql("genres", engine, if_exists="replace", index=False)
    directors_df.to_sql("directors", engine, if_exists="replace", index=False)
    stars_df.to_sql("stars", engine, if_exists="replace", index=False)
    movie_genre_df.to_sql("movie_genres", engine, if_exists="replace", index=False)
    movie_director_df.to_sql(
        "movie_directors", engine, if_exists="replace", index=False
    )
    movie_star_df.to_sql("movie_stars", engine, if_exists="replace", index=False)


main()
