Vue.use(VueCharts);

const vm = new Vue({
    el: '#mrc-ui',
    data: {
        serverUrl: 'nboost/',
        apiRoute: 'status',
        results: [],
        top_deck: [],
        second_deck: [],
        hist_num_request: {
            'last': -1,
            'value': [],
            'label': []
        },
        hist_num_client: {
            'last': -1,
            'value': [],
            'label': []
        },
        max_num_points: 720
    },
    mounted: function () {
        this.$nextTick(function () {
            this.refreshDatabase();
        })
    },
    computed: {
        databaseUrl: function () {
            return this.serverUrl + this.apiRoute
        },
        runningTime: function () {
            return moment(this.results.server_start_time).fromNow()
        }
    },
    methods: {
        histReqLabels: function (long) {
            return this.hist_num_request.label.slice(-(long ? this.max_num_points : 60))
        },
        histReqValues: function (long) {
            return this.hist_num_request.value.slice(-(long ? this.max_num_points : 60))
        },
        histClientLabels: function (long) {
            return this.hist_num_client.label.slice(-(long ? this.max_num_points : 60))
        },
        histClientValues: function (long) {
            return this.hist_num_client.value.slice(-(long ? this.max_num_points : 60))
        },
        refreshDatabase: function () {
            $.ajax({
                url: this.databaseUrl,
                dataType: 'text',
                cache: false,
                beforeSend: function () {
                    console.log("Loading");
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.log(jqXHR);
                    console.log(textStatus);
                    console.log(errorThrown);
                },
                success: function (data) {
                    console.log('Success');
                    vm.results = JSON.parse(data);
                    vm.first_deck = [];
                    vm.second_deck = [];
                    vm.third_deck = [];
                    // add to top deck, high priority
                    console.log(vm.results)
                    Object.keys(vm.results.time).forEach(
                        function (value, index) {
                            prop = vm.results.time[value];
                            if (Object.prototype.hasOwnProperty.call(vm.results.time, value)) {
                                value = value + " (ms)";
                                if (vm.first_deck.length < 4) {
                                    vm.addToDeck(value, prop.avg, vm.first_deck, false);
                                } else {
                                    vm.addToDeck(value, prop.avg, vm.second_deck, false);
                                }
                            }
                        })
                    Object.keys(vm.results.vars).forEach(
                        function (value, index) {
                            prop = vm.results.vars[value];
                            if (Object.prototype.hasOwnProperty.call(vm.results.vars, value)) {
                                vm.addToDeck(value, prop.avg, vm.third_deck, false);
                            }
                        })
                },
                complete: function () {
                    console.log('Finished all tasks');
                }
            });
        },
        addToDeck: function (text, value, deck, round) {
            round = typeof round !== 'undefined' ? round : true;
            round = (!isNaN(parseFloat(value)) && isFinite(value)) ? round : false;
            deck.push({'text': text, 'value': round ? Math.round(value) : value.toFixed(2)})
        },
        addNewTimeData: function (ds, new_val, delta) {
            if (ds.last >= 0)
                ds.value.push(new_val - (delta ? ds.last : 0));
            else
                ds.value.push(0);
            ds.last = new_val;
            ds.label.push(moment().format('h:mm:ss'));
            if (ds.label.length > vm.max_num_points) {
                ds.label = ds.label.slice(-vm.max_num_points);
                ds.value = ds.value.slice(-vm.max_num_points)
            }
        }
    }
});


setInterval(function () {
    vm.refreshDatabase();
    console.log('update database!')
}, 1 * 1000);