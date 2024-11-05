# Copyright (c) 2023 All Rights Reserved
# Generated code

from flask import Flask

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['USER_APP_NAME'] = "{{- projectname}}"
app.config['USER_ENABLE_EMAIL'] = False      
app.config['USER_ENABLE_USERNAME'] = True    
app.config['USER_REQUIRE_RETYPE_PASSWORD'] = False
app.config['SECRET_KEY'] = '_5#yfasQ8DdAsaQ5ndsFaHxeGc/ls][#1'
app.config['USER_UNAUTHORIZED_ENDPOINT'] = 'error'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
