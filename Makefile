.PHONY: help db-up db-down web cli streamlit data

help:
	@echo "Available commands:"
	@echo "  make web       - Run the Flask Clinical Web Server (port 5002)"
	@echo "  make cli       - Run the Command Line Chatbot Interface"
	@echo "  make streamlit - Run the Streamlit UI (port 8501)"
	@echo "  make db-up     - Start the database using Docker Compose"
	@echo "  make db-down   - Stop the database"
	@echo "  make data      - Run scripts to load all data into the database"
	@echo "  make install   - Install required Python dependencies"

web:
	python3 server.py

cli:
	python3 main_app.py

streamlit:
	streamlit run app_web.py

db-up:
	docker-compose up -d db

db-down:
	docker-compose down

data:
	python3 scripts/final_data_loader.py
	python3 scripts/create_default_users.py

install:
	pip install -r requirements.txt
