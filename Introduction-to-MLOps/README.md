## MLFlow

- Start MLFlow web UI in Linux

```bash
mlflow ui --port 5000 >/dev/null 2>&1
```

- Start MLFlow web UI in Windows

```bash
mlflow ui --port 5000
```

## Feast

- Init new feast repo

```bash
feast init <repo_name> # example feature_repo
```

- Start UI

```bash
cd feature_repo/feature_repo
feast ui
```

- Navigate to `http://localhost:8888`
