# rent_management/models/rent_dashboard.py

from odoo import models, fields, api
from datetime import date, timedelta
import calendar


class RentDashboard(models.AbstractModel):
    _name = "rent.dashboard"
    _description = "Rent Dashboard"

    @api.model
    def get_user_info(self):
        """Mengambil nama pengguna yang sedang login."""
        return {"user_name": self.env.user.name}

    def _get_date_range(self, period):
        """Helper untuk mendapatkan rentang tanggal dari string periode."""
        today = date.today()
        date_from = today
        date_to = today

        if period == "week":
            date_from = today - timedelta(days=today.weekday())
            date_to = date_from + timedelta(days=6)
        elif period == "month":
            date_from = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            date_to = today.replace(day=last_day)
        elif period == "quarter":
            start_month = ((today.month - 1) // 3) * 3 + 1
            date_from = today.replace(month=start_month, day=1)
            end_month = start_month + 2
            last_day = calendar.monthrange(today.year, end_month)[1]
            date_to = today.replace(month=end_month, day=last_day)
        elif period == "year":
            date_from = today.replace(month=1, day=1)
            date_to = today.replace(month=12, day=31)

        return date_from, date_to

    @api.model
    def get_rent_kpis(self, period="month"):
        """Mengambil data KPI berdasarkan periode yang dipilih."""
        date_from, date_to = self._get_date_range(period)

        available_vehicles = self.env["vehicle.vehicle"].search_count(
            [("state", "=", "available")]
        )
        rented_vehicles = self.env["vehicle.vehicle"].search_count(
            [("state", "=", "rent")]
        )

        booking_domain = [("from_date", ">=", date_from), ("from_date", "<=", date_to)]
        expense_domain = [
            ("expense_date", ">=", date_from),
            ("expense_date", "<=", date_to),
        ]

        bookings = self.env["booking.transaction"].search(booking_domain)
        total_revenue_float = sum(
            b.total_amount for b in bookings if b.state in ["rented", "done"]
        )

        expenses = self.env["rent.expense"].search(expense_domain)
        total_expense = sum(e.total_amount for e in expenses if e.state == "confirmed")

        new_bookings_count = len(bookings)

        return {
            "available_vehicles": available_vehicles,
            "rented_vehicles": rented_vehicles,
            "total_revenue": f"Rp {total_revenue_float:,.0f}".replace(",", "."),
            "total_expense": total_expense,
            "new_bookings": new_bookings_count,
        }

    @api.model
    def get_revenue_vs_expense_data(self, period="month"):
        """Mengambil data pendapatan vs pengeluaran dengan grouping dinamis."""
        date_from, date_to = self._get_date_range(period)

        # Tentukan interval dan format label berdasarkan periode
        if period == "week":
            interval = "1 day"
            format_str = "TMDay"
            label_prefix = ""
        elif period == "month":
            interval = "1 week"
            format_str = "W"
            label_prefix = "Minggu ke-"
        else:  # quarter or year
            interval = "1 month"
            format_str = "TMMonth"
            label_prefix = ""

        # PERBAIKAN: Gunakan hanya placeholder %s dan susun parameter dalam satu tuple
        query = """
                SELECT
                    to_char(period_start, %s) as period_label,
                    COALESCE(SUM(bt.total_amount), 0) as revenue,
                    (SELECT COALESCE(SUM(re.total_amount), 0)
                     FROM rent_expense re
                     WHERE re.expense_date >= period_start AND re.expense_date < period_start + %s::interval
                    AND re.state = 'confirmed') as expense
                FROM
                    generate_series(%s::date, %s::date, %s::interval) as period_start
                    LEFT JOIN
                    booking_transaction bt ON bt.from_date >= period_start AND bt.from_date < period_start + %s::interval
                    AND bt.state IN ('rented', 'done')
                GROUP BY
                    period_start
                ORDER BY
                    period_start; \
                """

        # Susun semua parameter ke dalam satu tuple sesuai urutan %s
        params = (format_str, interval, date_from, date_to, interval, interval)

        self.env.cr.execute(query, params)
        results = self.env.cr.dictfetchall()

        # Format label
        labels = [f"{label_prefix}{r['period_label'].strip()}" for r in results]
        revenues = [r["revenue"] for r in results]
        expenses = [r["expense"] for r in results]

        return {"labels": labels, "revenues": revenues, "expenses": expenses}

    @api.model
    def get_popular_vehicles_data(self, period="month"):
        """Data untuk Bar Chart kendaraan terpopuler berdasarkan periode."""
        date_from, date_to = self._get_date_range(period)

        query = """
                SELECT
                    vv.name,
                    COUNT(btl.id) as booking_count
                FROM
                    booking_transaction_line btl
                        JOIN
                    booking_transaction bt ON btl.booking_transaction_id = bt.id
                        JOIN
                    vehicle_vehicle vv ON btl.vehicle_id = vv.id
                WHERE
                    bt.from_date >= %s AND bt.from_date <= %s
                GROUP BY
                    vv.name
                ORDER BY
                    booking_count DESC
                    LIMIT 10; \
                """
        self.env.cr.execute(query, (date_from, date_to))
        results = self.env.cr.dictfetchall()
        labels = [r["name"] for r in results]
        counts = [r["booking_count"] for r in results]
        return {"labels": labels, "counts": counts}

    @api.model
    def get_vehicle_status_data(self):
        """Data untuk Pie Chart status kendaraan (selalu real-time)."""
        status_data = self.env["vehicle.vehicle"].read_group(
            domain=[], fields=["state"], groupby=["state"], lazy=False
        )
        selection_dict = dict(self.env["vehicle.vehicle"]._fields["state"].selection)
        labels = [selection_dict.get(s["state"]) for s in status_data if s["state"]]
        counts = [s["__count"] for s in status_data if s["state"]]
        return {"labels": labels, "counts": counts}

    @api.model
    def get_booking_transactions(self, period="month"):
        """Mengambil 10 transaksi booking terakhir berdasarkan periode."""
        date_from, date_to = self._get_date_range(period)

        domain = [("from_date", ">=", date_from), ("from_date", "<=", date_to)]

        recent_bookings = self.env["booking.transaction"].search(
            domain, limit=10, order="from_date desc"
        )

        transactions = []
        for booking in recent_bookings:
            transactions.append(
                {
                    "id": booking.id,
                    "name": booking.name,
                    "customer": booking.customer_id.name or "N/A",
                    "from_date": booking.from_date.strftime("%d %b %Y"),
                    "to_date": booking.to_date.strftime("%d %b %Y"),
                    "total_amount": booking.total_amount,
                    "currency_symbol": booking.currency_id.symbol,
                    "state": dict(booking._fields["state"].selection).get(
                        booking.state
                    ),
                }
            )

        return transactions
