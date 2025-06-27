install:
	pip install -r backend/requirements.lock
	cd frontend && npm install

dev:
	python -m backend.api & cd frontend && npm run dev

test:
	pytest -q
	cd frontend && npm run lint

lint:
	black backend && isort backend
	cd frontend && npm run lint

build-front:
	cd frontend && npm run build

build-docker:
	docker build -t meridian-v2.1 .

render-open:
	open https://dashboard.render.com/deploy
