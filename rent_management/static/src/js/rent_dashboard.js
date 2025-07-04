/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class RentDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.action = useService("action");

        this.revenueVsExpenseChartRef = useRef('revenueVsExpenseChartRef');
        this.vehicleStatusChartRef = useRef('vehicleStatusChartRef');
        this.popularVehiclesChartRef = useRef('popularVehiclesChartRef');

        this.state = useState({
            kpis: {},
            charts: [],
            period: 'month',
            recent_bookings: [],
            user_name: "",
        });

        // onWillStart hanya untuk mengambil data yang tidak akan pernah berubah (statis)
        onWillStart(async () => {
            const userInfo = await this.orm.call('rent.dashboard', 'get_user_info');
            this.state.user_name = userInfo.user_name;
        });

        // useEffect akan menangani semua pengambilan data dinamis dan rendering
        useEffect(() => {
            this.loadDashboardData();
        }, () => [this.state.period]);
    }

    async loadDashboardData() {
        // Ambil semua data yang bergantung pada periode
        const [kpiData, bookingData] = await Promise.all([
            this.orm.call('rent.dashboard', 'get_rent_kpis', [], { period: this.state.period }),
            this.orm.call('rent.dashboard', 'get_booking_transactions', [], { period: this.state.period }),
        ]);
        this.state.kpis = kpiData;
        this.state.recent_bookings = bookingData;

        // Hancurkan chart lama sebelum render yang baru
        this.state.charts.forEach(chart => chart.destroy());
        this.state.charts = [];
        this.renderAllCharts();
    }

    async renderAllCharts() {
        // Panggil semua fungsi render grafik
        this.renderVehicleStatusChart();
        this.renderRevenueVsExpenseChart();
        this.renderPopularVehiclesChart();
    }

    async renderRevenueVsExpenseChart() {
        const data = await this.orm.call('rent.dashboard', 'get_revenue_vs_expense_data', [], { period: this.state.period });
        if (this.revenueVsExpenseChartRef.el) {
            const chart = new Chart(this.revenueVsExpenseChartRef.el, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Pendapatan',
                        data: data.revenues,
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    }, {
                        label: 'Pengeluaran',
                        data: data.expenses,
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    }]
                },
                options: {
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value, index, values) {
                                    return 'Rp ' + new Intl.NumberFormat('id-ID').format(value);
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += 'Rp ' + new Intl.NumberFormat('id-ID').format(context.parsed.y);
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
            this.state.charts.push(chart);
        }
    }

    async renderVehicleStatusChart() {
        const data = await this.orm.call('rent.dashboard', 'get_vehicle_status_data');
        if (this.vehicleStatusChartRef.el) {
            const chart = new Chart(this.vehicleStatusChartRef.el, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Status Kendaraan',
                        data: data.counts,
                        backgroundColor: ['#28a745', '#ffc107', '#dc3545', '#6c757d'],
                    }]
                }
            });
            this.state.charts.push(chart);
        }
    }

    async renderPopularVehiclesChart() {
        const data = await this.orm.call('rent.dashboard', 'get_popular_vehicles_data', [], { period: this.state.period });
        if (this.popularVehiclesChartRef.el) {
            const chart = new Chart(this.popularVehiclesChartRef.el, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Jumlah Booking',
                        data: data.counts,
                        backgroundColor: '#4a90e2',
                    }]
                },
                options: { indexAxis: 'y' }
            });
            this.state.charts.push(chart);
        }
    }
}

RentDashboard.template = 'rent_management.RentDashboard';
registry.category("actions").add("rent_dashboard", RentDashboard);