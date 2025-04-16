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

4. Run the uvicorn server:
```shell
uvicorn app.main:app --reload
```