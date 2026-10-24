# ShopFlow --- Electronics Store

ShopFlow is a demo electronics storefront built with **Python** and
**FastAPI**. It uses a modern dark navy design with cyan-blue accents
and includes sample products, a shopping cart, checkout, order tracking,
and an admin area.

> **Project status:** Demo / learning project. Product and order data
> are stored in memory, so this version is not ready for real customer
> orders or production use.

## Features

### Customer storefront

-   Browse sample electronics and accessories
-   Search and filter products
-   Add items to a session-based shopping cart
-   Complete the demo checkout flow
-   Look up an order using its order number and customer email

### Admin area

-   Sign in to the admin dashboard
-   View orders and update their status
-   Manage the product catalogue, including adding or deleting products
-   Review basic order information

### Design

-   Dark navy and black interface
-   Cyan-blue highlights
-   Responsive HTML/CSS pages

## Built With

-   Python
-   FastAPI
-   Uvicorn
-   Starlette SessionMiddleware
-   HTML and CSS

## Requirements

-   Python 3.10 or newer recommended
-   Internet connection for the externally hosted sample product images

## Run Locally on Windows

### 1. Open the project folder

Open PowerShell in the folder containing `app.py`.

### 2. Create and activate a virtual environment (recommended)

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can skip activation and use the
Python commands below, or follow your system's approved PowerShell
policy.

### 3. Install dependencies

``` powershell
python -m pip install fastapi "uvicorn[standard]" itsdangerous
```

### 4. Check the Python file

``` powershell
python -m py_compile app.py
```

No output means the syntax check passed.

### 5. Start the development server

``` powershell
python -m uvicorn app:app --reload
```

Open the storefront:

-   http://127.0.0.1:8000

Open the admin area:

-   http://127.0.0.1:8000/admin

Stop the server with **Ctrl + C** in the terminal.

## Admin Login

The current demo code uses this admin password:

``` text
11223344
```

**Security warning:** This password is hardcoded for local demonstration
only. Change it before sharing or deploying the app. Do not use this
demo configuration to protect real customer or business data.

## Configuration for Deployment

The app reads these environment variables:

  -----------------------------------------------------------------------
  Variable                            Purpose
  ----------------------------------- -----------------------------------
  `SESSION_SECRET`                    Secret used to sign session
                                      cookies. Set a long, random secret
                                      in deployment settings.

  `COOKIE_HTTPS_ONLY`                 Set to `true` when the site is
                                      served over HTTPS.
  -----------------------------------------------------------------------

For example, in PowerShell for the current terminal session:

``` powershell
$env:SESSION_SECRET = "replace-this-with-a-long-random-secret"
$env:COOKIE_HTTPS_ONLY = "false"
python -m uvicorn app:app --reload
```

For a public HTTPS deployment, configure `COOKIE_HTTPS_ONLY=true` in the
hosting provider's environment variables.

## Important Limitations

-   **No persistent database:** products and orders are held in memory
    and reset when the app process restarts. They may also be lost
    between serverless requests or instances, so this version is
    unsuitable for reliable production use.
-   **Demo checkout:** do not assume real payment processing is
    implemented. Do not collect or store real payment card details.
-   **Demo credentials:** the admin password is currently hardcoded and
    must be replaced with secure configuration before public deployment.
-   **Before production:** add persistent database storage, secure admin
    credential management, input validation and security review, error
    handling, backups, and a real payment provider only if required.

## Project Structure

``` text
ShopFlow/
├── app.py
└── README.md
```

## Future Improvements

-   Add a persistent SQLite or PostgreSQL database
-   Move admin credentials to secure environment variables and hash
    passwords
-   Add automated tests and stronger production security
-   Add a payment provider integration if the business needs online
    payments

## License

No license has been specified yet. Add a `LICENSE` file before
distributing the project if you want to define reuse permissions.
