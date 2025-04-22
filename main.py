import os
from website import create_app


app = create_app()

# Create the "root" folder if it doesn't exist
if not os.path.exists('root'):
    os.makedirs('root')

if __name__ == "__main__":
    app.run(debug=True)
