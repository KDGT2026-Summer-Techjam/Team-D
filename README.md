# Team-D

Djangoを使ったイベント共有アプリの学習用プロジェクトです。

## 現在の学習範囲

現在は次の画面用ファイルだけを用意しています。ファイルの中身、URL、ビュー、
フォーム、データベース処理はまだ実装していません。

- `templates/core/home.html`
- `templates/core/search_results.html`
- `templates/core/event_form.html`
- `templates/core/review_form.html`
- `templates/core/event_detail.html`
- `templates/core/review_detail.html`
- `static/css/style.css`
- `core/views.py`
- `core/urls.py`
- `core/forms.py`
- `core/tests.py`

## 必要な環境

- Python 3.10以上（Python 3.14で動作確認）
- Django 5.2 LTS

## セットアップ

Windows PowerShellの場合:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

ブラウザで <http://127.0.0.1:8000/> を開いてください。管理画面は
<http://127.0.0.1:8000/admin/> です。

管理ユーザーを作る場合:

```powershell
python manage.py createsuperuser
```

## テスト

```powershell
python manage.py test
```

## 構成

```text
config/             プロジェクト全体の設定
core/               画面用の空ファイルを置くアプリ
templates/          HTMLテンプレート
static/             CSSなどの静的ファイル
manage.py           Django管理コマンドの入口
requirements.txt    Python依存パッケージ
```

## 環境変数

本番環境では次の環境変数を設定してください。

- `DJANGO_SECRET_KEY`: 十分に長いランダムな秘密鍵
- `DJANGO_DEBUG`: 本番では `false`
- `DJANGO_ALLOWED_HOSTS`: カンマ区切りの許可ホスト名
