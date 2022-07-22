from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, Optional
import requests as rq

# Movie API details
key = "[Your api key]"
search_url = "https://api.themoviedb.org/3"
token = "{Your token}"

headers = {
    "access_token": token
}

# Declaring app
app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = "{Your secret key}"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Adding bootstrap styling to app
Bootstrap(app)

# Creating a database
db = SQLAlchemy(app)


# Class for database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True, nullable=False)  # Unique title and cannot have null/ None value
    year = db.Column(db.Integer, nullable=False)  # Cannot have null value
    description = db.Column(db.String(200), nullable=False)  # Cannot have null value
    review = db.Column(db.String(200), nullable=True)  # Can have null value (Because we have to add these)
    rating = db.Column(db.Float, nullable=True)  # Can have null value (Because we have to add these)
    ranking = db.Column(db.Integer, nullable=True)  # Can have null value (Because we have to add these)
    img_url = db.Column(db.String(300), nullable=False)  # Cannot have null value


# Creating database
db.create_all()


# Creating class for editing form
class EditForm(FlaskForm):
    new_rating = FloatField(label="Your Rating out of 10", validators=[Optional()])
    new_review = StringField(label="Your Review", validators=[Optional()])
    submit = SubmitField(label="Update")


# Creating class of Flask form
class AddForm(FlaskForm):
    movie_title = StringField(label='Movie Title:', validators=[DataRequired()])
    submit = SubmitField(label='Add')


# Calling the data from the database:
movie_list = db.session.query(Movie).all()


# Routes
#  for home
@app.route("/")
def home():
    # Creates a list in order of Movie rating
    movie_list_order = Movie.query.order_by(Movie.rating).all()
    # Looping through list
    for i in range(len(movie_list_order)):
        # Adding rank to the item number i as per list
        movie_list_order[i].ranking = len(movie_list_order) - i
    # Committing data
    db.session.commit()
    # Rendering template
    return render_template("index.html", movies=movie_list)


# For editing data: rating and review
@app.route("/edit/<int:id>", methods=["POST", "GET"])  # Giving methods for requests and entering id as a parameter
def edit(id):  # Adding id as parameter
    #  Creating form object
    edit_form = EditForm()
    # Conditions:
    if edit_form.validate_on_submit():  # If form is validated on submit, it returns True
        # Getting the movie with id to find that movie in the database
        change_this_movie_rating = Movie.query.get(id)
        # Since form is optional to fill, it will be better to add two conditions
        if edit_form.new_rating.data:  # If user adds rating
            change_this_movie_rating.rating = edit_form.new_rating.data
        if edit_form.new_review.data:  # If user adds review
            change_this_movie_rating.review = edit_form.new_review.data
        # Committing changes to database
        db.session.commit()
        # Redirecting to home page
        return redirect(url_for('home'))
    # Rendering template
    return render_template('edit.html', id=id, form=edit_form)


# For deleting entry in database as well as in webpage
@app.route('/delete/<int:id>')
def delete(id):  # Giving id as a parameter to delete that specific database
    # Getting the movie to be deleted with id
    delete_movie = Movie.query.get(id)
    # Command to delete movie
    db.session.delete(delete_movie)
    # Committing changes to the database
    db.session.commit()
    # Rendering template
    return redirect(url_for('home'))


# For adding new movie to the list
@app.route('/add', methods=['GET', 'POST'])  # Adding methods
def add():
    # Creating form object to get data from the form
    add_form = AddForm()
    # If form is validated
    if add_form.validate_on_submit():
        # Data received from form
        data = add_form.data
        # Giving custom parameters
        params = {
            "api_key": key,
            "query": data['movie_title']
        }
        # Requesting data from API
        response = rq.get(url=f"{search_url}/search/movie", params=params, headers=headers)
        # Creating a json file for received data
        new_movies_list = response.json()['results']
        # Rendering Select webpage to select the movie form the list (Because there are a lot of movies with same name)
        return render_template('select.html', list=new_movies_list)  # Giving list as parameter
    # Rendering template
    return render_template('add.html', form=add_form)


# For selecting the required movie
@app.route('/select/<int:id>')  # Taking id as a parameter to get the details of the movie from API
def select(id):
    # Giving custom parameters
    params = {
        "api_key": key,
    }
    # Getting the data of selected movie
    response = rq.get(url=f"{search_url}/movie/{int(id)}", params=params, headers=headers)
    # Converting response into json
    movie = response.json()
    # Adding new entry to the database with required keys from json file
    new_movie = Movie(
        title=movie['original_title'],
        year=movie['release_date'].split("-")[0],
        description=movie['overview'],
        rating=None,
        ranking=None,
        review=None,
        img_url=f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    )
    # Adding new data into the database
    db.session.add(new_movie)
    # Committing the changes to the database
    db.session.commit()
    # Rendering the template
    return redirect(url_for('edit', id=new_movie.id))  # Going to edit the rating and review which was given as none


# Running app if path of interpreter is same
if __name__ == '__main__':
    app.run(debug=True) # Turing on debugging mode
