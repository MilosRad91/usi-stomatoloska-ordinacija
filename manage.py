# manage.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from main import app        # import Flask instance iz src/main.py
from extensions import db
from flask_migrate import Migrate
import models               # import svih modela iz src/models.py

migrate = Migrate(app, db)