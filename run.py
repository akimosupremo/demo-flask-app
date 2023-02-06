# "app" folder made into a package by the __init__.py file
from app import app

# ensure that the application is only run if the script is run as a standalone program
if __name__ == '__main__':
    app.run(debug=True)  # start the development server, error logging

