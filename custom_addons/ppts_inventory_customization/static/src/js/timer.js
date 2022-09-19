odoo.define('project_task_timer.timer', function (require) {
"use strict";
var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var time = require('web.time');
var FieldManagerMixin = require('web.FieldManagerMixin');

var _t = core._t;

//  $(document).on('click','#timer', function(){
//  if ($(this).hasClass('btn-secondary'))
//  { $(this).removeClass('btn-secondary');
//    $(this).addClass('btn-primary');
//  }
//    });

var TimeCounterNew  = AbstractField.extend({

        willStart: function () {
        var self = this;
        var def = this._rpc({
            model: 'action.timing.line',
            method: 'search_read',
            domain:  [['container_id', '=', this.res_id], ['user_id', '=', self.record.context['uid']]],
        }).then(function (result) {
            if (self.mode === 'readonly') {
                var currentDate = new Date();
                self.duration = 0;
                _.each(result, function (data) {
                    self.duration += data.date_end ?
                        self._getDateDifference(data.date_start, data.date_end):
                        self._getDateDifference(time.auto_str_to_date(data.date_start), currentDate);
                });
            }
        });
        return $.when(this._super.apply(this, arguments), def);
    },
    destroy: function () {
        this._super.apply(this, arguments);
        clearTimeout(this.timer);
    },
    isSet: function () {
        return true;
    },
    _getDateDifference: function (dateStart, dateEnd) {
        return moment(dateEnd).diff(moment(dateStart));
    },

    _render: function () {
        this._startTimeCounter();
    },
    _startTimeCounter: function () {
        var self = this;
        clearTimeout(this.timer);
        if (this.record.data.is_user_working) {
            this.timer = setTimeout(function () {
                self.duration += 1000;
                self._startTimeCounter();
            }, 1000);
        } else {
            clearTimeout(this.timer);
        }
        this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
    },
});

var TimeCounter  = AbstractField.extend({

        willStart: function () {
        var self = this;
        var def = this._rpc({
            model: 'picking.timing.line',
            method: 'search_read',
            domain:  [['picking_id', '=', this.res_id], ['user_id', '=', self.record.context['uid']]],
        }).then(function (result) {
            if (self.mode === 'readonly') {
                var currentDate = new Date();
                self.duration = 0;
                _.each(result, function (data) {
                    self.duration += data.date_end ?
                        self._getDateDifference(data.date_start, data.date_end):
                        self._getDateDifference(time.auto_str_to_date(data.date_start), currentDate);
                });
            }
        });
        return $.when(this._super.apply(this, arguments), def);
    },
    destroy: function () {
        this._super.apply(this, arguments);
        clearTimeout(this.timer);
    },
    isSet: function () {
        return true;
    },
    _getDateDifference: function (dateStart, dateEnd) {
        return moment(dateEnd).diff(moment(dateStart));
    },

    _render: function () {
        this._startTimeCounter();
    },
    _startTimeCounter: function () {
        var self = this;
        clearTimeout(this.timer);
        if (this.record.data.is_user_working) {
            this.timer = setTimeout(function () {
                self.duration += 1000;
                self._startTimeCounter();
            }, 1000);
        } else {
            clearTimeout(this.timer);
        }
        this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
    },
});

var TimeCounterReception  = AbstractField.extend({
        willStart: function () {
        var self = this;
        var def = this._rpc({
            model: 'reception.timing.line',
            method: 'search_read',
            domain:  [['picking_id', '=', this.res_id], ['user_id', '=', self.record.context['uid']]],
        }).then(function (result) {
            if (self.mode === 'readonly') {
                var currentDate = new Date();
                self.reception_duration = 0; 
                _.each(result, function (data) {
                    self.reception_duration += data.date_end ?
                        self._getDateDifference(data.date_start, data.date_end):
                        self._getDateDifference(time.auto_str_to_date(data.date_start), currentDate);
                });
            }
        });
        return $.when(this._super.apply(this, arguments), def);
    },
    destroy: function () {
        this._super.apply(this, arguments);
        clearTimeout(this.timer);
    },
    isSet: function () {
        return true;
    },
    _getDateDifference: function (dateStart, dateEnd) {
        return moment(dateEnd).diff(moment(dateStart));
    },

    _render: function () {
        this._startTimeCounter();
    },
    _startTimeCounter: function () {
        var self = this;
        clearTimeout(this.timer);
        if (this.record.data.is_user_working) {
            this.timer = setTimeout(function () {
                self.reception_duration += 1000;
                self._startTimeCounter();
            }, 1000);
        } else {
            clearTimeout(this.timer);
        }
        this.$el.html($('<span>' + moment.utc(this.reception_duration).format("HH:mm:ss") + '</span>'));
    },
});


field_registry.add('timesheet_uoms1', TimeCounter);
field_registry.add('timesheet_uoms2', TimeCounterReception);
field_registry.add('timesheet_uoms', TimeCounterNew);
});


