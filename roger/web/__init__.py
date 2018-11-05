from flask import Blueprint, render_template
from rpy2.robjects.packages import importr

ribios_plot = importr("ribiosPlot")
ribios_ngs = importr("ribiosNGS")
ribios_expression = importr("ribiosExpression")
base = importr("base")
limma = importr("limma")
stats = importr("stats")
made4 = importr("made4")
graphics = importr("graphics")

web_blueprint = Blueprint('web', __name__, template_folder='templates')


@web_blueprint.route('/', defaults={'path': ''})
@web_blueprint.route('/<path:path>')
def react_provide(path):
    return render_template('index.html')
