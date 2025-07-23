## Step-by-Step Instructions

### 1. **Make sure you have Python installed**

Check with:

```bash
python --version
```

or

```bash
python3 --version
```

If not installed, download from: [https://www.python.org/downloads/](https://www.python.org/downloads/)

---

### 2. **Create the virtual environment**

In your project folder, run:

#### On Windows:

```bash
python -m venv .venv
```

#### On macOS/Linux:

```bash
python3 -m venv .venv
```

#### Upgrade pip
```bash
python.exe -m pip install --upgrade pip
```

> This creates a new folder named `.venv/` containing an isolated Python environment.

---

### 3. **Activate the virtual environment**

#### On Windows (CMD):

```bash
.venv\Scripts\activate
```

#### On Windows (PowerShell):

```bash
.venv\Scripts\Activate.ps1
```

#### On macOS/Linux:

```bash
source .venv/bin/activate
```

You should now see the environment name in your terminal prompt like this:

```
(venv) your-folder-name $
```

---

### 4. **Install packages inside the venv**

Now you can install packages with `pip`, and they'll stay isolated to this environment:

```bash
pip install pandas matplotlib
```

---

### 5. **Deactivate when done**

To exit the virtual environment:

```bash
deactivate
```

## Use Requirements

```bash
pip freeze > requirements.txt
```

This will save all installed packages (and their versions) into `requirements.txt`.

Then you can commit this file to your repo. Others can install everything with:

```bash
pip install -r requirements.txt
```
