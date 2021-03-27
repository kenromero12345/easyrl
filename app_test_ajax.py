from flask import Flask, url_for, render_template, g, request, jsonify, flash
import random
import time

app = Flask(__name__)
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
@app.route('/ajax')
def index():
    # flash(1000)
    return render_template('ajax.html')

@app.route('/add1')
def add_numbers():
    input = request.args.get('input', 0, type=int)
    return jsonify(result=random.randint(0, 100))

# @app.route('/flash')
# def flashing():
#     flash("1000");

@app.route('/add1Infinity')
def add_1():
    # input = request.args.get('input', 0, type=int)
    return jsonify(result=random.randint(0, 100))
# flag = False;

# @app.route('/add1Initialize')
# def add_1_initialize():
#     # flag=True;
#     # if
#     # input = request.args.get('input', 0, type=int)
#     return jsonify(result=10)
#     # start_flashing();
#
# # def start_flashing():
# #     while(True):
# #         flashing();
# #
# # def flashing():
# #     flash(random.randint(0, 9))

if __name__ == "__main__":
    app.run()