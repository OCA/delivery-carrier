/** @odoo-module **/

import publicWidget from "web.public.widget";
import "website_sale_delivery.checkout";
import {qweb as QWeb} from "web.core";
// temporary for OnNoResultReturned bug
import {registry} from "@web/core/registry";
import {UncaughtCorsError} from "@web/core/errors/error_service";

const WebsiteSaleDeliveryWidget = publicWidget.registry.websiteSaleDelivery;

const errorHandlerRegistry = registry.category("error_handlers");
const rpc = require('web.rpc');

function corsIgnoredErrorHandler(env, error) {
    if (error instanceof UncaughtCorsError) {
        return true;
    }
}

WebsiteSaleDeliveryWidget.include({
    xmlDependencies: (WebsiteSaleDeliveryWidget.prototype.xmlDependencies || []).concat(['/website_sale_delivery_withdrawal/static/src/xml/website_sale_delivery_withdrawal.xml',]),
    events: _.extend({
        "click #btn_confirm_withdrawal_point": "_onClickBtnConfirmWithdrawalPoint",
    }, WebsiteSaleDeliveryWidget.prototype.events),

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Loads Withdrawal Points the first time, else show it.
     *
     * @override
     */
    _handleCarrierUpdateResult: function (result) {
        this._super(...arguments);
        if (result.withdrawal_point) {
            if (!$('#modal_withdrawal').length) {
                this._loadWithdrawalPointModal(result);
            } else {
                this.$modal_withdrawal.find('#btn_confirm_withdrawal_point').toggleClass('disabled', !result.withdrawal_point.current);
                this.$modal_withdrawal.modal('show');
            }
        }
    },
    /**
     * This method render the modal, and inject it in dom with the withdrawal points.
     *
     * @private
     *
     * @param {Object} result: dict returned by call of _update_website_sale_delivery_return (python)
     */
    _loadWithdrawalPointModal: async function (result) {

        // add modal to body and bind 'save' button
        $(QWeb.render('website_sale_delivery_withdrawal', {})).appendTo('body');
        const modal = this.$modal_withdrawal = $('#modal_withdrawal');
        console.log(modal);
        console.log(this);
        document.querySelector('#btn_confirm_withdrawal_point').addEventListener("click", () => {
            this._onClickBtnConfirmWithdrawalPoint()
        })
        this.$calendar = 0;
        this.$number_delivery_period = 0;
        this.$select_delivery_period = "day"
        const addressCard = document.querySelector('.addressCard')
        this.$modal_withdrawal.find('#btn_confirm_relay').on('click', this._onClickBtnConfirmWithdrawalPoint.bind(this));
        await this._rpc({
            model: 'delivery.carrier', method: 'search_read', kwargs: {
                fields: ['number_delivery_period', 'select_delivery_period'], domain: [['id', '=', result.carrier_id]],
            }
        }).then(async (carrier_data) => {
            this.$number_delivery_period = carrier_data[0].number_delivery_period
            this.$select_delivery_period = carrier_data[0].select_delivery_period
        })
        for (const item of result.withdrawal_point.allowed_points) {
            await this._rpc({
                model: 'delivery.withdrawal.point', method: 'search_read', kwargs: {
                    fields: ['partner_address_street', 'partner_address_city', 'partner_address_zip', 'partner_country_id', 'partner_image_url', 'resource_calendar_id', 'stock_picking_type_id'],
                    domain: [['id', '=', item]],
                }
            }).then(async (result) => {
                // Clone the HTML element, and update the date for each withdrawal point
                let clone = addressCard.cloneNode(true);
                clone.classList.remove('d-none')
                clone.id = result[0].id
                clone.addEventListener('click', () => {
                    if (modal.find('.WP_RList')[0].querySelector('.active')) {
                        modal.find('.WP_RList')[0].querySelector('.active').classList.remove('active');
                    }
                    clone.classList.add('active');
                    console.log(result[0])
                    this.$calendar = result[0].resource_calendar_id[0]
                    this.$city = result[0].partner_address_city
                    this.$street = result[0].partner_address_street
                    this.$zip = result[0].partner_address_zip
                    this.$country = result[0].partner_country_id
                    this.$picking_type_id = result[0].stock_picking_type_id[0]
                    this._onClickWithdrawalPoint()
                });
                clone.querySelector('.WPTitle').innerHTML = (result[0].partner_address_city).toUpperCase();
                clone.querySelector('.WPStreet').innerHTML = clone.querySelector('.WPStreet').innerHTML + (result[0].partner_address_street).toUpperCase();
                clone.querySelector('.WPCity').innerHTML = (result[0].partner_address_zip) + " - " + (result[0].partner_address_city).toUpperCase();
                clone.querySelector('.imgPartner').src = "data:image/gif;base64," + result[0].partner_image_url;
                modal.find('.WP_RList')[0].append(clone);
            })
        }
        this.$modal_withdrawal.modal('show');
    },


    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    /**
     * Update the shipping address on the order and refresh the UI.
     *
     * @private
     *
     */
    _onClickBtnConfirmWithdrawalPoint: function () {
        if (!this.lastRelaySelected) {
            return;
        }
        this._rpc({
            route: '/website_sale_delivery_withdrawal/update_shipping', params: {
                ...this.lastRelaySelected,
            },
        }).then((o) => {
            $('#address_on_payment').html(o.address);
            this.$modal_withdrawal.modal('hide');
        });
    },
    /**
     * Update the withdrawal point and refresh the UI.
     *
     * @private
     *
     */
    _onClickWithdrawalPoint: async function () {
        const modal = this.$modal_withdrawal = $('#modal_withdrawal');
        const withdrawalCard = document.querySelector('.withdrawalCard')
        modal.find('.WP_RDaysList')[0].innerHTML = ""
        let id = this.$calendar
        // Search the planning for the current withdrawal point selected
        await this._rpc({
            model: 'resource.calendar', method: 'search_read', kwargs: {
                fields: ['attendance_ids'], domain: [['id', '=', id]]
            }
        }).then(async (resource_calendar) => {
            let working_days = [];
            // For each working lines, get the data and update the UI
            for (const calendar_attendance of resource_calendar[0].attendance_ids) {
                await this._rpc({
                    model: 'resource.calendar.attendance', method: 'search_read', kwargs: {
                        fields: ['hour_from', 'hour_to', 'dayofweek', 'hour_delay', 'select_type_delay'],
                        domain: [['id', '=', calendar_attendance]]
                    }
                }).then(async (resource_calendar_attendance) => {
                    let dayOfWeek = parseInt(resource_calendar_attendance[0].dayofweek) + 1
                    let hour_delay = resource_calendar_attendance[0].hour_delay
                    let select_delay_type = resource_calendar_attendance[0].select_type_delay
                    let select_type = this.$select_delivery_period
                    let dateToday = new Date();
                    let lastDate = new Date(dateToday)
                    if (select_type == "day") {
                        lastDate.setDate(lastDate.getDate() + this.$number_delivery_period);
                    } else if (select_type == "week") {
                        lastDate.setDate(lastDate.getDate() + 7 * this.$number_delivery_period);
                    } else {
                        lastDate.setMonth(lastDate.getMonth() + this.$number_delivery_period);
                    }
                    let numOfDays = ((dayOfWeek + 7 - dateToday.getDay()) % 7)
                    let nextDay = new Date(dateToday)
                    let delay = 0
                    nextDay.setDate(nextDay.getDate() + numOfDays)
                    nextDay.setHours(0, 0, 0, 0)
                    while (nextDay.getTime() < lastDate.getTime()) {
                        let dateWithdrawal = {}
                        if (select_delay_type == "hour") {
                            delay = Math.floor(Math.abs(nextDay - dateToday) / 3600000)
                        }
                        if (select_delay_type == "day") {
                            delay = Math.floor(Math.abs(nextDay - dateToday) / (1000 * 60 * 60 * 24))
                        } else if (select_delay_type == "week") {
                            delay = Math.floor(Math.abs(nextDay - dateToday) / (1000 * 60 * 60 * 24 * 7))
                        }
                        if (delay >= hour_delay) {
                            dateWithdrawal.city = this.$city
                            dateWithdrawal.street = this.$street
                            dateWithdrawal.zip = this.$zip
                            dateWithdrawal.country = this.$country
                            dateWithdrawal.hour_from = this._convertFloatToTime(resource_calendar_attendance[0].hour_from)
                            dateWithdrawal.hour_to = this._convertFloatToTime(resource_calendar_attendance[0].hour_to)
                            dateWithdrawal.date = new Date(nextDay)
                            dateWithdrawal.picking_type_id = this.$picking_type_id
                            dateWithdrawal.commitment_date = new Date(nextDay.getFullYear(), nextDay.getMonth(), nextDay.getDate(), dateWithdrawal.hour_from.toString().split(":")[0], dateWithdrawal.hour_from.toString().split(":")[1]).toLocaleDateString("fr", {
                                hour: '2-digit', minute: '2-digit'
                            })
                            working_days.push(dateWithdrawal)
                        }
                        nextDay.setDate(nextDay.getDate() + 7)
                    }
                })
            }
            working_days.sort((a, b) => {
                return new Date(a.date).getTime() - new Date(b.date).getTime();
            }).forEach((sortedDate, index) => {
                let cloneWithdrawal = withdrawalCard.cloneNode(true);
                cloneWithdrawal.classList.remove('d-none')
                cloneWithdrawal.addEventListener('click', () => {
                    if (modal.find('.WP_RDaysList')[0].querySelector('.active')) {
                        modal.find('.WP_RDaysList')[0].querySelector('.active').classList.remove('active');
                    }
                    this.lastRelaySelected = sortedDate;
                    this.$modal_withdrawal.find('#btn_confirm_withdrawal_point').removeClass('disabled');
                    cloneWithdrawal.classList.add('active');
                });
                cloneWithdrawal.querySelector('.WPDay').innerHTML = (new Date(sortedDate.date).toLocaleDateString(undefined, {
                    day: 'numeric'})).toUpperCase()
                cloneWithdrawal.querySelector('.WPMonth').innerHTML = (new Date(sortedDate.date).toLocaleDateString(undefined, {month: 'short'})).toUpperCase()
                cloneWithdrawal.querySelector('.WPHourSlotFrom').innerHTML = sortedDate.hour_from;
                cloneWithdrawal.querySelector('.WPHourSlotTo').innerHTML = sortedDate.hour_to;
                modal.find('.WP_RDaysList')[0].append(cloneWithdrawal);
            })
        })
    },
    _convertFloatToTime: function (number) {
        // Check sign of given number
        var sign = (number >= 0) ? 1 : -1;

        // Set positive value of number of sign negative
        number = number * sign;

        // Separate the int from the decimal part
        var hour = Math.floor(number);
        var decpart = number - hour;

        var min = 1 / 60;
        // Round to nearest minute
        decpart = min * Math.round(decpart / min);

        var minute = Math.floor(decpart * 60) + '';

        // Add padding if need
        if (minute.length < 2) {
            minute = '0' + minute;
        }

        // Add Sign in final result
        sign = sign == 1 ? '' : '-';

        // Concate hours and minutes
        return sign + hour + ':' + minute;
    }
});
