from flask import Blueprint, render_template

from roger.persistence.dge import get_all_ds
from roger.persistence import db

web = Blueprint('web', __name__, template_folder='templates')


@web.route('/')
@web.route('/index')
def index():
    studies = get_all_ds(db.session())
    return render_template('index.html', title='Home', studies=studies)
