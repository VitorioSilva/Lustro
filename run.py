from app import create_app
import os

app = create_app()

# Handler para Vercel
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
else:
    # Para Vercel serverless
    application = app