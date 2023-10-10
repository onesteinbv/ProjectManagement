odoo.define('management_dashboard.PMDashboardView', function (require) {
    "use strict";

    var core = require('web.core');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var ajax = require('web.ajax');
    const { loadBundle } = require("@web/core/assets");
    var field_utils = require('web.field_utils');
    var AbstractAction = require('web.AbstractAction');
    var Widget = require('web.Widget');
    var QWeb = core.qweb;
    var _t = core._t;

    var PMDashboardView = AbstractAction.extend({

        jsLibs: [
            '/management_dashboard/static/src/lib/js/datatables.js',
            '/management_dashboard/static/src/lib/js/gantt.js',
            '/management_dashboard/static/src/lib/js/Chart.min.js',
        ],
        cssLibs: [
            '/management_dashboard/static/src/lib/css/datatables.css',
            '/management_dashboard/static/src/lib/css/gantt.css',
        ],

        events: {
            'click .project_name': '_goto_project',
            'click .dashboard_sidebar-toggle': '_toggle_sidebar',
            'click .dashboard_filter_btn': '_filter_dashboard',
            'click .show_open_task': '_goto_open_tasks',
            'click .show_all_task': '_goto_all_tasks',
            'click .show_open_issue': '_goto_open_issues',
            'click .show_all_issue': '_goto_all_issues',
            'click .running_cost': '_open_timesheet_invoice',
            'click .btn_at_risk_projects': '_open_at_risk_projects',
            'click #budget-risk-project-chart': '_goto_budget_projects_list',
            'click #projects-time-risk-chart': '_goto_projects_list',
        },

        format_date: function (value) {
            return field_utils.format.date(field_utils.parse.date(value, {
                isUTC: true
            }));
        },

        server_date: function (value) {
            return field_utils.parse.date(value, {
                isUTC: true
            }).format("YYYY-MM-DD");
        },

        getRandomColor: function () {
            var letters = '0123456789ABCDEF'.split('');
            var color = '#';
            for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        },

        /**
         * @override
         */
        init: function (parent, context) {
            var self = this;
            this._super(parent, context);
            self._rpc({
                model: 'management.dashboard',
                method: 'get_config_values',
            }).then(function (data) {
                self.fail_counter = data.fail_counter;
                self.card_header_color = '#1d355e';
                self.color_red = '#ef3f45'
                self.color_green = '#689f38'
                self.color_orange = '#f8913e'

            });

        },

        /**
         * @override
         */
        willStart: function () {
            var self = this;
            self.filter = 'month';
            var start_date = new Date(new Date().setMonth(new Date().getMonth(),1))
                    start_date.setHours(23)
            var end_date = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0)
            end_date.setHours(23)

            self.start_date = field_utils.parse.date(new Date(start_date), {
                isUTC: true
            });
            self.end_date = field_utils.parse.date(end_date,{
                isUTC: false
            });
            self.week_number = moment(new Date()).week();
            self.last_update_on = new Date('1990-01-01');
            return Promise.all([loadBundle(this), this._super()]).then(function() {
                return self.fetch_data();
            })
//            return $.when(ajax.loadLibs(this), this._super()).then(function () {
//                return self.fetch_data();
//            });
        },

        /**
         * @override
         */
        // left
        fetch_data: function () {
            var self = this;
            var data = this._rpc({
                model: 'project.project',
                method: 'search_read',
                fields: ['progress', 'id', 'name', 'date_start','date',
                    'expected_end_date', 'date', 'projected_end_date', 'percentage_completed',
                    'spent_budget','revised_budget','actual_budget',
                    'project_phase_stage', 'running_cost',
                    'write_date','resource_count',
                    'open_tasks_count', 'task_count', 'close_tasks_count',
                    'open_issues_count', 'close_issues_count',
                    'budget_of_completion', 'forecast_up_range', 'forecast_low_range'],
                context: {
                    'start_date': self.server_date(self.start_date),
                    'end_date': self.server_date(self.end_date),
                }
            });
            data.then(function (details) {
                if (details !== undefined) {
                    var project_ids = [];
                    var list_proj = [];
                    var project_phase_stage = {};
                    
                    _.each(details, function (project) {
                        var end_date = project.date || project.expected_end_date;
                        if (end_date && project.date_start){
                            if (end_date >= self.server_date(self.start_date) &&
                                project.date_start <= self.server_date(self.end_date)){
                                list_proj.push(project)
                                project_ids.push(project.id)
                                if(project_phase_stage[project.project_phase_stage]){
                                    project_phase_stage[project.project_phase_stage] += 1; 
                                }
                                else{
                                    project_phase_stage[project.project_phase_stage] = 1
                                }
                            }
                        }
                        else if(end_date){
                            if (end_date >= self.server_date(self.start_date)){
                                list_proj.push(project)
                                project_ids.push(project.id)
                                if(project_phase_stage[project.project_phase_stage]){
                                    project_phase_stage[project.project_phase_stage] += 1; 
                                }
                                else{
                                    project_phase_stage[project.project_phase_stage] = 1
                                }
                            }
                        }
                        else if(project.date_start){
                            if (project.date_start <= self.server_date(self.end_date)){
                                list_proj.push(project)
                                project_ids.push(project.id)
                                if(project_phase_stage[project.project_phase_stage]){
                                    project_phase_stage[project.project_phase_stage] += 1; 
                                }
                                else{
                                    project_phase_stage[project.project_phase_stage] = 1
                                }
                            }
                        }
                        else{
                            list_proj.push(project)
                            project_ids.push(project.id)
                            if(project_phase_stage[project.project_phase_stage]){
                                project_phase_stage[project.project_phase_stage] += 1; 
                            }
                            else{
                                project_phase_stage[project.project_phase_stage] = 1
                            }
                        }
                    })
                    self.projects = list_proj;
                    self.project_ids = project_ids;
                    self.project_phase_stage = project_phase_stage
                }
            });
            return data
        },

    //     /**
    //      * @override
    //      */
        on_attach_callback: function () {
            var self = this;
            self.hide_sidebar();
        },

    //     /**
    //      * @override
    //      */
        start: function () {
            var self = this;
            var res = this._super().then(function(){
                self.render_dashboard();
            })
            return res;
        },

        render_dashboard: function () {
            var self = this;
            self.$el.html('');
            self.$el.append(QWeb.render('management_dashboard.PMDashboardView', {
                widget: this
            }));
            this.task_chart = this.$("#task-chart");
            this.proj_status_chart = this.$("#project-status-chart");
            this.budget_risk_project_chart = this.$("#budget-risk-project-chart");
            this.projects_time_risk_chart = this.$("#projects-time-risk-chart");
            this.vendor_utilization_chart = this.$("#vendor-utilization-chart");
            this.heat_map_table = this.$("#heat-map-table");
            this.summery_table = this.$("#summery-table");
            this.hours_progress = this.$("#hours_progress")[0];
            this.risk_projects = this.$("#risk_projects")[0];
            this.heat_map = self.$("#heat-map-table").DataTable({
                "autoWidth": false,
                "searching": false,
                "lengthChange": false,
                "info": false,
                "columnDefs": [{
                    "orderable": false,
                    "targets": [1],
                }],
                "createdRow": function (row, data, index) {
                    $('td', row).eq(1).addClass('text-center');
                    $('td', row).eq(2).addClass('text-center');
                    $('td', row).eq(3).addClass('text-center');
                    $('td', row).eq(4).addClass('text-center');
                    $('td', row).eq(5).addClass('text-center');
                    var open_task = $(data[6]).attr("data-t");
                    if (open_task == 1) {
                        $('td', row).eq(6).addClass('bg-yellow text-center');
                    } else if (open_task == 0) {
                        $('td', row).eq(6).addClass('bg-green text-center');
                    } else {
                        $('td', row).eq(6).addClass('bg-red text-center');
                    }

                    $('td', row).eq(7).addClass('text-center');

                    var open_issue = $(data[8]).attr("data-i");

                    if (open_issue == 1) {
                        $('td', row).eq(8).addClass('bg-yellow text-center');
                    } else if (open_issue == 0) {
                        $('td', row).eq(8).addClass('bg-green text-center');
                    } else {
                        $('td', row).eq(8).addClass('bg-red text-center');
                    }

                    $('td', row).eq(9).addClass('text-center');

                    var spent_budget = $(data[10]).attr("data-b");
                    if (spent_budget == 1) {
                        $('td', row).eq(10).addClass('bg-yellow text-center');
                    } else if (spent_budget == 0) {
                        $('td', row).eq(10).addClass('bg-green text-center');
                    } else {
                        $('td', row).eq(10).addClass('bg-red text-center');
                    }

                    var pending_invoice = $(data[11]).attr("data-p");
                    if (pending_invoice == 1) {
                        $('td', row).eq(11).addClass('bg-yellow text-center');
                    } else if (pending_invoice == 0) {
                        $('td', row).eq(11).addClass('bg-green text-center');
                    } else {
                        $('td', row).eq(11).addClass('bg-red text-center');
                    }

                    $('td', row).eq(12).addClass('text-center');
                    $('td', row).eq(13).addClass('text-center');
                },
            });
            self.init_project_status_chart();
            self.init_gantt_view();
            self.init_project_heatmap_table();
            self.init_project_budget_risk();
            self.init_project_time_risk();
            self.init_vender_utilization();

            document.body.classList.remove('is-closed');
            document.body.classList.remove('is-expand');

            self.datepicker_widget_start = new datepicker.DateWidget(this, {
                useCurrent: true,
                defaultDate: self.start_date,
            });
            self.datepicker_widget_start.appendTo(self.$('#start_date'));

            self.datepicker_widget_end = new datepicker.DateWidget(this, {
                useCurrent: true,
                defaultDate: self.end_date,
            });
            self.datepicker_widget_end.appendTo(self.$('#end_date'));

            // self.datepicker_widget_start.$input.on('dp.change', function (ev) {
            //     if (ev.date) {
            //         if (self.datepicker_widget_start._formatClient(self.start_date) !== self.datepicker_widget_start._formatClient(ev.date)) {
            //             self.start_date = ev.date;
            //             if(self.server_date(self.end_date) < self.server_date(self.start_date)){
            //                 alert("end date must be  greater than project start date.")
            //                 self.end_date = ev.date;
            //             }
            //             self.$el.html('');
            //             self.fetch_data();
            //             self.$(".dashboard_filter_btn").removeClass('filter_active');
            //         }
            //     } else {
            //         self.datepicker_widget_start.setValue(self.start_date);
            //     }
            // });

            // self.datepicker_widget_end.$input.on('dp.change', function (ev) {
            //     if (ev.date) {
            //         if (self.datepicker_widget_end._formatClient(self.end_date) !== self.datepicker_widget_end._formatClient(ev.date)) {
            //             self.end_date = ev.date;
            //             self.$el.html('');
            //             self.fetch_data();
            //             self.$(".dashboard_filter_btn").removeClass('filter_active');
            //         }
            //     } else {
            //         self.datepicker_widget_end.setValue(self.end_date);
            //     }
            // });
        },

        show_sidebar: function () {
            document.body.classList.remove('is-closed');
            document.body.classList.remove('is-expand');
        },

        hide_sidebar: function () {
            document.body.classList.remove('is-closed');
            document.body.classList.remove('is-expand');
        },

        _toggle_sidebar: function (ev) {
            ev.currentTarget.classList.toggle('is-closed');
            document.body.classList.remove('is-closed');
            document.body.classList.remove('is-expand');
            self.$(".gantt-wrapper")[0].classList.toggle('gantt-full-width');
        },

    //     /**
    //      * @override
    //      */
        destroy: function () {
            this.show_sidebar();
            this._super.apply(this, arguments);
        },

        init_project_status_chart: function () {
            var self = this;
            Chart.defaults.global.defaultFontColor = '#292b2c';
            const keys = Object.keys(self.project_phase_stage);
            const values = Object.values(self.project_phase_stage);
            self.project_status_color = {}
            const bc_color = []
            _.each(keys, function (key){
                let col = self.getRandomColor()
                self.project_status_color[key] = col
                bc_color.push(col)
            });
            self.proj_status_chart = new Chart(self.proj_status_chart, {
                type: 'pie',
                data: {
                    labels: keys,
                    datasets: [{
                        label: "Project Stage",
                        hoverBorderColor: bc_color,
                        backgroundColor: bc_color,
                        data: values
                    }]
                },
                options: {
                    title: {
                        display: false,
                        text: 'Overall Project Status',
                    },
                    responsive: true,
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            fontSize: 10,
                            padding: 15,
                            usePointStyle: true,
                        }
                    },
                    animation: {
                        animateScale: true,
                        easing: 'linear',
                    },
                }
            });
        },

        init_project_heatmap_table: function () {
            var self = this;
            _.each(self.projects, function (project) {
                var spent_budget_amount = project.spent_budget;
                var running_cost = '<a class="running_cost" data-project="';
                running_cost += project.id;
                running_cost += '">';
                running_cost += parseFloat(project.running_cost).toFixed(2);
                running_cost += '</a>';

                var actual_budget = (project.revised_budget > 0) ? project.revised_budget : project.actual_budget;

                var name_cell = '<a class="project_name" data-project="';
                name_cell += project.id;
                name_cell += '">';
                name_cell += project.name;
                name_cell += '</a>';

                var class_list = 'circle-label';
                var style = '';
                var color_value = 0;
                _.each(self.project_status_color, function (color, key) {
                    if (project.project_phase_stage == key){
                        style += 'background-color:' + color;
                    }
                })

                var color_data = '<span class="d-none">';
                // color_data += color_value;
                color_data += '</span><label class="';
                color_data += class_list;
                color_data += '" ';
                color_data += 'style="';
                color_data += style;
                color_data += '" />';

                var active = (project.resource_count !== undefined) ? project.resource_count : 0;

                var html = '<p style="display: none;">' + active + '</p>';
                for (var i = 0; i < 10; i++) {
                    if (i < active) {
                        html += '<i class="resource_icon fa fa-male active"></i>';
                    } else {
                        html += '<i class="resource_icon fa fa-male block"></i>';
                    }
                }
                var resource_cell = html;

                var project_start = ((project.date_start !== false) ? self.format_date(project.date_start) : 'N/A');

                var planned_date = ((project.expected_end_date !== false) ? self.format_date(project.expected_end_date) : 'N/A');

                var project_end = ((project.date !== false) ? self.format_date(project.date) : 'N/A');

                var open_tasks = project.open_tasks_count;
                var close_tasks = project.close_tasks_count;
                var tasks_count = project.task_count;
                self._rpc({
                    model: 'management.dashboard',
                    method: 'get_color_code',
                    args: [project],
                    context: {
                        'start_date': self.server_date(self.start_date),
                        'end_date': self.server_date(self.end_date)
                    }
                }).then(function (data){
                    var open_task = parseInt(data['open_task'])
                    var open_issue = parseInt(data['open_issue'])
                    var spent_budget = parseInt(data['spent_budget'])
                    var pending_invoice = parseInt(data['pending_invoice'])

                    var open_issues = project.open_issues_count;
                    var close_issues = project.close_issues_count;
                    var progress = project.progress;
                    self.heat_map.row.add([
                        name_cell,
                        color_data,
                        resource_cell,
                        project_start,
                        planned_date,
                        project_end,
                        '<span class="d-none" data-t="'+open_task+'">' + parseInt(open_tasks) + '</span><a class="goto_link show_open_task" data-project="' + project.id + '">' + parseInt(open_tasks) + '</a>',
                        '<span class="d-none">' + tasks_count + '</span><a class="goto_link show_all_task" style="color:unset" data-project="' + project.id + '">' + tasks_count + '</a>',
                        '<span class="d-none" data-i="'+open_issue+'">' + parseInt(open_issues) + '</span><a class="goto_link show_open_issue" data-project="' + project.id + '">' + parseInt(open_issues) + '</a>',
                        '<span class="d-none">' + (close_issues + open_issues) + '</span><a class="goto_link show_all_issue" style="color:unset"  data-project="' + project.id + '" >' + (close_issues + open_issues) + '</a>',
                        '<span class="d-none" data-b="'+spent_budget+'"></span>'+ parseFloat(spent_budget_amount).toFixed(2),
                        '<span class="d-none" data-p="'+pending_invoice+'"></span>'+ running_cost,
                        parseFloat(actual_budget).toFixed(2),
                        progress
                    ]).draw(false);
                    // _.each(data, function (chart_date) {
                    //     var color = (isNaN(chart_date.color)) ? chart_date.color : self.getRandomColor();
                    //     self.addPieChartData(self.task_chart, $.trim(chart_date.name), chart_date.count, color);
                    // });
                });
            });

        },

        init_project_budget_risk: function(){
            var self = this;
            Chart.defaults.global.defaultFontColor = '#292b2c';

            var red = 0;
            var red_project = [''];
            var orange = 0;
            var orange_project = ['']
            var green = 0;
            var green_project = ['']
            self.b_red_prj_ids = []
            self.b_orange_prj_ids = []
            self.b_green_prj_ids = []
            var labels = false;

            _.each(self.projects, function (project) {
                var diff = ((project.budget_of_completion - project.actual_budget)/project.actual_budget)*100
                labels = ["Forecast > "+project.forecast_up_range+" %", "Forecast > "+project.forecast_low_range+" % & <= "+project.forecast_up_range+" %", "Forecast <= "+project.forecast_low_range+" %"]
                var up_range = parseFloat(project.forecast_up_range) - 100
                var low_range = parseFloat(project.forecast_low_range) - 100
                if (project.revised_budget > 0){
                    red += 1;
                    red_project.push(project.name)
                    self.b_red_prj_ids.push(project.id)
                }
                else{
                    if (diff > up_range){
                        red += 1;
                        red_project.push(project.name)
                        self.b_red_prj_ids.push(project.id)
                    }
                    if (diff > low_range && diff <= up_range){
                        orange +=1;
                        orange_project.push(project.name);
                        self.b_orange_prj_ids.push(project.id)
                    }
                    if (diff <= low_range){
                        green +=1
                        green_project.push(project.name)
                        self.b_green_prj_ids.push(project.id)
                    }
                }
            })

            self.budget_risk_project_chart = new Chart(self.budget_risk_project_chart, {
                type: 'pie',
                data: {
                    // labels: [red_project, orange_project, green_project],
                    labels: labels,
                    datasets: [{
                        label: "Project Budget Phase",
                        hoverBorderColor: [
                            self.color_red,
                            self.color_orange,
                            self.color_green,
                        ],
                        backgroundColor: [
                            self.color_red,
                            self.color_orange,
                            self.color_green,
                        ],
                        data: [red, orange, green]
                    }]
                },
                options: {

                    title: {
                        display: false,
                        text: 'Projects at Budget Risk',
                    },
                    responsive: true,
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            fontSize: 10,
                            padding: 15,
                            usePointStyle: true,
                        }
                    },
                    animation: {
                        animateScale: true,
                        easing: 'linear',
                    },
                }
            });
        },

        init_project_time_risk: function(){
            var self = this;
            Chart.defaults.global.defaultFontColor = '#292b2c';
            var red = 0;
            var red_project = [''];
            var orange = 0;
            var orange_project = ['']
            var green = 0;
            var green_project = ['']
            self.red_prj_ids = []
            self.orange_prj_ids = []
            self.green_prj_ids = [];
            var labels = false;

            _.each(self.projects, function (project) {
                var start_date = new Date(project.date_start)
                var expected_end_date = new Date(project.expected_end_date)
                var projected_end_date = new Date(project.projected_end_date)
                var millisBetween = expected_end_date.getTime() - start_date.getTime();
                var plan_days = millisBetween / (1000 * 3600 * 24);
                var millisBetween_2 = projected_end_date.getTime() - start_date.getTime();
                var projected_days = millisBetween_2 / (1000 * 3600 * 24);
                var diff = ((projected_days - plan_days)/plan_days)*100
                labels = ["Forecast > "+project.forecast_up_range+" %", "Forecast > "+project.forecast_low_range+" % & <= "+project.forecast_up_range+" %", "Forecast <= "+project.forecast_low_range+" %"]
                var up_range = parseFloat(project.forecast_up_range) - 100
                var low_range = parseFloat(project.forecast_low_range) - 100
                if (diff > up_range){
                    red += 1;
                    red_project.push(project.name)
                    self.red_prj_ids.push(project.id)
                }
                if (diff > low_range && diff <=up_range){
                    orange +=1;
                    orange_project.push(project.name);
                    self.orange_prj_ids.push(project.id)
                }
                if (diff <= low_range){
                    green +=1
                    green_project.push(project.name)
                    self.green_prj_ids.push(project.id)
                }
            })

            self.projects_time_risk_chart = new Chart(self.projects_time_risk_chart, {
                type: 'pie',
                data: {
                    // labels: [red_project, orange_project, green_project],
                    labels: labels,
                    datasets: [{
                        label: "Projects Time Risk Phase",
                        hoverBorderColor: [
                            self.color_red,
                            self.color_orange,
                            self.color_green,
                        ],
                        backgroundColor: [
                            self.color_red,
                            self.color_orange,
                            self.color_green,
                        ],
                        data: [red, orange, green]
                    }]
                },
                options: {
                    title: {
                        display: false,
                        text: 'Projects at Time Risk',
                    },
                    responsive: true,
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            fontSize: 10,
                            padding: 15,
                            usePointStyle: true,
                        }
                    },
                    animation: {
                        animateScale: true,
                        easing: 'linear',
                    },
                }
            });
        },

        getRandomColor: function(){
            var letters = '0123456789ABCDEF';
            var color = '#';
            for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        },

        init_vender_utilization: function(){
            var self = this;

            return this._rpc({
                model: 'timesheet.invoice',
                method: 'search_read',
                fields: ['total_amount', 'partner_id'],
                domain: [['project_id', 'in', self.project_ids],
                         ['state', 'in', ['pre-approved','confirm','approved','completed']]],
            }).then(function (details) {
                var partner_dict = {}
                if (details !== undefined) {
                    _.each(details, function (invoice) {
                        if (invoice.partner_id[0] in partner_dict){
                            var amount = parseFloat(partner_dict[invoice.partner_id[0]][1]) + parseFloat(invoice.total_amount)
                            partner_dict[invoice.partner_id[0]] = [invoice.partner_id[1], amount]
                        }
                        else{
                            partner_dict[invoice.partner_id[0]] = [invoice.partner_id[1], invoice.total_amount]
                        }
                    })
                    self.invoices = partner_dict;

                    Chart.defaults.global.defaultFontColor = '#292b2c';

                    var lab = [];
                    var data = [];
                    var colors = [];
                    var data_dict = {};

                    _.each(self.invoices, function (inv) {
                        data_dict[inv[1].toFixed(2)] = inv[0]
                        data.push(inv[1].toFixed(2));
                    })
                    var s_data = (data).sort(function(a, b){
                      return b - a;
                    });

                    _.each(s_data, function (inv){
                        lab.push(data_dict[inv])
                        colors.push(self.getRandomColor());
                    });
                    self.lab_len = lab.length
                    if (self.lab_len >= 25){
                        $(self.vendor_utilization_chart).attr("width", "385");
                        $(self.vendor_utilization_chart).css("max-width", "375px");
                    }
                    else if (self.lab_len < 25 && self.lab_len >= 19){
                        $(self.vendor_utilization_chart).attr("width", "348");
                        $(self.vendor_utilization_chart).css("max-width", "338px");
                    }
                    else if (self.lab_len < 19 && self.lab_len >= 13){
                        $(self.vendor_utilization_chart).attr("width", "313");
                        $(self.vendor_utilization_chart).css("max-width", "303px");
                    }
                    else if (self.lab_len < 13 && self.lab_len >= 7){
                        $(self.vendor_utilization_chart).attr("width", "275");
                        $(self.vendor_utilization_chart).css("max-width", "265px");
                    }
                    else if (self.lab_len < 7){
                        $(self.vendor_utilization_chart).attr("width", "240");
                        $(self.vendor_utilization_chart).css("max-width", "230px");
                    }
                    self.vendor_utilization_chart = new Chart(self.vendor_utilization_chart, {
                        type: 'pie',
                        data: {
                            labels: lab,
                            datasets: [{
                                label: "Vendor Utilization Phase",
                                hoverBorderColor: colors,
                                backgroundColor: colors,
                                data: s_data,
                            }]
                        },
                        options: {
                            title: {
                                display: false,
                                text: 'Vendor Utilization',
                            },
                            responsive: false,
                            legend: {
                                display: true,
                                position: 'right',
                                labels: {
                                    fontSize: 11,
                                    padding: 15,
                                    usePointStyle: true,
                                    generateLabels: function(chart) {
                                        var data = chart.data;
                                        if (data.labels.length && data.datasets.length) {
                                            return data.labels.map(function(label, i) {
                                                if (i < 6){
                                                    var meta = chart.getDatasetMeta(0);
                                                    var ds = data.datasets[0];
                                                    var arc = meta.data[i];
                                                    var custom = arc && arc.custom || {};
                                                    var getValueAtIndexOrDefault = Chart.helpers.getValueAtIndexOrDefault;
                                                    var arcOpts = chart.options.elements.arc;
                                                    var fill = custom.backgroundColor ? custom.backgroundColor : getValueAtIndexOrDefault(ds.backgroundColor, i, arcOpts.backgroundColor);
                                                    var stroke = custom.borderColor ? custom.borderColor : getValueAtIndexOrDefault(ds.borderColor, i, arcOpts.borderColor);
                                                    var bw = custom.borderWidth ? custom.borderWidth : getValueAtIndexOrDefault(ds.borderWidth, i, arcOpts.borderWidth);

                                                    // We get the value of the current label
                                                    var value = chart.config.data.datasets[arc._datasetIndex].data[arc._index];
                                                    return {
                                                        // Instead of `text: label,`
                                                        // We add the value to the string
                                                        text: label.substr(0, 8),
                                                        fillStyle: fill,
                                                        strokeStyle: stroke,
                                                        lineWidth: bw,
                                                        hidden: isNaN(ds.data[i]) || meta.data[i].hidden,
                                                        index: i
                                                    };
                                                }
                                                else{
                                                    return{
                                                        text: '',
                                                        hidden: true,
                                                        lineWidth: 0,
                                                        fillStyle: 'transparent',
                                                        strokeStyle: 'transparent',
                                                        pointStyle: false,
                                                        index: i,
                                                    }
                                                }
                                            });
                                        } else {
                                            return [];
                                        }
                                    },
                                },
                            },
                            animation: {
                                animateScale: true,
                                easing: 'linear',
                            },
                        }
                    });
                }
            });
        },

        init_task_chart: function () {
            var self = this;
            Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
            Chart.defaults.global.defaultFontColor = '#292b2c';
            self.task_chart = new Chart(self.task_chart, {
                type: 'pie',
                data: {
                    labels: [],
                    datasets: [{
                        label: "Task Status",
                        backgroundColor: [],
                        hoverBorderColor: [],
                        data: [],
                        borderWidth: 1,
                        hoverBorderWidth: 3,
                    }]
                },
                options: {
                    title: {
                        display: false,
                        text: 'Overall Task Status',
                    },
                    responsive: true,
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            fontSize: 10,
                            usePointStyle: true,
                        }
                    },
                    animation: {
                        animateScale: true,
                        easing: 'linear',
                    },
                }
            });
            self._rpc({
                model: 'management.dashboard',
                method: 'get_task_chart_data',
                args: []
            }).done(function (data) {
                _.each(data, function (chart_date) {
                    var color = (isNaN(chart_date.color)) ? chart_date.color : self.getRandomColor();
                    self.addPieChartData(self.task_chart, $.trim(chart_date.name), chart_date.count, color);
                });
            });
        },

        addPieChartData: function (chart, label, data, color) {
            var self = this;
            chart.data.labels.push(label);
            _.each(chart.data.datasets, function (dataset) {
                dataset.data.push(data);
                dataset.backgroundColor.push(color);
                dataset.hoverBorderColor.push(color);
            });
            chart.update();
        },

        init_gantt_view: function () {
            var self = this;
            var tasks = [];
            if (self.projects.length > 0) {
                _.each(self.projects, function (project_data) {
                    var project_start = ((project_data.date_start !== false) ? new Date(project_data.date_start) : new Date());
                    var day = 60 * 60 * 24 * 1000;
                    var project_end;
                    if (project_data.date !== false) {
                        project_end = new Date(self.format_date(project_data.date));
                    } else if (project_data.expected_end_date !== false) {
                        project_end = new Date(self.format_date(project_data.expected_end_date));
                    } else {
                        project_end = new Date(project_start.getTime() + (day * 7));
                    }
                    var name = project_data.name;
                    var id = project_data.id;
                    var progress = project_data.percentage_completed;
                    var gant_data = {
                        start: project_start,
                        end: project_end,
                        date_start: project_data.date_start,
                        expected_end_date: project_data.expected_end_date,
                        actual_end_date: project_data.date,
                        name: name,
                        id: id,
                        title: name,
                        progress: progress.toFixed(2),
                        row_height: 35,
                        custom_class: 'l-r-disabled',
                        dragging: false,
                    };
                    tasks.push(gant_data);
                });
            } else {
                var start = new Date().toISOString().substr(0, 10);
                var end = new Date().toISOString().substr(0, 10);
                var ganttdata = {
                    start: start,
                    end: end,
                    name: "",
                    id: 'Task 0',
                    invalid: true,
                    custom_class: "no-data"
                };
                tasks.push(ganttdata);
            }
            self.gantt_chart = new Gantt(self.$(".gantt-target")[0], tasks, {
                view_mode: 'Week',
                language: 'en',
                bar_height: 20,
                bar_corner_radius: 3,
                arrow_curve: 5,
                padding: 16,
                start_date: new Date(new Date().getFullYear(), 0, 1),
                end_date: new Date(new Date().getFullYear(), 11, 31),
                date_padding: false,
                format_date: function (date) {
                    return self.format_date(date);
                },
                custom_popup_html: function (task) {
                    // the task object will contain the updated
                    // dates and progress value
                    var task_end_date = task._end;
                    var html = '<div class="details-container">';
                    html += '<h5 class="detail-header">' + task.name + '</h5>';
                    html += '<p>' + task.progress + '% completed!</p>';
                    html += '<hr/>';
                    html += '<p class="m-0"><strong class="detail-main">Start Date : </strong> ' + self.format_date(task.start) + '</p>';
                    html += '<p class="m-0"><strong class="detail-main">Planned Finish Date : </strong> ' + self.format_date(task.expected_end_date) + '</p>';
                    html += '</div>';
                    return html;
                }
            });
            $(".bar-wrapper[data-id='Task 0']").remove(); // remove bar made by sample data
        },

        _filter_dashboard: function (ev) {
            var self = this;
            var filter = ev.currentTarget.dataset.filter;
            ev.currentTarget.classList.add('filter_active');
            $(ev.currentTarget).siblings().removeClass('filter_active');
            switch (filter) {
                case 'week':
                    self.filter = 'week';
                    var curr = new Date();
                    var first = curr.getDate() - curr.getDay();
                    var last = first + 6;
                    var starting_date = new Date(curr.setDate(first))
                    starting_date.setHours(23)

                    self.start_date = field_utils.parse.date(starting_date, {
                        isUTC: true
                    });

                    var day = 6 * 60 * 60 * 24 * 1000;
                    var end_date = new Date(starting_date.getTime() + day);
                    self.end_date = field_utils.parse.date(end_date, {
                        isUTC: true
                    });

                    self.datepicker_widget_start.setValue(self.start_date);
                    self.datepicker_widget_end.setValue(self.end_date);
                    break;
                case 'year':
                    self.filter = 'year';

                    var start_date = new Date(new Date().getFullYear(), 0, 1)
                    start_date.setHours(23)

                    var end_date = new Date(new Date().getFullYear(), 11, 31)
                    end_date.setHours(23)


                    self.start_date = field_utils.parse.date(start_date, {
                        isUTC: true
                    });
                    self.end_date = field_utils.parse.date(end_date, {
                        isUTC: true
                    });
                    self.datepicker_widget_start.setValue(self.start_date);
                    self.datepicker_widget_end.setValue(self.end_date);
                    break;
                case 'today':
                    var start_date = new Date()
                    start_date.setHours(23)
                    var end_date = new Date()
                    end_date.setHours(23)

                    self.start_date = field_utils.parse.date(start_date, {
                        isUTC: true
                    });
                    self.end_date = field_utils.parse.date(end_date, {
                        isUTC: true
                    });

                    self.filter = 'today';
                    self.datepicker_widget_start.setValue(self.start_date);
                    self.datepicker_widget_end.setValue(self.end_date);
                    break;
                default:
                    self.filter = 'month';
                    var start_date = new Date(new Date().setMonth(new Date().getMonth(),1))
                    start_date.setHours(23)

                    var end_date = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0)
                    end_date.setHours(23)

                    self.start_date = field_utils.parse.date(new Date(start_date), {
                        isUTC: true
                    });
                    self.end_date = field_utils.parse.date(end_date,{
                        isUTC: false
                    });

                    self.datepicker_widget_start.setValue(self.start_date);
                    self.datepicker_widget_end.setValue(self.end_date);
                    break;

            }
            self.fetch_data();
            self.render_dashboard();
        },

        _goto_project: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: 'Project',
                res_model: 'project.project',
                res_id: parseInt(ev.currentTarget.dataset.project),
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
            });
        },

        _goto_budget_projects_list: function (evt) {
            evt.preventDefault();
            var self = this;
            var activePoints = self.budget_risk_project_chart.getElementsAtEvent(evt);
            if (activePoints[0]) {
                self.show_sidebar();
                var chartData = activePoints[0]['_chart'].config.data;
                var idx = activePoints[0]['_index'];

                var label = chartData.labels[idx];
                var value = chartData.datasets[0].data[idx];

                var project_ids = []
                if (label === 'Forecast <= 110%'){
                    project_ids = self.b_green_prj_ids
                }else if (label === 'Forecast > 110% & <= 120%'){
                    project_ids = self.b_orange_prj_ids
                }else if (label === 'Forecast > 120%'){
                    project_ids = self.b_red_prj_ids
                }

                self._rpc({
                    model: 'management.dashboard',
                    method: 'get_treeview_id',
                    args: ['project.view_project_kanban'],
                }).then(function (viewId) {
                    self.do_action({
                        name: "Projects",
                        type:'ir.actions.act_window',
                        res_model: 'project.project',
                        views: [[viewId[0] || false, 'list'],
                            [false, 'form'],
                        ],
                        view_type: "list",
                        view_mode: "list",
                        domain: [
                            ['id', 'in', project_ids]
                        ],
                    });
                });
            }
        },

        _goto_projects_list: function (evt) {
            evt.preventDefault();
            var self = this;
            var activePoints = self.projects_time_risk_chart.getElementsAtEvent(evt);
            if (activePoints[0]) {
                self.show_sidebar();
                var chartData = activePoints[0]['_chart'].config.data;
                var idx = activePoints[0]['_index'];

                var label = chartData.labels[idx];
                var value = chartData.datasets[0].data[idx];

                var project_ids = []
                if (label === 'Forecast <= 110%'){
                    project_ids = self.green_prj_ids
                }else if (label === 'Forecast > 110% & <= 120%'){
                    project_ids = self.orange_prj_ids
                }else if (label === 'Forecast > 120%'){
                    project_ids = self.red_prj_ids
                }
                self._rpc({
                    model: 'management.dashboard',
                    method: 'get_treeview_id',
                    args: ['project.view_project_kanban'],
                }).then(function (viewId) {
                    self.do_action({
                        name: "Projects",
                        type:'ir.actions.act_window',
                        res_model: 'project.project',
                        views: [[viewId[0] || false, 'list'],
                            [false, 'form'],
                        ],
                        view_type: "list",
                        view_mode: "list",
                        domain: [
                            ['id', 'in', project_ids]
                        ],
                    });
                });
            }
        },

        _goto_open_tasks: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: "Open Tasks",
                res_model: 'project.task',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                    [false, 'kanban'],
                ],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
                domain: [
                    ['date_end', '=', false],
                    ['stage_id.name', 'not in', ["Done", "Completed", "Approval", "Canceled", "Closure", "Release", "Implementation"]],
                    ['project_id', '=', parseInt(ev.currentTarget.dataset.project)]
                ],
                context: {
                    'default_project_id': parseInt(ev.currentTarget.dataset.project)
                }
            });
        },

        _goto_all_tasks: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: "All Tasks",
                res_model: 'project.task',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                    [false, 'kanban'],
                ],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
                domain: [
                    ['project_id', '=', parseInt(ev.currentTarget.dataset.project)]
                ],
                context: {
                    'default_project_id': parseInt(ev.currentTarget.dataset.project)
                }
            });
        },

        _goto_open_issues: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: "Open Issues",
                res_model: 'helpdesk.ticket',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                ],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
                domain: [
                    ['closed_date', '=', false],
                    ['project_id', '=', parseInt(ev.currentTarget.dataset.project)]
                ],
                context: {
                    'view_project_issues': '1',
                    'default_project_id': parseInt(ev.currentTarget.dataset.project),
                }
            });
        },

        _goto_all_issues: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: "All Issues",
                res_model: 'helpdesk.ticket',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                ],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
                domain: [
                    ['project_id', '=', parseInt(ev.currentTarget.dataset.project)]
                ],
                context: {
                    'view_project_issues': '1',
                    'default_project_id': parseInt(ev.currentTarget.dataset.project)
                }
            });
        },

        _open_timesheet_invoice: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: "Timesheet Invoices",
                res_model: 'timesheet.invoice',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                ],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
                domain: [
                    ['project_id', '=', parseInt(ev.currentTarget.dataset.project)],
                    ['state', 'in', ['draft', 'confirm', 'pre-approved']]
                ],
                context: {
                    'default_project_id': parseInt(ev.currentTarget.dataset.project)
                }
            });
        },

        _open_at_risk_projects: function (ev) {
            ev.preventDefault();
            var self = this;
            self.show_sidebar();
            this.do_action({
                name: "At Risk Projects",
                res_model: 'project.project',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                ],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
                context: {
                    'search_default_at_risk_project': true,
                }
            });
        }
    });

    core.action_registry.add('management_dashboard.PMDashboardView', PMDashboardView);

    return PMDashboardView;

});
