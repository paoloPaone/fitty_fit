# Setup

Put the following command in systemd or similar and start it from the directory containing `app.py`:

`gunicorn --workers 3 --bind unix:app.sock -m 007 app:app`

Add the proxy options to nginx:
```
    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/app.sock;
    }
```