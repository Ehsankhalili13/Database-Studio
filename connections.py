"""Connection management, schema browsing, and SQL execution routes."""

from flask import Blueprint, flash, redirect, render_template, request, url_for, Response
from flask_login import current_user, login_required
from sqlalchemy import MetaData, Table, func, inspect, select

import csv\nimport io\n\nfrom database_drivers import (
    create_database_engine,
    encrypt_password,
    list_databases,
    list_tables,
    table_columns,
    test_connection,
    run_query,
)
from extensions import db
from models import DatabaseConnection

connections_bp = Blueprint("connections", __name__, url_prefix="/connections")

DRIVERS = {
    "sqlite": "SQLite",
    "mysql": "MySQL",
    "sqlserver": "Microsoft SQL Server",
}


def _owned_connection(connection_id):
    return DatabaseConnection.query.filter_by(
        id=connection_id,
        owner_id=current_user.id,
    ).first_or_404()


def _read_form(connection=None):
    driver = request.form.get("driver", "sqlite").strip().lower()
    if driver not in DRIVERS:
        raise ValueError("نوع دیتابیس انتخاب‌شده پشتیبانی نمی‌شود.")

    name = request.form.get("name", "").strip()
    if not name or len(name) > 100:
        raise ValueError("نام اتصال الزامی است و حداکثر ۱۰۰ کاراکتر دارد.")

    def number(field, default):
        raw = request.form.get(field, "").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError("شماره پورت باید عددی باشد.") from exc
        if not 1 <= value <= 65535:
            raise ValueError("شماره پورت باید بین ۱ و ۶۵۵۳۵ باشد.")
        return value

    values = {
        "name": name,
        "driver": driver,
        "host": request.form.get("host", "").strip()[:255] or None,
        "port": number("port", 3306 if driver == "mysql" else 1433),
        "database_name": request.form.get("database_name", "").strip()[:255] or None,
        "database_path": request.form.get("database_path", "").strip()[:1000] or "database.sqlite",
        "username": request.form.get("username", "").strip()[:255] or None,
        "odbc_driver": request.form.get("odbc_driver", "ODBC Driver 18 for SQL Server").strip()[:255],
        "encrypt_connection": request.form.get("encrypt_connection") == "on",
        "trust_server_certificate": request.form.get("trust_server_certificate") == "on",
    }

    password = request.form.get("password", "")
    if password:
        values["password_encrypted"] = encrypt_password(password)
    elif connection is not None:
        values["password_encrypted"] = connection.password_encrypted
    else:
        values["password_encrypted"] = ""

    if driver == "sqlite":
        values["host"] = None
        values["port"] = None
        values["username"] = None
        values["database_name"] = None
    else:
        if not values["host"]:
            raise ValueError("آدرس میزبان الزامی است.")
        if not values["database_name"]:
            raise ValueError("نام دیتابیس الزامی است.")
        if driver == "sqlserver" and not values["username"]:
            raise ValueError("نام کاربری SQL Server الزامی است.")

    return values


@connections_bp.get("/")
@login_required
def index():
    connections = DatabaseConnection.query.filter_by(
        owner_id=current_user.id
    ).order_by(DatabaseConnection.name).all()
    return render_template("connections.html", connections=connections, drivers=DRIVERS)


@connections_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        try:
            values = _read_form()
            connection = DatabaseConnection(owner_id=current_user.id, **values)
            ok, message = test_connection(connection)
            if not ok:
                flash(f"اتصال ذخیره نشد؛ تست اتصال ناموفق بود: {message}", "error")
                return render_template(
                    "connection_form.html",
                    connection=None,
                    drivers=DRIVERS,
                    form_values=request.form,
                )

            db.session.add(connection)
            db.session.commit()
            flash("اتصال ذخیره شد و تست اتصال موفق بود.", "success")
            return redirect(url_for("connections.index"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception:
            db.session.rollback()
            flash("ذخیره اتصال انجام نشد. تنظیمات را بررسی کنید.", "error")

    return render_template(
        "connection_form.html",
        connection=None,
        drivers=DRIVERS,
        form_values=request.form,
    )


@connections_bp.route("/<int:connection_id>/edit", methods=["GET", "POST"])
@login_required
def edit(connection_id):
    connection = _owned_connection(connection_id)
    if request.method == "POST":
        try:
            values = _read_form(connection)
            for key, value in values.items():
                setattr(connection, key, value)
            ok, message = test_connection(connection)
            if not ok:
                db.session.rollback()
                flash(f"تست اتصال ناموفق بود: {message}", "error")
                return render_template(
                    "connection_form.html",
                    connection=connection,
                    drivers=DRIVERS,
                    form_values=request.form,
                )
            db.session.commit()
            flash("تنظیمات اتصال ذخیره شد.", "success")
            return redirect(url_for("connections.index"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception:
            db.session.rollback()
            flash("ویرایش اتصال انجام نشد. تنظیمات را بررسی کنید.", "error")

    return render_template(
        "connection_form.html",
        connection=connection,
        drivers=DRIVERS,
        form_values={},
    )


@connections_bp.post("/<int:connection_id>/delete")
@login_required
def delete(connection_id):
    connection = _owned_connection(connection_id)
    db.session.delete(connection)
    db.session.commit()
    flash("اتصال حذف شد.", "success")
    return redirect(url_for("connections.index"))


@connections_bp.post("/<int:connection_id>/test")
@login_required
def test(connection_id):
    connection = _owned_connection(connection_id)
    ok, message = test_connection(connection)
    flash(message, "success" if ok else "error")
    return redirect(url_for("connections.index"))


@connections_bp.get("/<int:connection_id>/explorer")
@login_required
def explorer(connection_id):
    connection = _owned_connection(connection_id)
    try:
        databases = list_databases(connection)
        tables = list_tables(connection)
        selected_table = request.args.get("table", "").strip()
        columns = table_columns(connection, selected_table) if selected_table else []
        return render_template(
            "explorer.html",
            connection=connection,
            databases=databases,
            tables=tables,
            selected_table=selected_table,
            columns=columns,
        )
    except Exception as exc:
        flash(f"خواندن ساختار دیتابیس ناموفق بود: {str(exc).splitlines()[0][:300]}", "error")
        return redirect(url_for("connections.index"))


@connections_bp.route("/<int:connection_id>/query", methods=["GET", "POST"])
@login_required
def query(connection_id):
    connection = _owned_connection(connection_id)
    result = None
    sql = request.form.get("sql", "SELECT 1;")
    if request.method == "POST":
        try:
            result = run_query(connection, sql)
            flash(result["message"], "success")
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception as exc:
            flash(f"اجرای کوئری ناموفق بود: {str(exc).splitlines()[0][:500]}", "error")

    return render_template(
        "query.html",
        connection=connection,
        sql=sql,
        result=result,
    )



@connections_bp.get("/<int:connection_id>/table/<path:table_name>")
@login_required
def table_data(connection_id, table_name):
    connection = _owned_connection(connection_id)
    try:
        engine = create_database_engine(connection)
        try:
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                flash("جدول موردنظر پیدا نشد.", "error")
                return redirect(url_for("connections.explorer", connection_id=connection.id))

            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)
            page = max(1, request.args.get("page", 1, type=int))
            per_page = 100
            with engine.connect() as conn:
                total = conn.execute(select(table.count())).scalar_one()
                result = conn.execute(
                    select(table).limit(per_page).offset((page - 1) * per_page)
                )
                columns = list(result.keys())
                rows = [
                    [str(value) if value is not None else None for value in row]
                    for row in result.fetchall()
                ]
            return render_template(
                "table_data.html",
                connection=connection,
                table_name=table_name,
                columns=columns,
                rows=rows,
                page=page,
                per_page=per_page,
                total=total,
                pages=max(1, (total + per_page - 1) // per_page),
            )
        finally:
            engine.dispose()
    except Exception as exc:
        flash(f"خواندن جدول ناموفق بود: {str(exc).splitlines()[0][:300]}", "error")
        return redirect(url_for("connections.explorer", connection_id=connection.id, table=table_name))


@connections_bp.get("/<int:connection_id>/table/<path:table_name>/export.csv")
@login_required
def export_table(connection_id, table_name):
    connection = _owned_connection(connection_id)
    engine = create_database_engine(connection)
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            flash("جدول موردنظر پیدا نشد.", "error")
            return redirect(url_for("connections.explorer", connection_id=connection.id))

        table = Table(table_name, MetaData(), autoload_with=engine)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        with engine.connect() as conn:
            result = conn.execute(select(table))
            writer.writerow(result.keys())
            for row in result:
                writer.writerow([
                    value.decode("utf-8", errors="replace")
                    if isinstance(value, bytes)
                    else value
                    for value in row
                ])

        filename = f"{table_name}.csv".replace("\\", "_").replace("/", "_")
        return Response(
            "\\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    finally:
        engine.dispose()


@connections_bp.route("/<int:connection_id>/table/<path:table_name>/import", methods=["GET", "POST"])
@login_required
def import_table(connection_id, table_name):
    connection = _owned_connection(connection_id)
    if request.method == "POST":
        uploaded = request.files.get("csv_file")
        if not uploaded or not uploaded.filename:
            flash("فایل CSV را انتخاب کن.", "error")
            return redirect(request.url)

        try:
            content = uploaded.stream.read(2 * 1024 * 1024 + 1)
            if len(content) > 2 * 1024 * 1024:
                raise ValueError("حجم فایل باید حداکثر ۲ مگابایت باشد.")
            text_content = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text_content))
            if not reader.fieldnames:
                raise ValueError("فایل CSV باید ردیف عنوان ستون‌ها را داشته باشد.")

            engine = create_database_engine(connection)
            try:
                inspector = inspect(engine)
                if table_name not in inspector.get_table_names():
                    raise ValueError("جدول موردنظر پیدا نشد.")
                table = Table(table_name, MetaData(), autoload_with=engine)
                allowed_columns = {column.name for column in table.columns}
                incoming_columns = set(reader.fieldnames)
                if not incoming_columns.issubset(allowed_columns):
                    unknown = ", ".join(sorted(incoming_columns - allowed_columns))
                    raise ValueError(f"این ستون‌ها در جدول وجود ندارند: {unknown}")
                rows = []
                for row in reader:
                    rows.append({key: value if value != "" else None for key, value in row.items()})
                    if len(rows) > 10000:
                        raise ValueError("حداکثر ۱۰٬۰۰۰ ردیف در هر بار وارد کردن مجاز است.")
                if not rows:
                    raise ValueError("فایل CSV هیچ ردیفی برای وارد کردن ندارد.")
                with engine.begin() as conn:
                    conn.execute(table.insert(), rows)
                flash(f"{len(rows)} ردیف وارد شد.", "success")
                return redirect(url_for("connections.table_data", connection_id=connection.id, table_name=table_name))
            finally:
                engine.dispose()
        except (UnicodeDecodeError, csv.Error, ValueError) as exc:
            flash(str(exc), "error")
        except Exception as exc:
            flash(f"وارد کردن CSV ناموفق بود: {str(exc).splitlines()[0][:400]}", "error")

    return render_template("import_table.html", connection=connection, table_name=table_name)
