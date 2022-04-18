from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, HiddenField
from wtforms.validators import DataRequired, NumberRange
import requests
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-list.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
API_key = "c9993132821011ba0fca0e06d7064a6c"
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(400), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True, unique=True)
    review = db.Column(db.Text, nullable=True)
    thumbnail = db.Column(db.Text, nullable=True)


class EditForm(FlaskForm):
    e_id = HiddenField('Id', validators=[DataRequired()])
    e_rating = FloatField('Your rating: ', validators=[DataRequired(), NumberRange(min=0, max=10)])
    e_review = StringField('Your review: ')
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie title to look for:', validators=[DataRequired()])
    submit = SubmitField('Find movie')


def get_year(date):
    return int(date.split('-')[0])


@app.route("/")
def home():
    movies_list = Movie.query.order_by(Movie.rating.asc()).all()
    for i in range(len(movies_list)):
        movies_list[i].ranking += 1000
    db.session.commit()
    for i in range(len(movies_list)):
        movies_list[i].ranking = len(movies_list) - i
    db.session.commit()
    return render_template("index.html", movies=movies_list)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    edit_form = EditForm()
    if request.method == 'POST':
        if edit_form.validate_on_submit():
            edit_movie = Movie.query.get(edit_form.e_id.data)
            edit_movie.rating = edit_form.e_rating.data
            edit_movie.review = edit_form.e_review.data
            db.session.commit()
            return redirect(url_for('home'))
    edit_id = request.args.get('id')
    edit_movie = Movie.query.get(edit_id)
    return render_template('edit.html', movie=edit_movie, form=edit_form)


@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = AddForm()
    if request.method == 'POST':
        if add_form.validate_on_submit():
            parameters = {
                'api_key': API_key,
                'query': add_form.title.data,
            }
            response = requests.get('https://api.themoviedb.org/3/search/movie', params=parameters)
            data = response.json()
            result_list = [{'title': movie['title'], 'release': movie['release_date'], 'api_id': movie['id']} for movie in data['results']]
            return render_template('select.html', movie_list=result_list)
    return render_template('add.html', add_form=add_form)


@app.route('/select')
def select():
    response = requests.get(f"https://api.themoviedb.org/3/movie/{request.args.get('movie_id')}", params={'api_key': API_key})
    data = response.json()
    new_movie = Movie(
        title=data['title'],
        year=get_year(data['release_date']),
        description=data['overview'],
        ranking=random.randint(1, 1000),
        thumbnail=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


@app.route('/delete')
def delete():
    delete_movie = Movie.query.get(request.args.get('id'))
    db.session.delete(delete_movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
