# Sistema de Inventario Backend

Backend API del sistema de inventario, construido con Django REST Framework, JWT y PostgreSQL.

## Stack

- Python 3.13
- Django
- Django REST Framework
- Simple JWT
- django-filter
- PostgreSQL

## Funcionalidades

- Login con JWT
- Endpoint del usuario autenticado
- Roles `admin` y `employee`
- Gestion de usuarios
- Gestion de categorias
- Gestion de productos
- Registro de movimientos de inventario
- Dashboard resumido
- Reportes de movimientos
- Filtros, busqueda y paginacion

## Reglas de negocio

- El stock no puede quedar negativo
- Una entrada suma stock
- Una salida resta stock
- Un ajuste define el stock final
- No se permite una salida mayor al stock disponible
- Todo movimiento queda registrado con usuario y fecha

## Variables de entorno

Crear `.env` basado en `.env.example`:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DJANGO_TIME_ZONE=America/Bogota

DB_ENGINE=django.db.backends.postgresql
DB_NAME=inventory_app_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5434

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
API_PAGE_SIZE=10
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
```

## Instalacion

```powershell
pip install -r requirements.txt
```

## Migraciones

```powershell
python manage.py migrate
```

## Desarrollo

```powershell
python manage.py runserver
```

## Verificacion

```powershell
python manage.py check
```

## Endpoints principales

- `POST /api/auth/login`
- `GET /api/auth/me`
- `PATCH /api/auth/me`
- `GET /api/users/`
- `POST /api/users/`
- `PATCH /api/users/:id/`
- `GET /api/categories/`
- `POST /api/categories/`
- `PUT /api/categories/:id/`
- `DELETE /api/categories/:id/`
- `GET /api/products/`
- `POST /api/products/`
- `PATCH /api/products/:id/`
- `PATCH /api/products/:id/deactivate/`
- `GET /api/movements/`
- `POST /api/movements/`
- `GET /api/dashboard/summary`
- `GET /api/reports/movements`

## Credenciales demo

- Email: `admin@inventario.com`
- Password: `Admin12345!`

## Estado

Backend listo para demostracion de portafolio, con permisos por rol, validaciones de inventario y base preparada para crecimiento.
