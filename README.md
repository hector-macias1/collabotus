# Collabotus
A Telegram bot for collab projects

## Setup
1. Clone repository:
```shell
git clone https://github.com/hector-macias1/collabotus
cd collabotus
```

2. Create virtual environment (venv) and activate it:
```shell
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```shell
pip install -r requirements.txt
```

4. Download and install [ngrok](https://ngrok.com/downloads).

5. Run ngrok on port 8000:
```shell
ngrok http 8000
```
6. Copy the generated url and paste it in the correspondent env variable (WEBHOOK_URL).

7. Run the uvicorn server:
```shell
uvicorn app.main:app --reload
```
